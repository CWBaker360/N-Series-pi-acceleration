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

Run a SHA-256 verification against `SHA256SUMS.txt` after downloading or
extracting the repository archive.
