"""
Unit tests for settle_expenses.py
"""

import unittest
from settle_expenses import (
    settle_expenses,
    validate_expense,
    parse_csv,
    net_balances,
)
import tempfile
import os


class TestAutoSettlement(unittest.TestCase):
    """Tests for the settle_expenses function (default 'auto' method)."""

    def test_empty_input(self):
        """Empty input should return empty list."""
        result = settle_expenses([])
        self.assertEqual(result, [])

    def test_zero_value_expense(self):
        """Zero-value expense should produce no payments."""
        expenses = [{"payer": "Alice", "amount": 0, "participants": ["Alice", "Bob"]}]
        result = settle_expenses(expenses)
        self.assertEqual(result, [])

    def test_two_people_even_split(self):
        """Two people, equal split."""
        expenses = [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]}]
        result = settle_expenses(expenses)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sender"], "Bob")
        self.assertEqual(result[0]["recipient"], "Alice")
        self.assertEqual(result[0]["amount"], 50)

    def test_three_people_even_split(self):
        """Three people, equal split."""
        expenses = [{"payer": "Alice", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]}]
        result = settle_expenses(expenses)
        self.assertEqual(len(result), 2)
        amounts_from = {p["sender"]: p["amount"] for p in result}
        self.assertEqual(amounts_from.get("Bob"), 100)
        self.assertEqual(amounts_from.get("Charlie"), 100)

    def test_uneven_split(self):
        """Uneven split: 100 among 3 people."""
        expenses = [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]}]
        result = settle_expenses(expenses)
        self.assertTrue(all(p["amount"] > 0 for p in result))
        total_paid = sum(p["amount"] for p in result)
        self.assertEqual(total_paid, 66)

    def test_payer_not_in_participants(self):
        """Payer who is not a participant."""
        expenses = [
            {"payer": "Dave", "amount": 100, "participants": ["Alice", "Bob"]}
        ]
        result = settle_expenses(expenses)
        self.assertTrue(len(result) >= 1)
        total_received = sum(p["amount"] for p in result if p["recipient"] == "Dave")
        self.assertEqual(total_received, 100)

    def test_repeated_expenses_same_people(self):
        """Multiple expenses involving the same people."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        result = settle_expenses(expenses)
        self.assertEqual(result, [])

    def test_multiple_cases_independent(self):
        """Different participant groups within one case."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Charlie", "amount": 100, "participants": ["Charlie", "Dave"]},
        ]
        result = settle_expenses(expenses)
        self.assertTrue(len(result) >= 2)

    def test_large_amount(self):
        """Large integer amount."""
        expenses = [{"payer": "Alice", "amount": 1000000, "participants": ["Alice", "Bob"]}]
        result = settle_expenses(expenses)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["amount"], 500000)

    def test_unicode_names(self):
        """Names with Unicode characters."""
        expenses = [
            {"payer": "Alice Müller", "amount": 200, "participants": ["Alice Müller", "Böb", "Çarlie"]}
        ]
        result = settle_expenses(expenses)
        self.assertTrue(all(isinstance(p["sender"], str) and isinstance(p["recipient"], str) for p in result))

    def test_final_balances_zero(self):
        """Verify all final balances are zero."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Bob", "amount": 150, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 200, "participants": ["Alice", "Bob", "Charlie"]},
        ]
        result = settle_expenses(expenses)

        balances = net_balances(expenses)

        for p in result:
            balances[p["sender"]] += p["amount"]
            balances[p["recipient"]] -= p["amount"]

        self.assertTrue(all(b == 0 for b in balances.values()), f"Non-zero balances: {balances}")

    def test_minimum_payments_for_cycle(self):
        """Cycle: AâBâCâA should be settled with minimum payments."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 100, "participants": ["Charlie", "Alice"]},
        ]
        result = settle_expenses(expenses)
        self.assertEqual(result, [])

    def test_no_self_payments(self):
        """No payment from a person to themselves."""
        expenses = [
            {"payer": "Alice", "amount": 200, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        result = settle_expenses(expenses)
        for p in result:
            self.assertNotEqual(p["sender"], p["recipient"])

    def test_no_zero_payments(self):
        """No zero-value payments."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        result = settle_expenses(expenses)
        self.assertTrue(all(p["amount"] > 0 for p in result))

    def test_multiple_independent_cases(self):
        """Multiple independent cases in one CSV processed correctly."""
        csv_content = """case_id,payer,amount,participants
1,Alice,100,Alice;Bob
2,Charlie,200,Charlie;Dave
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(csv_content)
            tmp_path = f.name

        try:
            expenses_by_case = parse_csv(tmp_path)
            self.assertIn("1", expenses_by_case)
            self.assertIn("2", expenses_by_case)
            self.assertEqual(len(expenses_by_case["1"]), 1)
            self.assertEqual(len(expenses_by_case["2"]), 1)

            result_1 = settle_expenses(expenses_by_case["1"])
            result_2 = settle_expenses(expenses_by_case["2"])
            self.assertEqual(len(result_1), 1)
            self.assertEqual(len(result_2), 1)
        finally:
            os.unlink(tmp_path)


class TestValidateExpense(unittest.TestCase):
    """Tests for validate_expense function."""

    def test_valid_expense(self):
        """Valid expense should pass validation."""
        expense = {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]}
        validate_expense(expense, 1)

    def test_missing_payer(self):
        """Missing payer should raise ValueError."""
        expense = {"amount": 100, "participants": ["Alice", "Bob"]}
        with self.assertRaises(ValueError):
            validate_expense(expense, 1)

    def test_negative_amount(self):
        """Negative amount should raise ValueError."""
        expense = {"payer": "Alice", "amount": -100, "participants": ["Alice", "Bob"]}
        with self.assertRaises(ValueError):
            validate_expense(expense, 1)

    def test_non_integer_amount(self):
        """Non-integer amount should raise ValueError."""
        expense = {"payer": "Alice", "amount": 100.5, "participants": ["Alice", "Bob"]}
        with self.assertRaises(ValueError):
            validate_expense(expense, 1)

    def test_boolean_amount(self):
        """Boolean amount should raise ValueError."""
        expense = {"payer": "Alice", "amount": True, "participants": ["Alice", "Bob"]}
        with self.assertRaises(ValueError):
            validate_expense(expense, 1)

    def test_empty_participants(self):
        """Empty participant list should raise ValueError."""
        expense = {"payer": "Alice", "amount": 100, "participants": []}
        with self.assertRaises(ValueError):
            validate_expense(expense, 1)

    def test_duplicate_participants(self):
        """Duplicate participants should raise ValueError."""
        expense = {"payer": "Alice", "amount": 100, "participants": ["Alice", "Alice"]}
        with self.assertRaises(ValueError):
            validate_expense(expense, 1)

    def test_empty_payer_name(self):
        """Empty payer name should raise ValueError."""
        expense = {"payer": "", "amount": 100, "participants": ["Alice", "Bob"]}
        with self.assertRaises(ValueError):
            validate_expense(expense, 1)

    def test_whitespace_trimming(self):
        """Whitespace in payer should be trimmed."""
        expense = {"payer": "  Alice  ", "amount": 100, "participants": [" Alice ", " Bob "]}
        validate_expense(expense, 1)


class TestParseCsv(unittest.TestCase):
    """Tests for parse_csv function."""

    def test_parse_valid_csv(self):
        """Valid CSV should parse correctly."""
        csv_content = """case_id,payer,amount,participants
1,Alice,100,Alice;Bob
2,Bob,200,Bob;Charlie
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(csv_content)
            tmp_path = f.name

        try:
            result = parse_csv(tmp_path)
            self.assertEqual(len(result), 2)
            self.assertIn("1", result)
            self.assertIn("2", result)
            self.assertEqual(result["1"][0]["amount"], 100)
            self.assertEqual(result["2"][0]["payer"], "Bob")
        finally:
            os.unlink(tmp_path)

    def test_missing_columns(self):
        """CSV with missing columns should raise ValueError."""
        csv_content = """case_id,payer,amount
1,Alice,100
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(csv_content)
            tmp_path = f.name

        try:
            with self.assertRaises(ValueError):
                parse_csv(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_empty_file(self):
        """Empty CSV should raise ValueError."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("")
            tmp_path = f.name

        try:
            with self.assertRaises(ValueError):
                parse_csv(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        """Non-existent file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            parse_csv("/nonexistent/file.csv")

    def test_semicolon_splitting(self):
        """Participants should be split on semicolons."""
        csv_content = """case_id,payer,amount,participants
1,Alice,100,Alice; Bob ; Charlie
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(csv_content)
            tmp_path = f.name

        try:
            result = parse_csv(tmp_path)
            participants = result["1"][0]["participants"]
            self.assertEqual(participants, ["Alice", "Bob", "Charlie"])
        finally:
            os.unlink(tmp_path)

    def test_unicode_in_csv(self):
        """Unicode in CSV should parse correctly."""
        csv_content = "1,Älice,100,Älice; Böb"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write("case_id,payer,amount,participants\n")
            f.write(csv_content + "\n")
            tmp_path = f.name

        try:
            result = parse_csv(tmp_path)
            self.assertEqual(result["1"][0]["payer"], "Älice")
        finally:
            os.unlink(tmp_path)

    def test_malformed_row(self):
        """Malformed row should raise ValueError with row number."""
        csv_content = """case_id,payer,amount,participants
1,Alice,-100,Alice;Bob
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(csv_content)
            tmp_path = f.name

        try:
            with self.assertRaises(ValueError) as cm:
                parse_csv(tmp_path)
            self.assertIn("Row 2", str(cm.exception))
        finally:
            os.unlink(tmp_path)


class TestMinimumPayments(unittest.TestCase):
    """Tests for minimum payment optimization."""

    def test_optimal_for_known_case(self):
        """Test against a known optimal solution."""
        expenses = [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]}]
        result = settle_expenses(expenses)
        self.assertEqual(len(result), 1)

    def test_three_people_optimal(self):
        """Three people should need at most 2 payments."""
        expenses = [{"payer": "Alice", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]}]
        result = settle_expenses(expenses)
        self.assertEqual(len(result), 2)

    def test_complex_case_optimal(self):
        """Complex case should achieve optimal payment count."""
        expenses = [
            {"payer": "Alice", "amount": 500, "participants": ["Alice", "Bob", "Charlie", "Dave"]},
            {"payer": "Bob", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 200, "participants": ["Alice", "Charlie"]},
        ]
        result = settle_expenses(expenses)
        self.assertEqual(len(result), 3)


