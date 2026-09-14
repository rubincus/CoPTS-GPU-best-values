"""Reproduce the objective and constraint checks for the 48 published solutions.

Uses the original float64 evaluator and the Decimal capacity checks used during
the export. This checks feasibility and objective consistency, not optimality.
"""
import argparse
import csv
import hashlib
import json
import platform
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np
from gqmkp_io import parse_instance

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OBJECTIVE_TOLERANCE = Decimal('1e-7')


def decimal(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError(f'Nonfinite numeric value: {value!r}')
    return result


def normalized_sha256(path):
    """Ignore platform differences in CRLF/LF line endings, preserve other bytes."""
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def verify_solution(instance, solution, reported_objective):
    """Return the recomputed objective and all constraint measurements.

    Validate the vector before calling the original evaluator, which assumes a
    correctly shaped integer assignment vector.
    """
    if not isinstance(solution, list) or len(solution) != instance.n:
        raise ValueError(f'Solution must contain exactly {instance.n} assignments')
    if any(type(k) is not int or not 0 <= k <= instance.m for k in solution):
        raise ValueError(f'Assignments must be integers in 0..{instance.m}')

    checks = []

    def add(kind, index, value, operator, limit):
        value, limit = decimal(value), decimal(limit)
        checks.append({
            'constraint_type': kind, 'index_0_based': str(index),
            'observed_value': str(value), 'operator': operator, 'limit': str(limit),
            'slack': str(limit - value),
            'satisfied': str(value == limit if operator == 'equal to' else value <= limit).lower(),
        })

    add('solution_length', '', len(solution), 'equal to', instance.n)
    add('assignment_domain', '', 0, 'equal to', 0)
    weights = [decimal(w) for w in instance.w]
    setups = [decimal(s) for s in instance.s]
    capacity = decimal(instance.cap)
    class_knapsacks = [set() for _ in range(instance.h)]

    for k in range(instance.m):
        items = [j for j, assigned in enumerate(solution) if assigned == k]
        classes = sorted({int(instance.t_jr[j]) for j in items})
        for r in classes:
            class_knapsacks[r].add(k)
        item_weight = sum((weights[j] for j in items), Decimal(0))
        setup_weight = sum((setups[r] for r in classes), Decimal(0))
        add('knapsack_capacity', k, item_weight + setup_weight, '<=', capacity)

    for r in range(instance.h):
        knapsacks = sorted(class_knapsacks[r])
        add('class_knapsack_limit', r, len(knapsacks), '<=', int(instance.nr[r]))

    for check in checks:
        if check['satisfied'] != 'true':
            raise ValueError(f"{check['constraint_type']}[{check['index_0_based']}]: "
                             f"{check['observed_value']} exceeds {check['limit']}")
    feasible, message = instance.feasible(solution)
    if not feasible:
        raise ValueError(f'Original evaluator rejected solution: {message}')
    objective = decimal(instance.objective(solution))
    error = abs(objective - decimal(reported_objective))
    if error > OBJECTIVE_TOLERANCE:
        raise ValueError(f'Objective mismatch: reported={reported_objective}, '
                         f'recomputed={objective}, absolute_error={error}')
    return objective, checks


def read_csv(path, fields=None):
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f'{Path(path).name}: missing or duplicate headers')
        if fields is not None and reader.fieldnames != fields:
            raise ValueError(f'{Path(path).name}: expected columns {fields}')
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError(f'{Path(path).name}: malformed CSV row')
    return rows


def run_verification(instances_dir, solutions_path, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    if normalized_sha256(HERE / 'gqmkp_io.py') != manifest['evaluator_sha256_normalized_lf']:
        raise ValueError('Original evaluator differs from the recorded snapshot')
    rows = read_csv(solutions_path, ['instance', 'best_objective', 'solution'])
    names = [r['instance'] for r in rows]
    entries = manifest['instances']
    if len(entries) != 48 or len(names) != len(set(names)) or set(names) != set(entries):
        raise ValueError('Solutions CSV must contain exactly the 48 manifest instances, once each')

    candidates = {}
    for path in Path(instances_dir).rglob('*.inc'):
        candidates.setdefault(path.stem, []).append(path)
    constraint_count, objectives = 0, []
    for row in rows:
        name = row['instance']
        matches = candidates.get(name, [])
        if len(matches) != 1:
            raise ValueError(f'{name}: expected one .inc file, found {len(matches)}')
        instance_path = matches[0]
        if normalized_sha256(instance_path) != entries[name]['sha256_normalized_lf']:
            raise ValueError(f'{name}: input hash does not match the certified dataset')
        instance = parse_instance(instance_path)
        if [instance.n, instance.m, instance.h] != [entries[name][k] for k in ('n_items', 'n_knapsacks', 'n_classes')]:
            raise ValueError(f'{name}: unexpected instance dimensions')
        try:
            objective, checks = verify_solution(instance, json.loads(row['solution']), row['best_objective'])
        except ValueError as exc:
            raise ValueError(f'{name}: {exc}') from exc
        constraint_count += len(checks)
        objectives.append({'instance': name, 'reported_objective': row['best_objective'],
                           'recomputed_objective': str(objective),
                           'absolute_error': str(abs(objective - decimal(row['best_objective'])))})

    return {'status': 'passed', 'solutions_verified': len(rows),
            'constraint_checks_verified': constraint_count, 'failed_checks': 0,
            'objective_absolute_tolerance': str(OBJECTIVE_TOLERANCE),
            'maximum_objective_absolute_error': str(max(decimal(r['absolute_error']) for r in objectives)),
            'instance_hashes_verified': len(rows), 'python_version': platform.python_version(),
            'numpy_version': np.__version__, 'objectives': objectives}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instances-dir', type=Path, required=True,
                        help='Directory containing the original benchmark .inc files (searched recursively)')
    parser.add_argument('--solutions', type=Path, default=ROOT / 'Best_Instances_CoPTS-GPU_48.csv')
    parser.add_argument('--manifest', type=Path, default=HERE / 'input_manifest.json')
    parser.add_argument('--report', type=Path, help='Optional destination for the complete JSON report')
    args = parser.parse_args(argv)
    try:
        report = run_verification(args.instances_dir, args.solutions, args.manifest)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError, KeyError, TypeError, AssertionError, InvalidOperation) as exc:
        print(f'VERIFICATION FAILED: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in report.items() if k != 'objectives'}, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
