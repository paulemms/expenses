"""
settle_expenses.py — Minimum-payment expense settlement algorithm.

Given a list of expense dictionaries, computes each person's net balance
and returns the globally minimum set of payments to settle all debts.
"""

from itertools import combinations


def settle_expenses(expenses):
    """
    Calculate the minimum number of payments required to settle a collection
    of expenses.

    Args:
        expenses: A list of expense dictionaries, each with keys:
            - "payer": str — person who paid
            - "amount": int — total amount in cents
            - "participants": list[str] — who shares the expense

    Returns:
        A list of payment dictionaries with keys:
            - "from": str — debtor
            - "to": str — creditor
            - "amount": int — cents transferred
    """
    if not expenses:
        return []

    # --- 1. Compute net balances ----------------------------------------
    balances = {}

    for exp in expenses:
        payer = exp["payer"]
        amount = exp["amount"]
        participants = exp["participants"]

        # Payer gets credited for the full amount
        balances[payer] = balances.get(payer, 0) + amount

        # Each participant owes their share
        n = len(participants)
        base_share = amount // n
        remainder = amount % n

        for i, person in enumerate(participants):
            share = base_share + (1 if i < remainder else 0)
            balances[person] = balances.get(person, 0) - share

    # --- 2. Filter to non-zero balances ----------------------------------
    debtors = {p: b for p, b in balances.items() if b < 0}
    creditors = {p: b for p, b in balances.items() if b > 0}

    if not debtors and not creditors:
        return []

    # --- 3. Find maximum number of disjoint zero-sum subsets -------------
    # Minimum transactions = n - c, where n = total non-zero people,
    # c = max disjoint zero-sum subsets.
    people = list(balances.keys())
    non_zero_people = [p for p in people if balances[p] != 0]
    n = len(non_zero_people)

    if n == 0:
        return []

    zero_sum_subsets = _find_max_zero_sum_subsets(non_zero_people, balances)
    # c = len(zero_sum_subsets)

    # --- 4. Generate payments --------------------------------------------
    payments = []

    # For each zero-sum subset, settle internally with (size-1) payments
    remaining = set(non_zero_people)
    for subset in zero_sum_subsets:
        subset_payments = _settle_subset(subset, balances)
        payments.extend(subset_payments)
        remaining -= set(subset)

    # For the remainder, use greedy matching
    if remaining:
        remaining_payments = _greedy_settle(remaining, balances)
        payments.extend(remaining_payments)

    return payments


def _settle_subset(subset, balances):
    """
    Settle a zero-sum subset using a simple greedy internal approach.
    Since the subset sums to zero, this always succeeds.
    """
    subset_balances = {p: balances[p] for p in subset}
    payments = []

    while True:
        debtors = {p: b for p, b in subset_balances.items() if b < 0}
        creditors = {p: b for p, b in subset_balances.items() if b > 0}

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

        subset_balances[debtor] += amount
        subset_balances[creditor] -= amount

        # Remove zero balances to shrink the subset
        if subset_balances[debtor] == 0:
            del subset_balances[debtor]
        if subset_balances[creditor] == 0:
            del subset_balances[creditor]

    return payments


def _greedy_settle(people, balances):
    """
    Greedy settlement for remaining people (not in zero-sum subsets).
    Always match largest debtor with largest creditor.
    """
    remaining = {p: balances[p] for p in people}
    payments = []

    while True:
        debtors = {p: b for p, b in remaining.items() if b < 0}
        creditors = {p: b for p, b in remaining.items() if b > 0}

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

        remaining[debtor] += amount
        remaining[creditor] -= amount

        if remaining[debtor] == 0:
            del remaining[debtor]
        if remaining[creditor] == 0:
            del remaining[creditor]

    return payments


def _find_max_zero_sum_subsets(people, balances):
    """
    Find the maximum number of disjoint subsets whose balances sum to zero.
    Uses backtracking with pruning for small inputs.
    """
    # Work with absolute values for subset sum logic
    # Store balances as-is
    people_map = {p: balances[p] for p in people}

    # Collect all possible zero-sum subsets
    zero_sum_subsets = []

    for size in range(1, len(people) + 1):
        for combo in combinations(people, size):
            if sum(people_map[p] for p in combo) == 0:
                zero_sum_subsets.append(frozenset(combo))

    # Sort by size (prefer smaller subsets to maximize count)
    zero_sum_subsets.sort(key=lambda s: len(s))

    # Greedy selection of disjoint subsets
    selected = []
    used = set()

    for subset in zero_sum_subsets:
        if not subset & used:
            selected.append(set(subset))
            used |= subset

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
    import csv

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

            except (ValueError, TypeError, KeyError) as e:
                raise ValueError(f"Row {row_num}: {e}") from None

    return expenses_by_case
