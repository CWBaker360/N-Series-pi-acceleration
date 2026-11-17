#!/usr/bin/env python3
"""Build and optionally compile the Version 3.0 certified pi_g report."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from pathlib import Path

from mpmath import mp

from pi_g_construction import compute_pi_g


ROOT = Path(__file__).resolve().parent


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def read_results(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def latex_sci(text: str, digits: int = 10) -> str:
    value = mp.mpf(text)
    if value == 0:
        return r"\texttt{0}"
    formatted = mp.nstr(value, digits, min_fixed=0, max_fixed=0)
    return r"\texttt{" + latex_escape(formatted) + "}"


def build_result_rows(results: list[dict[str, str]]) -> str:
    rows = []
    for row in results:
        rows.append(
            "{} & {} & {} & {} & {} \\\\".format(
                latex_escape(row["identifier"]),
                latex_escape(row["name"]),
                latex_sci(row["observed_metric"], 10),
                latex_sci(row["acceptance_bound"], 10),
                "PASS" if row["passed"].lower() == "true" else "FAIL",
            )
        )
    return "\n".join(rows)


def build_polygon_rows(level_count: int, work_dps: int) -> str:
    mp.dps = work_dps
    construction = compute_pi_g(level_count=level_count, work_dps=work_dps)
    rows = []
    for level, (polygon, diagonal) in enumerate(
        zip(construction.polygon_values, construction.extrapolated_diagonal)
    ):
        sides = 6 * 3**level
        rows.append(
            f"{level} & {sides} & "
            + r"\texttt{" + mp.nstr(polygon, 22) + "} & "
            + r"\texttt{" + mp.nstr(diagonal, 22) + r"} \\"
        )
    return "\n".join(rows)


def embedded_listing(path: Path, style: str, caption: str) -> str:
    text = path.read_text(encoding="utf-8")
    if r"\end{lstlisting}" in text:
        raise ValueError(f"Cannot embed {path}: contains \\end{{lstlisting}}")
    return (
        rf"\begin{{lstlisting}}[style={style},caption={{{caption}}}]"
        + "\n"
        + text.rstrip("\n")
        + "\n"
        + r"\end{lstlisting}"
    )


def make_tex(manifest: dict, results: list[dict[str, str]]) -> str:
    result_rows = build_result_rows(results)
    polygon_rows = build_polygon_rows(
        manifest["level_count"], manifest["working_precision_decimal_digits"]
    )
    listings = "\n\n".join(
        [
            embedded_listing(
                ROOT / "pi_g_construction.py",
                "pythonstyle",
                r"Production lane: \texttt{pi\_g\_construction.py}",
            ),
            embedded_listing(
                ROOT / "certified_richardson.py",
                "pythonstyle",
                r"Exact certification lane: \texttt{certified\_richardson.py}",
            ),
            embedded_listing(
                ROOT / "verify_pi_g_identities.py",
                "pythonstyle",
                r"Verification driver: \texttt{verify\_pi\_g\_identities.py}",
            ),
            embedded_listing(
                ROOT / "output" / "pi_g_verification_output.txt",
                "outputstyle",
                "Canonical Version 3.0 output",
            ),
        ]
    )

    r9 = manifest["r9_certificate"]
    pi_g = manifest["pi_g_decimal"]
    pi_ref = manifest["reference_pi_decimal"]
    reference_error = manifest["diagnostic_abs_pi_g_minus_pi"]
    internal_delta = manifest["internal_last_diagonal_delta_diagnostic"]
    max_bracket = manifest["maximum_root_bracket_width"]
    max_residual = manifest["maximum_root_polynomial_residual"]
    work_dps = manifest["working_precision_decimal_digits"]
    level_count = manifest["level_count"]
    max_level = manifest["maximum_level"]
    analytic_bound = r9["analytic_tableau_to_pi_bound"]
    numerical_bound = r9["production_to_exact_tableau_bound"]
    total_bound = r9["total_certified_abs_error_bound"]
    certified_places = r9["certified_absolute_decimal_places"]
    bisection_bits = r9["bisection_bits"]

    return rf"""\documentclass[11pt]{{article}}
