#!/usr/bin/env python3
# =============================================================================
# BAKER CHORD N-SERIES PI  --  GMPY-ready, pi-free core
#
# This script computes polygonal approximations to pi from chord lengths only.
# It never forms angles and never uses sin/asin/acos in the computation core.
#
# Geometry:
#   Let c_N = sin(pi/N) = half the side length of the inscribed regular N-gon.
#   The half-perimeter is P_N = N*c_N.
#
#   Tripling the side count is the algebraic chord-trisection step:
#       c_N = 3*c_{3N} - 4*c_{3N}^3,
#   equivalently
#       4*u^3 - 3*u + c_N = 0,  u = c_{3N}.
#
#   The N-series tableau uses scale k=3 to cancel successive even-power error
#   terms of the polygonal half-perimeter sequence.
#
# Pi usage:
#   mp.pi is used ONLY at the end/along the way to count verified digits.
#   It is not used to construct the approximation.
#
# GMPY2:
#   mpmath automatically uses gmpy2 if available. This script reports the
#   detected backend at startup. You want: backend = gmpy.
# =============================================================================

import argparse
import math
import os
import time
from mpmath import mp, mpf

try:
    import mpmath.libmp.backend as mp_backend
    MPMATH_BACKEND = mp_backend.BACKEND
except Exception:
    MPMATH_BACKEND = "unknown"


def parse_args():
    p = argparse.ArgumentParser(
        description="Pi-free chord-trisection polygon computation with scale-3 N-series acceleration."
    )
    p.add_argument("--target-digits", type=int, default=10_000,
                   help="verified decimal digits to target (default: 10000)")
    p.add_argument("--seed", choices=["hexagon", "triangle"], default="hexagon",
                   help="starting polygon: hexagon gives 6->18->54; triangle gives 3->9->27")
    p.add_argument("--guard", type=int, default=None,
                   help="extra decimal precision; default scales mildly with target")
    p.add_argument("--outdir", default=".", help="directory for output files")
    p.add_argument("--report-lines", type=int, default=20,
                   help="about how many progress lines to print")
    p.add_argument("--max-extra-levels", type=int, default=16,
                   help="extra levels beyond asymptotic estimate")
    p.add_argument("--certificate", action="store_true",
                   help="track max cubic residual and derivative root-error bound")
    return p.parse_args()


class NSeriesRow:
    """Memory-frugal one-row Richardson/N-series tableau for scale k=3."""
    def __init__(self):
        self.row = []
        self.denoms = []
        self._p9 = 1

    def feed(self, p):
        j = len(self.row)
        if not self.row:
            self.row = [p]
            return p

        while len(self.denoms) < j:
            self._p9 *= 9
            self.denoms.append(self._p9 - 1)

        prev_old = self.row[0]
        self.row[0] = p

        for s in range(1, j + 1):
            # new diagonal entry: A_s(new) = A_{s-1}(new) + (A_{s-1}(new)-A_{s-1}(old))/(9^s-1)
            new = self.row[s - 1] + (self.row[s - 1] - prev_old) / self.denoms[s - 1]
            if s < len(self.row):
                prev_old = self.row[s]
                self.row[s] = new
            else:
                self.row.append(new)

        return self.row[j]

    @property
    def diag(self):
        return self.row[-1]


def initial_inverse_series(c):
    """Series seed for the small root of 3u - 4u^3 = c."""
    c2 = c * c
    return c * (
        mpf(1) / 3
        + c2 * (
            mpf(4) / 81
            + c2 * (
                mpf(16) / 729
                + c2 * (
                    mpf(256) / 19683
                    + c2 * (mpf(14080) / 1594323)
                )
            )
        )
    )


def trisect_chord(c, tol_abs, certificate=False):
    """
    Given c = c_N, compute u = c_{3N} from 4u^3 - 3u + c = 0.

    This is the algebraic chord-trisection step. It uses Newton iteration only;
    no trigonometric functions and no pi are used.
    """
    u = initial_inverse_series(c)

    # Newton convergence to the current working precision.
    # For this root range u < 1/2, f'(u)=12u^2-3 stays safely away from zero
    # for the hexagon and triangle seeds and all later trisections.
    for _ in range(80):
        u2 = u * u
        f = 4 * u * u2 - 3 * u + c
        fp = 12 * u2 - 3
        step = f / fp
        u -= step
        if abs(step) <= tol_abs:
            break

    if not certificate:
        return u, None, None

    residual = abs(4 * u**3 - 3 * u + c)
    deriv_abs = abs(12 * u**2 - 3)
    root_bound = residual / deriv_abs if deriv_abs != 0 else mp.inf
    return u, residual, root_bound


def verified_digits(value, pi_ref, target):
    err = abs(value - pi_ref)
    if err == 0:
        return target
    d = int(mp.floor(-mp.log10(err)))
    if d < 0:
        return 0
    return min(target, d)


