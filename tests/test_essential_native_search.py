import importlib.util
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from covering64.core import Universe

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "essential_native", SCRIPTS / "essential_native_search.py"
)
native = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)


def test_native_projection_and_private_flags_on_all_small_families():
    for v, k, t in [(4, 2, 1), (4, 3, 2)]:
        universe = Universe.build(v, k, t)
        base = native.native_model(universe, len(universe.blocks))
        flags = native.add_essential_native(universe, base)
        solver = native.make_solver(base)
        try:
            for mask in range(1 << len(universe.blocks)):
                blocks = [b for i, b in enumerate(universe.blocks) if mask >> i & 1]
                counts = Counter(s for b in blocks for s in combinations(b, t))
                expected = len(counts) == len(universe.triples) and all(
                    any(point in s and counts[s] == 1 for s in combinations(b, t))
                    for b in blocks
                    for point in b
                )
                assumptions = [
                    i + 1 if mask >> i & 1 else -i - 1 for i in range(len(universe.blocks))
                ]
                assert solver.solve(assumptions=assumptions) == expected
                if expected:
                    true = {lit for lit in solver.get_model() if lit > 0}
                    assert all(
                        (flag in true) == (counts[s] == 1)
                        for s, flag in zip(universe.triples, flags)
                    )
        finally:
            solver.delete()
