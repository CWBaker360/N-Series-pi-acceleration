# Checkpoint: constructible-ladder formalization

Generated: 2026-11-15 16:14:58 -03:30
Toolchain: leanprover/lean4:v4.36.0-rc2

## Sources (SHA-256, as-is on disk)

| file | sha256 | bytes |
|---|---|---|
| NSeriesSeedCubicBounds.lean | `4ce0930b0d775a61b9b7f2660456fb67aeaf834911d31d01600919d215cffdee` | 13354 |
| NSeriesCubicIteration.lean | `b99fef74593c9e3ea781ce9f4b99457ef86436483f046a2737be78a47e8923d1` | 2396 |
| NSeriesGeometricSchedule.lean | `cdfe3951bed1b0171d9d6dbc3bf2e6d7dd6cda82fe6d3a74cb4e309d3e00bd95` | 3913 |
| NSeriesLadderTableau.lean | `7c54a81a272cff816a81acad0722e18dea3aa9006a8096b4b64bfd792ed78a1a` | 25498 |
| NSeriesRefinementSchedule.lean | `b1afa3e77d74ada9e3d0d9714ca6b905c58af5c8ef1578e7d31e578f1c12e93f` | 14695 |
| NSeriesCanonicalLadder.lean | `3d139e64df336ec018cf7e5c4a0c1234b7c2edb6e3bc2c371751fc9fe1c1d882` | 7846 |
| NSeriesCanonicalTableau.lean | `a2f3f408252127a4ef8d2a1a7feacafffdeee6f1600125cb62f2b6a6d9585eab` | 4503 |
| lakefile.toml | `ecef06ebc49c2dda580e08a00483ecad9c7fbc137ab484f6799669cc397645bb` | 1110 |

## Note on hashing

These hashes are over the files as they sit on disk (CRLF on Windows).
If these sources are committed to git, regenerate the repository
manifest with regen_manifest.py, which hashes git index content (LF).
Mixing the two is what made SHA256SUMS.txt fail on a fresh clone.

## Result

PASS -- all required theorems audited to [propext, Classical.choice, Quot.sound].
