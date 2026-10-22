"""
run_csv_tests.py — Loads the CSV file and executes each test case.
"""

import sys
from settle_expenses import settle_expenses, parse_csv


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
        balances = {}
        for exp in expenses:
            payer = exp["payer"]
            amount = exp["amount"]
            participants = exp["participants"]
            balances[payer] = balances.get(payer, 0) + amount
            n = len(participants)
            base = amount // n
            rem = amount % n
            for i, person in enumerate(participants):
                share = base + (1 if i < rem else 0)
                balances[person] = balances.get(person, 0) - share

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
