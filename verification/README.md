# Reproducing the verification

This folder contains the verification code used to check the published solution
vectors, packaged for execution from this repository:

- `gqmkp_io.py`: the original instance parser, objective evaluator, and feasibility
  checker, copied unchanged from the experiment's CPU verification module.
- `verify_results.py`: a portable runner that applies the assignment checks and
  Decimal capacity calculations used during the export, then cross-checks the
  original evaluator.
- `input_manifest.json`: identifiers, dimensions, and SHA-256 hashes of the 48
  original `.inc` files, plus the evaluator hash. Hashing normalizes CRLF to LF.

## Requirements and execution

Use Python 3.10 or later and NumPy. The original benchmark `.inc` files are required;
provide the directory containing them with `--instances-dir`. It is searched recursively
and must contain exactly one matching file for each published instance identifier.
Input hashes are checked against the manifest before parsing.

From the repository root:

```bash
python -m pip install -r verification/requirements.txt
python verification/verify_results.py --instances-dir /path/to/benchmark/instances
```

For an optional JSON report with per-instance objective comparisons:

```bash
python verification/verify_results.py --instances-dir /path/to/benchmark/instances --report verification_report.json
```

On Windows, quote input paths containing spaces. `--solutions` can specify another
CSV with the same three columns and the same 48 instance identifiers.

The program returns exit code **0** only after every solution passes; any missing,
duplicate, malformed, or mismatched input, infeasible solution, or objective mismatch
returns a nonzero exit code. A successful run reports **48 solutions** and **5,376
constraint checks** verified.

## Checks and arithmetic

1. Each solution has exactly one integer assignment per item, in `0..m`.
2. For each real knapsack, item weights plus one setup weight per present class
   do not exceed capacity. These loads use Decimal arithmetic and no tolerance.
3. Each class occupies at most its permitted number of distinct real knapsacks.
4. The objective is recomputed using the original NumPy float64 evaluator:
   individual profits plus pair profits for items in the same real knapsack.
   The absolute difference from the published value must be at most `1e-7`.
5. The original evaluator must also report the solution as feasible.

This establishes feasibility and consistency of the published objective values.
It does not establish global optimality or reproduce the original search campaigns.

The bundled evaluator's original standalone entry point expects the experiment
directory layout. Use `verify_results.py` as shown above to verify this public CSV.

## Validated run

Tested with Python 3.12.14 and NumPy 2.3.5: all 48 solutions and 5,376 constraint
checks passed. The largest absolute objective difference was `1e-11`, below the
`1e-7` tolerance.

## Tests

```bash
python -m unittest discover -s verification -p "test_*.py"
```

The tests cover valid solutions, one setup charge per present class, unassigned
items, invalid vector lengths and domains, false objective values, capacity
violations, and class-spread violations.
