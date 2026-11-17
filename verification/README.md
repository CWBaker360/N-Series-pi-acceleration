# Lean 4 formal verification — source and scope

This research repository has a separate, public Lean 4/Mathlib companion:

- [N-Series Lean verification source](https://github.com/CWBaker360/nseries-lean-verification)
- [Pinned A–E10 source revision](https://github.com/CWBaker360/nseries-lean-verification/tree/bf262aaf52a12001ca64545757d758b507b09a18)
- [Companion release report](https://github.com/CWBaker360/nseries-lean-verification/blob/main/RELEASE-REPORT.md)
- [Companion axiom-audit evidence](https://github.com/CWBaker360/nseries-lean-verification/blob/main/evidence/axiom-reproduction.log)
- [Companion build evidence](https://github.com/CWBaker360/nseries-lean-verification/blob/main/evidence/build-reproduction.log)

## Recorded A–E10 verification (13 November 2026)

The companion repository reports a successful integrated Lean 4 build of **28 release modules** and an audit of **112 named declarations**. The recorded final axiom reports contain only `propext`, `Classical.choice`, and `Quot.sound`, with no `sorryAx` in the audited declarations.

The pinned environment uses Lean **4.36.0-rc2** and Mathlib revision `9d581dfff2e41de989072ea63abf3daf69311520`. The recorded build reused verified dependency caches; it was not an independent build of Lean and Mathlib from scratch. Mathematical coverage includes sine-remainder and polygonal error bounds, two- and three-scale cancellation, moment weights, accelerated limits, and trisection identities. See the actual theorem signatures and audit logs for the exact formal statements.

## Later constructible-ladder checkpoint (15 November 2026)

A **separate local seven-module** constructible-ladder/canonical-tableau checkpoint was reported clean, with no `sorryAx` and only the three standard axioms above. The checkpoint includes `canonical_ladder_certified`, `canonical_residual_bounds`, and `canonical_tableau_certified`. This later checkpoint is **not** counted among the pinned A–E10 audit's 112 declarations. A separate later compile report also covers the division-form Proposition 4.6 budget identity; it must not be silently treated as part of the earlier pinned audit.

The seven-module checkpoint did **not** cover every subsequent manuscript claim (in particular the independent analytic `B_an` theorem or the one-refinement counterexample). Before declaring the corrected November manuscript fully machine-checked, archive the corresponding source revision, imports, theorem crosswalk, combined axiom audit, and reproducible build evidence.

## Repository and publication policy

This repository's original manuscript files remain unchanged by this documentation update. The companion repository is the source of the pinned Lean development; this document does not purport to copy or recompile it.

Changes committed to this repository's `main` branch are **not** a new tagged release and do not modify any previously archived Zenodo release. Do not describe a future manuscript or source revision as an archived DOI artifact until it is deliberately deposited.

For code use the repository's MIT license; for manuscript and research documentation use CC BY 4.0 as specified in the root license notices.

## November 15, 2026 frozen constructive-ladder source

The exact seven-module local checkpoint and its audit evidence are preserved in
[constructible-ladder-2026-11-15](constructible-ladder-2026-11-15/).
The checkpoint archive was integrity-checked using its `FREEZE_MANIFEST.txt`;
source files are retained byte-for-byte. This is a recorded local build and axiom
audit, not a claim of independent fresh-clone reproduction or complete
formalization of all manuscript results. No manuscript PDF/TeX was replaced.

## Certified Richardson v3.0 (30 July 2026; independently reproduced November 2026)

The [certification source, original report and verified outputs](certified_richardson_v3_0/)
provide the R9 exact-rational enclosure for the canonical eleven-input *algebraic*
scale-3 Richardson tableau. The recorded and independently regenerated 9/9 checks
and four unit tests pass, with absolute error bound below `1e-80`.

The included `PACKAGE_MANIFEST.json` verifies 15 original files exactly. The
supplementary uppercase `REQUIREMENTS.txt` was not recovered; `requirements.txt`
(the actual pinned Python dependency) is present. See `INDEPENDENT_REPRODUCTION.md`.
This is not an end-to-end Lean proof of Theorem 6.1 or a physical straightedge-
and-compass error-tolerance certificate. No manuscript files were replaced here.
## November 15 manuscript update (main branch)

The revised 25-page manuscript and matching LaTeX are in `paper/`. It distinguishes
the algebraic R9 finite-value certificate, the separately frozen constructible
ladder, and the parts of the analytical argument not formalized in Lean. The
historical million-digit Chudnovsky reference software version is not known.
No new Zenodo DOI or tagged release is implied by this source update.
