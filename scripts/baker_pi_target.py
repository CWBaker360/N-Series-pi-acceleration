#!/usr/bin/env python3
# =============================================================================
# BAKER N-SERIES PI  --  pi-free geometric computation  (resumable)
#
#                   >>>  EDIT ONE NUMBER BELOW AND RUN  <<<
#
#   TARGET_DIGITS = 10_000      # ten thousand
#   TARGET_DIGITS = 100_000     # hundred thousand
#   TARGET_DIGITS = 1_000_000   # one million
#   TARGET_DIGITS = 1_500_000   # the real 1.5 million
#
# Everything else (levels, precision) is sized automatically.
#
# HOW IT WORKS (no pi is ever used to COMPUTE the answer):
#   * polygons are built by TRISECTION -- each step triples the side count by
#     solving the triple-angle cubic (the Baker trisection step);
#   * the chords are summed into the inscribed half-perimeter n*sin(pi/n);
#   * the Baker N-series operator (scale k=3, denominators 9^s-1) accelerates it.
#   The seed is the algebraic triangle side sqrt(3); pi appears ONLY at the end,
#   to verify how many digits are correct.
#
# RESUMABLE: progress is checkpointed every CHECKPOINT_EVERY levels.  If the run
# is interrupted (sleep, reboot, power loss, Ctrl-C), just launch it again with
# the SAME TARGET_DIGITS and it picks up where it left off instead of restarting.
# =============================================================================

import math, time, pickle, os, sys
from mpmath import mp, mpf

# ============================================================================
TARGET_DIGITS = 1_500_000        # <-- EDIT THIS
# ============================================================================

CHECKPOINT_EVERY = 25           # save resume-state every this many levels
KEEP_CHECKPOINT  = False        # True => keep the .ckpt file after finishing
STALL_MAX        = 40           # stop after this many levels with no new digits