class TestNetBalances(unittest.TestCase):
    """Tests for the net_balances function."""

    def test_single_expense_two_people(self):
        """Single expense between two people."""
        expenses = [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]}]
        balances = net_balances(expenses)
        self.assertEqual(balances["Alice"], 50)
        self.assertEqual(balances["Bob"], -50)

    def test_single_expense_three_people(self):
        """Single expense split among three people."""
        expenses = [{"payer": "Alice", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]}]
        balances = net_balances(expenses)
        self.assertEqual(balances["Alice"], 200)
        self.assertEqual(balances["Bob"], -100)
        self.assertEqual(balances["Charlie"], -100)

    def test_uneven_split(self):
        """Uneven split distributes remainder to first participants."""
        expenses = [{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]}]
        balances = net_balances(expenses)
        self.assertEqual(balances["Alice"], 66)
        self.assertEqual(balances["Bob"], -33)
        self.assertEqual(balances["Charlie"], -33)

    def test_multiple_expenses(self):
        """Multiple expenses accumulate correctly."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        balances = net_balances(expenses)
        self.assertEqual(balances["Alice"], 0)
        self.assertEqual(balances["Bob"], 0)

    def test_payer_not_in_participants(self):
        """Payer not in participants list."""
        expenses = [{"payer": "Dave", "amount": 100, "participants": ["Alice", "Bob"]}]
        balances = net_balances(expenses)
        self.assertEqual(balances["Dave"], 100)
        self.assertEqual(balances["Alice"], -50)
        self.assertEqual(balances["Bob"], -50)

    def test_zero_sum(self):
        """Net balances should sum to zero."""
        expenses = [
            {"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Bob", "amount": 200, "participants": ["Bob", "Charlie", "Dave"]},
        ]
        balances = net_balances(expenses)
        self.assertEqual(sum(balances.values()), 0)

    def test_empty_expenses(self):
        """Empty expense list returns empty dict."""
        balances = net_balances([])
        self.assertEqual(balances, {})


if __name__ == "__main__":
    unittest.main()
