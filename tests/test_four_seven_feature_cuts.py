# Document:    Certified Heavy-Link Feature Cut Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      8fdb55064cfaf12e48c95bca7995e21e6dfdfb3232332a1c7618ccf8a4ccb94b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import sys
from itertools import combinations, permutations
from pathlib import Path

import pytest
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import four_seven_feature_cuts as cuts  # noqa: E402
from four_seven_double_cuts import add_double_triple_cuts  # noqa: E402
from four_seven_search import build_model  # noqa: E402

ARTIFACT = ROOT / "experiments/2026-10-03/four-seven-link-orbits/safe-linear-cuts.json"
PROOF = json.loads(ARTIFACT.read_text())


def protobuf(model):
    result = cp_model_pb2.CpModelProto()
    text_format.Parse(str(model.proto), result)
    return result


def graph(case):
    return {(0, 1), (1, 2), (2, 3), (0, 3)} if case == "cycle" else {(0, 1), (2, 3)}


def edge_sets(case):
    groups = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    hubs = [4, 8, 12, 16]
    adjacent_ah, adjacent_aa, nonadjacent_aa = set(), set(), set()
    for left, right in combinations(range(4), 2):
        aa = {tuple(sorted((a, b))) for a in groups[left] for b in groups[right]}
        if (left, right) in graph(case):
            adjacent_aa |= aa
            adjacent_ah |= {tuple(sorted((p, hubs[right]))) for p in groups[left]}
            adjacent_ah |= {tuple(sorted((p, hubs[left]))) for p in groups[right]}
        else:
            nonadjacent_aa |= aa
    own_ah = {(p, hubs[g]) for g in range(4) for p in groups[g]}
    return {"adjacent_anchor_hub": adjacent_ah, "adjacent_anchor_anchor": adjacent_aa,
            "nonadjacent_anchor_anchor": nonadjacent_aa,
            "hub_hub_or_own_anchor_hub": set(combinations(hubs, 2)) | own_ah}


def test_proof_coefficients_and_relabeling_are_exact():
    assert hashlib.sha256(ARTIFACT.read_bytes()).hexdigest() == cuts.PROOF_MANIFEST_SHA256
    assert PROOF["lp_results_sha256"] == cuts.LP_RESULTS_SHA256
    assert PROOF["lp_audit_sha256"] == cuts.LP_AUDIT_SHA256
    blocks = list(combinations(range(1, 17), 5))
    for rule in PROOF["rules"]:
        case, predicate = rule["case"], rule["predicate"]
        assert (predicate, rule["sense"], rule["bound"]) in cuts.RULES[case]
        autos = {perm for perm in permutations(range(4))
                 if {tuple(sorted((perm[a], perm[b]))) for a, b in graph(case)} == graph(case)}
        assert autos == {tuple(p) for p in rule["full_hub_graph_automorphisms"]}
        assert len(autos) == 8 and {p[0] for p in autos} == set(range(4))
        base_edges = {tuple(c["edge"]) for c in rule["target_groups"][0]["coefficients"]}
        for target in rule["target_groups"]:
            group, anchors = target["group_index"], set(target["anchor_triple"])
            assert anchors == set(range(4 * group + 1, 4 * group + 4))
            gp = tuple(target["base_to_target_group_permutation"])
            assert gp in autos and gp[0] == group
            points = target["base_to_target_point_permutation"]
            inverse = target["target_to_base_point_permutation"]
            assert sorted(points) == sorted(inverse) == list(range(1, 17))
            assert all(inverse[points[p - 1] - 1] == p for p in range(1, 17))
            assert all((points[p - 1] - 1) // 4 == gp[(p - 1) // 4] for p in range(1, 17))
            expected = {edge for edge in edge_sets(case)[predicate] if not anchors & set(edge)}
            actual = {tuple(c["edge"]) for c in target["coefficients"]}
            transported = {tuple(sorted(points[p - 1] for p in edge)) for edge in base_edges}
            assert actual == expected == transported
            assert len(actual) == len(target["coefficients"])
            for term in target["coefficients"]:
                block = tuple(sorted(anchors | set(term["edge"])))
                assert len(block) == 5 and term["coefficient"] == 1
                assert tuple(term["block"]) == blocks[term["variable_index"]] == block


@pytest.fixture(scope="module", params=["cycle", "matching"])
def base(request):
    universe, model, xs, _ = build_model(request.param)
    return request.param, universe, model, xs


@pytest.mark.parametrize("double_lift", [False, True])
def test_all_added_rows_and_preservation_of_prior_proto(base, double_lift):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    if double_lift:
        add_double_triple_cuts(universe, model, xs, case)
    model.add_hint(xs[0], 0)
    model.minimize(xs[0])
    before = protobuf(model)
    info = cuts.add_feature_cuts(universe, model, xs, case)
    after = protobuf(model)
    assert info["new_rows"] == (8 if case == "cycle" else 12)
    assert info["new_variables"] == 0
    expected = []
    for rule in PROOF["rules"]:
        if rule["case"] != case:
            continue
        for target in rule["target_groups"]:
            coefficients = tuple(sorted((c["variable_index"], c["coefficient"])
                                        for c in target["coefficients"]))
            domain = (-(2**63), rule["bound"]) if rule["sense"] == "<=" else (
                rule["bound"], 2**63 - 1)
            expected.append((coefficients, domain))
    actual = []
    for row, application in zip(after.constraints[len(before.constraints):], info["rows"],
                                strict=True):
        assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
        assert row.name == application["row_name"]
        actual.append((tuple(sorted(zip(row.linear.vars, row.linear.coeffs))),
                       tuple(row.linear.domain)))
        assert sorted(row.linear.vars) == application["variable_indices"]
    assert actual == expected
    del after.constraints[len(before.constraints):]
    assert after == before
    unchanged = protobuf(model)
    with pytest.raises(ValueError, match="already present"):
        cuts.add_feature_cuts(universe, model, xs, case)
    assert protobuf(model) == unchanged


def test_wrong_branch_and_missing_coverage_rejected_without_mutation(base):
    case, universe, original, _ = base
    model = original.clone()
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    before = protobuf(model)
    with pytest.raises(ValueError, match="pair target"):
        cuts.add_feature_cuts(universe, model, xs, "matching" if case == "cycle" else "cycle")
    assert protobuf(model) == before
    with pytest.raises(ValueError, match="order"):
        cuts.add_feature_cuts(universe, model, [xs[1], xs[0], *xs[2:]], case)
    assert protobuf(model) == before
    partial_universe, partial, partial_xs, _ = build_model(case, max_missing=1)
    before_partial = protobuf(partial)
    with pytest.raises(ValueError, match="coverage"):
        cuts.add_feature_cuts(partial_universe, partial, partial_xs, case)
    assert protobuf(partial) == before_partial
    for row in model.proto.constraints:
        if row.has_linear() and list(row.linear.domain) == [20, 20]:
            row.linear.domain[0] = 19
            break
    damaged = protobuf(model)
    with pytest.raises(ValueError, match="degree"):
        cuts.add_feature_cuts(universe, model, xs, case)
    assert protobuf(model) == damaged
