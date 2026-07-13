# Reproducibility

## Paper compilation

From the `paper` directory:

```bash
pdflatex nseries_pi_acceleration.tex
pdflatex nseries_pi_acceleration.tex
```

The temporary LaTeX files may be deleted after the PDF is generated.

## Python environment

Recommended:

```text
Python 3.10 or later
mpmath
gmpy2 (strongly recommended for large targets)
```

Install dependencies with:

```bash
python -m pip install mpmath gmpy2
```

## Configurable chord verification

Example, 10,000 digits with the hexagon seed and certificate:

```bash
python scripts/baker_chord_nseries.py ^
  --target-digits 10000 ^
  --seed hexagon ^
  --certificate ^
  --outdir outputs
```

Triangle-seed cross-check:

```bash
python scripts/baker_chord_nseries.py ^
  --target-digits 10000 ^
  --seed triangle ^
  --certificate ^
  --outdir outputs_triangle
```

The script uses no trigonometric functions in the construction core. `mp.pi` is used only to count verified digits.

## Large resumable production run

Edit `TARGET_DIGITS` near the top of:

```text
scripts/baker_pi_target.py
```

Then run:

```bash
python scripts/baker_pi_target.py
```

The script writes an atomic checkpoint periodically and resumes automatically when restarted with the same target.

## Interpretation

The numerical runs verify implementation behavior and decimal agreement. The theorem in the paper is proved analytically from the even-power expansion and moment-cancellation identities.
