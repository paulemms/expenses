# Expenses Settler

Python tool that reads a CSV of shared expenses and computes the minimum number of payments needed to settle all debts.

## What it does

Given a CSV like:

```csv
case_id,payer,amount,participants
1,Alice,1000,Alice;Bob;Charlie
2,Bob,500,Bob;Dave
3,Alice,300,Alice;Eve
```

the program calculates each person's net balance (total paid minus total owed) and produces a list of payments that settles everyone. The default `method="auto"` uses method `"exact2"` to find the fewest payments possible for up to 18 people with non-zero balances, then warns and falls back to `"greedy"` above that threshold. Explicit `"exact2"` and `"exact1"` always use exact solvers; `"heuristic"` and `"greedy"` do not guarantee the fewest payments.

Expected output (payment order may vary):

```text
Case 1:
  Bob -> Alice: 333 cents
  Charlie -> Alice: 333 cents
Case 2:
  Dave -> Bob: 250 cents
Case 3:
  Eve -> Alice: 150 cents

All cases settled successfully.
```

## Usage

```bash
python run_csv_tests.py inputs.csv
```

## Settlement methods

`settle_expenses(expenses, method=...)` accepts:

| Method | Description | Time | Space | Guaranteed minimal? |
|--------|-------------|------|-------|---------------------|
| `exact1` | Bitmask dynamic programming, practical up to about 18 non-zero balances. | O(3^n) | O(2^n) | Yes |
| `exact2` | Bitmask dynamic programming with no enforced size limit. Time and memory still grow exponentially. | O(n · 2^n) | O(2^n) | Yes |
| `heuristic` | Exponential subset enumeration. | O(2^n · n) | O(n · 2^n) | No |
| `greedy` | Greedy matching of the largest debtor to the largest creditor across all balances. | O(n log n) | O(n) | No |
| `auto` | Uses `exact2` for 18 or fewer non-zero balances, then warns and falls back to `greedy` for larger inputs. | Varies | Varies | For eligible inputs |

`auto` is the default. The default threshold of 18 is adjustable via the `threshold` parameter.

## How it works

Function `net_balances(expenses)` sums paid minus owed per person. Uneven splits distribute the extra cents to **earlier** participants (CSV order) via `divmod(amount, n)`:

```
11 cents among ["A", "B"] → A gets 6, B gets 5
```

With `n` non-zero balances and `c` disjoint zero-sum subsets found, the minimum payment count is `n − c`. Each zero-sum subset of size `k` reduces the count by 1 (it can be settled with `k − 1` payments).

## Requirements

- Python 3.8+
- Standard library only (`csv`, `heapq`, `itertools`, `unittest`, `sys`)

## Tests

```bash
python -m unittest discover -v
```
