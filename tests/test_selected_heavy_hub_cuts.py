# Document:    Selected Heavy Hub Encoding Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check prefix preservation, every new row, threshold truth, and damaged controls."""

import sys
from itertools import product
from pathlib import Path

import pytest
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import selected_heavy_hub_cuts as cuts  # noqa: E402
from first_family_hub_cuts import add_normalized_hub_cuts  # noqa: E402
from first_family_residual_cuts import add_residual_pair_cuts  # noqa: E402
from first_family_search import build_model  # noqa: E402
from heavy_triple_search import add_heavy_count_cuts  # noqa: E402

from covering64.core import read_blocks  # noqa: E402


def protobuf(model):
    result = cp_model_pb2.CpModelProto()
    text_format.Parse(str(model.proto), result)
    return result


@pytest.fixture(scope="module")
def base():
    blocks = read_blocks(ROOT / "experiments/2026-10-03/structured-hub-escape/candidate-h9.txt")
    family = [tuple(p for p in b if p != 1) for b in blocks if set(b) & {1, 2, 3} == {1}]
    u, model, xs, holes = build_model(
        family, 9, require_outside_pair_bound=False, require_opposite_spoke=False,
    )
    add_residual_pair_cuts(u, model, xs, holes)
    add_heavy_count_cuts(u, model, xs)
    add_normalized_hub_cuts(u, model, xs)
    return u, model, blocks


def row_signature(row):
    assert row.WhichOneof("constraint") == "linear"
    return (tuple(sorted(row.enforcement_literal)),
            tuple(sorted(zip(row.linear.vars, row.linear.coeffs))), tuple(row.linear.domain))


def test_all_new_rows_and_preservation_of_every_prior_proto_field(base):
    u, original, _ = base
    model = original.clone()
    before = protobuf(model)
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    result = cuts.add_selected_hub_cuts(u, model, xs)
    after = protobuf(model)
    assert result["new_variables"] == 52 and result["new_rows"] == 280
    assert len(after.variables) == 6480 and len(after.constraints) == 7534
    all_rows = list(after.constraints[len(before.constraints):])
    names = {v.name: i for i, v in enumerate(after.variables)}
    expected = []
    lower, upper = -(2**63), 2**63 - 1

    def add(terms, lo, hi, literals=()):
        expected.append((tuple(sorted(literals)), tuple(sorted(terms)), (lo, hi)))

    for triple in cuts.SELECTED:
        tid = u.triples.index(triple)
        six, seven = names[f"heavy6_{tid}"], names[f"heavy7_{tid}"]
        hubs = []
        for p in range(1, 17):
            if p in triple:
                continue
            h = names[f"selected_hub_{tid}_{p}"]
            hubs.append(h)
            terms = [(i, 1) for i, b in enumerate(u.blocks) if set((*triple, p)) <= set(b)]
            add([(h, 1), (six, -1)], lower, 0)
            add(terms, 2, upper, [h])
            add(terms, lower, 1, [six, -h - 1])
            add(terms, lower, 3, [six])
            add(terms, lower, 2, [seven])
        add([(h, 1) for h in hubs], lower, 1)
    for p in range(1, 17):
        heavy = [(names[f"heavy6_{i}"], 1) for i, t in enumerate(u.triples) if p in t]
        hubs = [(names[f"selected_hub_{u.triples.index(t)}_{p}"], 1)
                for t in cuts.SELECTED if p not in t]
        add(heavy + hubs, lower, 1)
    assert [row_signature(row) for row in all_rows] == expected
    del after.variables[len(before.variables):]
    del after.constraints[len(before.constraints):]
    assert after == before  # Includes the two allowed-assignment tables.


def test_auxiliary_hints_by_independent_subset_recount(base):
    u, _, blocks = base
    values = cuts.selected_hub_hint_values(u, blocks)
    assert len(values) == 52
    assert {name for name, value in values.items() if value} == {
        "selected_hub_0_4", "selected_hub_457_12", "selected_hub_480_15",
    }
    for t in cuts.SELECTED:
        for p in range(1, 17):
            if p in t:
                continue
            heavy = sum(set(t) <= set(b) for b in blocks) >= 6
            repeated = sum(set((*t, p)) <= set(b) for b in blocks) >= 2
            assert values[f"selected_hub_{u.triples.index(t)}_{p}"] == int(heavy and repeated)


def test_local_hub_truth_table_rejects_damaged_auxiliary_values(base):
    u, original, _ = base
    model = original.clone()
    first = len(model.proto.constraints)
    cuts.add_selected_hub_cuts(u, model,
                               [model.get_int_var_from_proto_index(i) for i in range(4368)])
    proto = protobuf(model)
    rows = proto.constraints[first:first + 5]
    names = {v.name: i for i, v in enumerate(proto.variables)}
    common = [i for i, b in enumerate(u.blocks) if {1, 2, 3, 4} <= set(b)]
    for q, six, seven, hub in product(range(13), (0, 1), (0, 1), (0, 1)):
        values = {i: int(i in common[:q]) for i in range(len(proto.variables))}
        values.update({names["heavy6_0"]: six, names["heavy7_0"]: seven,
                       names["selected_hub_0_4"]: hub})
        valid = True
        for row in rows:
            active = all(values[e] if e >= 0 else not values[-e - 1]
                         for e in row.enforcement_literal)
            if active:
                total = sum(values[v] * c for v, c in zip(row.linear.vars, row.linear.coeffs))
                domain = row.linear.domain
                valid &= any(domain[i] <= total <= domain[i + 1]
                             for i in range(0, len(domain), 2))
        expected = (hub == int(six and q >= 2)) and (not six or q <= 3) and (not seven or q <= 2)
        assert valid == expected


def test_damaged_base_and_selection_controls(base):
    u, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    with pytest.raises(ValueError, match="order"):
        cuts.add_selected_hub_cuts(u, model, [xs[1], xs[0], *xs[2:]])
    with pytest.raises(ValueError, match="duplicate selected"):
        cuts.add_selected_hub_cuts(u, model, xs, [(1, 2, 3), (1, 2, 3)])
    model.proto.variables[0].domain[1] = 2
    with pytest.raises(ValueError, match="Boolean"):
        cuts.add_selected_hub_cuts(u, model, xs)
    model = original.clone()
    # Weaken the exact-six forward implication; retaining only a name is insufficient.
    high = next(i for i, v in enumerate(model.proto.variables) if v.name == "heavy6_0")
    row = next(i for i, c in enumerate(model.proto.constraints)
               if list(c.enforcement_literal) == [high])
    model.proto.constraints[row].linear.domain[0] = 5
    with pytest.raises(ValueError, match="forward row"):
        cuts.add_selected_hub_cuts(u, model,
                                   [model.get_int_var_from_proto_index(i) for i in range(4368)])
