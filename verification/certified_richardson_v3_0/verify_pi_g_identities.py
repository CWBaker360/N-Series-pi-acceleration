#!/usr/bin/env python3
"""Referee-safe cross-domain numerical consistency checks for Baker's pi_g.

The algebraic construction is imported from ``pi_g_construction.py``.  The
classical constant pi is used only after construction, for a separately
labelled reference comparison.  It is never used to choose or alter pi_g.

The first eight checks are cross-domain residuals or finite enclosures.  The
ninth check is a rigorous a priori certificate for the constructed Richardson
value itself: exact rational cubic brackets are propagated through the complete
tableau and combined with an analytic sine-series remainder bound.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import mpmath
from mpmath import mp

from pi_g_construction import PiGConstructionResult, compute_pi_g
from certified_richardson import (
    RichardsonCertificate,
    build_richardson_certificate,
)


DEFAULT_WORK_DPS = 120
DEFAULT_LEVEL_COUNT = 11
DIRECT_RESIDUAL_TOLERANCE_TEXT = "1e-65"
CERTIFIED_ABSOLUTE_ERROR_TARGET_TEXT = "1e-80"
DEFAULT_CERTIFICATE_BITS = 300


@dataclass(frozen=True)
class CheckResult:
    identifier: str
    name: str
    domain: str
    method: str
    observed_metric_name: str
    observed_metric: mp.mpf
    acceptance_bound: mp.mpf
    passed: bool
    details: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sci(value: mp.mpf, digits: int = 18) -> str:
    value = mp.mpf(value)
    if value == 0:
        return "0"
    return mp.nstr(value, digits, min_fixed=0, max_fixed=0)


def dec(value: mp.mpf, digits: int = 80) -> str:
    return mp.nstr(mp.mpf(value), digits)


def fraction_to_mpf(value: object) -> mp.mpf:
    """Convert a fractions.Fraction to mp.mpf in the active precision."""

    return mp.mpf(value.numerator) / mp.mpf(value.denominator)


def check_gaussian_integral(pi_g: mp.mpf, work_dps: int) -> CheckResult:
    """Check 2*integral_0^A exp(-x^2) dx against sqrt(pi_g).

    The omitted two-sided tail obeys

        2*integral_A^infinity exp(-x^2) dx <= exp(-A^2)/A.

    A repeat-precision difference is added as a conservative numerical
    stability allowance for the finite quadrature.
    """

    cutoff = mp.mpf(13)

    with mp.workdps(work_dps):
        integral_low = 2 * mp.quad(lambda x: mp.exp(-(x * x)), [0, cutoff])
    with mp.workdps(work_dps + 30):
        integral_high = 2 * mp.quad(lambda x: mp.exp(-(x * x)), [0, cutoff])

    integral_high = +integral_high
    stability = abs(integral_high - integral_low)
    tail_bound = mp.exp(-(cutoff * cutoff)) / cutoff
    roundoff = mp.power(10, -(work_dps - 15))
    allowance = tail_bound + 10 * stability + roundoff
    residual = abs(mp.sqrt(pi_g) - integral_high)

    return CheckResult(
        identifier="G1",
        name="Gaussian integral",
        domain="Analysis / probability",
        method="finite quadrature, analytic two-sided tail bound, repeat-precision stability check",
        observed_metric_name="abs(sqrt(pi_g) - finite integral)",
        observed_metric=residual,
        acceptance_bound=allowance,
        passed=residual <= allowance,
        details=(
            f"cutoff A=13; analytic tail<={sci(tail_bound)}; "
            f"repeat-precision delta={sci(stability)}"
        ),
    )


def check_basel(pi_g: mp.mpf) -> CheckResult:
    """Check zeta(2)=pi_g^2/6 using a rapidly convergent positive series.

        zeta(2) = 3 * sum_{n>=1} 1/(n^2 * binom(2n,n)).

    The term ratio is n^2/((2n+2)(2n+1)) < 1/4, so the omitted zeta tail
    after n=N is smaller than 4 times the first omitted unscaled term.
    """

    terms = 120
    term = mp.mpf(1) / 2  # n=1
    partial_unscaled = mp.mpf(0)

    for n in range(1, terms + 1):
        partial_unscaled += term
        term *= mp.mpf(n * n) / ((2 * n + 2) * (2 * n + 1))

    partial = 3 * partial_unscaled
    tail_bound = 4 * term
    roundoff = mp.power(10, -(mp.dps - 15))
    residual = abs((pi_g * pi_g) / 6 - partial)
    allowance = tail_bound + roundoff

    return CheckResult(
        identifier="B2",
        name="Basel identity",
        domain="Number theory",
        method="central-binomial zeta(2) series with geometric ratio tail bound",
        observed_metric_name="abs(pi_g^2/6 - accelerated partial sum)",
        observed_metric=residual,
        acceptance_bound=allowance,
        passed=residual <= allowance,
        details=f"terms={terms}; explicit tail<={sci(tail_bound)}",
    )


def check_leibniz(pi_g: mp.mpf) -> CheckResult:
    """Check pi_g/4 using the Euler-transformed Gregory-Leibniz series.

    If I_0=1 and I_{k+1}=2(k+1)I_k/(2k+3), then

        pi/4 = sum_{k>=0} I_k/2^(k+1).

    Consecutive transformed terms have ratio (k+1)/(2k+3)<1/2, so the
    omitted tail is smaller than twice the first omitted term.
    """

    terms = 230
    term = mp.mpf(1) / 2
    partial = mp.mpf(0)

    for k in range(terms):
        partial += term
        term *= mp.mpf(k + 1) / (2 * k + 3)

    tail_bound = 2 * term
    roundoff = mp.power(10, -(mp.dps - 15))
    residual = abs(pi_g / 4 - partial)
    allowance = tail_bound + roundoff

    return CheckResult(
        identifier="L3",
        name="Gregory-Leibniz identity",
        domain="Series",
        method="Euler-transformed alternating series with explicit ratio tail bound",
        observed_metric_name="abs(pi_g/4 - transformed partial sum)",
        observed_metric=residual,
        acceptance_bound=allowance,
        passed=residual <= allowance,
        details=f"transformed terms={terms}; explicit tail<={sci(tail_bound)}",
    )


def check_wallis(pi_g: mp.mpf) -> CheckResult:
    """Check pi_g/2 against standard finite Wallis bounds.

        W_N < pi/2 < W_N * (2N+1)/(2N).
    """

    terms = 100_000
    product = mp.mpf(1)
    for n in range(1, terms + 1):
        n_mp = mp.mpf(n)
        product *= (4 * n_mp * n_mp) / (4 * n_mp * n_mp - 1)

    lower = product
    upper = product * mp.mpf(2 * terms + 1) / (2 * terms)
    target = pi_g / 2
    lower_gap = target - lower
    upper_gap = upper - target
    violation = max(mp.mpf(0), -lower_gap, -upper_gap)
    roundoff = mp.power(10, -(mp.dps - 15))

    return CheckResult(
        identifier="W4",
        name="Wallis product",
        domain="Infinite products",
        method="standard two-sided finite Wallis enclosure",
        observed_metric_name="interval violation",
        observed_metric=violation,
        acceptance_bound=roundoff,
        passed=(lower_gap >= 0 and upper_gap >= 0),
        details=(
            f"terms={terms}; enclosure width={sci(upper-lower)}; "
            f"lower gap={sci(lower_gap)}; upper gap={sci(upper_gap)}"
        ),
    )


def check_stirling_robbins(pi_g: mp.mpf) -> CheckResult:
    """Check exact factorials against Robbins' sharpened Stirling bounds."""

    test_values = (10, 100, 1000, 10_000)
    minimum_margin = mp.inf
    worst_n = None
    violations: list[mp.mpf] = []

    for n in test_values:
        log_factorial = mp.fsum(mp.log(k) for k in range(1, n + 1))
        base = mp.mpf("0.5") * mp.log(2 * pi_g * n) + n * (mp.log(n) - 1)
        lower = base + mp.mpf(1) / (12 * n + 1)
        upper = base + mp.mpf(1) / (12 * n)
        margin = min(log_factorial - lower, upper - log_factorial)
        violation = max(mp.mpf(0), -margin)
        violations.append(violation)
        if margin < minimum_margin:
            minimum_margin = margin
            worst_n = n

    maximum_violation = max(violations)
    roundoff = mp.power(10, -(mp.dps - 15))

    return CheckResult(
        identifier="S5",
        name="Robbins-Stirling bounds",
        domain="Asymptotics / combinatorics",
        method="exact log-factorial sum tested inside Robbins' two-sided bounds",
        observed_metric_name="maximum bound violation",
        observed_metric=maximum_violation,
        acceptance_bound=roundoff,
        passed=maximum_violation == 0,
        details=(
            f"n={list(test_values)}; smallest positive log-margin={sci(minimum_margin)} "
            f"at n={worst_n}"
        ),
    )


