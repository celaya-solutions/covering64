#!/usr/bin/env python3
# Document:    Independent Fixed-g1 Whole-Link Certificate Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check exact signed row certificates and an audited finite partition; never solve."""

import copy
import gzip
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
PLAN = ROOT / "experiments/scratch/g1-next-route-plan-20261004"
SOURCE = DAY / "g1-whole-link-certificates"
BUNDLE = ROOT / "experiments/scratch/g1-whole-link-certificates-20261004/all-g1-cuts.json"

spec = importlib.util.spec_from_file_location(
    "independent_g1_certificate_basis", DAY / "g1-link-descent-independent/independent.py"
)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def read(path):
    return json.loads(Path(path).read_text())


def compressed(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def verify_cut(cut, rows, ordinary_support, heavy_support, global_ids, family_sha):
    assert cut["graph_index"] == 1 and cut["family_sha256"] == family_sha
    denominator = cut["denominator"]
    assert type(denominator) is int and denominator == cut["dual"]["denominator"] == 1000000
    source = cut["source_heavy_global_ids"]
    assert len(source) == len(set(source)) == 28 and source == sorted(source)
    assert all(type(index) is int and index in global_ids for index in source)
    weights, seen = [0] * len(rows), set()
    for row_index, weight in cut["dual"]["weights"]:
        assert type(row_index) is int and 0 <= row_index < len(rows) and row_index not in seen
        assert type(weight) is int and 0 < abs(weight) <= denominator
        assert weight > 0 or rows[row_index][3] != ind.INF
        seen.add(row_index)
        weights[row_index] = weight
    ordinary = [sum(weights[r] for r in support) for support in ordinary_support]
    heavy = [sum(weights[r] for r in support) for support in heavy_support]
    constant = sum(
        weight * (rows[r][2] if weight > 0 else rows[r][3])
        for r, weight in enumerate(weights)
        if weight
    )
    box = sum(max(0, coefficient) for coefficient in ordinary)
    lhs = sum(heavy[global_ids.index(index)] for index in source)
    assert cut["ordinary_coefficients"] == ordinary and cut["coefficients"] == heavy
    assert (cut["constant"], cut["ordinary_box_max"], cut["source_lhs"], cut["rhs"]) == (
        constant, box, lhs, constant - box
    )
    assert cut["maximum_signed_row_weight"] == max(map(abs, weights))
    assert cut["dual"]["rhs_numerator"] == constant - lhs
    assert cut["dual"]["box_max_numerator"] == box
    gap = Fraction(constant - box - lhs, denominator)
    assert gap > 0 and cut["dual"]["gap"] == [gap.numerator, gap.denominator]
    assert cut["dual"]["proves_infeasible"] is True
    return gap


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    extraction = read(SOURCE / "result.json")
    for path, expected in extraction["input_files"].items():
        assert ind.sha(ROOT / path) == expected
    assert extraction["bundle_sha256"] == ind.sha(BUNDLE)
    assert extraction["source_sha256"] == ind.sha(SOURCE / "extract.py")
    bundle, old = read(BUNDLE), read(PLAN / "g1-cuts.json")
    screen_path = DAY / "g1-larger-independent/audit.json"
    screen = read(screen_path)
    assert screen["passed"] and screen["conditional_bundle_sha256"] == ind.sha(
        PLAN / "g1-cuts.json"
    )
    assert screen["envelope_results_sha256"] == ind.sha(PLAN / "envelope-results.json")
    assert bundle["prior_bundle_sha256"] == ind.sha(PLAN / "g1-cuts.json")
    assert bundle["source_sha256"] == extraction["source_sha256"]
    assert (bundle["count"], bundle["prior_count"], bundle["new_count"]) == (1000, 243, 757)
    assert bundle["graph_index"] == old["graph_index"] == extraction["graph_index"] == 1
    assert bundle["hub_excesses"] == [0, 1, 1, 1, 1, 0]
    assert bundle["six_row_changes"] == old["six_row_changes"]
    assert bundle["cuts"][:243] == old["cuts"]
    assert len(bundle["cuts"]) == len({c["id"] for c in bundle["cuts"]}) == 1000
    assert len({tuple(c["source_heavy_global_ids"]) for c in bundle["cuts"]}) == 1000
    blocks, _, ordinary, heavy, rows = ind.basis()
    global_ids = [blocks.index(block) for block in heavy]
    assert bundle["heavy_global_ids"] == global_ids
    assert bundle["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    ordinary_support = [[r for r, row in enumerate(rows) if i in row[0]] for i in range(1200)]
    heavy_support = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(276)]
    family_sha = bundle["family_sha256"]
    assert family_sha == old["family_sha256"] == extraction["family_sha256"]
    checked = []
    for cut in bundle["cuts"]:
        gap = verify_cut(cut, rows, ordinary_support, heavy_support, global_ids, family_sha)
        checked.append({"id": cut["id"], "gap": [gap.numerator, gap.denominator]})
    controls = []
    for label in (
        "duplicate_weight_row", "damaged_heavy_coefficient", "oversized_weight", "duplicate_block"
    ):
        damaged = copy.deepcopy(bundle["cuts"][-1])
        if label == "duplicate_weight_row":
            damaged["dual"]["weights"].append(damaged["dual"]["weights"][0])
        elif label == "damaged_heavy_coefficient":
            damaged["coefficients"][0] += 1
        elif label == "oversized_weight":
            damaged["dual"]["weights"][0][1] = 1000001
        else:
            damaged["source_heavy_global_ids"][1] = damaged["source_heavy_global_ids"][0]
        try:
            verify_cut(damaged, rows, ordinary_support, heavy_support, global_ids, family_sha)
        except AssertionError:
            controls.append(label)
        else:
            raise AssertionError(f"Control accepted: {label}")

    pool_path = DAY / "g1-whole-link-pool/result.json"
    pool = read(pool_path)
    post_path = DAY / "g1-whole-link-pool-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"] and post["result_sha256"] == ind.sha(pool_path)
    assert bundle["new_source_result_sha256"] == ind.sha(pool_path)
    assert pool["complete_pool"] and len(pool["records"]) == 757
    records = {record["rank"]: record for record in pool["records"]}
    assert set(records) == set(range(757))
    source_states = set()
    for cut in bundle["cuts"][243:]:
        rank = int(cut["id"].removeprefix("g1-whole-link-rank"))
        record = records.pop(rank)
        source = cut["source_heavy_global_ids"]
        chosen = [blocks[index] for index in source]
        assert source == record["heavy_global_ids"]
        assert ind.digest(chosen) == cut["source_heavy_sha256"] == record["heavy_sha256"]
        assert ind.digest(ind.shifted(rows, heavy, chosen)) == cut["source_shifted_rows_sha256"]
        assert cut["source_shifted_rows_sha256"] == record["shifted_rows_sha256"]
        assert record["family_sha256"] == family_sha
        assert cut["source_objective"] == record["objective"]
        assert cut["numerical_dual_path"] == record["dual_path"]
        assert ind.sha(ROOT / record["dual_path"]) == cut["numerical_dual_sha256"]
        assert cut["numerical_dual_sha256"] == record["dual_sha256"]
        source_states.add(tuple(source))
    assert not records and len(source_states) == 757

    enumeration_path = DAY / "g1-larger-independent/enumeration.json"
    enumeration = read(enumeration_path)
    assert enumeration["passed"] and screen["enumeration_sha256"] == ind.sha(enumeration_path)
    archive = ROOT / "experiments/scratch/g1-larger-independent-20261004/states.npz"
    assert ind.sha(archive) == enumeration["states_archive_sha256"]
    local = np.load(archive)["whole_link"]
    states = compressed(PLAN / "whole-link.json.gz")
    assert np.array_equal(np.asarray(global_ids)[local], np.asarray(states))
    prior = screen["neighborhoods"]["whole-link"]
    assert ind.sha(PLAN / "whole-link.json.gz") == prior["states_sha256"]
    assert ind.sha(PLAN / "whole-link-envelopes.json.gz") == prior["scores_sha256"]
    scores = compressed(PLAN / "whole-link-envelopes.json.gz")
    assert len(states) == len(scores) == len({tuple(s) for s in states}) == 100076
    positive, zero = set(), set()
    for state, (g1, broad, combined) in zip(states, scores, strict=True):
        assert all(type(value) is int and value >= 0 for value in (g1, broad, combined))
        assert combined == max(g1, broad)
        (positive if combined > 0 else zero).add(tuple(state))
    assert len(positive) == prior["combined_positive"] == 99319
    assert len(zero) == prior["unexcluded"] == 757
    unexcluded = set(map(tuple, compressed(PLAN / "whole-link-unexcluded.json.gz")))
    assert zero == source_states == unexcluded
    assert ind.sha(PLAN / "whole-link-unexcluded.json.gz") == screen["whole_link_pool_sha256"]
    assert positive.isdisjoint(source_states) and len(positive | source_states) == 100076
    minimum = min(checked[243:], key=lambda item: Fraction(*item["gap"]))
    assert minimum["gap"] == extraction["minimum_new_source_gap"] == [165832, 15625]
    assert minimum["id"] == extraction["minimum_new_source_gap_id"]
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": ind.sha(__file__),
        "independent_basis_sha256": ind.sha(DAY / "g1-link-descent-independent/independent.py"),
        "extraction_result_sha256": ind.sha(SOURCE / "result.json"),
        "bundle_path": str(BUNDLE.relative_to(ROOT)),
        "bundle_sha256": ind.sha(BUNDLE),
        "family_sha256": family_sha,
        "graph_index": 1,
        "replayed_graph_specific_planes": 1000,
        "prior_planes": 243,
        "new_positive_certificates": 757,
        "broad_planes_kept_separate": 353,
        "prior_screen_audit_sha256": ind.sha(screen_path),
        "pool_postcheck_sha256": ind.sha(post_path),
        "enumeration_sha256": ind.sha(enumeration_path),
        "finite_whole_link_states": 100076,
        "prior_positive_envelope_states": 99319,
        "new_positive_source_states": 757,
        "finite_whole_link_excluded": True,
        "minimum_new_source_gap": minimum,
        "negative_controls_rejected": controls,
        "certificates": checked,
        "scope": "Exact arithmetic excludes only all 100076 registry-safe fixed-g1 whole-link "
        "states in the independently enumerated neighborhood of the saved incumbent. "
        "The prior 99319 positive states use the hash-bound earlier exact screen. "
        "No whole-family exclusion, elastic local optimum, or unrestricted covering bound.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    summary = {key: value for key, value in report.items() if key != "certificates"}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
