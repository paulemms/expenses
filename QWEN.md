# QWEN.md — Expenses Settler Project Context

## Project Overview

This project implements a **minimum-payment expense settlement algorithm**. Given a CSV of shared expenses (who paid what, who shares), it computes each person's net balance and produces the globally minimum set of payments to settle all debts.

**Core innovation**: Uses bitmask dynamic programming to find maximum disjoint zero-sum subsets, achieving optimal payment counts for small cases (≤18 people), with a greedy heuristic fallback for larger inputs.

**Key constraint**: Python 3.8+ standard library only — no external dependencies.

---

## Project Structure

```
expenses/
├── settle_expenses.py       # Core algorithm (net_balances, settle_expenses, validate_expense, parse_csv)
├── run_csv_tests.py         # CLI runner — reads CSV, prints settlements, verifies zero-sum
├── edge_case_inputs.csv     # Sample/test dataset with 20 cases
├── test_settle_expenses.py  # Comprehensive unit tests (TestSettleExpenses, TestValidateExpense, TestParseCsv, TestMinimumPayments, TestNetBalances)
├── test_heuristic.py        # Heuristic-specific tests
├── test_exact.py            # Exact DP-specific tests
├── test_heuristic_vs_exact.py  # Tests proving heuristic suboptimality on crafted cases
├── spec.md                  # Original specification (assessment prompt)
├── README.md                # Project summary
└── .gitignore               # Excludes .spyder/, .spyproject/, __pycache__
```

---

## Building and Running

### Run the CLI against a CSV
```bash
python run_csv_tests.py inputs.csv
```

### Run all unit tests
```bash
python -m unittest discover -v
```

### Run specific test classes
```bash
python -m unittest test_settle_expenses.TestNetBalances -v
python -m unittest test_settle_expenses.TestMinimumPayments -v
python -m unittest test_heuristic.TestHeuristicMethod -v
python -m unittest test_exact.TestExactMethod -v
python -m unittest test_heuristic_vs_exact.TestHeuristicVsExact -v
```

### Run edge case inputs
```bash
python run_csv_tests.py edge_case_inputs.csv
```

---

## Algorithm Details

### Net Balance Computation (`net_balances()`)
- For each expense, credit the payer their full amount, debit each participant their share.
- Uneven splits: `divmod(amount, n)` — remainder cents go to earlier participants (CSV order).
- Returns `{person: net_balance}` where positive = owed, negative = owes.

### Settlement Algorithm (`settle_expenses()`)
1. Compute net balances via `net_balances()`.
2. Filter to non-zero balances.
3. Find maximum disjoint zero-sum subsets:
   - **Exact** (`method="exact"`): Bitmask DP, O(3^n) time, O(2^n) space. Limited to ≤18 people.
   - **Heuristic** (`method="heuristic"`): Greedy smallest-subset-first enumeration.
   - **Auto** (default): Exact for n≤18, heuristic otherwise.
4. Within each zero-sum subset, settle using greedy largest-debtor-to-largest-creditor matching.
5. Settle remaining people with the same greedy matching.

**Formula**: Minimum payments = `n - c` where `n` = non-zero balances, `c` = disjoint zero-sum subsets found.

---

## Key Functions

| Function | File | Purpose |
|----------|------|---------|
| `net_balances(expenses)` | settle_expenses.py | Compute per-person net balance from expenses |
| `settle_expenses(expenses, method="auto")` | settle_expenses.py | Main entry point — returns payment list |
| `validate_expense(expense, row_num)` | settle_expenses.py | Validate a single expense dict, raise ValueError |
| `parse_csv(csv_path)` | settle_expenses.py | Parse CSV into `{case_id: [expenses]}` dict |
| `_settle(people, balances)` | settle_expenses.py | Internal: greedy settlement for a zero-sum group |
| `_find_max_zero_sum_subsets_exact()` | settle_expenses.py | Internal: bitmask DP for optimal subset selection |
| `_find_max_zero_sum_subsets_heuristic()` | settle_expenses.py | Internal: greedy subset enumeration |

---

## Data Types

