# A Constructive N-Series Acceleration Law for Polygonal Approximation of π

**Author:** Wayne Baker  
**Date:** July 3, 2026  
**Status:** Preprint / source and reproducibility archive

This repository contains the paper, LaTeX source, and supporting Python scripts for:

> **A Constructive N-Series Acceleration Law for Polygonal Approximation of π**

## Read the paper

- [Read the paper (PDF)](paper/nseries_pi_acceleration.pdf)
- [LaTeX source](paper/nseries_pi_acceleration.tex)
- [Version 1.0.0 release](https://github.com/CWBaker360/N-Series-pi-acceleration/releases/tag/v1.0.0)

## Main result

For the polygonal half-perimeter sequence

$$
P_N
=
N\sin\!\left(\frac{\pi}{N}\right),
$$

the symmetry-induced error expansion contains only even powers of $N^{-1}$:

$$
P_N
=
\pi
-
\frac{\pi^3}{6N^2}
+
\frac{\pi^5}{120N^4}
-
\frac{\pi^7}{5040N^6}
+
O(N^{-8}).
$$

For any fixed integer $k>1$, define

$$
\widehat P_N^{(k)}
=
P_{kN}
+
\frac{P_{kN}-P_N}{k^2-1}.
$$

Then

$$
\widehat P_N^{(k)}
=
\pi+O(N^{-4}).
$$

More generally, weighted multiscale operators cancel successive even-power
terms through a Vandermonde moment system.

## π-free computational lane

The repository scripts generate polygonal approximants algebraically from chord
half-lengths. The side count is tripled by solving

$$
4u^3-3u+c_N=0,
\qquad
u=c_{3N},
$$

and the scale-$3$ N-series tableau accelerates the resulting half-perimeter
sequence. The value of $\pi$ is used only afterward to count verified digits.

## Scripts

### `baker_chord_nseries.py`

Configurable verification script with:

- triangle or hexagon algebraic seed;
- scale-$3$ N-series acceleration;
- optional cubic residual and derivative root-error certificate;
- configurable target precision and output directory.

### `baker_pi_target.py`

Resumable large-target production script with:

- automatic precision and level sizing;
- atomic checkpointing;
- triangle-seeded chord-trisection ladder;
- high-digit output generation.

## Scope

The paper does not redefine $\pi$. The accelerated sequence has the same
Archimedean limit and changes only the finite-resolution error structure.

The two-scale operator is a Richardson-type cancellation. The geometric
contribution is the identification of the chord symmetry that supplies the
even-power expansion and makes the cancellation exact at the asymptotic level.

## Research triad

This paper is the third work in a three-paper research sequence:

1. [A Constructible Cubic Error Cascade for Approximate Angle Trisection](https://github.com/CWBaker360/Constructible-Cubic-Trisection/releases/tag/v1.0.0)
2. [A Local Cubic Refinement Law for Proportional-Subtended Angle Division](https://github.com/CWBaker360/proportional-subtended-cubic-refinement/releases/tag/v1.0.0)
3. [A Constructive N-Series Acceleration Law for Polygonal Approximation of π](https://github.com/CWBaker360/N-Series-pi-acceleration/releases/tag/v1.0.0)

The sequence progresses from a specific constructible approximation, through
the general local cubic cancellation law, to higher-order acceleration of
polygonal approximations.

## Repository structure

```text
.
├── README.md
├── CITATION.cff
├── REPRODUCIBILITY.md
├── LICENSE_NOTICE.md
├── CHANGELOG.md
├── SHA256SUMS.txt
├── .gitignore
├── paper/
│   ├── nseries_pi_acceleration.tex
│   ├── nseries_pi_acceleration.pdf
│   └── README.md
├── scripts/
│   ├── baker_chord_nseries.py
│   ├── baker_pi_target.py
│   └── README.md
└── docs/
    ├── abstract.md
    ├── repository_description.md
    └── github_upload_checklist.md
```

## Rights

Copyright © 2026 Wayne Baker. All rights reserved unless otherwise stated.
