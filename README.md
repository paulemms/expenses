# Expenses — Settler

A small Python tool that reads a CSV of shared expenses and computes the minimum number of payments needed to settle all debts.

## What it does

Given a CSV like:

```csv
case_id,payer,amount,participants
1,Alice,1000,Alice;Bob;Charlie
2,Bob,500,Bob;Dave
3,Alice,300,Alice;Eve
```

the program calculates each person's net balance (total paid minus total owed) and produces a list of payments that settles everyone — using the fewest payments possible for up to 18 people (exact), and a greedy heuristic that settles everyone but is not guaranteed minimal beyond that.

## Files

| File | Purpose |
|---|---|
| `settle_expenses.py` | Core algorithm — parse, validate, and settle |
| `run_csv_tests.py` | CLI runner — reads a CSV and prints settlements |
| `test_settle_expenses.py` | Unit tests (standard-library `unittest`) |
| `test_heuristic_vs_exact.py` | Tests where the heuristic is provably suboptimal vs the exact DP |
| `edge_case_inputs.csv` | Sample / edge-case test data |

## Usage

```bash
python run_csv_tests.py inputs.csv
```

## Settlement methods

`settle_expenses(expenses, method=...)` accepts:

- **`"exact"`** (default via `"auto"`) — bitmask dynamic programming. Returns the
  provably minimum number of payments for up to 18 people with non-zero
  balances; impractically slow beyond that.
- **`"heuristic"`** — greedy subset selection. Fast for any size, but **not
  guaranteed** to use the fewest payments (see `test_heuristic_vs_exact.py`).
- **`"auto"`** — `"exact"` for 18 or fewer non-zero balances, `"heuristic"`
  otherwise.

## Requirements

- Python 3.8+
- Standard library only (`csv`, `itertools`, `unittest`, `sys`)

## Tests

```bash
python -m unittest discover -v
```