def main():
    args = parse_args()
    target = args.target_digits
    guard = args.guard if args.guard is not None else max(100, target // 5000 + 100)
    mp.dps = target + guard

    # Empirical asymptotic estimate: verified digits grow roughly like
    # (1/2)*L^2*log10(9) for the diagonal scale-3 tableau.
    lmax = int(math.sqrt(2 * target / 0.9542425094393249)) + args.max_extra_levels
    report_every = max(1, lmax // max(1, args.report_lines))

    os.makedirs(args.outdir, exist_ok=True)

    if args.seed == "hexagon":
        c = mpf(1) / 2     # sin(pi/6), algebraic hexagon seed, no pi
        n = 6
        seed_base = 6
        seed_desc = "hexagon: 6 -> 18 -> 54 -> ..."
    else:
        c = mp.sqrt(3) / 2 # sin(pi/3), algebraic triangle seed, no pi
        n = 3
        seed_base = 3
        seed_desc = "triangle: 3 -> 9 -> 27 -> ..."

    tol_abs = mpf(10) ** (-(mp.dps - 20))

    print("=" * 76)
    print(f"BAKER CHORD N-SERIES PI   target = {target:,} digits")
    print(f"precision = {mp.dps:,} dps   guard = {guard:,}   max levels = {lmax}")
    print(f"mpmath backend = {MPMATH_BACKEND}")
    print(f"seed = {seed_desc}")
    print("core trig usage = none   mp.pi usage = verification only")
    print("=" * 76)

    print("computing reference pi for verification...")
    tref = time.time()
    pi_ref = mp.pi
    print(f"  reference ready in {time.time() - tref:.3f}s\n")

    acc = NSeriesRow()
    best_d = -1
    best_val = None
    best_level = 0
    stall = 0
    max_residual = mpf(0)
    max_root_bound = mpf(0)
    t0 = time.time()

    print(f"{'level':>6} {'N form':>14} {'digits(N)':>10} {'verified digits':>16} {'elapsed':>10}")
    print("-" * 76)

    j = 0
    for j in range(lmax + 1):
        acc.feed(n * c)  # half-perimeter P_N = N*c_N
        d = verified_digits(acc.diag, pi_ref, target)

        if d > best_d:
            best_d = d
            best_val = +acc.diag
            best_level = j
            stall = 0
        else:
            stall += 1

        if j % report_every == 0 or d >= target:
            n_form = f"{seed_base}*3^{j}"
            n_digits = len(str(n))
            print(f"{j:6d} {n_form:>14} {n_digits:10d} {d:16,} {time.time() - t0:9.1f}s")

        if d >= target or stall >= 6:
            break

        c, residual, root_bound = trisect_chord(c, tol_abs, args.certificate)
        if args.certificate:
            if residual > max_residual:
                max_residual = residual
            if root_bound > max_root_bound:
                max_root_bound = root_bound
        n *= 3

    elapsed = time.time() - t0
    status = "PASS" if best_d >= target else "PLATEAU"

    print("-" * 76)
    print(f"status: {status}")
    print(f"VERIFIED CORRECT DIGITS: {best_d:,}")
    print(f"best level: {best_level}   levels used: {j + 1}   total time: {elapsed:.1f}s")
    if args.certificate:
        print(f"max cubic residual: {mp.nstr(max_residual, 8)}")
        print(f"max derivative root-error bound: {mp.nstr(max_root_bound, 8)}")

    digits_path = os.path.join(args.outdir, f"baker_chord_nseries_{best_d}_digits.txt")
    summary_path = os.path.join(args.outdir, f"baker_chord_nseries_summary_{target}.txt")

    with open(digits_path, "w", encoding="utf-8") as f:
        f.write(f"Baker chord N-series geometric pi -- {best_d} verified correct digits\n")
        f.write("pi-free core: algebraic chord trisection + scale-3 N-series acceleration\n")
        f.write(f"seed: {seed_desc}\n")
        f.write(f"mpmath backend: {MPMATH_BACKEND}\n")
        f.write("=" * 76 + "\n")
        f.write(mp.nstr(best_val, best_d + 5))
        f.write("\n")

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("Baker chord N-series pi-free run summary\n")
        f.write("=" * 76 + "\n")
        f.write(f"status: {status}\n")
        f.write(f"target digits: {target}\n")
        f.write(f"verified digits: {best_d}\n")
        f.write(f"precision dps: {mp.dps}\n")
        f.write(f"guard digits: {guard}\n")
        f.write(f"mpmath backend: {MPMATH_BACKEND}\n")
        f.write(f"seed: {seed_desc}\n")
        f.write(f"best level: {best_level}\n")
        f.write(f"levels used: {j + 1}\n")
        f.write(f"elapsed seconds: {elapsed:.6f}\n")
        f.write("core trig usage: none\n")
        f.write("mp.pi usage: verification only\n")
        if args.certificate:
            f.write(f"max cubic residual: {mp.nstr(max_residual, 30)}\n")
            f.write(f"max derivative root-error bound: {mp.nstr(max_root_bound, 30)}\n")

    print(f"saved digits to:  {digits_path}")
    print(f"saved summary to: {summary_path}")
    print("=" * 76)


if __name__ == "__main__":
    main()
