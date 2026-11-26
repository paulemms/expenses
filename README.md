# Expenses Settler

Python tool that reads a CSV of shared expenses and computes the minimum number of payments needed to settle all debts.

All amounts are dimensionless integers.

## What it does

Suppose an input file `inputs.csv` contains

```csv
case_id,payer,amount,participants
1,Alice,1000,Alice;Bob;Charlie
2,Bob,500,Bob;Dave
3,Alice,300,Alice;Eve
```

The program `run_csv_tests.py` calculates each person's net balance (total paid minus total owed) and produces a list of payments that settles everyone.

The default `--method="auto"` uses method `"exact2"` to find the fewest payments possible for up to 18 people with non-zero balances, then warns and falls back to `"greedy"` above that threshold.

```bash
python run_csv_tests.py inputs.csv
```

Expected output (payment order may vary):

```text
Case 1:
  Bob -> Alice: 333
  Charlie -> Alice: 333
Case 2:
  Dave -> Bob: 250
Case 3:
  Eve -> Alice: 150

All cases settled successfully.
```

The methods implemented are shown below.

| Method | Description | Time | Space | Guaranteed minimal? |
|--------|-------------|------|-------|---------------------|
| `exact0` | Recursive zero-sum partition search without caching. Suitable only for small inputs. | 2^Θ(n log n) | O(n) | Yes |
| `exact1` | Bottom-up bitmask dynamic programming with cached results for each subset, practical up to about 18 non-zero balances. | O(3^n) | O(2^n) | Yes |
| `exact2` | Bottom-up bitmask dynamic programming with cached results, adding one person at a time to maximize zero-sum group boundaries. No enforced size limit; time and memory still grow exponentially. | O(n*2^n) | O(2^n) | Yes |
| `heuristic` | Exponential subset enumeration. | O(n*2^n) | O(n*2^n) | No |
| `greedy` | Greedy matching of the largest debtor to the largest creditor across all balances. | O(n log n) | O(n) | No |
| `auto` | Uses `exact2` for 18 or fewer non-zero balances, then warns and falls back to `greedy` for larger inputs. | Varies | Varies | For eligible inputs |

## How it works

Function `net_balances(expenses)` sums paid minus owed per person. Uneven splits distribute the remainder one at a time to **earlier** participants (CSV order) via `divmod(amount, n)`:

```
11 among ["A", "B"] → A gets 6, B gets 5
```

With `n` non-zero balances and `c` disjoint zero-sum subsets found, the minimum payment count is `n − c`. Each zero-sum subset of size `k` reduces the count by 1 (it can be settled with `k − 1` payments).

`exact2` finds the maximum group count by considering orderings of the people. Each return of the running balance to zero marks a group boundary. It caches the best boundary count for each subset, trying each person as the last person added. This uses at most `n` transitions per subset, giving O(n*2^n) time, while `exact1` considers whole candidate groups and takes O(3^n) time.

## Requirements

- Python 3.8+
- Standard library only (`csv`, `heapq`, `itertools`, `unittest`, `sys`)

## Tests

```bash
python -m unittest discover -v
```
