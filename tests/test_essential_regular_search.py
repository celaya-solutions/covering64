import importlib.util
from itertools import combinations
from pathlib import Path

from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover

SPEC = importlib.util.spec_from_file_location(
    "essential_regular", Path(__file__).parents[1] / "scripts/essential_regular_search.py"
)
essential = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(essential)


def test_private_incidence_encoding_matches_exhaustive_small_families():
    universe = Universe.build(4, 3, 2)
    for mask in range(1 << len(universe.blocks)):
        model = cp_model.CpModel()
        variables = [model.new_bool_var(f"b{i}") for i in range(len(universe.blocks))]
        for i, x in enumerate(variables):
            model.add(x == bool(mask & (1 << i)))
        essential.add_essential_constraints(universe, model, variables)
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1
        status = solver.solve(model)
        blocks = [b for i, b in enumerate(universe.blocks) if mask & (1 << i)]
        expected = all(
            any(
                point in t and sum(set(t) <= set(other) for other in blocks) == 1
                for t in combinations(block, 2)
            )
            for block in blocks
            for point in block
        )
        assert (status == cp_model.OPTIMAL) == expected


def test_replacement_lemma_preserves_a_real_complete_cover():
    blocks = read_blocks(Path(__file__).parents[1] / "data/baselines/belic-1997.txt")
    unsupported = essential.unsupported_incidences(blocks)
    assert unsupported
    for index, point in unsupported:
        for outside in set(range(1, 17)) - set(blocks[index]):
            replacement = tuple(sorted((set(blocks[index]) - {point}) | {outside}))
            transformed = set(blocks)
            transformed.remove(blocks[index])
            transformed.add(replacement)
            assert verify_cover(transformed)["valid"]
            assert sum(point in b for b in transformed) == sum(point in b for b in blocks) - 1


def test_duplicate_replacement_really_allows_block_deletion():
    # Every pair on four points lies in two of these four triples.
    blocks = list(combinations(range(1, 5), 3))
    assert essential.unsupported_incidences(blocks, 2)
    replacement = (2, 3, 4)
    reduced = set(blocks) - {(1, 2, 3)}
    assert replacement in reduced
    assert verify_cover(reduced, 4, 3, 2)["valid"]
