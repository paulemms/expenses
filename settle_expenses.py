"""
settle_expenses.py — Minimum-payment expense settlement algorithm.

Given a list of expense dictionaries, computes each person's net balance
and returns a near-minimum set of payments to settle all debts.

Algorithm:
    1. Compute net balances: paid minus owed for each person.
       Uneven splits allocate remainder cents to earlier participants.
    2. Find maximum disjoint zero-sum subsets of non-zero balances.
       For n <= 18, uses exact DP with bitmask enumeration (O(3^n)).
       For n > 18, uses greedy heuristic (smallest subsets first).
    3. For each zero-sum subset of size k, settle with (k - 1) payments
       using greedy largest-debtor-to-largest-creditor matching.
    4. For remaining people (if any), settle with greedy matching.

The minimum number of payments equals n - c, where n is the number of
people with non-zero balances and c is the number of disjoint zero-sum
subsets found. This formula holds because each zero-sum subset reduces
the required payments by 1.

Complexity:
    Time:  O(3^n) for exact DP, O(2^n * n) for heuristic.
           Greedy matching within subsets is O(n^2).
    Space: O(2^n) for DP table or subset storage.

Limitations:
    - Exact DP is limited to n <= 18 due to exponential complexity.
    - Greedy heuristic is not provably optimal for all inputs.
"""

import csv
from itertools import combinations
from typing import Dict, List


Expense = Dict[str, object]
Payment = Dict[str, object]
Balances = Dict[str, int]

_EXACT_THRESHOLD = 18


def settle_expenses(expenses: List[Expense], method: str = "auto") -> List[Payment]:
    """
    Calculate a near-minimum set of payments required to settle expenses.

    Args:
        expenses: A list of expense dictionaries with keys:
            - "payer": str
            - "amount": int
            - "participants": List[str]
        method: "heuristic" (greedy, fast), "exact" (DP, correct),
                or "auto" (exact for n<=18, heuristic otherwise).

    Returns:
        A list of payment dictionaries with keys:
            - "from": str
            - "to": str
            - "amount": int
    """
    if method not in ("auto", "exact", "heuristic"):
        raise ValueError(f"Unknown method: {method!r}. Must be 'auto', 'exact', or 'heuristic'.")

    if not expenses:
        return []

    # --- 1. Compute net balances ----------------------------------------
    balances = {}

    for exp in expenses:
        payer, amount, participants = (
            exp["payer"], exp["amount"], exp["participants"])

        balances[payer] = balances.get(payer, 0) + amount

        n = len(participants)
        base_share = amount // n
        remainder = amount % n

        for i, person in enumerate(participants):
            share = base_share + (1 if i < remainder else 0)
            balances[person] = balances.get(person, 0) - share

    # --- 2. Filter to non-zero balances ----------------------------------
    non_zero_balances = {p: b for p, b in balances.items() if b != 0}
    if not non_zero_balances:
        return []

    # --- 3. Find maximum number of disjoint zero-sum subsets -------------
    people = list(non_zero_balances.keys())
    n = len(people)

    if n == 0:
        return []

    if method == "auto":
        effective_method = "exact" if n <= _EXACT_THRESHOLD else "heuristic"
    else:
        effective_method = method

    if effective_method == "exact":
        zero_sum_groups = _find_max_zero_sum_subsets_exact(people, non_zero_balances)
    else:
        zero_sum_groups = _find_max_zero_sum_subsets_heuristic(people, non_zero_balances)

    # --- 4. Generate payments --------------------------------------------
    payments = []

    remaining = set(people)
    for group in zero_sum_groups:
        group_payments = _settle(group, non_zero_balances)
        payments.extend(group_payments)
        remaining -= set(group)

    if remaining:
        remaining_payments = _settle(remaining, non_zero_balances)
        payments.extend(remaining_payments)

    return payments


def _settle(people, balances):
    """
    Settle debts for a group of people using greedy largest-debtor-to-largest-creditor.
    Since the group sums to zero, this always succeeds.
    """
    balances_copy = {p: balances[p] for p in people}
    payments = []

    while True:
        debtors = {p: b for p, b in balances_copy.items() if b < 0}
        creditors = {p: b for p, b in balances_copy.items() if b > 0}

        if not debtors or not creditors:
            break

        debtor = max(debtors, key=debtors.get)
        creditor = max(creditors, key=creditors.get)

        amount = min(-debtors[debtor], creditors[creditor])
        payments.append({
            "from": debtor,
            "to": creditor,
            "amount": amount
        })

        balances_copy[debtor] += amount
        balances_copy[creditor] -= amount

        if balances_copy[debtor] == 0:
            del balances_copy[debtor]
        if balances_copy[creditor] == 0:
            del balances_copy[creditor]

    return payments


