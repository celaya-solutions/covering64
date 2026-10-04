# Document:    Independent Fixed G5 Whole Link Closure
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay every new signed-row certificate and all tail envelopes without a solver."""

import copy
import gzip
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "g5-whole-link-certificates"
TAIL = DAY / "g5-whole-link-tail-screen"
PLAN = DAY / "g5-larger-screen"
spec = importlib.util.spec_from_file_location(
    "g5_signed_check", DAY / "g5-larger-independent/check.py"
)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
ind = base.ind


def read(path):
    return json.loads(Path(path).read_text())


def compressed(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def main():
    result = read(SOURCE / "result.json")
    for folder in (SOURCE, TAIL):
        for name, expected in read(folder / "files.json").items():
            assert ind.sha(folder / name) == expected
    for path, expected in result["input_files"].items():
        assert ind.sha(ROOT / path) == expected
    tail_manifest = read(TAIL / "manifest.json")
    for path, expected in tail_manifest["input_files"].items():
        assert ind.sha(ROOT / path) == expected
    bundle_path = ROOT / result["bundle_path"]
    assert ind.sha(bundle_path) == result["bundle_sha256"]
    bundle = read(bundle_path)
    compact_path = ROOT / result["compact_path"]
    assert ind.sha(compact_path) == result["compact_sha256"]
    archive = compressed(compact_path)
    assert archive["original_sha256"] == ind.sha(bundle_path)
    prior_path = ROOT / "experiments/scratch/g5-larger-screen-20261004/g5-cuts.json"
    prior = read(prior_path)
    prior_audit = read(DAY / "g5-larger-independent/audit.json")
    assert prior_audit["passed"] and bundle["prior_bundle_sha256"] == ind.sha(prior_path)
    pool_path = DAY / "g5-whole-link-pool/result.json"
    pool = read(pool_path)
    post_path = DAY / "g5-whole-link-pool-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"] and post["result_sha256"] == ind.sha(pool_path)
    assert bundle["new_source_result_sha256"] == ind.sha(pool_path)
    assert bundle["count"] == len(bundle["cuts"]) == 4161
    assert bundle["prior_count"] == 720 and bundle["new_count"] == 3441
    assert bundle["cuts"][:720] == prior["cuts"]
    blocks, _, ordinary, heavy, rows = ind.basis()
    gids = [blocks.index(block) for block in heavy]
    family = ind.digest({"rows": rows, "ordinary_global_ids": [blocks.index(b) for b in ordinary],
                         "graph_index": 5})
    assert family == bundle["family_sha256"] == result["family_sha256"]
    assert bundle["graph_index"] == 5 and bundle["hub_excesses"] == [2, 0, 0, 0, 0, 2]
    assert bundle["heavy_global_ids"] == gids
    assert bundle["ordinary_global_ids"] == [blocks.index(b) for b in ordinary]
    assert archive["unconditional_rows"] == json.loads(json.dumps(rows))
    support_o = [[r for r, row in enumerate(rows) if i in row[0]] for i in range(1200)]
    support_h = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(276)]
    assert len({cut["id"] for cut in bundle["cuts"]}) == 4161
    checked, minimum = [], None
    for cut, record in zip(bundle["cuts"][720:], pool["records"], strict=True):
        assert cut["source_heavy_global_ids"] == record["heavy_global_ids"]
        chosen = tuple(blocks[i] for i in record["heavy_global_ids"])
        assert ind.digest(chosen) == cut["source_heavy_sha256"] == record["heavy_sha256"]
        assert ind.digest(ind.shifted(rows, heavy, chosen)) == cut["source_shifted_rows_sha256"]
        assert cut["source_shifted_rows_sha256"] == record["shifted_rows_sha256"]
        assert cut["numerical_dual_sha256"] == ind.sha(ROOT / cut["numerical_dual_path"])
        _, _, gap = base.check_cut(cut, rows, support_o, support_h, gids, family)
        minimum = gap if minimum is None else min(minimum, gap)
        checked.append({"id": cut["id"], "gap": [gap.numerator, gap.denominator]})
    assert [minimum.numerator, minimum.denominator] == result["minimum_new_source_gap"]
    # Restore the full JSON bytes from compact signed-row storage independently.
    restored = copy.deepcopy(archive["bundle"])
    for cut, full in zip(restored["cuts"], bundle["cuts"], strict=True):
        assert cut["ordinary_coefficients"] == cut["coefficients"] == "derived-from-signed-rows"
        weights = dict(cut["dual"]["weights"])
        cut["ordinary_coefficients"] = [sum(weights.get(r, 0) for r in s) for s in support_o]
        cut["coefficients"] = [sum(weights.get(r, 0) for r in s) for s in support_h]
        assert cut == full
    assert (json.dumps(restored, indent=2) + "\n").encode() == bundle_path.read_bytes()
    manifest = read(DAY / "g5-whole-link-pool/manifest.json")
    ordered = compressed(ROOT / manifest["pool_path"])["heavy_global_ids"]
    whole = compressed(PLAN / "whole-link.json.gz")
    unexcluded = compressed(PLAN / "whole-link-unexcluded.json.gz")
    assert len(whole) == 46436 and len(unexcluded) == 3496
    assert set(map(tuple, ordered)) == set(map(tuple, unexcluded))
    assert [r["heavy_global_ids"] for r in pool["records"]] == ordered[:3441]
    scores = read(TAIL / "scores.json")
    assert len(scores) == 55 and [s["heavy_global_ids"] for s in scores] == ordered[3441:]
    lookup = {g: i for i, g in enumerate(gids)}
    tail_min = None
    for rank, score in enumerate(scores, start=3441):
        assert score["rank"] == rank
        chosen = tuple(blocks[i] for i in score["heavy_global_ids"])
        assert not ind.validate_receipt(chosen, score["registry"])
        pos = [lookup[i] for i in score["heavy_global_ids"]]
        gaps = [(cut["rhs"] - sum(cut["coefficients"][i] for i in pos), cut["id"])
                for cut in bundle["cuts"][720:]]
        value = max(gap for gap, _ in gaps)
        assert value == score["new_bound_numerator"] == score["best_raw_gap_numerator"]
        assert (value, score["best_cut_id"]) in gaps
        assert score["denominator"] == 1000000 and score["positive"] and value > 0
        gap = Fraction(value, 1000000)
        tail_min = gap if tail_min is None else min(tail_min, gap)
    prior_closed = set(map(tuple, whole)) - set(map(tuple, ordered))
    assert len(prior_closed) == prior_audit["neighborhoods"]["whole-link"]["combined_positive"]
    assert len(prior_closed) + len(checked) + len(scores) == len(whole) == 46436
    controls = []
    for field in ("rhs", "ordinary_box_max", "source_lhs"):
        damaged = copy.deepcopy(bundle["cuts"][720])
        damaged[field] += 1
        try:
            base.check_cut(damaged, rows, support_o, support_h, gids, family)
        except AssertionError:
            controls.append(field)
        else:
            raise AssertionError("Damaged proof accepted")
    audit = {"passed": True, "optimizer_calls": 0, "checker_sha256": ind.sha(__file__),
             "helper_sha256": ind.sha(DAY / "g5-larger-independent/check.py"),
             "result_sha256": ind.sha(SOURCE / "result.json"),
             "tail_result_sha256": ind.sha(TAIL / "result.json"),
             "prior_audit_sha256": ind.sha(DAY / "g5-larger-independent/audit.json"),
             "pool_postcheck_sha256": ind.sha(post_path), "bundle_sha256": ind.sha(bundle_path),
             "compact_restore_verified": True, "graph_index": 5, "family_sha256": family,
             "new_certificates": 3441, "prior_planes": 720, "tail_states": 55,
             "minimum_source_gap": [minimum.numerator, minimum.denominator],
             "minimum_tail_gap": [tail_min.numerator, tail_min.denominator],
             "whole_link_states_excluded": 46436, "damaged_controls_rejected": controls,
             "certificates": checked,
             "scope": "Only the declared fixed-g5 whole-link neighborhood. No full-family "
                      "infeasibility, elastic local optimality, or global covering lower bound."}
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({k: v for k, v in audit.items() if k != "certificates"}))


if __name__ == "__main__":
    main()
