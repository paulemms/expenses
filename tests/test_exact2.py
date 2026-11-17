"""Optimality and reconstruction checks for the O(n * 2^n) solver."""

import itertools
import random
import unittest
import warnings
from unittest.mock import patch

from settle_expenses import (
    _find_max_zero_sum_subsets_exact,
    _find_max_zero_sum_subsets_exact2,
    net_balances,
    settle_expenses,
)


class TestExact2(unittest.TestCase):
    def test_default_uses_exact2_at_auto_threshold(self):
        expenses = [{"payer": "A", "amount": 10, "participants": ["B"]}]
        with patch(
            "settle_expenses._find_max_zero_sum_subsets_exact2",
            wraps=_find_max_zero_sum_subsets_exact2,
        ) as primary, patch(
            "settle_expenses._find_max_zero_sum_subsets_exact",
            side_effect=AssertionError("auto must use exact2"),
        ):
            result = settle_expenses(expenses, threshold=2)
        primary.assert_called_once()
        self.assertEqual(result, [{"sender": "B", "recipient": "A", "amount": 10}])

    def assert_settles(self, expenses, payments):
        balances = net_balances(expenses)
        for payment in payments:
            self.assertGreater(payment["amount"], 0)
            self.assertNotEqual(payment["sender"], payment["recipient"])
            balances[payment["sender"]] += payment["amount"]
            balances[payment["recipient"]] -= payment["amount"]
        self.assertTrue(all(value == 0 for value in balances.values()))

    def test_empty_and_zero_balances(self):
        self.assertEqual(settle_expenses([], method="exact2"), [])
        self.assertEqual(settle_expenses([
            {"payer": "A", "amount": 0, "participants": ["A", "B"]}
        ], method="exact2"), [])
        self.assertEqual(_find_max_zero_sum_subsets_exact2([], {}), [])

    def test_exhaustive_small_partitions(self):
        # Compare all small non-zero, zero-total balance vectors with the
        # independent O(3^n) solver, including repeated values and many ties.
        for n in range(2, 7):
            people = [str(i) for i in range(n)]
            for values in itertools.product((-2, -1, 1, 2), repeat=n):
                if sum(values) != 0:
                    continue
                with self.subTest(values=values):
                    balances = dict(zip(people, values))
                    groups = _find_max_zero_sum_subsets_exact2(people, balances)
                    reference = _find_max_zero_sum_subsets_exact(people, balances)
                    self.assertEqual(len(groups), len(reference))
                    members = [person for group in groups for person in group]
                    self.assertCountEqual(members, people)
                    self.assertTrue(all(sum(balances[p] for p in g) == 0 for g in groups))

    def test_random_expenses_match_exact(self):
        rng = random.Random(42)
        for case in range(100):
            people = [str(i) for i in range(rng.randint(2, 9))]
            expenses = [
                {"payer": rng.choice(people), "amount": rng.randint(0, 100),
                 "participants": rng.sample(people, rng.randint(1, len(people)))}
                for _ in range(rng.randint(1, 12))
            ]
            with self.subTest(case=case):
                result = settle_expenses(expenses, method="exact2")
                self.assertEqual(len(result), len(settle_expenses(expenses, method="exact")))
                self.assert_settles(expenses, result)

    def test_known_optimum_where_heuristic_fails(self):
        expenses = [
            {"payer": payer, "amount": amount, "participants": [payer, debtor]}
            for payer, amount, debtor in [
                ("A", 8, "C"), ("E", 10, "C"), ("B", 2, "F"),
                ("G", 4, "H"), ("I", 24, "D"), ("I", 10, "F"), ("I", 8, "H"),
            ]
        ]
        result = settle_expenses(expenses, method="exact2")
        self.assertEqual(len(result), 6)
        self.assert_settles(expenses, result)

    def test_explicit_exact2_above_auto_threshold(self):
        # 19 non-zero balances: nine +1/-1 pairs, plus an extra -1
        # sharing a creditor of +2. Optimum is ten payments.
        expenses = [
            {"payer": f"C{i}", "amount": 1, "participants": [f"D{i}"]}
            for i in range(9)
        ]
        expenses.append({"payer": "C0", "amount": 1, "participants": ["D9"]})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = settle_expenses(expenses, method="exact2", threshold=0)
        self.assertEqual(caught, [])
        self.assertEqual(len(result), 10)
        self.assert_settles(expenses, result)


if __name__ == "__main__":
    unittest.main()
