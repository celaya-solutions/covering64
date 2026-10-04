#!/usr/bin/env python3
# Document:    Independent Graph One Dual Envelope and Finite Pool Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Exact integer support planes and finite candidate screen, without optimization."""

import gzip
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/scratch/g1-next-route-plan-20261004"
RAW = ROOT / "experiments/scratch/g1-larger-independent-20261004"
path = HERE.parent / "g1-link-descent-independent/independent.py"
spec = importlib.util.spec_from_file_location("g1_pool_independent", path)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    bundle = json.loads((SOURCE / "g1-cuts.json").read_text())
    envelope = json.loads((SOURCE / "envelope-results.json").read_text())
    for name, expected in json.loads((SOURCE / "inputs.json").read_text()).items():
        assert ind.sha(ROOT / name) == expected
    assert bundle["source_sha256"] == envelope["source_sha256"] == ind.sha(SOURCE / "envelopes.py")
    assert envelope["bundle_sha256"] == ind.sha(SOURCE / "g1-cuts.json")
    assert bundle["graph_index"] == envelope["graph_index"] == 1
    blocks, _, ordinary, heavy, rows = ind.basis()
    global_ids = [blocks.index(block) for block in heavy]
    assert bundle["heavy_global_ids"] == global_ids
    assert bundle["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    assert json.loads(json.dumps(rows)) == json.loads(
        (SOURCE / "g1-unconditional-rows.json").read_text()
    )
    manifest = json.loads((HERE.parent / "g1-link-descent/manifest.json").read_text())
    descent_path = HERE.parent / "g1-link-descent/result.json"
    descent = json.loads(descent_path.read_text())
    assert bundle["descent_result_sha256"] == ind.sha(descent_path)
    assert bundle["family_sha256"] == manifest["family_sha256"]
    assert bundle["six_row_changes"] == manifest["six_row_changes"]
    assert bundle["hub_excesses"] == [0, 1, 1, 1, 1, 0]
    fresh = {
        (record["round"], record["rank"]): record
        for record in descent["records"]
        if not record["cached"]
    }
    support_o = [[r for r, row in enumerate(rows) if i in row[0]] for i in range(1200)]
    support_h = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(276)]
    assert len(fresh) == bundle["count"] == len(bundle["cuts"]) == 243
    for cut in bundle["cuts"]:
        prefix, rank_text = cut["id"].split("-rank")
        record = fresh.pop((int(prefix.removeprefix("g1-round")), int(rank_text)))
        assert cut["graph_index"] == 1 and cut["family_sha256"] == manifest["family_sha256"]
        assert cut["source_heavy_global_ids"] == record["heavy_global_ids"]
        assert cut["source_heavy_sha256"] == record["heavy_sha256"]
        assert cut["source_shifted_rows_sha256"] == record["shifted_rows_sha256"]
        assert cut["source_objective"] == record["objective"]
        assert cut["numerical_dual_path"] == record["dual_path"]
        assert (
            ind.sha(ROOT / cut["numerical_dual_path"])
            == cut["numerical_dual_sha256"]
            == record["dual_sha256"]
        )
        weights, seen = [0] * 697, set()
        assert cut["denominator"] == cut["dual"]["denominator"] == 1000000
        for row_index, weight in cut["dual"]["weights"]:
            assert type(row_index) is int and 0 <= row_index < 697 and row_index not in seen
            assert type(weight) is int and 0 < abs(weight) <= 1000000
            assert weight >= 0 or rows[row_index][3] != ind.INF
            weights[row_index] = weight
            seen.add(row_index)
        ordinary_coefficients = [sum(weights[r] for r in support) for support in support_o]
        heavy_coefficients = [sum(weights[r] for r in support) for support in support_h]
        constant = sum(
            w * (rows[r][2] if w > 0 else rows[r][3]) for r, w in enumerate(weights) if w
        )
        box = sum(max(0, value) for value in ordinary_coefficients)
        chosen = [global_ids.index(index) for index in record["heavy_global_ids"]]
        lhs = sum(heavy_coefficients[i] for i in chosen)
        assert cut["ordinary_coefficients"] == ordinary_coefficients
        assert cut["coefficients"] == heavy_coefficients
        assert (cut["constant"], cut["ordinary_box_max"], cut["source_lhs"], cut["rhs"]) == (
            constant,
            box,
            lhs,
            constant - box,
        )
        assert max(map(abs, weights)) == cut["maximum_signed_row_weight"]
        assert cut["dual"]["rhs_numerator"] == constant - lhs
        assert cut["dual"]["box_max_numerator"] == box
        gap = Fraction(constant - box - lhs, 1000000)
        assert gap > 0 and cut["dual"]["gap"] == [gap.numerator, gap.denominator]
    assert not fresh
    broad = json.loads((SOURCE / "broad-cuts-reference.json").read_text())["cuts"]
    old_path = (
        ROOT / "experiments/scratch/lp-guided-larger-intersection-20261004/checked-planes.json"
    )
    old_audit = json.loads(
        (HERE.parent / "lp-guided-complete-sweep-independent/cut-intersection.json").read_text()
    )
    assert old_audit["passed"] and old_audit["checked_planes_sha256"] == ind.sha(old_path)
    expected_broad = json.loads(old_path.read_text())
    margin = json.loads((HERE.parent / "margin-heavy-master/result.json").read_text())
    margin_audit = json.loads(
        (HERE.parent / "margin-heavy-master-independent/postcheck.json").read_text()
    )
    assert margin_audit["passed"] and margin_audit["result_sha256"] == ind.sha(
        HERE.parent / "margin-heavy-master/result.json"
    )
    for record, checked in zip(margin["records"], margin_audit["results"], strict=True):
        cut_path = (
            ROOT
            / "experiments/scratch/margin-heavy-master-20261004"
            / f"step-{record['step']:03d}/learned-cut.json"
        )
        assert ind.sha(cut_path) == record["learned_cut_sha256"] == checked["learned_cut_sha256"]
        expected_broad.append(json.loads(cut_path.read_text()))
    assert len(broad) == len(expected_broad) == 353
    for actual, expected in zip(broad, expected_broad, strict=True):
        assert all(
            actual[field] == expected[field] for field in ("coefficients", "rhs", "denominator")
        )
    assert envelope["broad_reference_sha256"] == ind.sha(SOURCE / "broad-cuts-reference.json")

    best = descent["trajectory"][-1]
    raw_values = json.loads((ROOT / best["vector_path"]).read_text())
    assert ind.sha(ROOT / best["vector_path"]) == best["vector_sha256"]
    values = [min(Fraction(1), max(Fraction(0), Fraction.from_float(v))) for v in raw_values]
    concrete = ind.shifted(rows, heavy, [blocks[i] for i in best["heavy_global_ids"]])
    upper = Fraction(0)
    for ids, coefficients, lower, upper_bound in concrete:
        value = sum((c * values[i] for i, c in zip(ids, coefficients, strict=True)), Fraction(0))
        upper += max(Fraction(0), lower - value)
        if upper_bound != ind.INF:
            upper += max(Fraction(0), value - upper_bound)
    certified_upper = Fraction(*envelope["incumbent_certified_upper"])
    assert upper <= certified_upper < upper + Fraction(1, 1000000000)
    threshold = (
        certified_upper.numerator * 1000000 + certified_upper.denominator - 1
    ) // certified_upper.denominator
    assert envelope["integer_threshold"] == threshold

    def score_matrix(cuts):
        coefficients = [
            [v * (1000000 // cut["denominator"]) for v in cut["coefficients"]] for cut in cuts
        ]
        rhs = [cut["rhs"] * (1000000 // cut["denominator"]) for cut in cuts]
        assert all(
            abs(bound) + sum(map(abs, row)) < 2**60
            for bound, row in zip(rhs, coefficients, strict=True)
        )
        return np.asarray(coefficients, dtype=np.int64), np.asarray(rhs, dtype=np.int64)

    conditional_matrix, conditional_rhs = score_matrix(bundle["cuts"])
    broad_matrix, broad_rhs = score_matrix(broad)
    enum = json.loads((HERE / "enumeration.json").read_text())
    assert enum["passed"] and enum["states_archive_sha256"] == ind.sha(RAW / "states.npz")
    arrays = np.load(RAW / "states.npz")
    summaries = {}
    global_array = np.asarray(global_ids)
    for own_name, source_name in (
        ("proper_three", "proper-three"),
        ("paired_two", "paired-two"),
        ("whole_link", "whole-link"),
    ):
        local = arrays[own_name]
        states = json.loads(gzip.decompress((SOURCE / f"{source_name}.json.gz").read_bytes()))
        assert np.array_equal(global_array[local], np.asarray(states))
        saved_scores = np.asarray(
            json.loads(gzip.decompress((SOURCE / f"{source_name}-envelopes.json.gz").read_bytes())),
            dtype=np.int64,
        )
        actual_scores = []
        for offset in range(0, len(local), 128):
            group = local[offset : offset + 128]
            c = np.maximum(
                0, (conditional_rhs[:, None] - conditional_matrix[:, group].sum(axis=2)).max(axis=0)
            )
            b = np.maximum(0, (broad_rhs[:, None] - broad_matrix[:, group].sum(axis=2)).max(axis=0))
            actual_scores.extend(
                zip(map(int, c), map(int, b), map(int, np.maximum(c, b)), strict=True)
            )
        scores = np.asarray(actual_scores)
        assert np.array_equal(scores, saved_scores)
        unexcluded = [state for state, score in zip(states, scores, strict=True) if score[2] == 0]
        assert unexcluded == json.loads(
            gzip.decompress((SOURCE / f"{source_name}-unexcluded.json.gz").read_bytes())
        )
        summary = {
            "states": len(states),
            "g1_positive": int((scores[:, 0] > 0).sum()),
            "combined_positive": int((scores[:, 2] > 0).sum()),
            "unexcluded": len(unexcluded),
            "pruned_against_incumbent": int((scores[:, 2] >= threshold).sum()),
            "states_sha256": ind.sha(SOURCE / f"{source_name}.json.gz"),
            "scores_sha256": ind.sha(SOURCE / f"{source_name}-envelopes.json.gz"),
        }
        saved = envelope["neighborhoods"][source_name]
        assert summary["states"] == saved["registry_safe_states"]
        assert summary["g1_positive"] == saved["g1_positive"]
        assert summary["combined_positive"] == saved["combined_positive"]
        assert summary["unexcluded"] == saved["combined_unexcluded"]
        assert (
            summary["pruned_against_incumbent"] == saved["combined_bound_reaches_incumbent_upper"]
        )
        summaries[source_name] = summary
    assert [summaries[n]["states"] for n in summaries] == [580, 5541, 100076]
    assert [summaries[n]["unexcluded"] for n in summaries] == [0, 0, 757]
    pool_path = SOURCE / "whole-link-unexcluded.json.gz"
    pool = json.loads(gzip.decompress(pool_path.read_bytes()))
    cache = json.loads(
        (ROOT / "experiments/scratch/g1-link-descent-20261004/final-cache.json").read_text()
    )
    cached = {tuple(record["heavy_global_ids"]) for record in cache.values()}
    assert all(tuple(state) not in cached for state in pool)
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": ind.sha(__file__),
        "conditional_bundle_sha256": ind.sha(SOURCE / "g1-cuts.json"),
        "envelope_results_sha256": ind.sha(SOURCE / "envelope-results.json"),
        "conditional_planes": 243,
        "broad_planes": 353,
        "graph_index": 1,
        "whole_link_survivors": 757,
        "whole_link_pool_path": str(pool_path.relative_to(ROOT)),
        "whole_link_pool_sha256": ind.sha(pool_path),
        "all_pool_states_uncached": True,
        "incumbent_exact_upper": [upper.numerator, upper.denominator],
        "enumeration_sha256": ind.sha(HERE / "enumeration.json"),
        "neighborhoods": summaries,
        "scope": "Exact positive envelopes exclude only the tested finite fixed-graph-one "
        "heavy patterns. No full-family exclusion or unrestricted bound is claimed.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
