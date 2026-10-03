# Document:    Independent Weighted Tree Replay and Damage Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5f5cea1ca279f44c8fce2dcfc91b5737deb5699c49e6d39ee54b29cf9518ef83
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRODUCER = load_script("independent_core_six")
CHECKER = load_script("check_independent_weighted_trees")
INPUT = ROOT / "experiments/2026-10-03/core-six-scan/dual-reduced-candidates.json.gz"
PROOF = ROOT / "experiments/2026-10-03/core-six-independent/weighted-trees.json.gz"


def sample():
    data = json.loads(gzip.decompress(INPUT.read_bytes()))
    proof = json.loads(gzip.decompress(PROOF.read_bytes()))
    data["candidates"] = data["candidates"][:1]
    proof["body"]["results"] = proof["body"]["results"][:1]
    return data, proof


def resign(data, proof):
    # Deliberately repair hashes so semantic damage cannot be rejected by hash alone.
    raw = PRODUCER.canonical(data)
    body = proof["body"]
    body["input_sha256"] = hashlib.sha256(raw).hexdigest()
    body["input_json_sha256"] = CHECKER.sha(data)
    for case, result in zip(data["candidates"], body["results"]):
        result["input_case_sha256"] = CHECKER.sha(case)
        result["trace_sha256"] = CHECKER.sha(result["trace"])
        result["capacities_sha256"] = CHECKER.sha(result["all_4368_capacity_numerators"])
    proof["document_header"]["SHA256"] = CHECKER.sha(body)
    return body["input_sha256"]


def test_all_33_complete_certificates_replay():
    raw = INPUT.read_bytes()
    data = json.loads(gzip.decompress(raw))
    proof = json.loads(gzip.decompress(PROOF.read_bytes()))
    result = CHECKER.verify(data, proof, hashlib.sha256(raw).hexdigest())
    assert result["cases"] == 33
    assert result["nodes"] == 133


@pytest.mark.parametrize("damage, expected", [
    ("duplicate_retained", "duplicate"),
    ("malformed_block", "retained blocks"),
    ("duplicate_weight", "duplicate"),
    ("omitted_branch", "omitted or extra branch"),
    ("omitted_child", "omitted child"),
    ("false_capacity", "saved capacities"),
    ("false_loss", "loss mismatch"),
    ("false_coverage", "uncovered mismatch"),
])
def test_semantic_damage_is_rejected_even_with_repaired_hashes(damage, expected):
    data, proof = sample()
    case = data["candidates"][0]
    result = proof["body"]["results"][0]
    root = result["trace"][0]
    if damage == "duplicate_retained":
        case["retained_block_ids"][1] = case["retained_block_ids"][0]
    elif damage == "malformed_block":
        case["retained_core_blocks"][0][-1] = 17
    elif damage == "duplicate_weight":
        case["weights"].append(copy.deepcopy(case["weights"][0]))
    elif damage == "omitted_branch":
        root["eligible_block_ids"].pop()
    elif damage == "omitted_child":
        root["children"].pop()
    elif damage == "false_capacity":
        result["all_4368_capacity_numerators"][0] += 1
    elif damage == "false_loss":
        root["loss_numerator"] += 1
    elif damage == "false_coverage":
        root["uncovered_mask_hex"] = "0x1"
    input_hash = resign(data, proof)
    with pytest.raises(ValueError, match=expected):
        CHECKER.verify(data, proof, input_hash)


def test_node_budget_yields_unknown_and_no_negative_certificate():
    data, proof = sample()
    _, blocks, triples_by_block, masks = PRODUCER.universe()
    case = data["candidates"][0]
    audit = PRODUCER.audit_case(case, 10, blocks, triples_by_block, masks)
    result = PRODUCER.enumerate_case(0, case, audit, 10, masks, blocks, 1, 5.0)
    assert result["status"] == "UNKNOWN"
    assert result["node_count"] == 1
    proof["body"]["results"][0] = result
    input_hash = resign(data, proof)
    with pytest.raises(ValueError, match="not a complete negative tree"):
        CHECKER.verify(data, proof, input_hash)


def test_producer_rejects_incomplete_pool():
    data, _ = sample()
    case = data["candidates"][0]
    case["allowed_block_ids"].pop()
    _, blocks, triples_by_block, masks = PRODUCER.universe()
    with pytest.raises(ValueError, match="incomplete or wrong reduced pool"):
        PRODUCER.audit_case(case, 10, blocks, triples_by_block, masks)
