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

the program calculates each person's net balance (total paid minus total owed) and produces a list of payments that settles everyone. With `method="auto"` or `"exact"` the result uses the fewest payments possible for up to 18 people with non-zero balances; `"heuristic"` and `"greedy"` offer fast, size-unbounded fallbacks that settle everyone but are not guaranteed to use the fewest payments.

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
- **`"heuristic"`** — exponential subset enumeration. Near-minimum for any
  size, but **not guaranteed** to use the fewest payments (see
  `test_heuristic_vs_exact.py`).
- **`"greedy"`** — polynomial O(n log n) greedy largest-debtor-to-largest-
  creditor matching over all balances. Fast and size-unbounded, but **not
  guaranteed** minimal (the minimum-transaction problem is NP-hard).
- **`"auto"`** — `"exact"` for 18 or fewer non-zero balances; **raises** for
  more than 18 rather than silently returning a non-minimal answer. Use
  `"heuristic"` or `"greedy"` explicitly when you need results for larger
  inputs.

## Requirements

- Python 3.8+
- Standard library only (`csv`, `heapq`, `itertools`, `unittest`, `sys`)

## Tests

```bash
python -m unittest discover -v
```