def check_gamma_half(pi_g: mp.mpf) -> CheckResult:
    residual = abs(mp.gamma(mp.mpf("0.5")) ** 2 - pi_g)
    return CheckResult(
        identifier="H6",
        name="Gamma at one half",
        domain="Special functions",
        method="direct residual gamma(1/2)^2 - pi_g",
        observed_metric_name="abs(gamma(1/2)^2 - pi_g)",
        observed_metric=residual,
        acceptance_bound=mp.mpf(DIRECT_RESIDUAL_TOLERANCE_TEXT),
        passed=residual <= mp.mpf(DIRECT_RESIDUAL_TOLERANCE_TEXT),
        details="library-level cross-check; not claimed to be algorithmically independent of pi",
    )


def check_euler_identity(pi_g: mp.mpf) -> CheckResult:
    residual = abs(mp.exp(mp.j * pi_g) + 1)
    return CheckResult(
        identifier="E7",
        name="Euler identity",
        domain="Complex analysis",
        method="direct complex residual exp(i*pi_g)+1",
        observed_metric_name="abs(exp(i*pi_g)+1)",
        observed_metric=residual,
        acceptance_bound=mp.mpf(DIRECT_RESIDUAL_TOLERANCE_TEXT),
        passed=residual <= mp.mpf(DIRECT_RESIDUAL_TOLERANCE_TEXT),
        details="no classical pi appears in the tested expression",
    )


