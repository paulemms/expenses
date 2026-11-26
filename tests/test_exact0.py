"""Optimality and settlement checks for the uncached recursive solver."""

import itertools
import unittest
import warnings

from settle_expenses import (
    _find_max_zero_sum_subsets_exact,
    _find_max_zero_sum_subsets_exact0,
    settle_expenses,
)


class TestExact0(unittest.TestCase):
    def test_empty_and_zero_balances(self):
        self.assertEqual(_find_max_zero_sum_subsets_exact0([], {}), [])
        self.assertEqual(settle_expenses([], method="exact0"), [])
        self.assertEqual(settle_expenses([
            {"payer": "A", "amount": 0, "participants": ["A", "B"]}
        ], method="exact0"), [])

    def test_exhaustive_small_partitions(self):
        # Check all small non-zero, zero-total balance vectors against the
        # independently implemented exact1 solver with cached subset results.
        for n in range(2, 7):
            people = [str(i) for i in range(n)]
            for values in itertools.product((-2, -1, 1, 2), repeat=n):
                if sum(values) != 0:
                    continue
                with self.subTest(values=values):
                    balances = dict(zip(people, values))
                    groups = _find_max_zero_sum_subsets_exact0(people, balances)
                    reference = _find_max_zero_sum_subsets_exact(people, balances)
                    self.assertEqual(len(groups), len(reference))
                    members = [person for group in groups for person in group]
                    self.assertCountEqual(members, people)
                    self.assertTrue(all(sum(balances[p] for p in g) == 0 for g in groups))

    def test_known_optimum_where_heuristic_fails(self):
        expenses = [
            {"payer": payer, "amount": amount, "participants": [payer, debtor]}
            for payer, amount, debtor in [
                ("A", 8, "C"), ("E", 10, "C"), ("B", 2, "F"),
                ("G", 4, "H"), ("I", 24, "D"), ("I", 10, "F"), ("I", 8, "H"),
            ]
        ]
        # These balances are calculated independently from the fixture.
        balances = {"A": 4, "B": 1, "C": -9, "D": -12, "E": 5,
                    "F": -6, "G": 2, "H": -6, "I": 21}
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            payments = settle_expenses(expenses, method="exact0", threshold=0)
        self.assertEqual(caught, [])
        self.assertEqual(len(payments), 6)
        for payment in payments:
            sender, recipient, amount = (
                payment["sender"], payment["recipient"], payment["amount"]
            )
            self.assertNotEqual(sender, recipient)
            self.assertGreater(amount, 0)
            self.assertLessEqual(amount, -balances[sender])
            self.assertLessEqual(amount, balances[recipient])
            balances[sender] += amount
            balances[recipient] -= amount
        self.assertTrue(all(value == 0 for value in balances.values()))


if __name__ == "__main__":
    unittest.main()
