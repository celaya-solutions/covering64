import importlib.util
from collections import Counter
from math import comb, prod
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "four_seven_link_orbits", Path(__file__).parents[1] / "scripts/four_seven_link_orbits.py"
)
links = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(links)


def test_enumeration_matches_independent_inclusion_exclusion_count():
    expected = sum((-1)**j * comb(3, j) * 3**j * comb(12 - 2*j, 2)
                   * prod(range(1, 10 - 2*j, 2)) for j in range(4))
    generated = list(links.families())
    assert len(generated) == len(set(generated)) == expected == 29970
    target = Counter({p: (2 if p == 4 else 1) for p in range(4, 17)})
    for family in generated:
        assert len(family) == len(set(family)) == 7
        assert Counter(p for edge in family for p in edge) == target
        assert not set(family) & links.FORBIDDEN


@pytest.mark.parametrize("case", ["cycle", "matching"])
def test_complete_disjoint_orbits_with_explicit_relabelings(case):
    result, maps = links.enumerate_orbits(case)
    assert len(result["representatives"]) == 129
    assert sum(r["orbit_size"] for r in result["representatives"]) == 29970
    seen = set()
    for rep, orbit in zip(result["representatives"], maps):
        assert rep["id"] == orbit["id"]
        for entry in orbit["maps"]:
            assert sorted(entry["from_representative"]) == list(range(1, 17))
            image = links.transform(rep["edges"], entry["from_representative"])
            assert image == entry["edges"]
            assert image not in seen
            seen.add(image)
    assert seen == set(links.families())
