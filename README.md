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

the program calculates each person's net balance (total paid minus total owed) and produces a list of payments that settles everyone — using the fewest payments possible.

## Files

| File | Purpose |
|---|---|
| `settle_expenses.py` | Core algorithm — parse, validate, and settle |
| `run_csv_tests.py` | CLI runner — reads a CSV and prints settlements |
| `test_settle_expenses.py` | Unit tests (standard-library `unittest`) |
| `edge_case_inputs.csv` | Sample / edge-case test data |

## Usage

```bash
python run_csv_tests.py inputs.csv
```

## Requirements

- Python 3.8+
- Standard library only (`csv`, `itertools`, `unittest`, `sys`)

## Tests

```bash
python -m unittest test_settle_expenses -v
```
