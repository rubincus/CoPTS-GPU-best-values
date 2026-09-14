# CoPTS-GPU Best Values

Best objective values and complete solution vectors obtained with **CoPTS-GPU** for
**48 benchmark instances** of the Generalized Quadratic Multiple Knapsack Problem
(GQMKP), together with detailed constraint checks.

## Data files

| File | Data rows | Contents |
| --- | ---: | --- |
| [Best_Instances_CoPTS-GPU_48.csv](Best_Instances_CoPTS-GPU_48.csv) | 48 | Instance identifier, best objective value, and complete solution vector |
| [Best_Instances_CoPTS-GPU_48_Constraints.csv](Best_Instances_CoPTS-GPU_48_Constraints.csv) | 5,376 | Individual assignment, capacity, and class constraint checks |

The main CSV contains exactly three columns:

- `instance`: benchmark instance identifier, such as `1_1`.
- `best_objective`: the best observed feasible objective value. Larger values are better.
- `solution`: a JSON array containing one knapsack assignment per item.

Both CSV files use UTF-8 with BOM, commas as field separators, and a decimal point.
JSON arrays are stored inside quoted CSV fields.

## Solution encoding

Item, knapsack, and class indices start at **0**. The value at position `j` in
`solution` is the assignment of item `j`:

- Values `0` through `m-1` identify the real knapsacks.
- Value `m` means that the item is unassigned, where `m` is the number of real knapsacks
  in the benchmark instance.

The vector must contain exactly as many entries as the instance has items. Every
entry must be an integer in `0..m`, representing one assignment per item.

## Constraint checks

The constraint CSV provides `constraint_type`, `index_0_based`, `observed_value`,
`operator`, `limit`, `slack`, and `satisfied` for each check.

| Constraint type | Meaning |
| --- | --- |
| `solution_length` | The vector contains exactly one entry per item. |
| `assignment_domain` | No assignment is noninteger or outside the allowed range. |
| `knapsack_capacity` | Item weights plus class setup weights do not exceed knapsack capacity. |
| `class_knapsack_limit` | The number of distinct real knapsacks containing a class does not exceed that class's limit. |

For capacity checks:

`item_weight + class_setup_weight <= limit`

A class setup weight is counted once per knapsack containing that class, regardless
of how many items from the class are present.

For class checks, `observed_value` counts distinct real knapsacks containing at least
one item of the class. Unassigned items do not contribute to this count.

**Slack = limit - observed value.** Positive slack indicates remaining allowance;
zero indicates a binding constraint. Equality checks require zero slack. The
`satisfied` field records whether each check passes.

Example: `class_knapsack_limit`, class `0`, observed value `2`, limit `4`, slack `2`,
and knapsacks `[1,6]` means that class 0 appears in two knapsacks out of four allowed,
so the constraint is satisfied.

All **5,376 checks** for the 48 exported solutions pass. Capacity loads were computed
with decimal arithmetic and cross-checked against the experiment evaluator. The
capacity and class limits are satisfied without relying on numerical tolerance.

## Selection and provenance

The exported values were selected from **1,951 recorded runs**:

- 1,479 runs of the static configuration over 48 instances.
- 360 runs of the adaptive configuration over 12 instances.
- 112 component-ablation runs over 8 instances, including the control without cooperation.

For each instance, the largest feasible recomputed objective across these campaigns
was selected. All 1,951 stored solutions were checked for feasibility, and their
recomputed objective values matched the recorded exact values.

Values within an absolute tolerance of `1e-7` were treated as ties. The lowest seed
was selected first, followed by the source filename in lexicographic order.
These are **best observed results**, rather than proofs of global optimality.
Run budgets differ between campaigns, so these maxima alone do not establish a
comparison of algorithm performance under equal budgets.

In the constraint CSV, `version`, `variant`, and `seed` describe the selected run.
`source_file` and `instance_file` are provenance labels identifying files in the
original experiment archive. Those labels are not paths within this public data repository.

Dataset snapshot: **2026-09-14**.
