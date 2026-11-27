# The Expenses Settlement Problem

This repository contains algorithms for calculating the minimum number of payments required to settle a collection of shared expenses. In general, this is a combinatorial optimisation problem that is NP-hard.

## Overview

Suppose an input file `inputs.csv` contains

```csv
case_id,payer,amount,participants
1,Alice,1000,Alice;Bob;Charlie
2,Bob,500,Bob;Dave
2,Dave,200,Bob;Dave
3,Alice,300,Eve;Bob;Charlie
```

All amounts are dimensionless integers.

The script `run_csv_tests.py` calculates each person's net balance (total paid minus total owed) for each independent case. It then produces a list of payments that settles everyone in each case.

The default `--method="auto"` uses method `"exact2"` to find the fewest payments possible for up to 18 people with non-zero balances, then warns and falls back to `"greedy"` above that threshold. The `"greedy"` method does not necessarily return the fewest payments.

```bash
python run_csv_tests.py inputs.csv --method=auto
```

Expected output (payment order may vary):

```text
Case 1:
  Bob -> Alice: 333
  Charlie -> Alice: 333
Case 2:
  Dave -> Bob: 150
Case 3:
  Eve -> Alice: 100
  Bob -> Alice: 100
  Charlie -> Alice: 100

All cases settled successfully.
```

The methods avaiable are shown below.

| Method | Description | Time | Space | Guaranteed minimal? |
|--------|-------------|------|-------|---------------------|
| `exact0` | Recursive zero-sum partition search without caching. Suitable only for small inputs. | 2^Θ(n log n) | O(n) | Yes |
| `exact1` | Bottom-up bitmask dynamic programming with cached results for each subset, practical up to about 18 non-zero balances. | O(3^n) | O(2^n) | Yes |
| `exact2` | Bottom-up bitmask dynamic programming with cached results, adding one person at a time to maximize zero-sum group boundaries. No enforced size limit. | O(n*2^n) | O(2^n) | Yes |
| `heuristic` | Exponential subset enumeration. | O(n*2^n) | O(n*2^n) | No |
| `greedy` | Greedy matching of the largest debtor to the largest creditor across all balances. | O(n log n) | O(n) | No |
| `auto` | Uses `exact2` for 18 or fewer non-zero balances, then warns and falls back to `greedy` for larger inputs. | Varies | Varies | For eligible inputs |

## Implementation

The script `run_csv_tests.py` uses the module `settle_expenses`.

Function `net_balances(expenses)` sums paid minus owed per person. Uneven splits distribute the remainder one at a time to **earlier** participants (CSV order) via `divmod(amount, n)`:

```
11 among ["A", "B"] → A gets 6, B gets 5
```

With `n` non-zero balances, the minimum payment count is `n − c`, where `c` is the maximum number of groups in a zero-sum partition. A zero-sum group of size `k` can be settled with at most `k − 1` payments.

Function `settle_expenses(expenses, method)` selects the algorithm through its `method` argument. Method `exact2` finds the maximum group count by considering orderings of the people. Each return of the running balance to zero marks a group boundary. It caches the best boundary count for each subset, trying each person as the last person added. This uses at most `n` transitions per subset, giving O(n*2^n) time, while method `exact1` considers whole candidate groups and takes O(3^n) time.

## Requirements

- Python 3.8+
- Standard library only (`csv`, `heapq`, `itertools`, `unittest`, `sys`)

## Tests

```bash
python -m unittest discover -v
```

## References

