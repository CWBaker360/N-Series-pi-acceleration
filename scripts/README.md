# Scripts

## `baker_chord_nseries.py`

Configurable algebraic chord-trisection and scale-\(3\) N-series verification script.

Example:

```bash
python baker_chord_nseries.py --target-digits 10000 --seed hexagon --certificate
```

## `baker_pi_target.py`

Resumable high-digit production script. Set `TARGET_DIGITS` near the top before running.

Both scripts construct approximants without using \(\pi\). They use `mp.pi` only as an external verification reference.
