"""Settlement scenario and validity checks for the cached exact1 solver."""

import unittest

from settle_expenses import net_balances, settle_expenses
from tests.settlement_method_checks import SettlementMethodTestsMixin


class TestExact1(SettlementMethodTestsMixin, unittest.TestCase):
    """Run the shared scenarios and settlement checks with exact1."""

    methods = ("exact1",)

    def test_exact1_produces_valid_settlement(self):
        """Exact1 result must settle all balances to zero."""
        expenses = [
            {"payer": "A", "amount": 8, "participants": ["A", "C"]},
            {"payer": "E", "amount": 10, "participants": ["E", "C"]},
            {"payer": "B", "amount": 2, "participants": ["B", "F"]},
            {"payer": "G", "amount": 4, "participants": ["G", "H"]},
            {"payer": "I", "amount": 24, "participants": ["I", "D"]},
            {"payer": "I", "amount": 10, "participants": ["I", "F"]},
            {"payer": "I", "amount": 8, "participants": ["I", "H"]},
        ]

        result = settle_expenses(expenses, "exact1")

        balances = net_balances(expenses)

        for p in result:
            balances[p["sender"]] += p["amount"]
            balances[p["recipient"]] -= p["amount"]

        self.assertEqual(set(balances.values()), {0})


if __name__ == "__main__":
    unittest.main()
