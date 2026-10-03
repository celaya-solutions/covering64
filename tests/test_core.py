from itertools import combinations

import pytest

from covering64.core import Universe, normalize_blocks, schonheim_bound, verify_cover


def test_target_universe_and_bound():
    universe = Universe.build()
    assert len(universe.blocks) == 4368
    assert len(universe.triples) == 560
    assert schonheim_bound(16, 5, 3) == 61
    assert all(len(indices) == 78 for indices in universe.containing)
    assert all(mask.bit_count() == 10 for mask in universe.masks)
    for triple_id, block_ids in enumerate(universe.containing):
        assert all(set(universe.triples[triple_id]) <= set(universe.blocks[b]) for b in block_ids)


def test_verifier_negative_control():
    cover = list(combinations(range(1, 5), 3))[:3]
    assert verify_cover(cover, 4, 3, 2)["valid"]
    assert not verify_cover(cover[:2], 4, 3, 2)["valid"]
    assert schonheim_bound(4, 3, 2) == 3


@pytest.mark.parametrize(
    "blocks",
    [
        [(1, 1, 2)],
        [(0, 1, 2)],
        [(1, 2, 5)],
        [(1, 2)],
        [(1, 2, 3), (3, 2, 1)],
        [(1, 2, "3")],
        [(True, 2, 3)],
    ],
)
def test_rejects_malformed_witnesses(blocks):
    with pytest.raises(ValueError):
        normalize_blocks(blocks, 4, 3)
