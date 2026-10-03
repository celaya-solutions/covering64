# Document:    Alternating Link Search Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import importlib.util
import random
from itertools import combinations
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "alternate", Path(__file__).resolve().parents[1] / "scripts/alternate_link_search.py")
alternate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alternate)


def test_family_bitmasks_match_independent_set_counts():
    template = alternate.links.projective_plane()
    triples = {t: i for i, t in enumerate(combinations(range(13), 3))}
    pairs = {p: i for i, p in enumerate(combinations(range(13), 2))}
    stats = alternate.family_data(template, triples, pairs)
    assert stats["triple_mask"].bit_count() == 52
    assert stats["pair_one"] == (1 << 78) - 1
    assert stats["pair_two"] == stats["spokes"] == 0
    assert stats["pair_counts"] == [1] * 78


def test_best_response_preserves_pair_bound_while_improving_coverage():
    # One synthetic pair must have total multiplicity5. Fixed families contribute3,
    # so each replacement needs multiplicity2 despite the tempting extra triple.
    families = [
        {"triple_mask": 0, "pair_one": 1, "pair_two": 1, "pair_counts": [2], "spokes": 1},
        {"triple_mask": 1, "pair_one": 1, "pair_two": 1, "pair_counts": [2], "spokes": 2},
        {"triple_mask": 0, "pair_one": 1, "pair_two": 0, "pair_counts": [1], "spokes": 2},
        {"triple_mask": 3, "pair_one": 1, "pair_two": 0, "pair_counts": [1], "spokes": 2},
    ]
    selected, history = alternate.choose_families(
        [0, 1, 2], families, [], {(0, 1, 2): 0, (0, 1, 3): 1}, {(0, 3): 0},
        random.Random(42))
    assert sum(families[i]["pair_counts"][0] for i in selected) >= 5
    assert history[-1]["holes"] <= history[0]["holes"]
