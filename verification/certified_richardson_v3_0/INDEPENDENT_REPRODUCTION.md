# Independent reproduction record — 2026-11-16

Source: uploaded Baker pi_g verification package v3.0 (2026-07-30).

Environment: Python 3, mpmath 1.3.0.

Verification:
- 15 of the 16 files in supplied PACKAGE_MANIFEST.json matched their recorded SHA-256 hashes and byte sizes.
- The absent original file is supplementary REQUIREMENTS.txt (uppercase). Do not represent this reconstruction as a complete byte-for-byte original package.
- python -m unittest -v test_certified_richardson.py: 4/4 PASS.
- python verify_pi_g_identities.py --output-dir <fresh output directory>: 9/9 PASS.
- Recomputed four files under output/ match their uploaded counterparts byte-for-byte.
- Canonical R9 error bound: 3.4062857583141178024467533003750371953541882810522e-81 < 1e-80.
- Scope: rigorous algebraic-lane finite-value certificate; not a Lean formalization of the analytic theorem and not a physical construction-tolerance result.

No PDF/TeX was edited, and no new DOI or GitHub release is required.
