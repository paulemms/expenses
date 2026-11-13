"""
settle_expenses.py — Minimum-payment expense settlement algorithm.

Given a list of expense dictionaries, computes each person's net balance
and returns a set of payments that settles all debts.

Public API:
    net_balances(expenses)              -> Balances                (per-person net balance)
    settle_expenses(expenses, method="auto", threshold=18) -> List[Payment]
    validate_expense(expense, row_num)  -> None
    parse_csv(csv_path)                 -> Dict[str, List[Expense]]

Method dispatch:
    "exact"      — bitmask DP, provably minimum for any n (exponential time)
    "heuristic"  — greedy subset selection, fast for any size
    "greedy"     — polynomial O(n log n), not guaranteed minimal
    "auto"       — exact for n <= threshold; warns + falls back to greedy
                   above the threshold.
"""

import csv
import warnings
from heapq import heapify, heappop, heappush
from itertools import combinations
from typing import Dict, Iterable, List, Set, TypedDict, Union


class Expense(TypedDict):
    payer: str
    amount: int
    participants: List[str]


class Payment(TypedDict):
    sender: str
    recipient: str
    amount: int


Balances = Dict[str, int]


def net_balances(expenses: List[Expense]) -> Balances:
    """Compute net balances for each person from a list of expenses.

    Args:
        expenses: A list of expense dictionaries with keys:
            - "payer": str
            - "amount": int
            - "participants": List[str]

    Returns:
        A dictionary mapping person names to their net balance
        (positive = owed money, negative = owes money).
    """
    balances = {}
    for exp in expenses:
        payer = exp["payer"]
        amount = exp["amount"]
        participants = exp["participants"]
        n = len(participants)
        if n == 0:
            raise ValueError("No participants")
        base_share, remainder = divmod(amount, n)
        balances[payer] = balances.get(payer, 0) + amount

        # Spread 1 cent over remainder participants
        for i, person in enumerate(participants):
            share = base_share + (1 if i < remainder else 0)
            balances[person] = balances.get(person, 0) - share
    return balances


def settle_expenses(expenses: List[Expense], method: str = "auto", threshold: int = 18) -> List[Payment]:
    """Calculate a near-minimum set of payments required to settle expenses.

    Args:
        expenses: A list of expense dictionaries with keys:
            - "payer": str
            - "amount": int
            - "participants": List[str]
        method: "exact" (bitmask DP, provably minimum for n <= threshold),
                "heuristic" (exponential subset enumeration, near-minimum,
                may miss the optimum), or "greedy" (polynomial O(n log n)
                largest-debtor-to-largest-creditor settlement, not
                guaranteed minimal, no size limit). "auto" uses exact and
                warns + falls back to greedy if n exceeds the threshold.
        threshold: The maximum number of non-zero balances for which the
            "exact" method is used with "auto" dispatch. Defaults to 18;
            the exact DP is O(3^n) and impractical past this size.

    Returns:
        A list of payment dictionaries with keys:
            - "sender": str
            - "recipient": str
            - "amount": int
    """
    if method not in ("auto", "exact", "heuristic", "greedy"):
        raise ValueError(
            f"Unknown method: {method!r}. Must be 'auto', 'exact', 'heuristic', "
            "or 'greedy'."
        )

    if not expenses:
        return []

    # Compute net balances
    balances = net_balances(expenses)

    # Filter to non-zero balances
    non_zero_balances = {p: b for p, b in balances.items() if b != 0}
    if not non_zero_balances:
        return []

    # Find maximum number of disjoint zero-sum subsets
    people = list(non_zero_balances.keys())
    n = len(people)

    if method == "auto":
        if n > threshold:
            warnings.warn(
                f"auto fell back to greedy: {n} non-zero balances exceeds "
                f"the exact threshold ({threshold}).",
                UserWarning,
            )
            effective_method = "greedy"
        else:
            effective_method = "exact"
    else:
        effective_method = method

    # Greedy: settle every balance directly with a polynomial largest-debtor
    # to largest-creditor pass. It does not decompose into zero-sum subsets, so
    # it is not guaranteed minimal, but it is fast (O(n log n)) and has no size
    # limit. It runs before the zero-sum-group logic, which both branches below.
    if effective_method == "greedy":
        return _greedy_settle_balances(non_zero_balances)

    if effective_method == "exact":
        zero_sum_groups = _find_max_zero_sum_subsets_exact(people, non_zero_balances)
    else:
        zero_sum_groups = _find_max_zero_sum_subsets_heuristic(people, non_zero_balances)

    # Generate payments
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


