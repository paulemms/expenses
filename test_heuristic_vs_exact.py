"""Tests for cases where heuristic and exact methods differ."""

import unittest
from settle_expenses import settle_expenses


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

        balances = {}
        for exp in expenses:
            payer = exp["payer"]
            amount = exp["amount"]
            participants = exp["participants"]
            balances[payer] = balances.get(payer, 0) + amount
            n = len(participants)
            base = amount // n
            rem = amount % n
            for i, person in enumerate(participants):
                share = base + (1 if i < rem else 0)
                balances[person] = balances.get(person, 0) - share

        for p in result:
            balances[p["from"]] -= p["amount"]
            balances[p["to"]] += p["amount"]

        self.assertEqual(set(balances.values()), {0})


if __name__ == "__main__":
    unittest.main()
