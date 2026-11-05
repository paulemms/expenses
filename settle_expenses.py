"""
settle_expenses.py — Minimum-payment expense settlement algorithm.

Given a list of expense dictionaries, computes each person's net balance
and returns a set of payments that settles all debts. With method="auto"
or "exact" the number of payments is provably minimum (for n <= 18);
method="heuristic" returns a near-minimum answer that is not guaranteed
minimal.

Algorithm:
    1. Compute net balances: paid minus owed for each person.
       Uneven splits allocate remainder cents to earlier participants.
    2. Find maximum disjoint zero-sum subsets of non-zero balances via
       exact bitmask DP (O(3^n)). The "auto" method raises for n > 18
       rather than silently returning a non-minimal heuristic answer.
    3. For each zero-sum subset of size k, settle with (k - 1) payments
       using greedy largest-debtor-to-largest-creditor matching.
    4. For remaining people (if any), settle with greedy matching.

The minimum number of payments equals n - c, where n is the number of
people with non-zero balances and c is the number of disjoint zero-sum
subsets found. This formula holds because each zero-sum subset reduces
the required payments by 1.

Complexity:
    Time:  O(3^n) for exact DP, O(2^n * n) for heuristic subset
           enumeration, O(n^2) for greedy matching. The greedy method's
           matching uses binary heaps, dropping it to O(n log n).
           Matching within a zero-sum subset (via _settle) is O(n^2).
    Space: O(2^n) for DP table or subset storage.

Limitations:
    - Exact DP is limited to n <= 18 due to exponential complexity.
    - "auto" refuses (raises) for n > 18 rather than returning a heuristic
      answer, so every auto/exact result is a globally minimum settlement.
      Use method="heuristic" explicitly if you need results for larger inputs.
"""

import csv
from heapq import heapify, heappop, heappush
from itertools import combinations
from typing import Dict, List, Set, Union


Expense = Dict[str, object]
Payment = Dict[str, object]
Balances = Dict[str, int]

_EXACT_THRESHOLD = 18


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


def settle_expenses(expenses: List[Expense], method: str = "auto") -> List[Payment]:
    """
    Calculate a near-minimum set of payments required to settle expenses.

    Args:
        expenses: A list of expense dictionaries with keys:
            - "payer": str
            - "amount": int
            - "participants": List[str]
        method: "exact" (bitmask DP, provably minimum for n <= 18),
                "heuristic" (exponential subset enumeration, near-minimum,
                may miss the optimum), or "greedy" (polynomial O(n log n)
                largest-debtor-to-largest-creditor settlement, not
                guaranteed minimal, no size limit). "auto" uses exact and
                raises if n > 18 rather than silently returning a
                non-minimal answer.

    Returns:
        A list of payment dictionaries with keys:
            - "from": str
            - "to": str
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
        if n > _EXACT_THRESHOLD:
            raise ValueError(
                f"auto cannot guarantee a globally minimum settlement for {n} "
                f"people with non-zero balances (the exact DP is practical "
                f"only for n <= {_EXACT_THRESHOLD}). The heuristic fallback is "
                f"not provably minimal, so returning it silently would violate "
                f"the optimisation requirement. Pass method='heuristic' to "
                f"accept a non-minimal answer, or keep the number of people "
                f"with non-zero balances at {_EXACT_THRESHOLD} or fewer."
            )
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


def _settle(people: Union[List[str], Set[str]], balances: Balances) -> List[Payment]:
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


def _greedy_settle_balances(balances: Balances) -> List[Payment]:
    """Settle every balance with a single largest-debtor-to-largest-creditor pass.

    This is the polynomial counterpart of :func:`_settle`: instead of splitting
    balances into zero-sum subsets, it settles all of them at once. It is not
    guaranteed minimal (the minimum-transaction problem is NP-hard), but it
    always reaches zero because :func:`net_balances` guarantees the balances sum
    to zero.

    The heap-based "refinement" keeps two binary heaps -- debtors keyed by
    their (negative) balance so the largest debtor sorts first, and creditors
    keyed by their negated balance so the largest creditor sorts first -- so
    each of the at most ``n - 1`` payments costs an O(log n) pop/push, giving
    O(n log n) overall instead of the O(n^2) of :func:`_settle`.
    """
    debtors = [(b, p) for p, b in balances.items() if b < 0]
    creditors = [(-b, p) for p, b in balances.items() if b > 0]
    heapify(debtors)
    heapify(creditors)

    payments = []
    while debtors and creditors:
        key_debtor, debtor = debtors[0]
        key_cred, creditor = creditors[0]
        amount = min(-key_debtor, -key_cred)  # both keys are negative magnitudes
        payments.append({"from": debtor, "to": creditor, "amount": amount})

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
                raise ValueError(f"Row {row_num}: {message}") from None

    return expenses_by_case
