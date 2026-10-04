# Document:    Exhaustive Hub Count Split Checks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e72a6fad26a9c592b8b444e73f57ecceca752f46079173b206688bbac4d2e155
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import sys
from itertools import combinations
from pathlib import Path

import pytest
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from four_seven_hub_split import CASES, add_hub_count_split  # noqa: E402
from four_seven_search import build_model, pair_targets  # noqa: E402


def test_partition_and_hub_nonedge_excess_bound():
    assert CASES == tuple((m4, z) for m4 in range(2) for z in range(3))
    hubs = (4, 8, 12, 16)
    for case in ("cycle", "matching"):
        targets = pair_targets(case)
        nonedges = [pair for pair in combinations(hubs, 2) if targets[pair] == 5]
        consumption = [sum(set(pair) <= set(triple) for pair in nonedges)
                       for triple in combinations(hubs, 3)]
        assert len(set(consumption)) == 1
        assert len(nonedges) // consumption[0] == 2
        possible = {(m4, z) for m4 in range(3) for z in range(3)
                    if 4 + z - 4 * m4 >= 0}
        assert possible == set(CASES)


@pytest.mark.parametrize("case", ("cycle", "matching"))
def test_all_split_rows_and_base_preservation(case):
    universe, base, xs, _ = build_model(case)
    base.add_hint(xs[0], 0)
    base.minimize(xs[-1])
    before = cp_model_pb2.CpModelProto()
    text_format.Parse(str(base.proto), before)
    expected_four = {}
    expected_triples = {}
    hub_triples = list(combinations((4, 8, 12, 16), 3))
    for i, block in enumerate(universe.blocks):
        if all(hub in block for hub in (4, 8, 12, 16)):
            expected_four[i] = 1
        value = sum(set(triple) <= set(block) for triple in hub_triples)
        if value:
            expected_triples[i] = value
    for m4, z in CASES:
        model = base.clone()
        application = add_hub_count_split(universe, model, xs, case, m4, z)
        after = cp_model_pb2.CpModelProto()
        text_format.Parse(str(model.proto), after)
        assert application["new_variables"] == 0
        assert application["new_rows"] == 2
        first, second = after.constraints[-2:]
        assert dict(zip(first.linear.vars, first.linear.coeffs)) == expected_four
        assert dict(zip(second.linear.vars, second.linear.coeffs)) == expected_triples
        assert list(first.linear.domain) == [m4, m4]
        assert list(second.linear.domain) == [4 + z, 4 + z]
        del after.constraints[-2:]
        assert after.SerializeToString() == before.SerializeToString()
        unchanged = str(model.proto)
        with pytest.raises(ValueError, match="already present"):
            add_hub_count_split(universe, model, xs, case, m4, z)
        assert str(model.proto) == unchanged
    for invalid in ((2, 4), (-1, 0), (0, 3), (True, 0), (0, False), (0.0, 0)):
        model = base.clone()
        unchanged = str(model.proto)
        with pytest.raises(ValueError, match="six exhaustive"):
            add_hub_count_split(universe, model, xs, case, *invalid)
        assert str(model.proto) == unchanged
    model = base.clone()
    unchanged = str(model.proto)
    with pytest.raises(ValueError):
        add_hub_count_split(universe, model, xs,
                            "matching" if case == "cycle" else "cycle", 0, 0)
    assert str(model.proto) == unchanged
