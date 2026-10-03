# Document:    Regular group search controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Test group actions, orbit coverage, and strict enumerator input."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from covering64.core import Universe

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.orbit_search import block_orbits  # noqa: E402
from scripts.regular_group_search import families, generated_group  # noqa: E402


def test_listed_actions_are_regular():
    for name, generators in families():
        group = generated_group(generators)
        assert len(group) == 16, name
        for point in range(16):
            assert {g[point] for g in group} == set(range(1, 17)), name


def test_orbits_partition_and_coverage_is_constant_on_triple_orbits():
    universe = Universe.build()
    triples = Universe.build(v=16, k=3, t=3)
    for _, generators in families():
        orbits = block_orbits(universe, generators)
        triple_orbits = block_orbits(triples, generators)
        assert sorted(b for o in orbits for b in o) == list(range(4368))
        assert sorted(t for o in triple_orbits for t in o) == list(range(560))
        assert {len(o) for o in (*orbits, *triple_orbits)} == {16}
        for orbit in orbits:
            covered = {t for b in orbit for t in universe.coverage[b]}
            assert all(not covered.intersection(o) or set(o) <= covered
                       for o in triple_orbits)


@pytest.fixture(scope="module")
def enumerator(tmp_path_factory):
    compiler = shutil.which("clang++")
    if not compiler:
        pytest.skip("C++ compiler unavailable")
    path = tmp_path_factory.mktemp("enumerator") / "enumerate"
    source = Path(__file__).parents[1] / "experiments/2026-10-03/orbit-enumerate.cpp"
    subprocess.run([compiler, "-std=c++17", "-O2", str(source), "-o", str(path)], check=True)
    return path


@pytest.mark.parametrize("data", ["0\n" * 272, "0\n" * 274,
                                  "0\n" * 273 + "junk", "0\n" * 272 + "12x",
                                  "0\n" * 272 + str(1 << 35),
                                  "0\n" * 272 + str(1 << 100),
                                  "0\n" * 272 + "-1"])
def test_enumerator_rejects_damaged_input(enumerator, tmp_path, data):
    source = tmp_path / "masks.txt"
    source.write_text(data)
    assert subprocess.run([str(enumerator), str(source)], capture_output=True).returncode == 3


def test_enumerator_positive_union_control(enumerator, tmp_path):
    source = tmp_path / "masks.txt"
    source.write_text((str((1 << 35) - 1) + "\n") * 273)
    run = subprocess.run([str(enumerator), str(source)], text=True, capture_output=True)
    assert run.returncode == 0
    assert "FOUND" in run.stdout
