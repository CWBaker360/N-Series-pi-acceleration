# Reproducibility

## Paper compilation

The authoritative manuscript source is:

```text
paper/nseries_pi_acceleration.tex
```

Compile the manuscript by opening a terminal in the `paper` directory and running:

```bash
pdflatex nseries_pi_acceleration.tex
pdflatex nseries_pi_acceleration.tex
```

The second pass resolves cross-references and page numbering. Temporary LaTeX
files may be removed after the PDF has been generated.

## Python environment

Recommended environment:

```text
Python 3.10 or later
mpmath
gmpy2
```

The `gmpy2` package is strongly recommended for large target calculations.

Install the dependencies using:

```bash
python -m pip install mpmath gmpy2
```

## Configurable chord verification

From the repository root, run a 10,000-digit verification using the hexagon
seed and derivative certificate:

```powershell
python scripts/baker_chord_nseries.py --target-digits 10000 --seed hexagon --certificate --outdir outputs
```

For an independent triangle-seed cross-check, run:

```powershell
python scripts/baker_chord_nseries.py --target-digits 10000 --seed triangle --certificate --outdir outputs_triangle
```

The construction core uses algebraic chord relations rather than
trigonometric-function evaluations. The value `mp.pi` is used only afterward
to count verified decimal digits.

## Large resumable production run

Set `TARGET_DIGITS` near the beginning of:

```text
scripts/baker_pi_target.py
```

Then run, from the repository root:

```powershell
python scripts/baker_pi_target.py
```

The production script writes an atomic checkpoint periodically and resumes
automatically when restarted with the same target configuration.

## Interpretation

The numerical runs verify implementation behavior and decimal agreement. They
do not replace the analytic proof.

The theorem in the manuscript is proved from the even-power asymptotic
expansion and the associated moment-cancellation identities.

## Integrity

The legacy root `SHA256SUMS.txt` may reflect historical Windows line endings
and does not cover the November verification directories. Do not treat it as a
current fresh-clone certificate. The frozen Lean checkpoint has its own
`FREEZE_MANIFEST.txt`, and the July Version 3.0 exact-rational verification
package has `PACKAGE_MANIFEST.json` plus `INDEPENDENT_REPRODUCTION.md`.
The latter preserves 15/16 original file hashes; the missing supplementary
`REQUIREMENTS.txt` is documented, and the actual pinned dependency file is present.

## November 2026 independently reproduced finite certificate

From `verification/certified_richardson_v3_0` with Python 3.10+ and
`mpmath==1.3.0` installed, run:

```powershell
python -m unittest -v test_certified_richardson.py
python verify_pi_g_identities.py --output-dir output
```

This reproduces four unit tests and nine verification checks for the
canonical eleven-input *algebraic* Richardson tableau, with a rigorous
absolute error bound below `1e-80`. The constructible-ladder Lean evidence
is a different, exact-operation statement. The historical million-digit
Chudnovsky reference implementation/version has not been recovered, so that
comparison is not claimed to be independently reproducible from this archive.