```python
Expense = Dict[str, object]   # {"payer": str, "amount": int, "participants": List[str]}
Payment = Dict[str, object]   # {"from": str, "to": str, "amount": int}
Balances = Dict[str, int]     # {person: net_balance_cents}
```

---

## Input/Output Contracts

### Expense Dictionary
```python
{
    "payer": "Alice",              # str, non-empty after strip
    "amount": 1000,                # int (cents), must be >= 0
    "participants": ["Alice", "Bob"]  # List[str], no duplicates, non-empty
}
```

### Payment Dictionary
```python
{
    "from": "Bob",                 # str, person paying
    "to": "Alice",                 # str, person receiving
    "amount": 500                  # int (cents), must be > 0
}
```

### CSV Format
```csv
case_id,payer,amount,participants
1,Alice,1000,Alice;Bob
2,Bob,500,Alice;Bob
```
- Semicolon-separated participants with whitespace trimmed.
- Each `case_id` processed independently.
- UTF-8 encoding required.

---

## Validation Rules

`validate_expense()` raises `ValueError` for:
- Missing required fields (`payer`, `amount`, `participants`)
- Empty/whitespace-only payer name
- Non-integer amount (including booleans)
- Negative amount
- Empty participant list
- Empty/whitespace-only participant name
- Duplicate participants within one expense

`parse_csv()` raises `ValueError` for:
- Missing required CSV columns
- Empty case_id
- Malformed rows (with row number in error message)
- FileNotFoundError for missing files

---

## Test Coverage

### `test_settle_expenses.py`
- **TestSettleExpenses**: Core settlement behavior (20+ tests)
- **TestValidateExpense**: Validation edge cases (9 tests)
- **TestParseCsv**: CSV parsing and error handling (9 tests)
- **TestMinimumPayments**: Optimal payment count verification (3 tests)
- **TestNetBalances**: Net balance computation correctness (7 tests)

### `test_heuristic.py`
- Heuristic-specific behavior verification (15 tests)

### `test_exact.py`
- Exact DP correctness verification (16 tests)

### `test_heuristic_vs_exact.py`
- Proof that heuristic is suboptimal on crafted input (7 payments vs 6)

---

## Important Implementation Notes

### Rounding Rule
Uneven splits allocate remainder cents to **earlier** participants (CSV order):
```python
base_share, remainder = divmod(amount, n)
# First `remainder` participants get base_share + 1
```

### Zero-Sum Subset Discovery
The exact DP precomputes all zero-sum masks, then uses parent pointers for reconstruction. The heuristic sorts all zero-sum subsets by size and greedily selects non-overlapping ones.

### Known Limitation
Exact DP has O(3^n) complexity — practical limit is n≈18. For larger inputs, the heuristic is used automatically but is not provably optimal.

### Payer-as-Participant
When the payer is also a participant, they receive +amount (credited) and -share (debited). Net effect: `payer_balance = amount - share`.

---

## Development Conventions

- **Testing**: Use Python's `unittest` framework. All tests must pass before committing.
- **Code style**: Type hints for public functions, docstrings for all public API.
- **No external dependencies**: Only `csv`, `itertools`, `unittest`, `sys`, `typing`.
- **Error handling**: Raise `ValueError` with descriptive messages including row numbers where applicable.
- **Commit messages**: Describe the "why", not just the "what".

---

## Files to Know

| File | Why it matters |
|------|----------------|
| `settle_expenses.py` | All logic lives here — algorithm, parsing, validation |
| `test_settle_expenses.py` | Most comprehensive test file — covers all public APIs |
| `edge_case_inputs.csv` | 20 edge cases: Unicode, uneven splits, zero-value, single participant, large amounts |
| `spec.md` | Original assessment specification — reference for requirements |
| `test_heuristic_vs_exact.py` | Documents the heuristic vs exact divergence case |

---

## Verification Strategy

Before committing changes:
1. Run `python -m unittest discover -v` — all 74 tests must pass.
2. Run `python run_csv_tests.py edge_case_inputs.csv` — all cases must settle to zero.
3. Check that no inline balance calculations remain (use `net_balances()` helper).
