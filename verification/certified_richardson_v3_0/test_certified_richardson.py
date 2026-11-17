#!/usr/bin/env python3
"""Unit tests for the exact Version 3.0 Richardson certificate."""

from __future__ import annotations

import unittest
from fractions import Fraction

from mpmath import mp

from certified_richardson import (
    _bisect_fixed_c_root,
    analytic_richardson_remainder_bound,
    build_richardson_certificate,
    cubic_fraction,
    richardson_weights,
)
from pi_g_construction import compute_pi_g


class CertifiedRichardsonTests(unittest.TestCase):
    def test_exact_initial_root_bracket(self) -> None:
        bracket = _bisect_fixed_c_root(Fraction(1, 2), 80)
        self.assertGreaterEqual(cubic_fraction(bracket.lower, Fraction(1, 2)), 0)
        self.assertLessEqual(cubic_fraction(bracket.upper, Fraction(1, 2)), 0)
        self.assertLess(bracket.width, Fraction(1, 2**80))

    def test_exact_richardson_moments(self) -> None:
        level_count = 11
        weights = richardson_weights(level_count)
        self.assertEqual(sum(weights, Fraction(0)), 1)
        for mode in range(1, level_count):
            moment = sum(
                weight / (6 * 3**level) ** (2 * mode)
                for level, weight in enumerate(weights)
            )
            self.assertEqual(moment, 0)

    def test_analytic_bound_is_positive_and_below_target(self) -> None:
        bound = analytic_richardson_remainder_bound(level_count=11)
        self.assertGreater(bound, 0)
        self.assertLess(bound, Fraction(1, 10**80))

    def test_canonical_r9_certificate(self) -> None:
        mp.dps = 120
        production = compute_pi_g(level_count=11, work_dps=120)
        certificate = build_richardson_certificate(
            production_value=production.value,
            level_count=11,
            bisection_bits=300,
        )
        self.assertTrue(certificate.production_value_inside_tableau_interval)
        self.assertLess(certificate.total_pi_error_bound, Fraction(1, 10**80))
        self.assertGreaterEqual(certificate.certified_decimal_places, 80)


if __name__ == "__main__":
    unittest.main()
