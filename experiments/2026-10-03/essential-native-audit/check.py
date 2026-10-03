# Document:    Independent audit of point-essential native SAT encoding
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      cb6dfcd88e45abba4a8d2ec02c76b276ec0bfeddd2c768881906e5d16d2fbab4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import importlib.metadata
import json
import random
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from ortools.sat.python import cp_model
from pysat.card import CardEnc

from covering64.core import Universe

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import essential_native_search as source  # noqa: E402


def audited_build(universe, model):
    n = len(universe.blocks)
    assert model['variables'] == n
    assert all(abs(lit) <= n for clause in model['clauses'] for lit in clause)
    assert all(abs(lit) <= n for ids, _ in model['atmost'] for lit in ids)
    boundary = n + len(universe.triples)
    used = set()
    records = []

    class TrackedCounters:
        @staticmethod
        def encode(kind, ids, **kwargs):
            assert kwargs['top_id'] >= boundary
            assert all(1 <= i <= n for i in ids)
            result = getattr(CardEnc, kind)(ids, **kwargs)
            occurring = {abs(lit) for clause in result.clauses for lit in clause}
            auxiliary = occurring - set(ids)
            assert all(i > kwargs['top_id'] for i in auxiliary)
            assert not auxiliary & used
            assert max(occurring, default=0) <= result.nv
            used.update(auxiliary)
            records.append({'kind': kind, 'top_before': kwargs['top_id'],
                            'top_after': result.nv, 'auxiliary_count': len(auxiliary)})
            return result

        @staticmethod
        def atmost(ids, **kwargs):
            return TrackedCounters.encode('atmost', ids, **kwargs)

        @staticmethod
        def atleast(ids, **kwargs):
            return TrackedCounters.encode('atleast', ids, **kwargs)

    original = source.CardEnc
    try:
        source.CardEnc = TrackedCounters
        private = source.add_essential_native(universe, model)
    finally:
        source.CardEnc = original
    assert private == list(range(n + 1, boundary + 1))
    assert model['variables'] == max([boundary, *(r['top_after'] for r in records)])
    assert all(abs(lit) <= model['variables'] for row in model['clauses'] for lit in row)
    assert len(used) == sum(r['auxiliary_count'] for r in records)
    return private, {'block_variables': n, 'private_variables': len(private),
                     'counter_calls': len(records), 'auxiliary_variables': len(used),
                     'maximum_variable': model['variables'],
                     'all_auxiliary_ranges_disjoint_and_above_private': True}


universe = Universe.build(5, 3, 2)
expected_full = {}
expected_essential = {}
for mask in range(1 << len(universe.blocks)):
    chosen = {i for i in range(len(universe.blocks)) if mask >> i & 1}
    multiplicities = [sum(i in chosen for i in containing)
                      for containing in universe.containing]
    if min(multiplicities) == 0:
        continue
    flags = tuple(int(count == 1) for count in multiplicities)
    expected_full[mask] = flags
    if all(any(flags[t] and p in universe.triples[t] for t in universe.coverage[i])
           for i in chosen for p in universe.blocks[i]):
        expected_essential[mask] = flags

base = source.native_model(universe, len(universe.blocks))
private, small_ids = audited_build(universe, base)
# The function appends exactly one block-point clause per incidence after
# constructing all flag equivalences. Remove only those clauses to test flags
# separately even on full covers that fail essentiality.
flag_only = {**base, 'clauses': base['clauses'][:-len(universe.blocks) * universe.k]}
solver = source.make_solver(base)
flag_solver = source.make_solver(flag_only)
wrong_flag_checks = 0
try:
    for mask in range(1 << len(universe.blocks)):
        assumptions = [i + 1 if mask >> i & 1 else -i - 1
                       for i in range(len(universe.blocks))]
        answer = solver.solve(assumptions=assumptions)
        assert answer == (mask in expected_essential), ('essential', mask)
        if answer:
            positive = {i for i in solver.get_model() if i > 0}
            assert tuple(int(p in positive) for p in private) == expected_essential[mask]
        flag_answer = flag_solver.solve(assumptions=assumptions)
        assert flag_answer == (mask in expected_full), ('coverage', mask)
        if flag_answer:
            positive = {i for i in flag_solver.get_model() if i > 0}
            assert tuple(int(p in positive) for p in private) == expected_full[mask]
            for variable, value in zip(private, expected_full[mask]):
                assert not flag_solver.solve(assumptions=assumptions
                                             + [-variable if value else variable])
                wrong_flag_checks += 1
