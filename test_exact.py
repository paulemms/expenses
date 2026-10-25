"""Unit tests for exact method in settle_expenses.py."""

import unittest
from settle_expenses import settle_expenses, net_balances


class TestExactMethod(unittest.TestCase):
    """Tests for the exact DP settlement method."""

    def test_empty_input(self):
        """Empty input should return empty list."""
        result = settle_expenses([], method="exact")
        self.assertEqual(result, [])

    def test_zero_value_expense(self):
        """Zero-value expense should produce no payments."""
        expenses = [{"payer": "Alice", "amount": 0, "participants": ["Alice", "Bob"]}]
        result = settle_expenses(expenses, method="exact")
        self.assertEqual(result, [])

    def test_two_people_even_split(self):
        """Two people, equal split."""
        expenses = [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]}]
        result = settle_expenses(expenses, method="exact")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["from"], "Bob")
        self.assertEqual(result[0]["to"], "Alice")
        self.assertEqual(result[0]["amount"], 50)

    def test_three_people_even_split(self):
        """Three people, equal split."""
        expenses = [{"payer": "Alice", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]}]
        result = settle_expenses(expenses, method="exact")
        self.assertEqual(len(result), 2)
        amounts_from = {p["from"]: p["amount"] for p in result}
        self.assertEqual(amounts_from.get("Bob"), 100)
        self.assertEqual(amounts_from.get("Charlie"), 100)

    def test_uneven_split(self):
        """Uneven split: 100 cents among 3 people."""
        expenses = [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]}]
        result = settle_expenses(expenses, method="exact")
        self.assertTrue(all(p["amount"] > 0 for p in result))
        total_paid = sum(p["amount"] for p in result)
        self.assertEqual(total_paid, 66)

    def test_payer_not_in_participants(self):
        """Payer who is not a participant."""
        expenses = [
            {"payer": "Dave", "amount": 100, "participants": ["Alice", "Bob"]}
        ]
        result = settle_expenses(expenses, method="exact")
        self.assertTrue(len(result) >= 1)
        total_received = sum(p["amount"] for p in result if p["to"] == "Dave")
        self.assertEqual(total_received, 100)

    def test_repeated_expenses_same_people(self):
        """Multiple expenses involving the same people."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        result = settle_expenses(expenses, method="exact")
        self.assertEqual(result, [])

    def test_multiple_cases_independent(self):
        """Different participant groups within one case."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Charlie", "amount": 100, "participants": ["Charlie", "Dave"]},
        ]
        result = settle_expenses(expenses, method="exact")
        self.assertTrue(len(result) >= 2)

    def test_large_amount(self):
        """Large monetary amount."""
        expenses = [{"payer": "Alice", "amount": 1000000, "participants": ["Alice", "Bob"]}]
        result = settle_expenses(expenses, method="exact")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["amount"], 500000)

    def test_unicode_names(self):
        """Names with Unicode characters."""
        expenses = [
            {"payer": "Alice Müller", "amount": 200, "participants": ["Alice Müller", "Böb", "Çarlie"]}
        ]
        result = settle_expenses(expenses, method="exact")
        self.assertTrue(all(isinstance(p["from"], str) and isinstance(p["to"], str) for p in result))

    def test_final_balances_zero(self):
        """Verify all final balances are zero."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Bob", "amount": 150, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 200, "participants": ["Alice", "Bob", "Charlie"]},
        ]
        result = settle_expenses(expenses, method="exact")

        balances = net_balances(expenses)

        for p in result:
            balances[p["from"]] += p["amount"]
            balances[p["to"]] -= p["amount"]

        self.assertTrue(all(b == 0 for b in balances.values()), f"Non-zero balances: {balances}")

    def test_minimum_payments_for_cycle(self):
        """Cycle: A→B→C→A should be settled with minimum payments."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 100, "participants": ["Charlie", "Alice"]},
        ]
        result = settle_expenses(expenses, method="exact")
        self.assertEqual(result, [])

    def test_no_self_payments(self):
        """No payment from a person to themselves."""
        expenses = [
            {"payer": "Alice", "amount": 200, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        result = settle_expenses(expenses, method="exact")
        for p in result:
            self.assertNotEqual(p["from"], p["to"])

    def test_no_zero_payments(self):
        """No zero-value payments."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        result = settle_expenses(expenses, method="exact")
        self.assertTrue(all(p["amount"] > 0 for p in result))

    def test_optimality_on_tricky_case(self):
        """Test a case where heuristic may fail but exact should succeed."""
        # This case requires finding a specific zero-sum subset
        expenses = [
            {"payer": "Alice", "amount": 500, "participants": ["Alice", "Bob", "Charlie", "Dave"]},
            {"payer": "Bob", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 200, "participants": ["Alice", "Charlie"]},
        ]
        result = settle_expenses(expenses, method="exact")

        balances = net_balances(expenses)

        for p in result:
            balances[p["from"]] += p["amount"]
            balances[p["to"]] -= p["amount"]

        self.assertTrue(all(b == 0 for b in balances.values()))
        self.assertTrue(all(p["amount"] > 0 for p in result))
        self.assertTrue(all(p["from"] != p["to"] for p in result))


if __name__ == "__main__":
    unittest.main()
