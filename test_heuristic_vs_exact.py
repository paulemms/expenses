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


if __name__ == "__main__":
    unittest.main()
