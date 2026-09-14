import unittest
from decimal import Decimal

import numpy as np

from gqmkp_io import Instance
from verify_results import verify_solution


def example_instance():
    ins = Instance()
    ins.name, ins.n, ins.m, ins.h = 'synthetic', 3, 2, 2
    ins.w = np.array([2., 3., 1.])
    ins.s = np.array([4., 1.])
    ins.t_jr = np.array([0, 0, 1])
    ins.nr = np.array([1, 2])
    ins.cap = 10.
    ins.p = np.array([[5., 4.], [6., 5.], [2., 3.]])
    ins.q = np.array([[0., 7., 2.], [7., 0., 1.], [2., 1., 0.]])
    return ins


class VerificationTests(unittest.TestCase):
    def test_valid_solution_and_single_setup_charge(self):
        value, checks = verify_solution(example_instance(), [0, 0, 1], '21')
        self.assertEqual(value, Decimal(21))
        self.assertEqual(len(checks), 6)
        load = next(c for c in checks if c['constraint_type'] == 'knapsack_capacity' and c['index_0_based'] == '0')
        self.assertEqual(Decimal(load['observed_value']), Decimal(9))

    def test_unassigned_item_is_excluded(self):
        value, checks = verify_solution(example_instance(), [0, 0, 2], '18')
        self.assertEqual(value, Decimal(18))
        unused = next(c for c in checks if c['constraint_type'] == 'class_knapsack_limit' and c['index_0_based'] == '1')
        self.assertEqual(Decimal(unused['observed_value']), Decimal(0))

    def test_wrong_objective_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Objective mismatch'):
            verify_solution(example_instance(), [0, 0, 1], '20')

    def test_nonfinite_objective_is_rejected(self):
        for value in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Nonfinite'):
                verify_solution(example_instance(), [0, 0, 1], value)

    def test_capacity_violation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'knapsack_capacity'):
            verify_solution(example_instance(), [0, 0, 0], '23')

    def test_class_spread_violation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'class_knapsack_limit'):
            verify_solution(example_instance(), [0, 1, 2], '10')

    def test_wrong_length_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exactly 3'):
            verify_solution(example_instance(), [0, 0], '18')

    def test_invalid_assignment_domains_are_rejected(self):
        for value in (-1, 3, 0.5, True, '0'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'integers'):
                verify_solution(example_instance(), [value, 0, 1], '21')


if __name__ == '__main__':
    unittest.main()