finally:
    solver.delete()
    flag_solver.delete()

# Independently constructed CP model, using linear incidence implications.
cp = cp_model.CpModel()
x = [cp.new_bool_var(f'x{i}') for i in range(len(universe.blocks))]
u = [cp.new_bool_var(f'u{i}') for i in range(len(universe.triples))]
for tid, containing in enumerate(universe.containing):
    count = sum(x[i] for i in containing)
    cp.add(count >= 1)
    cp.add(count == 1).only_enforce_if(u[tid])
    cp.add(count >= 2).only_enforce_if(u[tid].Not())
for bid, block in enumerate(universe.blocks):
    for p in block:
        cp.add(sum(u[t] for t in universe.coverage[bid]
                   if p in universe.triples[t]) >= x[bid])


class AllSolutions(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        super().__init__()
        self.results = {}

    def on_solution_callback(self):
        mask = sum(self.value(variable) << i for i, variable in enumerate(x))
        assert mask not in self.results
        self.results[mask] = tuple(self.value(variable) for variable in u)


collector = AllSolutions()
cp_solver = cp_model.CpSolver()
cp_solver.parameters.enumerate_all_solutions = True
cp_solver.parameters.num_search_workers = 1
status = cp_solver.solve(cp, collector)
assert status == cp_model.OPTIMAL and collector.results == expected_essential

# Check the actual native regular branch structurally, independently rebuilding
# its full collection of necessary point/pair and equality bounds.
full_universe = Universe.build()
full_base = source.native_model(full_universe, 64, branch='regular20', normalize=True)
n = len(full_universe.blocks)
assert full_universe.blocks == tuple(combinations(range(1, 17), 5))
assert full_base['clauses'] == [[i + 1 for i in c] for c in full_universe.containing] + [[1]]
expected_bounds = [(tuple(range(1, n + 1)), 64), (tuple(range(-n, 0)), n - 64)]
for p in range(1, 17):
    incident = tuple(i + 1 for i, block in enumerate(full_universe.blocks) if p in block)
    negatives = tuple(sorted(-i for i in incident))
    expected_bounds.extend([(negatives, len(incident) - 19),
                            (incident, 20), (negatives, len(incident) - 20)])
for pair in combinations(range(1, 17), 2):
    incident = [i + 1 for i, b in enumerate(full_universe.blocks) if set(pair) <= set(b)]
    expected_bounds.append((tuple(sorted(-i for i in incident)), len(incident) - 5))
assert Counter((tuple(sorted(ids)), bound) for ids, bound in full_base['atmost']) == Counter(
    expected_bounds)
_, full_ids = audited_build(full_universe, full_base)

rng = random.Random(2026100322)
for trial in range(128):
    blocks = rng.sample(list(full_universe.blocks), 64)
    order = list(min(blocks)) + [p for p in range(1, 17) if p not in min(blocks)]
    mapping = dict(zip(order, range(1, 17)))
    transformed = {tuple(sorted(mapping[p] for p in b)) for b in blocks}
    assert len(transformed) == 64 and (1, 2, 3, 4, 5) in transformed
    for size in [1, 2, 3]:
        before = Counter(t for b in blocks for t in combinations(b, size))
        after = Counter(t for b in transformed for t in combinations(b, size))
        assert {tuple(sorted(mapping[p] for p in t)): c for t, c in before.items()} == after

result = {
    'sources': {name: hashlib.sha256((ROOT / 'scripts' / name).read_bytes()).hexdigest()
                for name in ['essential_native_search.py', 'native_sat_search.py']},
    'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'python_sat_version': importlib.metadata.version('python-sat'),
    'ortools_version': importlib.metadata.version('ortools'),
    'families_examined': 1024,
    'full_cover_families': len(expected_full),
    'point_essential_full_cover_families': len(expected_essential),
    'sat_direct_oracle_and_independent_cp_agree': True,
    'wrong_private_flag_assumptions_rejected': wrong_flag_checks,
    'small_variable_audit': small_ids,
    'actual_regular_model_variable_audit': full_ids,
    'actual_regular_model_all_bounds_match': True,
    'normalization_trials': 128,
    'normalization_seed': 2026100322,
    'scope': 'Independent encoding audit; no existence or nonexistence result for C(16,5,3)',
}
print(json.dumps(result, indent=2))
