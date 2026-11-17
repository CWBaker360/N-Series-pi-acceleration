BAKER PI_G CERTIFIED VERIFICATION PACKAGE - VERSION 3.0
=======================================================

Purpose
-------
This package supplies two complementary lanes for Baker's algebraic
Archimedean pi approximation.

1. Production lane
   pi_g_construction.py begins from the exact hexagon seed c_0 = 1/2,
   repeatedly selects the small positive root of

       4 u^3 - 3 u + c = 0,

   builds the tripled polygon sequence, and applies the complete scale-3
   Richardson/N-Series tableau. The production construction does not call
   mp.pi, mp.sin, mp.cos, or any trigonometric oracle.

2. Certification lane
   certified_richardson.py uses only exact Python integers and Fraction
   objects. It propagates cubic-root intervals through every level, propagates
   the resulting polygon intervals through the complete Richardson tableau,
   verifies the Richardson moment conditions exactly, and combines that
   interval with an analytic sine-series remainder using pi < 22/7.

The canonical Version 3.0 run proves

    abs(pi_g - pi) < 3.406285758314118e-81,

which gives at least 80 decimal places of absolute accuracy. The former
last-diagonal delta remains in the output only as a diagnostic; it is no longer
used as an error bound.

What changed from Version 2.1
-----------------------------
- Added the rigorous R9 Richardson/tableau enclosure.
- Added exact rational interval propagation through recursively uncertain
  cubic coefficients.
- Added exact rational propagation through all Richardson stages.
- Added exact verification of constant preservation and cancellation of the
  N^-2, ..., N^-20 modes for the canonical 11-input table.
- Added a closed analytic Taylor-remainder bound using pi < 22/7.
- Added a theorem identifying the selected cubic root sequence with
  sin(pi/(6*3^L)); therefore the exact limiting sequence is the classical
  Archimedean polygon sequence and its limit is pi.
- Added unit tests and a synchronized Version 3.0 report.
- Retained the eight earlier cross-domain checks as supplementary consistency
  and reproducibility evidence.

Files
-----
pi_g_construction.py
    Fast arbitrary-precision production lane.

certified_richardson.py
    Exact rational R9 certification lane.

verify_pi_g_identities.py
    Runs R9 plus the eight cross-domain checks and regenerates all files in
    output/.

test_certified_richardson.py
    Unit tests for exact root brackets, Richardson moments, the analytic bound,
    and the canonical R9 result.

build_pi_g_report.py
    Regenerates the self-contained LaTeX report and optionally compiles it.

build_package_manifest.py
    Rebuilds PACKAGE_MANIFEST.json with SHA-256 hashes of shipped files.

pi_g_verification_report.tex
pi_g_verification_report.pdf
    The mathematical proof, numerical results, claim boundaries, embedded
    source code, and canonical output.

output/pi_g_verification_results.csv
output/pi_g_verification_manifest.json
output/pi_g_verification_output.txt
output/pi_g_verification_summary.txt
    Canonical run evidence.

requirements.txt
REQUIREMENTS.txt
    Runtime and optional report-build requirements.

Canonical commands
------------------
Run from the extracted package directory.

Windows PowerShell:

    python .\verify_pi_g_identities.py --output-dir ".\output"
    python -m unittest -v .\test_certified_richardson.py
    python .\build_pi_g_report.py --compile
    python .\build_package_manifest.py

Linux/macOS:

    python verify_pi_g_identities.py --output-dir output
    python -m unittest -v test_certified_richardson.py
    python build_pi_g_report.py --compile
    python build_package_manifest.py

Expected verdict
----------------

    checks passed: 9/9
    overall_verdict: PI_G_CERTIFIED_CONSTRUCTION_AND_CONSISTENCY_CHECKS_PASS

Canonical configuration
-----------------------
Working precision: 120 decimal digits
Polygon inputs: L = 0,...,10 (11 values)
Exact endpoint bisection steps: 300 bits per endpoint per level
R9 acceptance target: 1e-80 absolute error
Pinned numerical dependency: mpmath 1.3.0

Claim boundary
--------------
R9 is a rigorous finite-value enclosure. It does not use a numerical value of
pi to choose, alter, or certify the production result. Its proof does use the
classical mathematical facts represented by the triple-angle identity,
convergence of inscribed polygon perimeters, the alternating sine remainder,
and the rational inequality pi < 22/7.

G1 through S5 are supplementary high-precision checks using analytic tails or
two-sided inequalities. H6, E7, and R8 call library special functions and are
not claimed to be algorithmically independent of the library's implementation
of pi.

Reproducibility note
--------------------
The verification outputs and exact-arithmetic certificate are deterministic
under the pinned dependency. The shipped PACKAGE_MANIFEST.json verifies file
integrity. A PDF rebuilt under another TeX installation may have a different
binary hash because of generated metadata even when the rendered mathematical
content is unchanged.
