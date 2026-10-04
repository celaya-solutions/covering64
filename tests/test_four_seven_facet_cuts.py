# Document:    Signed Facet Row and Model Preservation Tests
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2b5e3b7067bd89a06529955ed2760ea60621ed11835be1fac0775357b0b97d78
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

import pytest
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import four_seven_facet_cuts as cuts  # noqa: E402
from four_seven_double_cuts import add_double_triple_cuts  # noqa: E402
from four_seven_feature_cuts import add_feature_cuts  # noqa: E402
from four_seven_search import build_model  # noqa: E402

ARTIFACT = ROOT / "experiments/2026-10-03/four-seven-link-orbits/safe-feature-facets.json"
PROOF = json.loads(ARTIFACT.read_text())


def protobuf(model):
    result = cp_model_pb2.CpModelProto()
    text_format.Parse(str(model.proto), result)
    return result


def new_facets(case):
    data = next(c for c in PROOF["cases"] if c["case"] == case)
    return [
        f
        for f in data["all_facets"]
        if f["excludes_certified_orbits"] and not f["already_in_five_rules"]
    ]


def test_all_signed_coefficients_match_proof_and_independent_edge_sets():
    assert hashlib.sha256(ARTIFACT.read_bytes()).hexdigest() == cuts.PROOF_MANIFEST_SHA256
    assert PROOF["source_sha256"] == cuts.PROOF_DERIVATION_SHA256
    assert PROOF["screen_sha256"] == cuts.LP_RESULTS_SHA256
    assert PROOF["audit_sha256"] == cuts.LP_AUDIT_SHA256
    groups = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    hubs = [4, 8, 12, 16]
    blocks = list(combinations(range(1, 17), 5))
    hh = set(combinations(hubs, 2))
    own = {(p, hubs[g]) for g in range(4) for p in groups[g]}
    for case in ("cycle", "matching"):
        adjacent = {(0, 1), (1, 2), (2, 3), (0, 3)} if case == "cycle" else {(0, 1), (2, 3)}
        ah, aa = set(), set()
        for g, h in adjacent:
            ah |= {tuple(sorted((p, hubs[h]))) for p in groups[g]}
            ah |= {tuple(sorted((p, hubs[g]))) for p in groups[h]}
            aa |= {tuple(sorted((a, b))) for a in groups[g] for b in groups[h]}
        facets = new_facets(case)
        assert len(facets) == (4 if case == "cycle" else 9)
        assert tuple((tuple(f["normal"]), f["upper_bound"]) for f in facets) == cuts.FACETS[case]
        for facet in facets:
            for target in facet["target_groups"]:
                anchors = set(target["anchor_triple"])
                assert anchors == groups[target["group_index"]]
                expected = {}
                for edge in combinations([p for p in range(1, 17) if p not in anchors], 2):
                    coefficient = sum(
                        n * (edge in subset)
                        for n, subset in zip(facet["normal"], (hh, own, ah, aa), strict=True)
                    )
                    if coefficient:
                        expected[edge] = coefficient
                actual = {tuple(c["edge"]): c["coefficient"] for c in target["coefficients"]}
                assert actual == expected
                assert all(c["coefficient"] != 0 for c in target["coefficients"])
                for term in target["coefficients"]:
                    block = tuple(sorted(anchors | set(term["edge"])))
                    assert blocks[term["variable_index"]] == tuple(term["block"]) == block


@pytest.fixture(scope="module", params=["cycle", "matching"])
def base(request):
    universe, model, xs, _ = build_model(request.param)
    return request.param, universe, model, xs


@pytest.mark.parametrize(
    "double_lift,first_features", [(False, False), (True, False), (False, True), (True, True)]
)
def test_every_row_and_prior_proto_preserved(base, double_lift, first_features):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    if double_lift:
        add_double_triple_cuts(universe, model, xs, case)
    if first_features:
        add_feature_cuts(universe, model, xs, case)
    model.add_hint(xs[0], 0)
    model.minimize(xs[0])
    before = protobuf(model)
    info = cuts.add_facet_cuts(universe, model, xs, case)
    after = protobuf(model)
    assert info["new_rows"] == (16 if case == "cycle" else 36)
    assert info["new_variables"] == 0
    expected = [
        (
            tuple(sorted((c["variable_index"], c["coefficient"]) for c in target["coefficients"])),
            (-(2**63), facet["upper_bound"]),
        )
        for facet in new_facets(case)
        for target in facet["target_groups"]
    ]
    actual = []
    for row, applied in zip(
        after.constraints[len(before.constraints) :], info["rows"], strict=True
    ):
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert row.name == applied["row_name"]
        terms = tuple(sorted(zip(row.linear.vars, row.linear.coeffs, strict=True)))
        actual.append((terms, tuple(row.linear.domain)))
        assert terms == tuple(
            (c["variable_index"], c["coefficient"]) for c in applied["coefficients"]
        )
    assert actual == expected
    del after.constraints[len(before.constraints) :]
    assert after == before
    unchanged = protobuf(model)
    with pytest.raises(ValueError, match="already present"):
        cuts.add_facet_cuts(universe, model, xs, case)
    assert protobuf(model) == unchanged


def test_invalid_inputs_leave_model_unchanged(base):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    before = protobuf(model)
    for wrong, message in [
        ("other", "unknown"),
        ("matching" if case == "cycle" else "cycle", "pair target"),
    ]:
        with pytest.raises(ValueError, match=message):
            cuts.add_facet_cuts(universe, model, xs, wrong)
        assert protobuf(model) == before
    with pytest.raises(ValueError, match="order"):
        cuts.add_facet_cuts(universe, model, [xs[1], xs[0], *xs[2:]], case)
    assert protobuf(model) == before
    partial_universe, partial, partial_xs, _ = build_model(case, max_missing=1)
    partial_before = protobuf(partial)
    with pytest.raises(ValueError, match="coverage"):
        cuts.add_facet_cuts(partial_universe, partial, partial_xs, case)
    assert protobuf(partial) == partial_before
    for row in model.proto.constraints:
        if row.has_linear() and list(row.linear.domain) == [20, 20]:
            row.linear.domain[0] = 19
            break
    damaged = protobuf(model)
    with pytest.raises(ValueError, match="degree"):
        cuts.add_facet_cuts(universe, model, xs, case)
    assert protobuf(model) == damaged
