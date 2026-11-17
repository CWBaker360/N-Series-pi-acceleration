#!/usr/bin/env python3
"""Exact rational enclosure for the Baker scale-3 polygon/Richardson pipeline.

This module is the rigorous certification lane.  It uses only Python integers
and ``fractions.Fraction`` for all branch brackets, interval propagation,
Richardson weights, and error bounds.  No floating-point arithmetic and no
numerical value of pi are used in the certificate itself.

The only analytic constant entering the remainder estimate is the classical
rational upper bound pi < 22/7.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import factorial
from typing import Sequence


@dataclass(frozen=True)
class RationalInterval:
    """Closed interval with exact rational endpoints."""

    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise ValueError("interval lower endpoint exceeds upper endpoint")

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    @property
    def midpoint(self) -> Fraction:
        return (self.lower + self.upper) / 2


@dataclass(frozen=True)
class ExactRootStep:
    """Exact propagated enclosure for one cubic trisection step."""

    input_interval: RationalInterval
    output_interval: RationalInterval
    endpoint_bisection_steps: int


@dataclass(frozen=True)
class RichardsonCertificate:
    """Complete a priori enclosure for the finite Richardson output."""

    level_count: int
    maximum_level: int
    base_sides: int
    bisection_bits: int
    chord_intervals: tuple[RationalInterval, ...]
    polygon_intervals: tuple[RationalInterval, ...]
    root_steps: tuple[ExactRootStep, ...]
    final_weights: tuple[Fraction, ...]
    tableau_interval: RationalInterval
    production_value: Fraction
    production_to_exact_tableau_bound: Fraction
    analytic_tableau_to_pi_bound: Fraction
    total_pi_error_bound: Fraction
    certified_decimal_places: int
    production_value_inside_tableau_interval: bool


def cubic_fraction(u: Fraction, c: Fraction) -> Fraction:
    """Evaluate 4*u^3 - 3*u + c exactly."""

    return 4 * u**3 - 3 * u + c


def mpf_to_fraction(value: object) -> Fraction:
    """Convert an mpmath mpf to its exact binary rational value.

    mpmath stores a finite mpf as ``(sign, mantissa, exponent, bitcount)`` and
    represents exactly ``(-1)^sign * mantissa * 2^exponent``.
    """

    try:
        sign, mantissa, exponent, _bitcount = value._mpf_  # type: ignore[attr-defined]
    except AttributeError as exc:  # pragma: no cover - defensive API guard
        raise TypeError("value is not an mpmath mpf") from exc

    numerator = -int(mantissa) if sign else int(mantissa)
    if exponent >= 0:
        return Fraction(numerator << exponent, 1)
    return Fraction(numerator, 1 << (-exponent))


def _bisect_fixed_c_root(c: Fraction, bits: int) -> RationalInterval:
    """Enclose the unique small positive root for an exact rational c.

    For 0 < c <= 1/2, the root lies uniquely in (0,c/2).  Exactly ``bits``
    sign-preserving bisection steps are performed using rational arithmetic.
    """

    if not (Fraction(0) < c <= Fraction(1, 2)):
        raise ValueError("expected 0 < c <= 1/2")
    if bits < 8:
        raise ValueError("bits must be at least 8")

    lower = Fraction(0)
    upper = c / 2
    if cubic_fraction(lower, c) <= 0 or cubic_fraction(upper, c) >= 0:
        raise ArithmeticError("initial exact cubic bracket is invalid")

    for _ in range(bits):
        midpoint = (lower + upper) / 2
        sign = cubic_fraction(midpoint, c)
        if sign > 0:
            lower = midpoint
        elif sign < 0:
            upper = midpoint
        else:
            return RationalInterval(midpoint, midpoint)

    if cubic_fraction(lower, c) < 0 or cubic_fraction(upper, c) > 0:
        raise ArithmeticError("exact bisection lost the sign-changing bracket")
    return RationalInterval(lower, upper)


def propagate_cubic_root_interval(
    c_interval: RationalInterval, bits: int
) -> ExactRootStep:
    """Propagate an interval-valued cubic coefficient through the root map.

    On the selected branch, the root r(c) is increasing in c because
    r'(c) = -1/(12*r(c)^2-3) > 0.  Therefore a rigorous enclosure is obtained
    from the lower bracket for r(c_lower) and the upper bracket for r(c_upper).
    """

    lower_root = _bisect_fixed_c_root(c_interval.lower, bits)
    upper_root = _bisect_fixed_c_root(c_interval.upper, bits)
    output = RationalInterval(lower_root.lower, upper_root.upper)
    return ExactRootStep(
        input_interval=c_interval,
        output_interval=output,
        endpoint_bisection_steps=bits,
    )


def build_chord_intervals(
    *, level_count: int, bisection_bits: int
) -> tuple[tuple[RationalInterval, ...], tuple[ExactRootStep, ...]]:
    """Build exact enclosures for c_L, beginning with c_0=1/2."""

    if level_count < 2:
        raise ValueError("level_count must be at least 2")

    chords: list[RationalInterval] = [RationalInterval(Fraction(1, 2), Fraction(1, 2))]
    steps: list[ExactRootStep] = []
    for _level in range(1, level_count):
        step = propagate_cubic_root_interval(chords[-1], bisection_bits)
        steps.append(step)
        chords.append(step.output_interval)
    return tuple(chords), tuple(steps)


def scale_interval(interval: RationalInterval, scalar: Fraction) -> RationalInterval:
    if scalar >= 0:
        return RationalInterval(scalar * interval.lower, scalar * interval.upper)
    return RationalInterval(scalar * interval.upper, scalar * interval.lower)


def affine_interval(
    first: RationalInterval,
    first_coefficient: Fraction,
    second: RationalInterval,
    second_coefficient: Fraction,
) -> RationalInterval:
    """Exact interval enclosure of a*A + b*B with independent intervals."""

    first_scaled = scale_interval(first, first_coefficient)
    second_scaled = scale_interval(second, second_coefficient)
    return RationalInterval(
        first_scaled.lower + second_scaled.lower,
        first_scaled.upper + second_scaled.upper,
    )


def richardson_weights(level_count: int) -> tuple[Fraction, ...]:
    """Return exact final scale-3 Richardson weights on all polygon inputs."""

    if level_count < 1:
        raise ValueError("level_count must be positive")

    previous: list[list[Fraction] | None] = []
    for column in range(level_count):
        previous.append(
            [Fraction(1 if index == column else 0) for index in range(level_count)]
        )

    for stage in range(1, level_count):
        current: list[list[Fraction] | None] = [None] * level_count
        denominator = 9**stage - 1
        right_factor = Fraction(9**stage, denominator)
        left_factor = Fraction(-1, denominator)
        for column in range(stage, level_count):
            right = previous[column]
            left = previous[column - 1]
            if right is None or left is None:
                raise ArithmeticError("malformed exact Richardson weight table")
            current[column] = [
                right_factor * right[index] + left_factor * left[index]
                for index in range(level_count)
            ]
        previous = current

    final = previous[-1]
    if final is None:
        raise ArithmeticError("missing final exact Richardson weights")
    weights = tuple(final)
    if sum(weights, Fraction(0)) != 1:
        raise ArithmeticError("Richardson weights do not preserve constants")
    return weights


def apply_richardson_intervals(
    polygon_intervals: Sequence[RationalInterval],
) -> RationalInterval:
    """Propagate exact polygon intervals through the full Richardson table."""

    if not polygon_intervals:
        raise ValueError("at least one polygon interval is required")

    previous: list[RationalInterval | None] = list(polygon_intervals)
    level_count = len(polygon_intervals)
    for stage in range(1, level_count):
        current: list[RationalInterval | None] = [None] * level_count
        denominator = 9**stage - 1
        right_factor = Fraction(9**stage, denominator)
        left_factor = Fraction(-1, denominator)
        for column in range(stage, level_count):
            right = previous[column]
            left = previous[column - 1]
            if right is None or left is None:
                raise ArithmeticError("malformed exact Richardson interval table")
            current[column] = affine_interval(
                right,
                right_factor,
                left,
                left_factor,
            )
        previous = current

    final = previous[-1]
    if final is None:
        raise ArithmeticError("missing final exact Richardson interval")
    return final


def analytic_richardson_remainder_bound(
    *, level_count: int, base_sides: int = 6
) -> Fraction:
    r"""Bound the exact tableau's distance from pi using pi < 22/7.

    Put s=level_count-1.  For N_j=base_sides*3^j,

        P_{N_j}=N_j sin(pi/N_j)

    is expanded through the N_j^{-2s} term.  The scale-3 Richardson weights
    preserve the constant term and cancel every mode N^{-2m}, 1<=m<=s.
    The alternating sine remainder for each input obeys

        |rem_j| <= U^(2s+3) / ((2s+3)! N_j^(2s+2)),  U=22/7.

    Applying the triangle inequality with the exact final weights yields a
    fully explicit rational bound.  This bound is intentionally conservative;
    it requires no empirical last-diagonal assumption.
    """

    if base_sides < 3:
        raise ValueError("base_sides must be at least 3")
    s = level_count - 1
    weights = richardson_weights(level_count)
    # Verify the moment conditions used in the proof, exactly rather than
    # assuming that the recursive table was implemented correctly.
    if sum(weights, Fraction(0)) != 1:
        raise ArithmeticError("Richardson weights fail constant preservation")
    for mode in range(1, s + 1):
        moment = sum(
            weight / (base_sides * 3**level) ** (2 * mode)
            for level, weight in enumerate(weights)
        )
        if moment != 0:
            raise ArithmeticError(
                f"Richardson weights fail exact cancellation at mode {mode}"
            )

    upper_pi = Fraction(22, 7)
    common = upper_pi ** (2 * s + 3) / factorial(2 * s + 3)

    weighted_scale_sum = Fraction(0)
    for level, weight in enumerate(weights):
        sides = base_sides * 3**level
        weighted_scale_sum += abs(weight) / sides ** (2 * s + 2)
    return common * weighted_scale_sum


def certified_decimal_places(bound: Fraction) -> int:
    """Largest D such that bound < 10^{-D}."""

    if bound <= 0:
        raise ValueError("bound must be positive")
    digits = 0
    while bound < Fraction(1, 10 ** (digits + 1)):
        digits += 1
    return digits


def build_richardson_certificate(
    *,
    production_value: object,
    level_count: int = 11,
    bisection_bits: int = 300,
    base_sides: int = 6,
) -> RichardsonCertificate:
    """Construct the complete exact rational R9 error certificate."""

    chords, root_steps = build_chord_intervals(
        level_count=level_count,
        bisection_bits=bisection_bits,
    )
    polygons = tuple(
        scale_interval(chord, Fraction(base_sides * 3**level))
        for level, chord in enumerate(chords)
    )
    tableau_interval = apply_richardson_intervals(polygons)
    weights = richardson_weights(level_count)
    production_fraction = mpf_to_fraction(production_value)

    production_inside = (
        tableau_interval.lower <= production_fraction <= tableau_interval.upper
    )
    production_bound = max(
        abs(production_fraction - tableau_interval.lower),
        abs(production_fraction - tableau_interval.upper),
    )
    analytic_bound = analytic_richardson_remainder_bound(
        level_count=level_count,
        base_sides=base_sides,
    )
    total_bound = production_bound + analytic_bound

    return RichardsonCertificate(
        level_count=level_count,
        maximum_level=level_count - 1,
        base_sides=base_sides,
        bisection_bits=bisection_bits,
        chord_intervals=chords,
        polygon_intervals=polygons,
        root_steps=root_steps,
        final_weights=weights,
        tableau_interval=tableau_interval,
        production_value=production_fraction,
        production_to_exact_tableau_bound=production_bound,
        analytic_tableau_to_pi_bound=analytic_bound,
        total_pi_error_bound=total_bound,
        certified_decimal_places=certified_decimal_places(total_bound),
        production_value_inside_tableau_interval=production_inside,
    )