- Yoshua Bengio, Andrea Lodi, and Antoine Prouvost, [Machine Learning for Combinatorial Optimization: a Methodological Tour d’Horizon](https://arxiv.org/abs/1811.06128v2), arXiv:1811.06128v2 (2020).
- K. T. Chung, C. K. M. Lee, and Y. P. Tsang, [Neural combinatorial optimization with reinforcement learning in industrial engineering: a survey](https://doi.org/10.1007/s10462-024-11045-1), *Artificial Intelligence Review*, 58, 130 (2025).
- Hanjun Dai, Elias B. Khalil, Yuyu Zhang, Bistra Dilkina, and Le Song, [Learning Combinatorial Optimization Algorithms over Graphs](https://arxiv.org/abs/1704.01665v4), NIPS 2017 (arXiv revision 2018).
- Guillaume Fertin, Oscar Fontaine, Géraldine Jean, and Stéphane Vialette, [The Maximum Zero-Sum Partition problem](https://doi.org/10.1016/j.tcs.2024.114811), *Theoretical Computer Science*, 1019, 114811 (2024).
- Guillaume Haeringer, [Minimizing settlements](https://doi.org/10.1016/j.jmateco.2023.102840), *Journal of Mathematical Economics*, 106, 102840 (2023). Studies the minimum-transfer objective through a buyer–seller transportation model. Connects minimum transfers to maximizing balanced connected components, gives an `n − 1` settlement construction, and establishes computational hardness. Closely matches the zero-sum-group explanation used here.
- Csaba Pătcaș, [On the debts’ clearing problem](https://www.cs.ubbcluj.ro/~studia-i/contents/2009-2/10-Patcas.pdf), *Studia Universitatis Babeș-Bolyai, Informatica*, 54(2), 109–120 (2009). Develops an exact dynamic-programming solution with exponential time and Θ(2^n) space. Provides context for `exact1`, although its formulation differs from this implementation.
- Csaba Pătcaș, [The debts’ clearing problem: a new approach](https://arxiv.org/abs/1111.3663), *Acta Universitatis Sapientiae, Informatica*, 3(2), 192–204 (2011). Extends the problem to changing debt graphs and develops an improved algorithm for the static problem. Useful for comparing alternative exact methods and considering future extensions.
- Csaba Pătcaș and Attila Bartha, [Evolutionary solving of the debts’ clearing problem](https://acta.sapientia.ro/content/docs/evolutionary-solving-of-the-debts-cleari.pdf) (2019).
- Michael I. Shamos and Michael Trick, [A Graph-Theoretic Model of Electronic Payments](https://euro.ecom.cmu.edu/people/faculty/mshamos/epay6.pdf) (2001 draft). Gives a graph-based treatment of settlement, a constructive method requiring at most `n − 1` payments, and an NP-completeness proof for minimizing payments. Provides foundational background.
- Yuanfan Yao, [Settling Debts Efficiently: Zero-Sum Set Packing](https://nrs.harvard.edu/urn-3:HUL.InstRepos:38811480), senior thesis, Harvard University (2017).

## Related work

These papers cover stochastic search methods for combinatorial optimisation and practical clearing procedures for invoice networks. Their methods and objectives would need to be adapted and evaluated for minimum-payment settlement.

- Peplluis de la Rosa Esteva and Sai Srikanth Madugula, [Multilateral Clearing on Invoice Graphs: Path Enabled Compensation Versus Cycle Restricted Netting](https://arxiv.org/abs/2606.26126), arXiv preprint (June 2026). Compares deterministic clearing procedures on real invoice networks, using local three-party reductions that preserve net positions. Focuses on reducing outstanding obligations rather than guaranteeing the fewest payments.
- Peplluis Esteva de la Rosa and Sai Srikanth Madugula, [Atomic Common-Day Invoice Clearing under Causal Daily Scheduling: Path-Enabled and Bounded-Cycle Policies](https://arxiv.org/abs/2608.23060), arXiv preprint (August 2026). Extends clearing to invoices with dates and execution constraints. Compares practical policies and distinguishes their benefits from global optimality.
- Thomas A. Feo and Mauricio G. C. Resende, [Greedy Randomized Adaptive Search Procedures](https://mauricio.resende.info/doc/gtut.pdf), *Journal of Global Optimization*, 6 (1995). Introduces GRASP: repeated randomised greedy construction followed by local improvement.
- David S. Johnson, Cecilia R. Aragon, Lyle A. McGeoch, and Catherine Schevon, [Optimization by Simulated Annealing: An Experimental Evaluation; Part II, Graph Coloring and Number Partitioning](https://doi.org/10.1287/opre.39.3.378), *Operations Research*, 39(3), 378–406 (1991). Compares simulated annealing with other heuristics, including repeated local search, on related optimisation problems.
- S. Kirkpatrick, C. D. Gelatt Jr., and M. P. Vecchi, [Optimization by Simulated Annealing](https://doi.org/10.1126/science.220.4598.671), *Science*, 220(4598), 671–680 (1983). Introduces simulated annealing for optimisation, using probabilistic acceptance of worse solutions to escape local optima.
- Helena R. Lourenço, Olivier C. Martin, and Thomas Stützle, [Iterated Local Search](https://arxiv.org/abs/math/0102188), arXiv:math/0102188 (2001 preprint). Surveys methods that repeatedly perturb a solution and apply local improvement.