def _find_max_zero_sum_subsets_heuristic(people, balances):
    """
    Greedy heuristic: enumerate all zero-sum subsets, pick smallest first.
    Fast but not provably optimal.
    """
    people_map = {p: balances[p] for p in people}
    zero_sum_subsets = []

    for size in range(1, len(people) + 1):
        for combo in combinations(people, size):
            if sum(people_map[p] for p in combo) == 0:
                zero_sum_subsets.append(frozenset(combo))

    zero_sum_subsets.sort(key=lambda s: len(s))

    selected = []
    used = set()
    for subset in zero_sum_subsets:
        if not subset & used:
            selected.append(set(subset))
            used |= subset

    return selected


def _find_max_zero_sum_subsets_exact(people, balances):
    """
    Exact DP: find maximum disjoint zero-sum subsets using bitmask DP.
    O(3^n) time, O(2^n) space. Limited to n <= 18 in practice.
    """
    n = len(people)
    person_to_idx = {p: i for i, p in enumerate(people)}
    balance_list = [balances[p] for p in people]

    # Precompute which masks sum to zero
    zero_sum_masks = set()
    for mask in range(1, 1 << n):
        total = 0
        for i in range(n):
            if mask & (1 << i):
                total += balance_list[i]
        if total == 0:
            zero_sum_masks.add(mask)

    # DP: dp[mask] = max disjoint zero-sum subsets within mask
    dp = [0] * (1 << n)
    parent = [0] * (1 << n)  # track which subset was last added

    for mask in range(1, 1 << n):
        # Option 1: don't include lowest bit person in any subset
        lowbit = mask & (-mask)
        dp[mask] = dp[mask ^ lowbit]
        parent[mask] = 0

        # Option 2: try all zero-sum submasks that include lowbit
        submask = (mask - 1) & mask
        while submask > 0:
            if submask & lowbit:  # must include lowbit to avoid duplicates
                if submask in zero_sum_masks:
                    value = dp[mask ^ submask] + 1
                    if value > dp[mask]:
                        dp[mask] = value
                        parent[mask] = submask
            submask = (submask - 1) & mask

    # Reconstruct selected subsets
    selected = []
    mask = (1 << n) - 1
    while mask > 0:
        sub = parent[mask]
        if sub == 0:
            break
        selected.append(frozenset(people[i] for i in range(n) if sub & (1 << i)))
        mask ^= sub

    return selected


def validate_expense(expense, row_num):
    """Validate a single expense dictionary. Raises ValueError on issues."""
    required = {"payer", "amount", "participants"}
    missing = required - set(expense.keys())
    if missing:
        raise ValueError(f"Row {row_num}: Missing required field(s): {missing}")

    if not isinstance(expense["payer"], str) or not expense["payer"].strip():
        raise ValueError(f"Row {row_num}: Empty or invalid payer")

    if not isinstance(expense["amount"], int) or isinstance(expense["amount"], bool):
        raise ValueError(f"Row {row_num}: Amount must be an integer")

    if expense["amount"] < 0:
        raise ValueError(f"Row {row_num}: Negative amount not allowed")

    if not isinstance(expense["participants"], list) or len(expense["participants"]) == 0:
        raise ValueError(f"Row {row_num}: Empty participant list")

    for p in expense["participants"]:
        if not isinstance(p, str) or not p.strip():
            raise ValueError(f"Row {row_num}: Empty participant name")

    if len(expense["participants"]) != len(set(expense["participants"])):
        raise ValueError(f"Row {row_num}: Duplicate participants")


def parse_csv(csv_path):
    """
    Parse the input CSV file and return grouped expenses by case_id.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        Dictionary mapping case_id to list of expense dictionaries.

    Raises:
        FileNotFoundError: If the CSV file doesn't exist.
        ValueError: If the CSV is invalid.
    """
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header")

        required_cols = {"case_id", "payer", "amount", "participants"}
        actual_cols = set(reader.fieldnames)
        missing = required_cols - actual_cols
        if missing:
            raise ValueError(f"Missing required CSV columns: {missing}")

        expenses_by_case = {}
        row_num = 1  # header is row 1

        for row in reader:
            row_num += 1
            try:
                amount = int(row["amount"])

                expense = {
                    "payer": row["payer"].strip(),
                    "amount": amount,
                    "participants": [p.strip() for p in row["participants"].split(";")]
                }

                validate_expense(expense, row_num)

                case_id = row["case_id"].strip()
                if not case_id:
                    raise ValueError(f"Row {row_num}: Empty case_id")

                if case_id not in expenses_by_case:
                    expenses_by_case[case_id] = []
                expenses_by_case[case_id].append(expense)

            except (ValueError, TypeError, KeyError, AttributeError) as e:
                raise ValueError(f"Row {row_num}: {e}") from None

    return expenses_by_case
