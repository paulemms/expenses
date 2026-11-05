"""Tests for cases where heuristic and exact methods differ."""

import unittest
from settle_expenses import settle_expenses, net_balances, _EXACT_THRESHOLD


class TestHeuristicVsExact(unittest.TestCase):
    """Test cases where heuristic produces suboptimal results."""

    def test_heuristic_uses_more_payments(self):
        """Heuristic uses 7 payments while exact uses 6."""
        expenses = [
            {"payer": "A", "amount": 8, "participants": ["A", "C"]},
            {"payer": "E", "amount": 10, "participants": ["E", "C"]},
            {"payer": "B", "amount": 2, "participants": ["B", "F"]},
            {"payer": "G", "amount": 4, "participants": ["G", "H"]},
            {"payer": "I", "amount": 24, "participants": ["I", "D"]},
            {"payer": "I", "amount": 10, "participants": ["I", "F"]},
            {"payer": "I", "amount": 8, "participants": ["I", "H"]},
        ]

        heuristic_result = settle_expenses(expenses, "heuristic")
        exact_result = settle_expenses(expenses, "exact")

        self.assertLess(len(exact_result), len(heuristic_result))
        self.assertEqual(len(exact_result), 6)
        self.assertEqual(len(heuristic_result), 7)

    def test_exact_produces_valid_settlement(self):
        """Exact result must settle all balances to zero."""
        expenses = [
            {"payer": "A", "amount": 8, "participants": ["A", "C"]},
            {"payer": "E", "amount": 10, "participants": ["E", "C"]},
            {"payer": "B", "amount": 2, "participants": ["B", "F"]},
            {"payer": "G", "amount": 4, "participants": ["G", "H"]},
            {"payer": "I", "amount": 24, "participants": ["I", "D"]},
            {"payer": "I", "amount": 10, "participants": ["I", "F"]},
            {"payer": "I", "amount": 8, "participants": ["I", "H"]},
        ]

        result = settle_expenses(expenses, "exact")

        balances = net_balances(expenses)

        for p in result:
            balances[p["from"]] += p["amount"]
            balances[p["to"]] -= p["amount"]

        self.assertEqual(set(balances.values()), {0})


class TestLargeNHeuristicRouting(unittest.TestCase):
    """Behaviour of the settle_expenses method dispatch for large inputs.

    The exact DP is O(3^n) and impractically slow past n=18 (50s+ at n=18),
    so n > 18 exercises the heuristic path. Under the optimisation
    requirement (spec.md:231) a heuristic answer is not provably minimal,
    so "auto" must refuse to emit one silently; callers opt in explicitly.
    """

    def _fixture(self):
        # 8 even 2-person expenses -> eight +1 / eight -1 (16 people)
        expenses = [
            {"payer": f"P{2 * k}", "amount": 2, "participants": [f"P{2 * k}", f"P{2 * k + 1}"]}
            for k in range(8)
        ]
        # One 3-person expense, amount 4 -> divmod(4, 3) = (1, 1):
        # payer credited +4, shares 2/1/1 -> +2 / -1 / -1 (3 people)
        expenses.append({"payer": "P16", "amount": 4, "participants": ["P16", "P17", "P18"]})
        return expenses

    def _assert_settles(self, result, non_zero):
        balances = dict(non_zero)
        for p in result:
            balances[p["from"]] += p["amount"]
            balances[p["to"]] -= p["amount"]
        self.assertTrue(all(v == 0 for v in balances.values()))

    def test_auto_raises_for_n_above_exact_threshold(self):
        """auto must not silently emit a non-minimal heuristic answer."""
        expenses = self._fixture()
        non_zero = {p: b for p, b in net_balances(expenses).items() if b != 0}

        self.assertEqual(len(non_zero), 19)
        self.assertGreater(len(non_zero), _EXACT_THRESHOLD)

        with self.assertRaises(ValueError) as ctx:
            settle_expenses(expenses)  # method defaults to "auto"
        message = str(ctx.exception).lower()
        self.assertIn("heuristic", message)
        self.assertIn(str(_EXACT_THRESHOLD), str(ctx.exception))

    def test_heuristic_settles_within_spec_bound(self):
        """method='heuristic' at n=19 settles to zero within the n-1 bound.

        This fixture's optimum is n - c = 19 - 9 = 10: the eight +1's cancel
        eight of the ten -1's, and the +2 cancels two more -1's -> c = 9
        disjoint zero-sum subsets. The heuristic reaches it here, and the
        count == 10 assertion guards against regressions.
        """
        expenses = self._fixture()
        non_zero = {p: b for p, b in net_balances(expenses).items() if b != 0}

        result = settle_expenses(expenses, "heuristic")

        self._assert_settles(result, non_zero)
        self.assertEqual(len(result), len(non_zero) - 9)
        self.assertLessEqual(len(result), len(non_zero) - 1)


if __name__ == "__main__":
    unittest.main()
