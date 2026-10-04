# Document:    Independent Fixed-g5 Larger-Neighborhood Exact Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay exact signed-row planes and compare an independent finite enumeration."""

import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "g5-larger-screen"
ARCHIVE = ROOT / "experiments/scratch/g5-larger-screen-20261004"
RAW = ROOT / "experiments/scratch/g5-larger-independent-20261004"
spec = importlib.util.spec_from_file_location(
    "independent_g5_screen", DAY / "g5-link-descent-independent/independent.py"
)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def read(path):
    return json.loads(Path(path).read_text())


def compressed(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def check_cut(cut, rows, support_o, support_h, gids, family_sha):
    assert cut["graph_index"] == 5 and cut["family_sha256"] == family_sha
    denominator = cut["denominator"]
    assert type(denominator) is int and denominator == cut["dual"]["denominator"] == 1000000
    selected = cut["source_heavy_global_ids"]
    assert selected == sorted(set(selected)) and len(selected) == 28
    assert all(type(index) is int and index in gids for index in selected)
    weights, seen = [0] * 697, set()
    for row_index, weight in cut["dual"]["weights"]:
        assert type(row_index) is int and 0 <= row_index < 697 and row_index not in seen
        assert type(weight) is int and 0 < abs(weight) <= denominator
        assert weight > 0 or rows[row_index][3] != ind.INF
        seen.add(row_index)
        weights[row_index] = weight
    ordinary = [sum(weights[r] for r in support) for support in support_o]
    heavy = [sum(weights[r] for r in support) for support in support_h]
    constant = sum(w * (rows[r][2] if w > 0 else rows[r][3])
                   for r, w in enumerate(weights) if w)
    box = sum(max(0, value) for value in ordinary)
    lhs = sum(heavy[gids.index(index)] for index in selected)
    assert cut["ordinary_coefficients"] == ordinary and cut["coefficients"] == heavy
    assert (cut["constant"], cut["ordinary_box_max"], cut["source_lhs"], cut["rhs"]) == (
        constant, box, lhs, constant - box
    )
    assert cut["maximum_signed_row_weight"] == max(map(abs, weights))
    assert cut["dual"]["rhs_numerator"] == constant - lhs
    assert cut["dual"]["box_max_numerator"] == box
    gap = Fraction(constant - box - lhs, denominator)
    assert gap > 0 and cut["dual"]["proves_infeasible"]
    assert cut["dual"]["gap"] == [gap.numerator, gap.denominator]
    return ordinary, heavy, gap


def main():
    assert not (HERE / "audit.json").exists()
    files = read(SOURCE / "files.json")
    for name, expected in files.items():
        assert ind.sha(SOURCE / name) == expected
    for path, expected in read(SOURCE / "inputs.json").items():
        assert ind.sha(ROOT / path) == expected
    archive = read(SOURCE / "archive.json")
    for item in archive["moved"]:
        assert ind.sha(ROOT / item["archived_path"]) == item["sha256"]
    compact_path = SOURCE / "g5-cuts.compact.json.gz"
    assert ind.sha(compact_path) == archive["compact_sha256"]
    compact = compressed(compact_path)
    assert compact["format"] == "g5-signed-row-compact-v1"
    bundle = read(ARCHIVE / "g5-cuts.json")
    assert ind.sha(ARCHIVE / "g5-cuts.json") == archive["original_sha256"]
    assert bundle == compressed(ARCHIVE / "g5-cuts.json.gz")
    envelope, counts = read(SOURCE / "envelope-results.json"), read(SOURCE / "counts.json")
    assert envelope["source_sha256"] == ind.sha(SOURCE / "envelopes.py")
    assert counts["source_sha256"] == ind.sha(SOURCE / "count.py")
    assert envelope["bundle_sha256"] == ind.sha(ARCHIVE / "g5-cuts.json.gz")
    blocks, _, ordinary, heavy, rows = ind.basis()
    gids = [blocks.index(block) for block in heavy]
    family_sha = ind.digest({
        "rows": rows, "ordinary_global_ids": [blocks.index(b) for b in ordinary], "graph_index": 5
    })
    assert bundle["family_sha256"] == family_sha
    assert bundle["graph_index"] == envelope["graph_index"] == counts["graph_index"] == 5
    assert bundle["hub_excesses"] == counts["hub_excesses"] == [2, 0, 0, 0, 0, 2]
    assert bundle["heavy_global_ids"] == gids
    assert bundle["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    assert json.loads(json.dumps(rows)) == compressed(SOURCE / "g5-unconditional-rows.json.gz")
    assert compact["unconditional_rows"] == json.loads(json.dumps(rows))
    source_path = DAY / "g5-link-continuation/result.json"
    result = read(source_path)
    post_path = DAY / "g5-link-continuation-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"] and post["result_sha256"] == ind.sha(source_path)
    assert bundle["descent_result_sha256"] == counts["descent_result_sha256"]
    assert counts["descent_result_sha256"] == ind.sha(source_path)
    cache_path = ROOT / "experiments/scratch/g5-link-continuation-20261004/final-cache.json"
    assert ind.sha(cache_path) == bundle["cache_sha256"] == result["raw_sha256"]["final-cache.json"]
    cache = read(cache_path)
    assert len(cache) == bundle["count"] == len(bundle["cuts"]) == 720
    support_o = [[r for r, row in enumerate(rows) if i in row[0]] for i in range(1200)]
    support_h = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(276)]
    checked, observed = [], set()
    for cut, compact_cut in zip(bundle["cuts"], compact["bundle"]["cuts"], strict=True):
        key = cut["id"].removeprefix("g5-cache-")
        assert key in cache and key not in observed
        observed.add(key)
        record = cache[key]
        assert cut["source_heavy_global_ids"] == record["heavy_global_ids"]
        chosen = tuple(blocks[i] for i in record["heavy_global_ids"])
        assert ind.digest(chosen) == record["heavy_sha256"] == cut["source_heavy_sha256"]
        shifted_sha = ind.digest(ind.shifted(rows, heavy, chosen))
        assert shifted_sha == record["shifted_rows_sha256"] == cut["source_shifted_rows_sha256"]
        assert cut["numerical_dual_path"] == record["dual_path"]
        assert cut["numerical_dual_sha256"] == record["dual_sha256"]
        assert ind.sha(ROOT / record["dual_path"]) == cut["numerical_dual_sha256"]
        assert cut["source_objective"] == record["objective"] and record["status"] == "OPTIMAL"
        oc, hc, gap = check_cut(cut, rows, support_o, support_h, gids, family_sha)
        assert compact_cut["ordinary_coefficients"] == "derived-from-signed-rows"
        assert compact_cut["coefficients"] == "derived-from-signed-rows"
        compact_cut["ordinary_coefficients"], compact_cut["coefficients"] = oc, hc
        assert compact_cut == cut
        checked.append({"id": cut["id"], "gap": [gap.numerator, gap.denominator]})
    assert observed == set(cache) and compact["bundle"] == bundle
    restored = (json.dumps(compact["bundle"], indent=2) + "\n").encode()
    assert hashlib.sha256(restored).hexdigest() == compact["original_sha256"] == archive[
        "original_sha256"
    ]
    assert len(restored) == compact["original_bytes"] == archive["original_bytes"]
    broad = compressed(ARCHIVE / "broad-cuts-reference.json.gz")["cuts"]
    assert envelope["broad_reference_sha256"] == ind.sha(ARCHIVE / "broad-cuts-reference.json.gz")
    old_plan = ROOT / "experiments/scratch/g1-next-route-plan-20261004"
    old_audit = read(DAY / "g1-larger-independent/audit.json")
    old_envelope = read(old_plan / "envelope-results.json")
    assert old_audit["passed"] and old_audit["envelope_results_sha256"] == ind.sha(
        old_plan / "envelope-results.json"
    )
    assert old_envelope["broad_reference_sha256"] == ind.sha(old_plan / "broad-cuts-reference.json")
    old_broad = read(old_plan / "broad-cuts-reference.json")["cuts"]
    assert len(broad) == len(old_broad) == 353
    for current, previous in zip(broad, old_broad, strict=True):
        assert all(current[field] == previous[field]
                   for field in ("coefficients", "rhs", "denominator"))

    def matrix(cuts):
        coefficients, rhs = [], []
        for cut in cuts:
            assert 1000000 % cut["denominator"] == 0
            factor = 1000000 // cut["denominator"]
            row = [value * factor for value in cut["coefficients"]]
            bound = cut["rhs"] * factor
            assert abs(bound) + sum(map(abs, row)) < 2**60
            coefficients.append(row)
            rhs.append(bound)
        return np.asarray(coefficients, dtype=np.int64), np.asarray(rhs, dtype=np.int64)

    cm, cr = matrix(bundle["cuts"])
    bm, br = matrix(broad)
    enumeration = read(HERE / "enumeration.json")
    assert enumeration["passed"] and enumeration["source_result_sha256"] == ind.sha(source_path)
    assert enumeration["states_archive_sha256"] == ind.sha(RAW / "states.npz")
    arrays = np.load(RAW / "states.npz")
    cached = {tuple(record["heavy_global_ids"]) for record in cache.values()}
    baseline = set(result["best_heavy_global_ids"])
    reports = {}
    for name, expected_count, expected_zero in (("proper-three", 492, 0),
                                                ("paired-two", 4106, 0),
                                                ("whole-link", 46436, 3496)):
        own_name = name.replace("-", "_")
        local = arrays[own_name]
        states = compressed(SOURCE / f"{name}.json.gz")
        assert np.array_equal(np.asarray(gids)[local], np.asarray(states))
        assert len(states) == len({tuple(state) for state in states}) == expected_count
        scores = []
        for offset in range(0, len(local), 128):
            group = local[offset:offset + 128]
            c = np.maximum(0, (cr[:, None] - cm[:, group].sum(axis=2)).max(axis=0))
            b = np.maximum(0, (br[:, None] - bm[:, group].sum(axis=2)).max(axis=0))
            scores.extend([int(x), int(y), int(max(x, y))] for x, y in zip(c, b, strict=True))
        assert scores == compressed(SOURCE / f"{name}-envelopes.json.gz")
        unexcluded = [state for state, score in zip(states, scores, strict=True) if score[2] == 0]
        assert unexcluded == compressed(SOURCE / f"{name}-unexcluded.json.gz")
        assert len(unexcluded) == expected_zero
        own = {
            "registry_safe_states": len(states), "g5_positive": sum(s[0] > 0 for s in scores),
            "g5_unexcluded": sum(s[0] == 0 for s in scores),
            "broad_positive": sum(s[1] > 0 for s in scores),
            "combined_positive": sum(s[2] > 0 for s in scores),
            "combined_unexcluded": len(unexcluded),
            "combined_unexcluded_uncached": sum(tuple(s) not in cached for s in unexcluded),
            "g5_minimum_lower_bound": [min(s[0] for s in scores), 1000000],
            "combined_minimum_lower_bound": [min(s[2] for s in scores), 1000000],
            "states_sha256": ind.sha(SOURCE / f"{name}.json.gz"),
            "scores_sha256": ind.sha(SOURCE / f"{name}-envelopes.json.gz"),
        }
        saved = envelope["neighborhoods"][name]
        assert all(saved[key] == value for key, value in own.items())
        indices = sorted(
            range(len(states)), key=lambda i: (scores[i][2], scores[i][0], states[i])
        )[:20]
        best_twenty = [
            {"heavy_global_ids": states[i], "g5_bound_numerator": scores[i][0],
             "broad_bound_numerator": scores[i][1], "combined_bound_numerator": scores[i][2],
             "cached": tuple(states[i]) in cached} for i in indices
        ]
        assert best_twenty == saved["best_twenty"]
        count_saved = counts[own_name]
        assert count_saved["accepted_sha256"] == ind.digest(states)
        if own_name != "whole_link":
            assert count_saved["structurally_valid"] == enumeration["neighborhoods"][own_name][
                "passes_triple_cap"
            ]
            assert count_saved["registry_accepted"] == len(states)
            assert count_saved["cached"] == sum(tuple(state) in cached for state in states)
        else:
            assert count_saved["accepted"] == len(states)
            assert count_saved["cached"] == sum(tuple(state) in cached for state in states) == 128
            distances = Counter(28 - len(baseline & set(state)) for state in states)
            actual_distances = {str(k): v for k, v in distances.items()}
            assert actual_distances == count_saved["edge_replacement_counts"]
            assert count_saved["proper_three_overlap"] == 492
            assert count_saved["paired_two_overlap"] == 0
        reports[name] = own
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": ind.sha(__file__),
        "source_files_index_sha256": ind.sha(SOURCE / "files.json"),
        "enumeration_sha256": ind.sha(HERE / "enumeration.json"),
        "g5_bundle_sha256": ind.sha(ARCHIVE / "g5-cuts.json.gz"),
        "compact_bundle_sha256": ind.sha(compact_path), "compact_restore_verified": True,
        "envelope_results_sha256": ind.sha(SOURCE / "envelope-results.json"),
        "counts_sha256": ind.sha(SOURCE / "counts.json"), "graph_index": 5,
        "family_sha256": family_sha, "g5_planes": 720, "broad_planes": 353,
        "neighborhoods": reports, "certificates": checked,
        "scope": "Exact finite fixed-g5 screen only. The720planes are graph-five specific. "
        "Positive bounds exclude only tested patterns; zero bounds remain inconclusive.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "certificates"}, indent=2))


if __name__ == "__main__":
    main()
