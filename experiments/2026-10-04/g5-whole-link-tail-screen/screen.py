# Document:    Exact Fixed-g5 Unevaluated Whole-Link Tail Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      188405112a44a75976977a0185a2943f04eeea2bd4b7a5a13e96f28567998f99
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze inputs, then score the 55 unevaluated states with integer arithmetic."""

import argparse
import gzip
import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
POOL = DAY / "g5-whole-link-pool"
CERTIFICATES = DAY / "g5-whole-link-certificates"
SCREEN = DAY / "g5-larger-independent/audit.json"
RAW = ROOT / "experiments/scratch/g5-whole-link-tail-screen-20261004"


def read(path):
    return json.loads(Path(path).read_text())


def compressed(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    report = read(CERTIFICATES / "result.json")
    post_path = DAY / "g5-whole-link-pool-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"] and post["result_sha256"] == sha(POOL / "result.json")
    assert report["graph_index"] == 5 and report["new_positive_certificates"] == 3441
    assert report["unexamined_pool_states"] == 55 and report["optimization_calls"] == 0
    assert report["source_sha256"] == sha(CERTIFICATES / "extract.py")
    for relative, expected in report["input_files"].items():
        assert sha(ROOT / relative) == expected
    manifest = read(POOL / "manifest.json")
    paths = [
        Path(__file__), CERTIFICATES / "extract.py", CERTIFICATES / "result.json",
        ROOT / report["bundle_path"], ROOT / report["compact_path"],
        POOL / "run.py", POOL / "manifest.json", POOL / "result.json", post_path,
        ROOT / manifest["pool_path"], ROOT / manifest["inventory_path"], SCREEN,
        DAY / "g5-larger-screen/whole-link-unexcluded.json.gz",
    ]
    inputs = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    assert sha(ROOT / report["bundle_path"]) == report["bundle_sha256"]
    assert sha(ROOT / report["compact_path"]) == report["compact_sha256"]
    dump(HERE / "manifest.json", {
        "source_sha256": sha(__file__), "input_files": inputs, "graph_index": 5,
        "family_sha256": manifest["family_sha256"], "tail_states": 55,
        "evaluated_states": 3441, "new_planes": 3441, "prior_planes": 720,
        "denominator": 1000000, "optimizer_calls": 0,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "scope": "Only the 55 frozen unevaluated fixed-g5 states. "
        "All certificate and coverage claims await independent replay.",
    })
    print(json.dumps({"manifest_sha256": sha(HERE / "manifest.json"),
                      "source_sha256": sha(__file__), "optimizer_calls": 0}))


def run():
    assert not (HERE / "result.json").exists() and not RAW.exists()
    manifest = read(HERE / "manifest.json")
    assert sha(__file__) == manifest["source_sha256"]
    for relative, expected in manifest["input_files"].items():
        assert sha(ROOT / relative) == expected
    extraction = read(CERTIFICATES / "result.json")
    bundle = read(ROOT / extraction["bundle_path"])
    assert bundle["graph_index"] == 5 and bundle["family_sha256"] == manifest["family_sha256"]
    assert (bundle["count"], bundle["prior_count"], bundle["new_count"]) == (4161, 720, 3441)
    pool_manifest = read(POOL / "manifest.json")
    pool = compressed(ROOT / pool_manifest["pool_path"])["heavy_global_ids"]
    inventory = compressed(ROOT / pool_manifest["inventory_path"])
    result = read(POOL / "result.json")
    records = result["records"]
    assert len(pool) == len({tuple(ids) for ids in pool}) == len(inventory) == 3496
    assert len(records) == 3441 and not result["complete_pool"]
    assert [record["rank"] for record in records] == list(range(3441))
    assert [record["heavy_global_ids"] for record in records] == pool[:3441]
    assert [item["heavy_global_ids"] for item in inventory] == pool
    assert set(map(tuple, pool)) == set(map(tuple, compressed(
        DAY / "g5-larger-screen/whole-link-unexcluded.json.gz"
    )))
    tail = pool[3441:]
    assert len(tail) == 55
    assert set(map(tuple, tail)).isdisjoint(map(tuple, pool[:3441]))
    prior, new = bundle["cuts"][:720], bundle["cuts"][720:]
    assert [cut["source_heavy_global_ids"] for cut in new] == pool[:3441]
    assert len({cut["id"] for cut in bundle["cuts"]}) == 4161
    for cut in bundle["cuts"]:
        assert cut["graph_index"] == 5 and cut["family_sha256"] == manifest["family_sha256"]
        assert cut["denominator"] == cut["dual"]["denominator"] == 1000000
        assert max(abs(weight) for _, weight in cut["dual"]["weights"]) <= 1000000
        assert len(cut["coefficients"]) == 276
        assert all(type(value) is int for value in cut["coefficients"])
        assert type(cut["rhs"]) is int
    lookup = {global_id: local for local, global_id in enumerate(bundle["heavy_global_ids"])}
    scores, unexcluded = [], []
    for rank, ids in enumerate(tail, start=3441):
        assert len(ids) == len(set(ids)) == 28 and ids == sorted(ids)
        local = [lookup[global_id] for global_id in ids]
        receipt = inventory[rank]["registry"]
        assert receipt["accepted"] and len(receipt["links"]) == 4
        assert max(cut["rhs"] - sum(cut["coefficients"][i] for i in local)
                   for cut in prior) <= 0
        best_gap, best_id = max(
            (cut["rhs"] - sum(cut["coefficients"][i] for i in local), cut["id"])
            for cut in new
        )
        bound = max(0, best_gap)
        scores.append({"rank": rank, "heavy_global_ids": ids,
                       "new_bound_numerator": bound, "denominator": 1000000,
                       "best_raw_gap_numerator": best_gap,
                       "best_cut_id": best_id, "positive": bound > 0,
                       "registry": receipt})
        if bound == 0:
            unexcluded.append(ids)
    RAW.mkdir()
    (RAW / "screen-frozen.py").write_bytes(Path(__file__).read_bytes())
    (RAW / "manifest.json").write_bytes((HERE / "manifest.json").read_bytes())
    dump(HERE / "scores.json", scores)
    dump(HERE / "unexcluded.json", unexcluded)
    minimum = min(scores, key=lambda score: score["new_bound_numerator"])
    gap = Fraction(minimum["new_bound_numerator"], 1000000)
    previous = read(SCREEN)["neighborhoods"]["whole-link"]
    assert previous["registry_safe_states"] == 46436
    assert previous["combined_positive"] == 42940 and previous["combined_unexcluded"] == 3496
    report = {
        "source_sha256": sha(__file__), "manifest_sha256": sha(HERE / "manifest.json"),
        "extraction_result_sha256": sha(CERTIFICATES / "result.json"),
        "bundle_sha256": extraction["bundle_sha256"], "graph_index": 5,
        "family_sha256": manifest["family_sha256"], "optimizer_calls": 0,
        "tail_states": 55, "new_planes": 3441, "integer_plane_state_evaluations": 55 * 3441,
        "positive_tail_states": 55 - len(unexcluded), "unexcluded_tail_states": len(unexcluded),
        "minimum_tail_bound": [gap.numerator, gap.denominator],
        "minimum_tail_rank": minimum["rank"], "minimum_tail_cut": minimum["best_cut_id"],
        "prior_positive_envelope_states": 42940, "new_positive_source_states": 3441,
        "finite_whole_link_states": 46436,
        "finite_whole_link_exclusion_pending_independent_replay": not unexcluded,
        "independently_checked_closure": False,
        "scores_sha256": sha(HERE / "scores.json"),
        "unexcluded_sha256": sha(HERE / "unexcluded.json"),
        "scope": "Integer arithmetic on saved conditional g5 planes and the 55 unevaluated "
        "states. Independent coefficient and coverage replay is still required. "
        "No full-family exclusion, elastic optimum, or unrestricted covering bound.",
    }
    dump(HERE / "result.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run"])
    args = parser.parse_args()
    prepare() if args.mode == "prepare" else run()
