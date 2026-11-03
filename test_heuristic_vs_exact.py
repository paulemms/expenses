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
    """Exercise the auto -> heuristic branch (n > _EXACT_THRESHOLD).

    The exact DP is O(3^n) and impractically slow past n=18 (50s+ at n=18),
    so this fixture exercises the heuristic path that `auto` selects once the
    balance count exceeds the exact threshold.
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

    def test_auto_routes_to_heuristic_and_settles(self):
        """19 non-zero balances: auto uses heuristic, settles to zero.

        Optimal packing: the eight +1's cancel eight of the ten -1's (8
        subsets) and the +2 cancels two more -1's (1 subset) -> c = 9, so
        the minimum payment count is n - c = 19 - 9 = 10.
        """
        expenses = self._fixture()
        non_zero = {p: b for p, b in net_balances(expenses).items() if b != 0}

        self.assertGreater(len(non_zero), _EXACT_THRESHOLD)
        self.assertEqual(len(non_zero), 19)
        self.assertEqual(sum(non_zero.values()), 0)

        result = settle_expenses(expenses)  # "auto" -> heuristic at n=19

        balances = dict(non_zero)
        for p in result:
            balances[p["from"]] += p["amount"]
            balances[p["to"]] -= p["amount"]
        self.assertTrue(all(v == 0 for v in balances.values()))

        self.assertEqual(len(result), len(non_zero) - 9)
        self.assertLessEqual(len(result), len(non_zero) - 1)


if __name__ == "__main__":
    unittest.main()
