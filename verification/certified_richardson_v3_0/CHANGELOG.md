# Changelog

## Version 3.0 - 2026-07-30

- Replaced the empirical last-diagonal error proxy with the rigorous R9 enclosure.
- Added `certified_richardson.py`, an exact rational certification lane.
- Propagated interval-valued cubic coefficients through every trisection level.
- Propagated polygon intervals through the complete scale-3 Richardson tableau.
- Verified all Richardson moment cancellations exactly.
- Added an explicit analytic sine-series remainder bound using \(\pi<22/7\).
- Certified the canonical production value to absolute error below
  \(3.406285758314118\times10^{-81}\).
- Added `test_certified_richardson.py`.
- Rewrote the report and README to distinguish rigorous certification from
  supplementary numerical consistency checks.

## Version 2.1 - 2026-07-12

- Made the LaTeX report self-contained by embedding source listings.
- Retained eight cross-domain numerical consistency checks.
- The final Richardson diagonal difference remained diagnostic rather than a
  rigorous error bound.