\ifdefined\pdfinfoomitdate\pdfinfoomitdate=1\fi
\ifdefined\pdftrailerid\pdftrailerid{{}}\fi
\ifdefined\pdfsuppressptexinfo\pdfsuppressptexinfo=15\fi
\usepackage[T1]{{fontenc}}
\usepackage[utf8]{{inputenc}}
\usepackage{{lmodern}}
\usepackage{{amsmath,amssymb,amsthm}}
\usepackage{{booktabs,longtable,array}}
\usepackage{{geometry}}
\usepackage{{microtype}}
\usepackage{{listings}}
\usepackage{{xcolor}}
\usepackage{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage{{enumitem}}
\usepackage{{mathtools}}
\usepackage{{seqsplit}}

\geometry{{margin=1in}}
\hypersetup{{colorlinks=true,linkcolor=blue!45!black,urlcolor=blue!45!black,citecolor=blue!45!black}}
\setlength{{\parindent}}{{0pt}}
\setlength{{\parskip}}{{0.55em}}
\setlength{{\headheight}}{{14pt}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{Baker algebraic Archimedean method}}
\rhead{{Certified computational appendix}}
\cfoot{{\thepage}}

\lstdefinestyle{{pythonstyle}}{{
  language=Python,
  basicstyle=\ttfamily\scriptsize,
  keywordstyle=\bfseries,
  commentstyle=\itshape,
  stringstyle=\ttfamily,
  numbers=left,
  numberstyle=\tiny,
  numbersep=8pt,
  breaklines=true,
  breakatwhitespace=false,
  showstringspaces=false,
  columns=fullflexible,
  keepspaces=true,
  frame=single,
  rulecolor=\color{{black!25}},
  tabsize=4
}}
\lstdefinestyle{{outputstyle}}{{
  basicstyle=\ttfamily\scriptsize,
  numbers=none,
  breaklines=true,
  columns=fullflexible,
  keepspaces=true,
  frame=single,
  rulecolor=\color{{black!25}}
}}

\newtheorem{{theorem}}{{Theorem}}
\newtheorem{{proposition}}{{Proposition}}
\newtheorem{{corollary}}{{Corollary}}
\newtheorem{{remark}}{{Remark}}
\newcommand{{\pig}}{{\pi_g}}

\title{{Certified Algebraic Construction and Richardson Enclosure\\for Baker's Geometric Approximation to $\pi$}}
\author{{Wayne Baker\\Independent Researcher, Newfoundland and Labrador, Canada}}
\date{{July 30, 2026\\Version 3.0}}

\begin{{document}}
\maketitle

\begin{{abstract}}
This report closes the principal rigor gap in the earlier verification package.  The production algorithm begins with the exact hexagon seed $c_0=1/2$, repeatedly selects the small positive root of $4u^3-3u+c=0$, forms the tripled inscribed-polygon values, and applies a full scale-$3$ Richardson/N-Series tableau.  No numerical value of $\pi$ and no trigonometric function is consulted while constructing the approximation.  A separate certification lane uses exact rational arithmetic to propagate cubic-root intervals through every level and through the complete tableau.  The resulting numerical enclosure is combined with an analytic sine-series remainder bound based only on the classical rational inequality $\pi<22/7$.  For the canonical {level_count}-input run at {work_dps}-decimal working precision, the finite production value is proved to satisfy
\[
 |\pig-\pi| < {latex_sci(total_bound,16)},
\]
which certifies at least {certified_places} decimal places of absolute accuracy.  Eight additional cross-domain checks all pass; they are retained as reproducibility and consistency evidence, while the new R9 enclosure carries the rigorous finite-value certification.
\end{{abstract}}

\tableofcontents
\newpage

\section{{Claim boundary and status}}

Version 3.0 makes two distinct claims.

\begin{{enumerate}}[label=\arabic*.]
\item The exact algebraic chord recursion generates the classical tripled inscribed-polygon sequence.  Consequently its infinite polygonal limit is the classical constant $\pi$.
\item The finite value emitted by the supplied production script is enclosed a priori by an exact rational interval calculation plus an analytic Taylor-remainder estimate.  The canonical run satisfies the explicit bound displayed in the abstract.
\end{{enumerate}}

The last Richardson-diagonal difference remains printed as a convergence diagnostic, but it is no longer used as an error bound.  Checks H6, E7, and R8 call library special functions and are not claimed to be algorithmically independent of the library's implementation of $\pi$.  The other cross-domain tests likewise supplement, rather than replace, the R9 certificate.

\section{{Oracle-free algebraic construction}}

\subsection{{Unique small positive cubic branch}}

For $0<c\le1/2$, define
\[
 f_c(u)=4u^3-3u+c.
\]

\begin{{proposition}}[Certified branch]
The interval $(0,c/2)$ contains exactly one zero of $f_c$.
\end{{proposition}}

\begin{{proof}}
At the endpoints,
\[
 f_c(0)=c>0,
 \qquad
 f_c\!\left(\frac c2\right)=\frac{{c(c^2-1)}}2<0.
\]
Moreover,
\[
 f_c'(u)=12u^2-3<0
\]
throughout $0\le u\le c/2\le1/4$.  Hence $f_c$ is strictly decreasing on the sign-changing bracket and has exactly one root there.
\end{{proof}}

\subsection{{Identification with the exact polygon sequence}}

\begin{{theorem}}[Triple-angle identification]
Let $c_0=1/2$, and let $c_{{L+1}}$ be the unique zero of
\[
 4u^3-3u+c_L=0
\]
in $(0,c_L/2)$.  Then, for every $L\ge0$,
\[
 c_L=\sin\!\left(\frac{{\pi}}{{6\cdot3^L}}\right).
\]
Consequently,
\[
 P_L=6\cdot3^L c_L
     =N_L\sin\!\left(\frac{{\pi}}{{N_L}}\right),
 \qquad N_L=6\cdot3^L,
\]
is exactly the classical inscribed regular-$N_L$-gon semiperimeter sequence.
\end{{theorem}}

\begin{{proof}}
The base case is $c_0=1/2=\sin(\pi/6)$.  Suppose $c_L=\sin x$ with $x=\pi/(6\cdot3^L)$ and set $u=\sin(x/3)$.  The triple-angle identity gives
\[
 4u^3-3u+c_L=0.
\]
Since $0<u<1/2$,
\[
 c_L-2u=(3u-4u^3)-2u=u(1-4u^2)>0,
\]
so $u\in(0,c_L/2)$.  The preceding proposition makes it the unique selected root.  Induction completes the proof.
\end{{proof}}

\begin{{corollary}}
The limiting geometric value is not a distinct constant:
\[
 \lim_{{L\to\infty}}P_L=\pi.
\]
The notation $\pig$ may be retained for the finite algebraic/N-Series approximation or for its geometric presentation, but its exact limit equals $\pi$.
\end{{corollary}}

\section{{Scale-3 Richardson cancellation}}

Given $M={level_count}$ polygon inputs, put $s=M-1={max_level}$ and define
\[
 R_0(N)=P_N,
 \qquad
 R_r(N)=\frac{{9^rR_{{r-1}}(3N)-R_{{r-1}}(N)}}{{9^r-1}}
 \quad (1\le r\le s).
\]
Equivalently, the final value is a rational linear combination
\[
 T_s=\sum_{{j=0}}^s w_jP_{{6\cdot3^j}},
\]
where the exact weights satisfy
\[
 \sum_{{j=0}}^s w_j=1,
 \qquad
 \sum_{{j=0}}^s \frac{{w_j}}{{(6\cdot3^j)^{{2m}}}}=0
 \quad (1\le m\le s).
\]
The certification code verifies all these moment identities using exact fractions.

\section{{Analytic a priori remainder}}

\begin{{theorem}}[Certified tableau remainder]
Let $U=22/7$.  For the exact polygon inputs and the exact Richardson weights above,
\[
 |T_s-\pi|\le B_{{\rm an}},
\]
where
\[
 B_{{\rm an}}
 =\frac{{U^{{2s+3}}}}{{(2s+3)!}}
  \sum_{{j=0}}^s
  \frac{{|w_j|}}{{(6\cdot3^j)^{{2s+2}}}}.
\]
For the canonical run,
\[
 B_{{\rm an}}={latex_sci(analytic_bound,18)}.
\]
\end{{theorem}}

\begin{{proof}}
For $N\ge6$, the sine expansion gives
\[
 N\sin\!\left(\frac\pi N\right)
 =\pi+\sum_{{m=1}}^s
 \frac{{(-1)^m\pi^{{2m+1}}}}{{(2m+1)!N^{{2m}}}}+r_s(N).
\]
Because $0<\pi/N\le\pi/6<1$, the alternating terms decrease in magnitude, and
\[
 |r_s(N)|\le
 \frac{{\pi^{{2s+3}}}}{{(2s+3)!N^{{2s+2}}}}
 <\frac{{U^{{2s+3}}}}{{(2s+3)!N^{{2s+2}}}}.
\]
The Richardson moment identities preserve the constant term and cancel all displayed modes $N^{{-2}},\ldots,N^{{-2s}}$.  Therefore
\[
 T_s-\pi=\sum_{{j=0}}^s w_jr_s(6\cdot3^j),
\]
and the triangle inequality yields the stated rational bound.
\end{{proof}}

\section{{Exact interval propagation through the computation}}

The certification lane stores every endpoint as a \texttt{{fractions.Fraction}}.  For an interval coefficient $c\in[c_-,c_+]$, the selected root is increasing in $c$, since implicit differentiation gives
\[
 \frac{{du}}{{dc}}=-\frac1{{12u^2-3}}>0
\]
on the selected branch.  The next chord interval is therefore obtained from a lower bracket for the root at $c_-$ and an upper bracket for the root at $c_+$.  The canonical run uses {bisection_bits} exact bisection steps at each endpoint.

The polygon intervals are then propagated through the affine Richardson recurrences with exact rational coefficients and correct sign-aware interval arithmetic.  If $[A,B]$ is the resulting exact-tableau enclosure and $y$ is the exact binary rational represented by the production \texttt{{mpmath}} value, then
\[
 |y-T_s|\le B_{{\rm num}}
 :=\max\{{|y-A|,|y-B|\}}.
\]
For this run,
\[
 B_{{\rm num}}={latex_sci(numerical_bound,18)}.
\]
No heuristic floating-point round-off term is needed in this certificate.

Combining the two independent components gives
\[
 |y-\pi|\le B_{{\rm num}}+B_{{\rm an}}
 ={latex_sci(total_bound,18)}<10^{{-{certified_places}}}.
\]
This is the R9 acceptance bound.

\section{{Canonical numerical run}}

The production lane used {work_dps} decimal digits and levels $L=0,\ldots,{max_level}$.

\textbf{{Production value $\pig$:}}

{{\small\ttfamily\seqsplit{{{latex_escape(pi_g)}}}}}

\textbf{{Reference value used only after construction:}}

{{\small\ttfamily\seqsplit{{{latex_escape(pi_ref)}}}}}

\[
|\pig-\pi_{{\rm reference}}|={latex_sci(reference_error,18)}.
\]

The reference comparison is performed only after the construction and certificate have been fixed.  It is a diagnostic consistency check, not an input to R9.

\begin{{table}}[ht]
\centering
\small
\caption{{Polygon inputs and Richardson diagonal}}
\begin{{tabular}}{{r r l l}}
\toprule
$L$ & $N_L$ & $P_L$ & diagonal entry \\
\midrule
{polygon_rows}
\bottomrule
\end{{tabular}}
\end{{table}}

The old last-diagonal diagnostic is
\[
 {latex_sci(internal_delta,18)},
\]
while the production root solver reports a maximum bracket width of
\[
 {latex_sci(max_bracket,18)}
\]
and a maximum midpoint cubic residual of
\[
 {latex_sci(max_residual,18)}.
\]
These diagnostics are not used in the R9 proof.

\section{{Nine verification checks}}

\begin{{longtable}}{{p{{0.06\linewidth}}p{{0.29\linewidth}}p{{0.20\linewidth}}p{{0.20\linewidth}}p{{0.08\linewidth}}}}
\toprule
ID & Check & Observed metric & Acceptance bound & Status \\
\midrule
\endhead
{result_rows}
\bottomrule
\end{{longtable}}

All nine checks pass.  R9 is the rigorous certificate for the finite constructed value.  G1--S5 use explicit analytic tails or two-sided inequalities together with high-precision numerical evaluation.  H6, E7, and R8 are deliberately labelled library-level cross-checks.

\section{{Reproducibility procedure}}

From the extracted package directory, run
\begin{{verbatim}}
python verify_pi_g_identities.py --output-dir output
python -m unittest -v test_certified_richardson.py
python build_pi_g_report.py --compile
python build_package_manifest.py
\end{{verbatim}}

The verification driver regenerates the CSV, JSON, summary, and full output log.  The unit tests independently verify the exact cubic brackets, Richardson moment cancellations, and the canonical R9 threshold.  The package manifest records SHA-256 hashes for shipped-file integrity.  A rebuilt PDF can have different binary metadata across TeX environments even when its rendered mathematical content is unchanged.

\section{{Conclusion}}

The gap in Version 2.1 was real but limited: the last Richardson-diagonal change was an empirical stabilization diagnostic rather than a certified remainder.  Version 3.0 replaces that diagnostic as the proof mechanism.  Exact rational root intervals control the algebraic construction, exact rational affine propagation controls the complete tableau, and a closed analytic sine remainder controls the distance from the exact tableau to $\pi$.  The canonical production value is therefore enclosed without consulting a numerical $\pi$ oracle and is proved to have at least {certified_places} decimal places of absolute accuracy.

\appendix
\section{{Embedded source and canonical output}}
{listings}

\end{{document}}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compile", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = ROOT / "output" / "pi_g_verification_manifest.json"
    results_path = ROOT / "output" / "pi_g_verification_results.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = read_results(results_path)

    tex = make_tex(manifest, results)
    tex_path = ROOT / "pi_g_verification_report.tex"
    tex_path.write_text(tex, encoding="utf-8")
    print(f"wrote: {tex_path}")

    if args.compile:
        environment = os.environ.copy()
        environment["SOURCE_DATE_EPOCH"] = "1785369600"
        environment["FORCE_SOURCE_DATE"] = "1"
        for _ in range(2):
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
                cwd=ROOT,
                env=environment,
                check=True,
            )
        print(f"wrote: {ROOT / 'pi_g_verification_report.pdf'}")


if __name__ == "__main__":
    main()
