"""Validity, optimality comparisons and dispatch checks for heuristic and greedy."""

import random
import unittest
from settle_expenses import _settle, net_balances, settle_expenses
from tests.settlement_method_checks import SettlementMethodTestsMixin


class TestHeuristicVsExact(unittest.TestCase):
    """Test cases where heuristic produces suboptimal results."""

    def test_heuristic_uses_more_payments(self):
        """Heuristic uses 7 payments while exact2 uses 6."""
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
        exact_result = settle_expenses(expenses, "exact2")

        self.assertLess(len(exact_result), len(heuristic_result))
        self.assertEqual(len(exact_result), 6)
        self.assertEqual(len(heuristic_result), 7)


class TestLargeNHeuristicRouting(unittest.TestCase):
    """Behaviour of the settle_expenses method dispatch for large inputs.

    Auto uses exact2's cached zero-sum prefix DP with one-person transitions
    (O(n * 2^n) time) up to its threshold (18 by default).
    Above that threshold it warns and falls back to polynomial greedy
    settlement, which is not guaranteed to minimize the payment count.
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
            balances[p["sender"]] += p["amount"]
            balances[p["recipient"]] -= p["amount"]
        self.assertTrue(all(v == 0 for v in balances.values()))

    def test_auto_warns_and_falls_back_to_greedy(self):
        """auto warns when n > threshold and uses greedy instead of raising."""
        import warnings

        expenses = self._fixture()
        non_zero = {p: b for p, b in net_balances(expenses).items() if b != 0}

        self.assertEqual(len(non_zero), 19)
        self.assertGreater(len(non_zero), 18)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = settle_expenses(expenses)  # method defaults to "auto"

        self.assertEqual(len(w), 1)
        self.assertTrue(issubclass(w[0].category, UserWarning))
        self.assertIn("auto", str(w[0].message).lower())
        self.assertIn("greedy", str(w[0].message).lower())

        # Greedy always settles to zero
        self._assert_settles(result, non_zero)

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


class TestHeuristicMethods(SettlementMethodTestsMixin, unittest.TestCase):
    """Shared settlement scenarios for both non-exact methods."""

    methods = ("heuristic", "greedy")


class TestGreedyMethod(unittest.TestCase):
    """Tests for the polynomial O(n log n) greedy settlement method.

    Greedy settles every balance at once with the largest-debtor-to-largest-
    creditor pass, so it is fast and size-unbounded but not guaranteed minimal.
    These tests pin that it stays valid, respects the n - 1 bound, matches exact
    where the optimum is obvious, and matches the payment count of the
    reference _settle() matching on a fixed example.
    """

    def _assert_valid(self, result, expenses, non_zero_count):
        """A settlement settles to zero, has no self-payments/zero amounts,
        and uses at most non_zero_count - 1 payments."""
        balances = net_balances(expenses)
        for p in result:
            self.assertNotEqual(
                p["sender"], p["recipient"], f"self-payment detected: {p}"
            )
            self.assertGreater(p["amount"], 0, f"non-positive payment: {p}")
            balances[p["sender"]] += p["amount"]
            balances[p["recipient"]] -= p["amount"]
        self.assertTrue(
            all(v == 0 for v in balances.values()),
            f"unsettled balances: {[v for v in balances.values() if v != 0]}",
        )
        if non_zero_count:
            self.assertLessEqual(len(result), non_zero_count - 1)

    def test_greedy_matches_exact2_on_trivial_scenarios(self):
        """Where the optimum is obvious, greedy equals exact2 exactly."""
        pinned = [
            ([{"payer": "Alice", "amount": 100, "participants": ["Alice", "Bob"]}],
             [{"sender": "Bob", "recipient": "Alice", "amount": 50}]),
            ([{"payer": "Alice", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]}],
             [{"sender": "Bob", "recipient": "Alice", "amount": 100},
              {"sender": "Charlie", "recipient": "Alice", "amount": 100}]),
            ([{"payer": "Alice", "amount": 1000000, "participants": ["Alice", "Bob"]}],
             [{"sender": "Bob", "recipient": "Alice", "amount": 500000}]),
        ]
        for expenses, expected in pinned:
            with self.subTest(scenario=expenses):
                result = settle_expenses(expenses, "greedy")
                result_dict = {(p["sender"], p["recipient"]): p["amount"] for p in result}
                expected_dict = {(e["sender"], e["recipient"]): e["amount"] for e in expected}
                self.assertEqual(result_dict, expected_dict)
                self.assertEqual(len(result), len(settle_expenses(expenses, "exact2")))

    def test_greedy_is_optimal_on_known_optimum(self):
        """On the known-optimum fixture, greedy matches exact2 (6), not heuristic (7).

        The fixture has a known optimum of 6 payments; the heuristic misses it
        with 7. Greedy reaches the optimum here, which also confirms the heap
        implementation settles to zero on this multi-group input.
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
        result = settle_expenses(expenses, "greedy")
        self._assert_valid(result, expenses, non_zero_count=9)
        self.assertEqual(len(result), 6)
        self.assertEqual(len(settle_expenses(expenses, "exact2")), 6)

    def test_greedy_uses_more_payments_than_exact2(self):
        """Largest-first matching uses five payments; the optimum is four."""
        expenses = [
            {"payer": "A", "amount": 8, "participants": ["D"]},
            {"payer": "B", "amount": 1, "participants": ["D"]},
            {"payer": "B", "amount": 6, "participants": ["E"]},
            {"payer": "C", "amount": 2, "participants": ["E"]},
            {"payer": "C", "amount": 4, "participants": ["F"]},
        ]
        # Balances: A +8, B +7, C +6, D -9, E -8, F -4.
        # The optimal partition is {A, E} and {B, C, D, F}.
        greedy_result = settle_expenses(expenses, "greedy")
        exact_result = settle_expenses(expenses, "exact2")
        self._assert_valid(greedy_result, expenses, non_zero_count=6)
        self._assert_valid(exact_result, expenses, non_zero_count=6)
        self.assertEqual(len(exact_result), 4)
        self.assertEqual(len(greedy_result), 5)

    def test_greedy_count_matches_reference_matching(self):
        """Greedy's payment count equals the O(n^2) _settle() reference."""
        expenses = [
            {"payer": "Alice", "amount": 500, "participants": ["Alice", "Bob", "Charlie", "Dave"]},
            {"payer": "Bob", "amount": 300, "participants": ["Alice", "Bob", "Charlie"]},
            {"payer": "Charlie", "amount": 200, "participants": ["Alice", "Charlie"]},
        ]
        balances = net_balances(expenses)
        non_zero = {p: b for p, b in balances.items() if b != 0}
        result = settle_expenses(expenses, "greedy")
        reference = _settle(list(non_zero), non_zero)
        self.assertEqual(len(result), len(reference))
        self.assertEqual(len(result), 3)  # matches the exact optimum here
        self._assert_valid(result, expenses, len(non_zero))

    def test_greedy_has_no_size_limit_and_stays_valid(self):
        """Greedy settles a large input (n=2000 pairs) within the n - 1 bound."""
        random.seed(1)
        expenses = [
            {"payer": f"P{2 * k}", "amount": random.randint(1, 1000),
             "participants": [f"P{2 * k}", f"P{2 * k + 1}"]}
            for k in range(2000)
        ]
        balances = net_balances(expenses)
        non_zero = {p: b for p, b in balances.items() if b != 0}
        result = settle_expenses(expenses, "greedy")
        self._assert_valid(result, expenses, len(non_zero))
        # n here is 4000, well past auto's 18-person exact threshold; the heap
        # implementation still settles to zero in O(n log n) without the limit.
        self.assertLess(len(result), len(non_zero))

    def test_greedy_no_self_payments_and_no_zero_amounts(self):
        """Structural invariants hold for the greedy method."""
        expenses = [
            {"payer": "Alice", "amount": 200, "participants": ["Alice", "Bob"]},
            {"payer": "Bob", "amount": 100, "participants": ["Alice", "Bob"]},
        ]
        result = settle_expenses(expenses, "greedy")
        self.assertTrue(all(p["sender"] != p["recipient"] for p in result))
        self.assertTrue(all(p["amount"] > 0 for p in result))

    def test_greedy_invalid_method_raises(self):
        """An unknown method name still raises ValueError."""
        expenses = [{"payer": "A", "amount": 10, "participants": ["A", "B"]}]
        with self.assertRaises(ValueError):
            settle_expenses(expenses, "bogus")

    def test_greedy_empty_input(self):
        """Empty input returns an empty list for the greedy method."""
        self.assertEqual(settle_expenses([], "greedy"), [])


if __name__ == "__main__":
    unittest.main()