def check_reflection_formula(pi_g: mp.mpf) -> CheckResult:
    points = (mp.mpf(1) / 3, mp.mpf(2) / 5, mp.mpf(1) / 7)
    maximum_normalized_residual = mp.mpf(0)
    worst_point = None

    for z in points:
        lhs = mp.gamma(z) * mp.gamma(1 - z)
        rhs = pi_g / mp.sin(pi_g * z)
        normalized = abs(lhs - rhs) / max(mp.mpf(1), abs(lhs), abs(rhs))
        if normalized > maximum_normalized_residual:
            maximum_normalized_residual = normalized
            worst_point = z

    return CheckResult(
        identifier="R8",
        name="Euler reflection formula",
        domain="Complex analysis / special functions",
        method="direct normalized residual at three rational arguments",
        observed_metric_name="maximum normalized reflection residual",
        observed_metric=maximum_normalized_residual,
        acceptance_bound=mp.mpf(DIRECT_RESIDUAL_TOLERANCE_TEXT),
        passed=maximum_normalized_residual <= mp.mpf(DIRECT_RESIDUAL_TOLERANCE_TEXT),
        details=f"z in {{1/3, 2/5, 1/7}}; worst z={mp.nstr(worst_point, 12)}",
    )



def check_richardson_enclosure(
    certificate: RichardsonCertificate,
) -> CheckResult:
    """Rigorous R9 enclosure for the production Richardson value.

    The certificate is computed with exact rational arithmetic.  It combines
    (i) the distance between the finite mpmath production value and the exact
    interval-propagated tableau, and (ii) an analytic Taylor-remainder bound
    for the exact polygon tableau, using only the rational inequality pi<22/7.
    """

    production_bound = fraction_to_mpf(
        certificate.production_to_exact_tableau_bound
    )
    analytic_bound = fraction_to_mpf(
        certificate.analytic_tableau_to_pi_bound
    )
    total_bound = fraction_to_mpf(certificate.total_pi_error_bound)
    target = mp.mpf(CERTIFIED_ABSOLUTE_ERROR_TARGET_TEXT)

    return CheckResult(
        identifier="R9",
        name="Certified Richardson enclosure",
        domain="Approximation theory / exact arithmetic",
        method=(
            "exact rational cubic interval propagation, exact Richardson weights, "
            "and analytic sine remainder with pi<22/7"
        ),
        observed_metric_name="certified abs(production pi_g - pi) upper bound",
        observed_metric=total_bound,
        acceptance_bound=target,
        passed=(total_bound < target and certificate.production_value_inside_tableau_interval),
        details=(
            f"analytic tableau bound={sci(analytic_bound, 24)}; "
            f"production/tableau bound={sci(production_bound, 24)}; "
            f"bisection bits={certificate.bisection_bits}; production inside exact tableau interval={certificate.production_value_inside_tableau_interval}; "
            f"certified absolute decimal places={certificate.certified_decimal_places}"
        ),
    )


