"""Shared settlement scenarios for method-specific test classes."""

from settle_expenses import net_balances, settle_expenses

# Sentinel for scenarios checked by name instead of a fixed payment list.
_NO_EXPECTED = object()


class SettlementMethodTestsMixin:
    """Shared scenario checks; subclasses select the methods to exercise."""

    # Shared scenarios for each explicitly selected settlement method
    _test_scenarios = [
        ("empty_input", [], []),
        ("zero_value_expense",
         [{"payer": "Alice", "amount": 0, "participants": ["Alice", "Bob"]}], []),
        ("two_people_even_split",
         [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]}],
         [{"sender": "Bob", "recipient": "Alice", "amount": 50}]),
        ("three_people_even_split",
         [{"payer": "Alice", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]}],
         [{"sender": "Bob", "recipient": "Alice", "amount": 100},
          {"sender": "Charlie", "recipient": "Alice", "amount": 100}]),
        ("uneven_split",
         [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]}],
         _NO_EXPECTED),  # Only check total_paid
        ("repeated_expenses_same_people",
         [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
          {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]}], []),
        ("no_self_payments",
         [{"payer": "Alice", "amount": 200, "participants": ["Alice", "Bob"]},
          {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]}],
         _NO_EXPECTED),
        ("no_zero_payments",
         [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
          {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]}],
         _NO_EXPECTED),
        ("minimum_payments_for_cycle",
         [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
          {"payer": "Bob", "amount": 100, "participants": ["Bob", "Charlie"]},
          {"payer": "Charlie", "amount": 100, "participants": ["Charlie", "Alice"]}], []),
        ("large_amount",
         [{"payer": "Alice", "amount": 1000000, "participants": ["Alice", "Bob"]}],
         [{"sender": "Bob", "recipient": "Alice", "amount": 500000}]),
        ("unicode_names",
         [{"payer": "Alice MÃ¼ller", "amount": 200,
           "participants": ["Alice MÃ¼ller", "BÃ¶b", "Ãarlie"]}],
         _NO_EXPECTED),
    ]

    def _run_scenario(self, scenario_name, expenses, expected):
        """Run a scenario for each selected method."""
        for method in self.methods:
            with self.subTest(method=method, scenario=scenario_name):
                result = settle_expenses(expenses, method=method)

                if expected is _NO_EXPECTED:
                    # Scenario-specific assertions
                    if scenario_name == "uneven_split":
                        self.assertTrue(all(p["amount"] > 0 for p in result))
                        self.assertEqual(sum(p["amount"] for p in result), 66)
                    elif scenario_name == "no_self_payments":
                        self.assertTrue(all(p["sender"] != p["recipient"] for p in result))
                    elif scenario_name == "no_zero_payments":
                        self.assertTrue(all(p["amount"] > 0 for p in result))
                    elif scenario_name == "unicode_names":
                        self.assertTrue(all(isinstance(p["sender"], str) and isinstance(p["recipient"], str) for p in result))
                else:
                    # Build a canonical dict to ignore payment order
                    result_dict = {(p["sender"], p["recipient"]): p["amount"] for p in result}
                    expected_dict = {(e["sender"], e["recipient"]): e["amount"] for e in expected}
                    self.assertEqual(result_dict, expected_dict)

    def test_scenarios(self):
        """Run all scenarios for the selected methods."""
        for name, expenses, expected in self._test_scenarios:
            self._run_scenario(name, expenses, expected)

    def test_balances_settle(self):
        """Verify final balances are zero for each selected method."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Bob", "amount": 150, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 200, "participants": ["Alice", "Bob", "Charlie"]},
        ]
        for method in self.methods:
            with self.subTest(method=method):
                result = settle_expenses(expenses, method=method)
                balances = net_balances(expenses)
                for p in result:
                    balances[p["sender"]] += p["amount"]
                    balances[p["recipient"]] -= p["amount"]
                self.assertTrue(all(b == 0 for b in balances.values()))

    def test_payer_not_in_participants(self):
        """Payer who is not a participant."""
        expenses = [{"payer": "Dave", "amount": 100, "participants": ["Alice", "Bob"]}]
        for method in self.methods:
            with self.subTest(method=method):
                result = settle_expenses(expenses, method=method)
                self.assertTrue(len(result) >= 1)
                total_received = sum(p["amount"] for p in result if p["recipient"] == "Dave")
                self.assertEqual(total_received, 100)

    def test_multiple_cases_independent(self):
        """Different participant groups within one case."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Charlie", "amount": 100, "participants": ["Charlie", "Dave"]},
        ]
        for method in self.methods:
            with self.subTest(method=method):
                result = settle_expenses(expenses, method=method)
                self.assertTrue(len(result) >= 2)