L_MAX   = int(math.sqrt(2 * TARGET_DIGITS / 0.954242509)) + 40   # predicted levels (margin bumped)
GUARD   = max(200, 6 * L_MAX)                                    # tableau-cancellation headroom
mp.dps  = TARGET_DIGITS + GUARD
REPORT_EVERY = max(1, L_MAX // 20)
CKPT = f"baker_pi_{TARGET_DIGITS}.ckpt"

# ----------------------- speed lever: gmpy2 check ---------------------------
try:
    import gmpy2  # noqa: F401
    _HAVE_GMPY2 = True
except Exception:
    _HAVE_GMPY2 = False

# ----------------------- trisection step (pi-free) --------------------------
def trisect_sin(c):
    """small positive root of 4u^3 - 3u + c = 0, polished to full precision."""
    u = c / 3
    for _ in range(100):
        step = (4*u**3 - 3*u + c) / (12*u*u - 3)
        u -= step
        if step == 0 or abs(step) < abs(u) * mp.eps * 16:
            break
    return u

# ------------- memory-frugal N-series accelerator (one row, k=3) -------------
class NSeriesRow:
    def __init__(self):
        self.row = []
        self.denoms = []      # 9^s - 1 (exact ints), rebuilt lazily
        self._p9 = 1
    def feed(self, p):
        j = len(self.row)
        if not self.row:
            self.row = [p]; return p
        while len(self.denoms) < j:
            self._p9 *= 9; self.denoms.append(self._p9 - 1)
        prev_old = self.row[0]; self.row[0] = p
        for s in range(1, j + 1):
            new = self.row[s-1] + (self.row[s-1] - prev_old) / self.denoms[s-1]
            if s < len(self.row):
                prev_old = self.row[s]; self.row[s] = new
            else:
                self.row.append(new)
        return self.row[j]
    @property
    def diag(self):
        return self.row[-1]

# ------------------------------ checkpointing -------------------------------
def save_checkpoint(next_j, n, c, acc, best_d, best_val, stall, elapsed):
    """Atomic write: dump to a temp file, then replace -- safe against a crash
       mid-write (a power loss never corrupts the live checkpoint)."""
    state = {
        "target": TARGET_DIGITS, "guard": GUARD,
        "next_j": next_j, "n": n, "c": c,
        "row": acc.row, "best_d": best_d, "best_val": best_val,
        "stall": stall, "elapsed": elapsed,
    }
    tmp = CKPT + ".tmp"
    with open(tmp, "wb") as f:
        pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(tmp, CKPT)

def load_checkpoint():
    if not os.path.exists(CKPT):
        return None
    try:
        with open(CKPT, "rb") as f:
            state = pickle.load(f)
    except Exception as e:
        print(f"  (checkpoint unreadable: {e} -- starting fresh)")
        return None
    if state.get("target") != TARGET_DIGITS:   # belongs to a different target
        return None
    return state

# --------------------------------- run --------------------------------------
print("=" * 70)
print(f"BAKER N-SERIES PI   target = {TARGET_DIGITS:,} digits")
print(f"precision = {mp.dps:,} dps   max levels = {L_MAX}   (pi-free)")
if not _HAVE_GMPY2:
    print("! gmpy2 NOT found -- arithmetic will be much slower.")
    print("!   For large/overnight runs install it first:  pip install gmpy2")
print("=" * 70)

print("computing reference pi for verification...")
t0 = time.time()
PI_REF = mp.pi
print(f"  reference ready in {time.time()-t0:.1f}s")

# resume or fresh start
state = load_checkpoint()
acc = NSeriesRow()
if state is not None:
    acc.row = state["row"]             # denoms/_p9 rebuild lazily on next feed
    j0      = state["next_j"]
    n       = state["n"]
    c       = state["c"]
    best_d  = state["best_d"]
    best_val= state["best_val"]
    stall   = state["stall"]
    base_elapsed = state["elapsed"]
    print(f"  RESUMING from checkpoint at level {j0} "
          f"(best so far: {best_d:,} digits)\n")
else:
    j0 = 0
    n  = 3
    c  = mp.sqrt(3) / 2                 # sin(pi/3): algebraic seed, NO pi
    best_d, best_val, stall = -1, None, 0
    base_elapsed = 0.0

t0 = time.time()
def elapsed():
    return base_elapsed + (time.time() - t0)

print(f"{'level':>6} {'verified digits':>16} {'elapsed':>11}")
print("-" * 70)
j = j0
for j in range(j0, L_MAX + 1):
    acc.feed(n * c)                       # inscribed half-perimeter = n*sin(pi/n)
    err = abs(acc.diag - PI_REF)
    d   = TARGET_DIGITS if err == 0 else min(TARGET_DIGITS, int(mp.floor(-mp.log10(err))))
    if d > best_d:
        best_d, best_val, stall = d, acc.diag, 0
    else:
        stall += 1
    if j % REPORT_EVERY == 0 or d >= TARGET_DIGITS:
        print(f"{j:>6} {d:>16,} {elapsed():>10.1f}s")
    if d >= TARGET_DIGITS or stall >= STALL_MAX:   # hit target, or precision plateau
        break
    c = trisect_sin(c)                     # TRISECTION advances the geometry
    n *= 3
    if (j + 1) % CHECKPOINT_EVERY == 0:    # save resume-state (atomic)
        save_checkpoint(j + 1, n, c, acc, best_d, best_val, stall, elapsed())

print("-" * 70)
print(f"VERIFIED CORRECT DIGITS: {best_d:,}")
print(f"levels used: {j+1}    total time: {elapsed():.1f}s")

out = f"baker_pi_{best_d}_digits.txt"
with open(out, "w") as f:
    f.write(f"Baker N-series geometric pi  --  {best_d} verified correct digits\n")
    f.write("pi-free: trisection-built polygons + N-series acceleration (k=3)\n")
    f.write("=" * 70 + "\n")
    f.write(mp.nstr(best_val, best_d + 5))
print(f"saved to {out}")

if not KEEP_CHECKPOINT and os.path.exists(CKPT):
    os.remove(CKPT)                        # clean finish: drop the resume file
print("=" * 70)