def write_csv(path: Path, checks: Iterable[CheckResult]) -> None:
    fieldnames = [
        "identifier",
        "name",
        "domain",
        "method",
        "observed_metric_name",
        "observed_metric",
        "acceptance_bound",
        "passed",
        "details",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for check in checks:
            writer.writerow(
                {
                    "identifier": check.identifier,
                    "name": check.name,
                    "domain": check.domain,
                    "method": check.method,
                    "observed_metric_name": check.observed_metric_name,
                    "observed_metric": sci(check.observed_metric, 30),
                    "acceptance_bound": sci(check.acceptance_bound, 30),
                    "passed": check.passed,
                    "details": check.details,
                }
            )


def build_output_text(
    construction: PiGConstructionResult,
    certificate: RichardsonCertificate,
    checks: list[CheckResult],
    reference_error: mp.mpf,
    overall_verdict: str,
) -> str:
    lines: list[str] = []
    emit = lines.append

    emit("CERTIFIED PI_G CONSTRUCTION AND CROSS-DOMAIN VERIFICATION SUITE")
    emit("=" * 72)
    emit(f"working precision: {construction.work_dps} decimal digits")
    emit(
        f"construction inputs: L=0,...,{construction.maximum_level} "
        f"({construction.level_count} polygon values)"
    )
    emit("construction selection: final N-series value, deterministic, no pi oracle")
    emit(f"pi_g: {dec(construction.value, 90)}")
    emit(f"reference pi: {dec(mp.pi, 90)}")
    emit(f"diagnostic abs(pi_g-pi): {sci(reference_error, 30)}")
    emit(
        "internal last-diagonal delta (diagnostic only): "
        + sci(construction.internal_last_diagonal_delta, 30)
    )
    emit(
        "R9 analytic tableau-to-pi bound: "
        + sci(fraction_to_mpf(certificate.analytic_tableau_to_pi_bound), 30)
    )
    emit(
        "R9 production-to-exact-tableau bound: "
        + sci(fraction_to_mpf(certificate.production_to_exact_tableau_bound), 30)
    )
    emit(
        "R9 total certified abs(pi_g-pi) bound: "
        + sci(fraction_to_mpf(certificate.total_pi_error_bound), 30)
    )
    emit(
        "R9 certified absolute decimal places: "
        + str(certificate.certified_decimal_places)
    )
    emit("maximum cubic root bracket width: " + sci(construction.maximum_root_bracket_width, 30))
    emit(
        "maximum cubic midpoint polynomial residual: "
        + sci(construction.maximum_root_polynomial_residual, 30)
    )
    emit("")
    emit("DIRECT CHECK RESULTS")
    emit("-" * 72)
    for check in checks:
        emit(
            f"{check.identifier} {check.name}: "
            f"observed={sci(check.observed_metric, 24)}; "
            f"bound={sci(check.acceptance_bound, 24)}; "
            f"status={'PASS' if check.passed else 'FAIL'}"
        )
        emit(f"    method: {check.method}")
        emit(f"    details: {check.details}")
    emit("")
    emit(f"checks passed: {sum(c.passed for c in checks)}/{len(checks)}")
    emit(f"overall_verdict: {overall_verdict}")
    emit("")
    emit("CLAIM BOUNDARY")
    emit("-" * 72)
    emit(
        "R9 is a rigorous finite-value enclosure derived without a numerical pi oracle. "
        "The exact limiting sequence is identified with the classical inscribed-polygon "
        "sequence by the triple-angle theorem. Checks H6, E7, and R8 remain library-level "
        "consistency checks and are not claimed to be algorithmically independent."
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="pi_g_verification_output")
    parser.add_argument("--work-dps", type=int, default=DEFAULT_WORK_DPS)
    parser.add_argument("--level-count", type=int, default=DEFAULT_LEVEL_COUNT)
    parser.add_argument("--certificate-bits", type=int, default=DEFAULT_CERTIFICATE_BITS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    mp.dps = args.work_dps
    construction = compute_pi_g(level_count=args.level_count, work_dps=args.work_dps)
    certificate = build_richardson_certificate(
        production_value=construction.value,
        level_count=args.level_count,
        bisection_bits=args.certificate_bits,
    )

    # This comparison is performed only after pi_g has been constructed and fixed.
    reference_error = abs(construction.value - mp.pi)

    checks = [
        check_richardson_enclosure(certificate),
        check_gaussian_integral(construction.value, args.work_dps),
        check_basel(construction.value),
        check_leibniz(construction.value),
        check_wallis(construction.value),
        check_stirling_robbins(construction.value),
        check_gamma_half(construction.value),
        check_euler_identity(construction.value),
        check_reflection_formula(construction.value),
    ]

    all_pass = all(check.passed for check in checks)
    overall_verdict = (
        "PI_G_CERTIFIED_CONSTRUCTION_AND_CONSISTENCY_CHECKS_PASS"
        if all_pass
        else "PI_G_CERTIFIED_CONSTRUCTION_AND_CONSISTENCY_CHECKS_FAIL"
    )

    csv_path = output_dir / "pi_g_verification_results.csv"
    output_path = output_dir / "pi_g_verification_output.txt"
    summary_path = output_dir / "pi_g_verification_summary.txt"
    manifest_path = output_dir / "pi_g_verification_manifest.json"

    write_csv(csv_path, checks)
    output_text = build_output_text(construction, certificate, checks, reference_error, overall_verdict)
    output_path.write_text(output_text, encoding="utf-8")

    summary_lines = [
        "Baker pi_g certified construction and verification summary",
        "=" * 58,
        f"checks_passed: {sum(c.passed for c in checks)}/{len(checks)}",
        f"working_precision_decimal_digits: {args.work_dps}",
        f"level_count: {args.level_count}",
        f"maximum_level: {args.level_count - 1}",
        f"diagnostic_abs_pi_g_minus_pi: {sci(reference_error, 30)}",
        "internal_last_diagonal_delta_diagnostic: " + sci(construction.internal_last_diagonal_delta, 30),
        "r9_analytic_tableau_to_pi_bound: " + sci(fraction_to_mpf(certificate.analytic_tableau_to_pi_bound), 30),
        "r9_production_to_exact_tableau_bound: " + sci(fraction_to_mpf(certificate.production_to_exact_tableau_bound), 30),
        "r9_total_certified_abs_error_bound: " + sci(fraction_to_mpf(certificate.total_pi_error_bound), 30),
        f"r9_certified_absolute_decimal_places: {certificate.certified_decimal_places}",
        f"overall_verdict: {overall_verdict}",
        "claim_boundary: R9 is rigorous; H6, E7, and R8 are library-level consistency checks.",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    script_dir = Path(__file__).resolve().parent
    construction_script = script_dir / "pi_g_construction.py"
    verification_script = Path(__file__).resolve()

    manifest = {
        "title": "Certified algebraic construction and cross-domain checks for Baker's pi_g",
        "working_precision_decimal_digits": args.work_dps,
        "level_count": args.level_count,
        "maximum_level": args.level_count - 1,
        "pi_g_decimal": dec(construction.value, 100),
        "reference_pi_decimal": dec(mp.pi, 100),
        "diagnostic_abs_pi_g_minus_pi": sci(reference_error, 40),
        "internal_last_diagonal_delta_diagnostic": sci(construction.internal_last_diagonal_delta, 40),
        "r9_certificate": {
            "bisection_bits": certificate.bisection_bits,
            "production_inside_exact_tableau_interval": certificate.production_value_inside_tableau_interval,
            "analytic_tableau_to_pi_bound": sci(fraction_to_mpf(certificate.analytic_tableau_to_pi_bound), 50),
            "production_to_exact_tableau_bound": sci(fraction_to_mpf(certificate.production_to_exact_tableau_bound), 50),
            "total_certified_abs_error_bound": sci(fraction_to_mpf(certificate.total_pi_error_bound), 50),
            "certified_absolute_decimal_places": certificate.certified_decimal_places,
            "acceptance_target": CERTIFIED_ABSOLUTE_ERROR_TARGET_TEXT,
        },
        "maximum_root_bracket_width": sci(construction.maximum_root_bracket_width, 40),
        "maximum_root_polynomial_residual": sci(
            construction.maximum_root_polynomial_residual, 40
        ),
        "software_requirements": {
            "python": ">=3.10",
            "mpmath": "==1.3.0",
        },
        "checks": [
            {
                **{
                    key: value
                    for key, value in asdict(check).items()
                    if key not in {"observed_metric", "acceptance_bound"}
                },
                "observed_metric": sci(check.observed_metric, 40),
                "acceptance_bound": sci(check.acceptance_bound, 40),
            }
            for check in checks
        ],
        "all_checks_pass": all_pass,
        "overall_verdict": overall_verdict,
        "claim_boundary": (
            "R9 rigorously encloses the finite constructed value using exact rational intervals "
            "and an analytic remainder. H6, E7, and R8 are not asserted to be "
            "implementation-independent."
        ),
        "sha256": {
            "pi_g_construction.py": sha256_file(construction_script),
            "certified_richardson.py": sha256_file(script_dir / "certified_richardson.py"),
            "verify_pi_g_identities.py": sha256_file(verification_script),
            "pi_g_verification_results.csv": sha256_file(csv_path),
            "pi_g_verification_output.txt": sha256_file(output_path),
            "pi_g_verification_summary.txt": sha256_file(summary_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(output_text, end="")
    print(f"output_dir: {output_dir}")
    print(f"manifest_sha256: {sha256_file(manifest_path)}")

    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
