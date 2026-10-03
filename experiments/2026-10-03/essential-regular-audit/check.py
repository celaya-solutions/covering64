# Document:    Independent point-essential model audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      713cf373a335fc5c6ee38e645866db8a5566194c8c47bce84be5f153b1e7da4e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import random
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.essential_regular_search import add_essential_constraints, build_model  # noqa: E402

universe = Universe.build(5, 3, 2)
expected = {}
for mask in range(1 << len(universe.blocks)):
    chosen = {i for i in range(len(universe.blocks)) if mask >> i & 1}
    counts = [sum(i in chosen for i in ids) for ids in universe.containing]
    valid = all(any(counts[t] == 1 and p in universe.triples[t]
                    for t in universe.coverage[i])
                for i in chosen for p in universe.blocks[i])
    if valid:
        expected[mask] = tuple(int(n == 1) for n in counts)
model = cp_model.CpModel()
variables = [model.new_bool_var(f'x{i}') for i in range(len(universe.blocks))]
private = add_essential_constraints(universe, model, variables)


class Collector(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        super().__init__()
        self.got = {}

    def on_solution_callback(self):
        mask = sum(self.value(v) << i for i, v in enumerate(variables))
        assert mask not in self.got
        self.got[mask] = tuple(self.value(v) for v in private)


collector = Collector()
solver = cp_model.CpSolver()
solver.parameters.enumerate_all_solutions = True
solver.parameters.num_search_workers = 1
status = solver.solve(model, collector)
assert status == cp_model.OPTIMAL
assert collector.got == expected

seed = 2026100316
rng = random.Random(seed)
blocks = list(combinations(range(1, 17), 5))
for trial in range(256):
    chosen = rng.sample(blocks, rng.randrange(1, 100))
    first = min(chosen)
    order = list(first) + [p for p in range(1, 17) if p not in first]
    mapping = dict(zip(order, range(1, 17)))
    assert sorted(mapping) == list(range(1, 17))
    assert sorted(mapping.values()) == list(range(1, 17))
    mapped = {tuple(sorted(mapping[p] for p in b)) for b in chosen}
    assert (1, 2, 3, 4, 5) in mapped and len(mapped) == len(chosen)
    before = Counter(t for b in chosen for t in combinations(b, 3))
    after = Counter(t for b in mapped for t in combinations(b, 3))
    assert Counter({tuple(sorted(mapping[p] for p in t)): n
                    for t, n in before.items()}) == after
    for b in chosen:
        for p in b:
            supported = any(before[t] == 1 and p in t for t in combinations(b, 3))
            mb = tuple(sorted(mapping[q] for q in b))
            mapped_supported = any(after[t] == 1 and mapping[p] in t
                                   for t in combinations(mb, 3))
            assert supported == mapped_supported
for max_missing in [0, 5]:
    _, full_model, _, _, _ = build_model(max_missing)
    assert full_model.validate() == ''
source = Path('scripts/essential_regular_search.py')
print(json.dumps({
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'audit_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'ortools_version': ortools.__version__,
    'all_1024_families_examined': True,
    'admissible_families': len(expected),
    'encoded_family_set_matches': collector.got == expected,
    'all_private_indicators_match': True,
    'normalization_trials': 256,
    'normalization_seed': seed,
    'normalization_preserves_distinctness_coverage_and_essentiality': True,
    'full_and_partial_model_validate': True,
    'solver_status': solver.status_name(status),
    'scope': ('Encoding equivalence on a complete small universe; normalization checks; '
              'no C(16,5,3) existence result'),
}, indent=2))
