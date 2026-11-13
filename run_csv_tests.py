"""
run_csv_tests.py — Loads the CSV file and executes each test case.
"""

import sys
from settle_expenses import settle_expenses, parse_csv, net_balances


def main():
    if len(sys.argv) != 2:
        print("Usage: python run_csv_tests.py <csv_file>")
        sys.exit(1)

    csv_path = sys.argv[1]

    try:
        expenses_by_case = parse_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: File '{csv_path}' not found.")
        sys.exit(1)
    except ValueError as e:
        print(f"Invalid input: {e}")
        sys.exit(1)

    if not expenses_by_case:
        print("No test cases found in the CSV file.")
        return

    for case_id in sorted(expenses_by_case.keys(), key=lambda x: (len(x), x)):
        expenses = expenses_by_case[case_id]
        try:
            payments = settle_expenses(expenses, threshold=18)
        except ValueError as e:
            print(f"Case {case_id}:")
            print(f"  ERROR: {e}")
            sys.exit(1)

        print(f"Case {case_id}:")
        if not payments:
            print("  No payments required.")
        else:
            for p in payments:
                print(f"  {p['sender']} -> {p['recipient']}: {p['amount']} cents")

        # Verify all balances are zero
        balances = net_balances(expenses)
        # n for the n-1 bound is the number of people with a nonzero NET
        # balance BEFORE settlement (post-settlement counts are always zero).
        n_nonzero = sum(1 for b in balances.values() if b != 0)

        for p in payments:
            balances[p["sender"]] += p["amount"]
            balances[p["recipient"]] -= p["amount"]
            if p["sender"] == p["recipient"]:
                print(f"  ERROR: Self-payment detected: {p}")
                sys.exit(1)
            if p["amount"] <= 0:
                print(f"  ERROR: Non-positive payment: {p}")
                sys.exit(1)

        non_zero = {p: b for p, b in balances.items() if b != 0}
        if non_zero:
            print(f"  ERROR: Unsettled balances: {non_zero}")
            sys.exit(1)

        # spec.md:223 — no more than n - 1 payments for n non-zero balances,
        # plus structural sanity: no self-payments and every amount > 0.
        # (n == 0 has no payments, so clamp the bound to >= 0.)
        if len(payments) > max(0, n_nonzero - 1):
            print(
                f"  ERROR: {len(payments)} payments exceed the n - 1 bound "
                f"(n = {n_nonzero})"
            )
            sys.exit(1)

    print("\nAll cases settled successfully.")


if __name__ == "__main__":
    main()
