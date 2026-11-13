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
| `tests/test_settle_expenses.py` | Unit tests (standard-library `unittest`) |
| `tests/test_heuristic_vs_exact.py` | Tests where the heuristic is provably suboptimal vs the exact DP |
| `tests/data/edge_case_inputs.csv` | Sample / edge-case test data |

## Usage

```bash
python run_csv_tests.py inputs.csv
```

## Settlement methods

`settle_expenses(expenses, method=...)` accepts:

- **`"exact"`** — bitmask dynamic programming. Returns the
  provably minimum number of payments for any n (exponential time;
  practical up to ~18 on typical hardware).
- **`"heuristic"`** — exponential subset enumeration. Near-minimum for any
  size, but **not guaranteed** to use the fewest payments (see
  `tests/test_heuristic_vs_exact.py`).
- **`"greedy"`** — polynomial O(n log n) greedy largest-debtor-to-largest-
  creditor matching over all balances. Fast and size-unbounded, but **not
  guaranteed** minimal (the minimum-transaction problem is NP-hard).
- **`"auto"`** (default) — `"exact"` for 18 or fewer non-zero balances;
  warns and falls back to `"greedy"` for larger inputs. The default threshold
  of 18 is adjustable via the `threshold` parameter.

## How it works

### Net balance

`net_balances(expenses)` sums paid minus owed per person. Uneven splits distribute the extra cents to **earlier** participants (CSV order) via `divmod(amount, n)`:

```
11 cents among ["A", "B"] → A gets 6, B gets 5
```

### Minimum payments = n − c

With `n` non-zero balances and `c` disjoint zero-sum subsets found, the minimum payment count is `n − c`. Each zero-sum subset of size `k` reduces the count by 1 (it can be settled with `k − 1` payments).

### Complexity by method

| Method | Time | Space | Guaranteed minimal? | Size limit |
|--------|------|-------|---------------------|------------|
| `exact` | O(3^n) | O(2^n) | Yes | ≤ 18 |
| `heuristic` | O(2^n · n) | O(2^n) | No | Any |
| `greedy` | O(n log n) | O(n) | No | Any |

### Design rationale

- **Why `auto` warns + falls back to greedy?** A silent heuristic fallback would return a non-minimal answer that looks correct. The warning keeps the caller informed of the trade-off.
- **Why `_settle` + `_greedy_settle_balances`?** The former settles individual zero-sum groups (any iterable); the latter settles the full balance set with binary heaps (O(n log n)). They serve different scopes.
- **Why `frozenset` for subsets?** They are never mutated after creation. Being hashable also allows future optimizations like caching subset indices.

## Requirements

- Python 3.8+
- Standard library only (`csv`, `heapq`, `itertools`, `unittest`, `sys`)

## Tests

```bash
python -m unittest discover -v
```
