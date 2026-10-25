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
        payments = settle_expenses(expenses)

        print(f"Case {case_id}:")
        if not payments:
            print("  No payments required.")
        else:
            for p in payments:
                print(f"  {p['from']} -> {p['to']}: {p['amount']} cents")

        # Verify all balances are zero
        balances = net_balances(expenses)

        for p in payments:
            balances[p["from"]] += p["amount"]
            balances[p["to"]] -= p["amount"]

        non_zero = {p: b for p, b in balances.items() if b != 0}
        if non_zero:
            print(f"  ERROR: Unsettled balances: {non_zero}")
            sys.exit(1)

    print("\nAll cases settled successfully.")


if __name__ == "__main__":
    main()
