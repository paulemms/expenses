# AGENTS.md — Expenses Settler Project Context

## Project Overview

This project implements a **minimum-payment expense settlement algorithm**. Given a CSV of shared expenses (who paid what, who shares), it computes each person's net balance and produces the globally minimum set of payments to settle all debts.

**Core innovation**: Uses cached bitmask dynamic programming to maximize the number of independent zero-sum groups. The default `auto` selects `exact2`, which caches zero-sum prefix counts using one-person transitions, for up to 18 non-zero balances; above that it warns and falls back to polynomial `greedy` settlement.

**Key constraint**: Python 3.8+ standard library only — no external dependencies.

---

## Project Structure

```
expenses/
├── settle_expenses.py       # Core algorithm (net_balances, settle_expenses, validate_expense, parse_csv)
├── run_csv_tests.py         # CLI runner — reads CSV, prints settlements, verifies zero-sum
├── edge_case_inputs.csv     # Sample/test dataset with 20 cases
├── test_settle_expenses.py  # Comprehensive unit tests (TestSettleExpenses, TestSettleExpensesMethods, TestValidateExpense, TestParseCsv, TestMinimumPayments, TestNetBalances)
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
- All amounts are dimensionless integers.
- Uneven splits: `divmod(amount, n)` — the remainder is allocated one at a time to earlier participants (CSV order).
- Returns `{person: net_balance}` where positive = owed, negative = owes.

### Settlement Algorithm (`settle_expenses()`)
1. Compute net balances via `net_balances()`.
2. Filter to non-zero balances.
3. Dispatch by method:
   - **Recursive exact** (`method="exact0"`): exhaustive zero-sum partition
     search without caching. Super-exponential worst-case time, O(n) space.
   - **Cached exact** (`method="exact1"`): bottom-up bitmask DP for maximum
     disjoint zero-sum subsets. Caches the optimal group count for each subset
     and reuses it when solving larger subsets. O(3^n) time / O(2^n) space;
     practical for small inputs (about 18 non-zero balances), no enforced limit.
   - **Faster cached exact** (`method="exact2"`): bottom-up bitmask DP that
     maximizes zero-sum prefixes in an ordering of each subset. Caches subset
     sums and best prefix counts; tries each person as the last one added.
     O(n*2^n) time / O(2^n) space, with no enforced size limit.
   - **Heuristic** (`method="heuristic"`): exponential smallest-subset-first
     enumeration — kept as the exponential fallback, not provably optimal.
   - **Greedy** (`method="greedy"`): polynomial O(n log n) greedy
     largest-debtor-to-largest-creditor matching over all balances at once via
     two binary heaps. Not guaranteed minimal, no size limit.
   - **Auto** (`method="auto"`): `exact2` for n≤18; **warns + falls back to greedy** for n>18.
4. For the exact/heuristic paths, settle each zero-sum subset with greedy
   largest-debtor-to-largest-creditor matching, then settle remaining people.

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
| `_find_max_zero_sum_subsets_exact0()` | settle_expenses.py | Internal: recursive optimal partition search without caching |
| `_find_max_zero_sum_subsets_exact()` | settle_expenses.py | Internal: exact1, bottom-up bitmask DP with cached subset results |
| `_find_max_zero_sum_subsets_exact2()` | settle_expenses.py | Internal: exact2, cached zero-sum prefix counts with one-person transitions |
| `_find_max_zero_sum_subsets_heuristic()` | settle_expenses.py | Internal: greedy subset enumeration |
| `_greedy_settle_balances(balances)` | settle_expenses.py | Internal: O(n log n) greedy matching over all balances via two binary heaps |

---

## Data Types

```python
Expense = Dict[str, object]   # {"payer": str, "amount": int, "participants": List[str]}
Payment = Dict[str, object]   # {"from": str, "to": str, "amount": int}
Balances = Dict[str, int]     # {person: net_balance}
```

---

## Input/Output Contracts

### Expense Dictionary
```python
{
    "payer": "Alice",              # str, non-empty after strip
    "amount": 1000,                # int, must be >= 0
    "participants": ["Alice", "Bob"]  # List[str], no duplicates, non-empty
}
```

### Payment Dictionary
```python
{
    "from": "Bob",                 # str, person paying
    "to": "Alice",                 # str, person receiving
    "amount": 500                  # int, must be > 0
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
- **TestSettleExpenses**: Core settlement behavior (15 tests)
- **TestSettleExpensesMethods**: Same scenarios run under both `exact1` (cached DP) and `heuristic` (5 tests)
- **TestValidateExpense**: Validation edge cases (9 tests)
- **TestParseCsv**: CSV parsing and error handling (7 tests)
- **TestMinimumPayments**: Optimal payment count verification (3 tests)
- **TestNetBalances**: Net balance computation correctness (7 tests)
- **TestGreedyMethod**: O(n log n) greedy method (validity, n-1 bound, matches `exact1` on trivial cases, no size limit, count matches `_settle` reference)

### `test_heuristic_vs_exact.py`
- Proof that heuristic is suboptimal on crafted input (7 payments vs 6)

---

## Important Implementation Notes

### Rounding Rule
Uneven splits allocate the remainder one at a time to **earlier** participants (CSV order):
```python
base_share, remainder = divmod(amount, n)
# First `remainder` participants get base_share + 1
```

### Zero-Sum Subset Discovery
`exact1` precomputes all zero-sum masks and evaluates the Bellman recurrence
bottom-up. It caches the maximum group count for each subset in `dp[mask]`,
so larger subsets reuse previous results. Parent pointers reconstruct the
chosen groups. `exact0` recursively explores partitions without caching.
`exact2` uses a different Bellman recurrence: its cached value is the maximum
number of nonempty zero-sum prefixes in any ordering of a subset. Try each
person as the last one added, reuse the predecessor's count, and add one if
the subset sum is zero. Every return to zero marks a group boundary. The
subset sums are cached too. This reduces the work per k-person subset from
2^(k-1) candidate groups in `exact1` to k transitions in `exact2`, giving
O(n*2^n) time and O(2^n) space. Parent bits recover the ordering and groups.
The heuristic sorts all zero-sum subsets by size and greedily selects
non-overlapping ones.

### Known Limitation
`exact1` still takes O(3^n) time despite caching, with O(2^n) space; explicit
`exact1` has no enforced size limit. The default `auto` uses `exact2` up to
18 non-zero balances, then warns and falls back to `greedy`.
`exact2` also has exponential time and memory requirements despite its
smaller transition count; increasing the `auto` threshold increases both.

### Payer-as-Participant
When the payer is also a participant, they receive +amount (credited) and -share (debited). Net effect: `payer_balance = amount - share`.

---

## Development Conventions

- **Testing**: Use Python's `unittest` framework. All tests must pass before committing.
- **Code style**: Type hints for public functions, docstrings for all public API.
- **No external dependencies**: Only `csv`, `heapq`, `itertools`, `unittest`, `sys`, `typing`.
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
1. Run `python -m unittest discover -v` — all 57 tests must pass.
2. Run `python run_csv_tests.py edge_case_inputs.csv` — all cases must settle to zero.
3. Check that no inline balance calculations remain (use `net_balances()` helper).
