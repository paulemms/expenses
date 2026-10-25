"""Test case showing exact method balance verification failure.

This test documents a case where the exact method produces 6 payments
but the balances don't sum to zero after applying them.

Run with: python test_exact_balance_failure.py
"""

import unittest
from settle_expenses import settle_expenses


class TestExactBalanceFailure(unittest.TestCase):
    """Test case for manual review."""

    def test_exact_balance_not_zero(self):
        """Exact result does NOT settle all balances to zero.

        This test is expected to FAIL. It documents a bug in the exact
        method or in the balance calculation.
        """
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

        # Compute net balances
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

        print("\nExpenses:")
        for exp in expenses:
            print(f"  {exp['payer']} paid {exp['amount']} for {exp['participants']}")

        print(f"\nNet balances: {balances}")
        print(f"\nExact payments ({len(result)}):")
        for p in result:
            print(f"  {p['from']} -> {p['to']}: {p['amount']}")

        for p in result:
            balances[p["from"]] -= p["amount"]
            balances[p["to"]] += p["amount"]

        print(f"\nAfter payments: {balances}")
        print(f"All zero? {all(v == 0 for v in balances.values())}")

        # This will fail - balances are not zero
        self.assertEqual(set(balances.values()), {0})


if __name__ == "__main__":
    unittest.main()
