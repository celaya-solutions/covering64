"""Check that orbit compression preserves exactly its named restricted family."""

import importlib.util
from pathlib import Path

import pytest

from covering64.core import Universe

SPEC = importlib.util.spec_from_file_location(
    "orbit_search", Path(__file__).resolve().parents[1] / "scripts" / "orbit_search.py"
)
orbit_search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(orbit_search)


def test_orbits_partition_and_close_under_all_generators():
    universe = Universe.build(4, 2, 2)
    generators = [(2, 1, 4, 3), (3, 4, 1, 2)]
    orbits = orbit_search.block_orbits(universe, generators)
    assert sorted(b for orbit in orbits for b in orbit) == list(range(6))
    for orbit in orbits:
        blocks = {universe.blocks[b] for b in orbit}
        for block in blocks:
            for generator in generators:
                assert tuple(sorted(generator[p - 1] for p in block)) in blocks


def test_orbit_cover_positive_and_negative_controls():
    universe = Universe.build(4, 2, 2)
    generator = orbit_search.cyclic_permutation([4], 4)
    good = orbit_search.search(universe, [generator], 6, 2, 0, 1)
    assert good["verification"]["valid"]
    assert len(good["witness"]) == 6
    bad = orbit_search.search(universe, [generator], 5, 2, 0, 1)
    assert bad["status"] == "INFEASIBLE"
    assert bad["witness"] is None


def test_invalid_generator_rejected():
    with pytest.raises(ValueError, match="permute"):
        orbit_search.block_orbits(Universe.build(4, 2, 2), [(1, 2, 3, 3)])
