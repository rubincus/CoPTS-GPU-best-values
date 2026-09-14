# CoPTS-GPU Best Values

Best observed objective values and complete solution vectors for **48 GQMKP
benchmark instances**, obtained with CoPTS-GPU.

## Results

[**Best_Instances_CoPTS-GPU_48.csv**](Best_Instances_CoPTS-GPU_48.csv)

The file contains one row per instance and three columns:

| Column | Meaning |
| --- | --- |
| `instance` | Benchmark instance identifier |
| `best_objective` | Best observed feasible objective value; larger is better |
| `solution` | JSON array containing one knapsack assignment per item |

Indices start at **0**. Assignments `0..m-1` identify real knapsacks; `m` means
unassigned, where `m` is the number of knapsacks in the original instance.
The CSV uses UTF-8 with BOM, comma separators, and a decimal point.

## Verification code

The [verification folder](verification/) contains the CPU evaluator used for the
checks and a runnable verifier. It recomputes the objective, capacity constraints,
class limits, and assignment validity directly from the original `.inc` inputs.

```bash
python -m pip install -r verification/requirements.txt
python verification/verify_results.py --instances-dir /path/to/benchmark/instances
```

The original benchmark input files are required. See the
[verification instructions](verification/README.md) for details.

## Provenance

These results were selected from 1,951 runs: 1,479 static, 360 adaptive, and 112
component-ablation runs. For each instance, the largest recomputed feasible objective
was selected. Ties within `1e-7` were resolved by the lowest seed, then source filename.
These values are best observed results; global optimality is not established.

Dataset snapshot: **2026-09-14**.
