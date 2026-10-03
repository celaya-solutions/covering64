# Document:    Independent Hub Classification and Proof Damage Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      70d71c4a07d013881bb5ad80dd961cb88d4bc7b92547fb5a3229b07ab4a5724c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import gzip
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDIT = load("audit_link_hub_shapes")
ENUMERATE = load("enumerate_link_hubs_independent")
REPLAY = load("check_link_hub_trees")


@lru_cache(maxsize=1)
def fixture():
    path = ROOT / "experiments/2026-10-03/link-hub-independent/audit-fixture.json.gz"
    return json.loads(gzip.decompress(path.read_bytes()))["body"]


@lru_cache(maxsize=1)
def independent_classes():
    return AUDIT.enumerate_classes()


def test_complete_independent_classification_and_all_cp_witnesses():
    classes, counts, labeled = independent_classes()
    assert labeled == 1335
    assert len(counts) == 8
    assert len(classes) == 206
    data = fixture()
    result = AUDIT.audit(data["metadata"], data["results"], classes)
    assert result["shape_count"] == 206
    assert result["witness_count"] == 4
    checked = 0
    for links in data["cp_solutions"].values():
        for link in links:
            AUDIT.check_link(link)
            checked += 1
    assert checked == 114


def test_loop_uses_two_degrees_and_cross_edge_uses_one_each():
    loop = list(AUDIT.multigraph_matrices([2, 0, 0, 0, 0, 0]))
    cross = list(AUDIT.multigraph_matrices([1, 1, 0, 0, 0, 0]))
    assert len(loop) == len(cross) == 1
    assert sum(loop[0]) == sum(cross[0]) == 1
    assert loop[0][AUDIT.MULTIEDGE_RANK[(0, 0)]] == 1
    assert cross[0][AUDIT.MULTIEDGE_RANK[(0, 1)]] == 1


@pytest.mark.parametrize("damage, expected", [
    ("missing_class", "missing or extra"),
    ("duplicate_class", "duplicate colored"),
    ("parallel_a", "parallel A"),
    ("bad_b_degree", "degree must be three"),
    ("bad_hub_label", "bad label"),
    ("bad_candidate_count", "residual candidate count"),
    ("duplicate_link", "duplicate block"),
])
def test_shape_and_link_damage_rejected(damage, expected):
    data = copy.deepcopy(fixture())
    metadata = data["metadata"]
    shapes = metadata["shapes"]
    results = data["results"]
    if damage == "missing_class":
        shapes.pop()
        metadata["shape_count"] -= 1
    elif damage == "duplicate_class":
        shapes[-1] = copy.deepcopy(shapes[0])
    elif damage == "parallel_a":
        shapes[0]["a_edges"][1] = shapes[0]["a_edges"][0].copy()
    elif damage == "bad_b_degree":
        shapes[0]["b_edges"][0] = [0, 0]
    elif damage == "bad_hub_label":
        shapes[0]["hub_blocks"][0][-1] = 17
    elif damage == "bad_candidate_count":
        results[0]["residual_candidate_count"] += 1
    elif damage == "duplicate_link":
        positive = next(r for r in results if r["link"])
        positive["link"][1] = positive["link"][0].copy()
    with pytest.raises(ValueError, match=expected):
        AUDIT.audit(metadata, results, independent_classes()[0])


def resign(case):
    case["body"]["trace_sha256"] = REPLAY.digest(case["body"]["trace"])
    case["document_header"]["SHA256"] = REPLAY.digest(case["body"])


def test_positive_and_negative_full_tree_replay():
    data = fixture()
    for index, expected_solutions in [(0, 0), (1, 12)]:
        result = REPLAY.replay(data["tree_cases"][str(index)],
                               data["metadata"]["shapes"][index]["hub_blocks"])
        assert result["unique_solutions"] == expected_solutions


@pytest.mark.parametrize("damage, expected", [
    ("omitted_branch", "omitted or extra branch"),
    ("omitted_child", "omitted child"),
    ("bad_demand", "state demand mismatch"),
    ("bad_candidate_pool", "candidate completeness"),
    ("missing_forced_row", "omitted forced carrier"),
    ("false_solution", "incomplete solution"),
    ("false_solution_count", "unique solution count"),
])
def test_semantic_tree_damage_rejected_after_hashes_repaired(damage, expected):
    case = copy.deepcopy(fixture()["tree_cases"]["0"])
    body = case["body"]
    trace = body["trace"]
    if damage == "omitted_branch":
        next(n for n in trace if n["status"] == "EXHAUSTED")["branches"].pop()
    elif damage == "omitted_child":
        next(n for n in trace if n["status"] == "EXHAUSTED")["children"].pop()
    elif damage == "bad_demand":
        trace[0]["demands_hex"] = "0x0"
    elif damage == "bad_candidate_pool":
        body["quad_candidates"].pop()
    elif damage == "missing_forced_row":
        next(n for n in trace if n["status"] == "FORCED")["forced_rows"].pop()
    elif damage == "false_solution":
        trace[0]["status"] = "SOLUTION"
    elif damage == "false_solution_count":
        body["unique_solutions"] = 1
    resign(case)
    hub = fixture()["metadata"]["shapes"][0]["hub_blocks"]
    with pytest.raises(ValueError, match=expected):
        REPLAY.replay(case, hub)


def test_budget_exhaustion_is_unknown():
    hub = fixture()["metadata"]["shapes"][0]["hub_blocks"]
    result = ENUMERATE.enumerate_hub(hub, 1, 5.0)
    assert result["status"] == "UNKNOWN"
    assert result["nodes"] == 1


def test_independent_positive_enumeration_matches_exact_solution_set():
    data = fixture()
    hub = data["metadata"]["shapes"][1]["hub_blocks"]
    result = ENUMERATE.enumerate_hub(hub, 250_000, 5.0)
    assert result["status"] == "COMPLETE"
    def canonical(links):
        return {tuple(sorted(tuple(b) for b in link)) for link in links}
    assert canonical(result["links"]) == canonical(data["cp_solutions"]["1"])