def _settle(people: Iterable[str], balances: Balances) -> List[Payment]:
    """Settle debts for a group of people using greedy largest-debtor-to-largest-creditor.

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
            "sender": debtor,
            "recipient": creditor,
            "amount": amount
        })

        balances_copy[debtor] += amount
        balances_copy[creditor] -= amount

        if balances_copy[debtor] == 0:
            del balances_copy[debtor]
        if balances_copy[creditor] == 0:
            del balances_copy[creditor]

    return payments


def _greedy_settle_balances(balances: Balances) -> List[Payment]:
    """Settle all balances in one greedy pass. Not provably minimal; relies on
    net_balances guaranteeing sum==0."""
    debtors = [(b, p) for p, b in balances.items() if b < 0]
    creditors = [(-b, p) for p, b in balances.items() if b > 0]
    # -b: negate so smallest heap entry = largest creditor
    heapify(debtors)
    heapify(creditors)

    payments = []
    while debtors and creditors:
        key_debtor, debtor = debtors[0]
        key_cred, creditor = creditors[0]
        amount = min(-key_debtor, -key_cred)  # both keys are negative magnitudes
        payments.append(
            {"sender": debtor, "recipient": creditor, "amount": amount}
        )

        heappop(debtors)
        heappop(creditors)
        rem_debtor = -key_debtor - amount
        rem_cred = -key_cred - amount
        if rem_debtor > 0:
            heappush(debtors, (key_debtor + amount, debtor))
        if rem_cred > 0:
            heappush(creditors, (key_cred + amount, creditor))

    return payments


def _find_max_zero_sum_subsets_heuristic(people: List[str], balances: Balances) -> List[Set[str]]:
    """Greedy heuristic: enumerate all zero-sum subsets, pick smallest first.

    Fast but not provably optimal.
    """
    people_map = {p: balances[p] for p in people}
    zero_sum_subsets = []

    for size in range(2, len(people) + 1):  # single-person subset can't sum to zero
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


def _find_max_zero_sum_subsets_exact(people: List[str], balances: Balances) -> List[frozenset]:
    """Exact DP: find maximum disjoint zero-sum subsets using bitmask DP.

    O(3^n) time, O(2^n) space. Limited to n <= 18 in practice.
    """
    n = len(people)
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
        rest = mask ^ lowbit
        submask = rest
        while True:
            candidate = submask | lowbit
            if candidate in zero_sum_masks:
                value = dp[mask ^ candidate] + 1
                if value > dp[mask]:
                    dp[mask] = value
                    parent[mask] = candidate
            if submask == 0:
                break
            submask = (submask - 1) & rest

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


def validate_expense(expense: Expense, row_num: int) -> None:
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


def parse_csv(csv_path: str) -> Dict[str, List[Expense]]:
    """Parse the input CSV file and return grouped expenses by case_id.

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
                # validate_expense() and the Empty case_id raise already format
                # their messages as "Row {row_num}: ..."; strip a matching prefix
                # here so we never emit a doubled "Row N: Row N:" message, while
                # bare errors (e.g. int() conversion) still get the prefix once.
                message = str(e)
                prefix = f"Row {row_num}: "
                if message.startswith(prefix):
                    message = message[len(prefix):]
                raise ValueError(f"Row {row_num}: {message}")

    return expenses_by_case
