# Document:    Exact Fixed-g1 Whole-Link Pool Certificates
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      12fbcd4cca4b9135ed866a777479cff538f51db2990a339bc1b4e3b34748ae0b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay saved duals into graph-specific positive certificates; never solve."""

import gzip
import importlib.util
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
POOL = DAY / "g1-whole-link-pool"
PLAN = ROOT / "experiments/scratch/g1-next-route-plan-20261004"
RAW = ROOT / "experiments/scratch/g1-whole-link-certificates-20261004"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def main():
    assert not RAW.exists() and not (HERE / "result.json").exists()
    branch = load(DAY / "g1-link-descent/run.py", "certificate_branch")
    helpers = load(DAY / "nearest-heavy-master/run.py", "certificate_helpers")
    exact = load(branch.generator.LP_CORE, "certificate_exact")
    sha = branch.sha
    result = json.loads((POOL / "result.json").read_text())
    manifest = json.loads((POOL / "manifest.json").read_text())
    post_path = DAY / "g1-whole-link-pool-independent/postcheck.json"
    post = json.loads(post_path.read_text())
    assert post["passed"] and result["complete_pool"] and len(result["records"]) == 757
    assert all(record["status"] == "OPTIMAL" for record in result["records"])
    old_path = PLAN / "g1-cuts.json"
    old = json.loads(old_path.read_text())
    screen_path = DAY / "g1-larger-independent/audit.json"
    screen = json.loads(screen_path.read_text())
    assert screen["passed"] and screen["conditional_bundle_sha256"] == sha(old_path)
    assert old["count"] == 243 and old["family_sha256"] == manifest["family_sha256"]
    blocks, ordinary, heavy, _, rows, changes = branch.basis()
    heavy_global = [blocks.index(b) for b in heavy]
    lookup = {global_id: local for local, global_id in enumerate(heavy_global)}
    new = []
    input_files = {
        str(path.relative_to(ROOT)): sha(path)
        for path in [
            Path(__file__),
            DAY / "g1-link-descent/run.py",
            DAY / "nearest-heavy-master/run.py",
            branch.generator.LP_CORE,
            POOL / "run.py",
            POOL / "manifest.json",
            POOL / "result.json",
            post_path,
            old_path,
            screen_path,
            PLAN / "whole-link-unexcluded.json.gz",
            PLAN / "envelope-results.json",
        ]
    }
    for record in result["records"]:
        family = [blocks[i] for i in record["heavy_global_ids"]]
        shifted = branch.generator.shifted_rows(rows, heavy, family)
        assert branch.data_hash(shifted) == record["shifted_rows_sha256"]
        assert record["family_sha256"] == manifest["family_sha256"]
        path = ROOT / record["dual_path"]
        assert sha(path) == record["dual_sha256"]
        input_files[record["dual_path"]] = record["dual_sha256"]
        numeric = json.loads(path.read_text())
        fixed = {lookup[i] for i in record["heavy_global_ids"]}
        cut = helpers.derive_cut(exact, rows, shifted, numeric, fixed, len(ordinary), len(heavy))
        assert cut is not None and cut["dual"]["proves_infeasible"]
        norm = max(abs(weight) for _, weight in cut["dual"]["weights"])
        assert norm <= cut["denominator"] == 1000000
        cut.update(
            id=f"g1-whole-link-rank{record['rank']:03d}",
            graph_index=1,
            family_sha256=manifest["family_sha256"],
            source_heavy_global_ids=record["heavy_global_ids"],
            source_heavy_sha256=record["heavy_sha256"],
            source_shifted_rows_sha256=record["shifted_rows_sha256"],
            numerical_dual_path=record["dual_path"],
            numerical_dual_sha256=record["dual_sha256"],
            maximum_signed_row_weight=norm,
            source_objective=record["objective"],
        )
        new.append(cut)
    expected = json.loads(gzip.decompress((PLAN / "whole-link-unexcluded.json.gz").read_bytes()))
    assert sorted(record["source_heavy_global_ids"] for record in new) == expected
    all_cuts = old["cuts"] + new
    assert len(all_cuts) == len({cut["id"] for cut in all_cuts}) == 1000
    assert len({tuple(cut["source_heavy_global_ids"]) for cut in all_cuts}) == 1000
    assert all(cut["graph_index"] == 1 for cut in all_cuts)
    RAW.mkdir()
    (RAW / "extract-frozen.py").write_bytes(Path(__file__).read_bytes())
    bundle = {
        "graph_index": 1,
        "hub_excesses": [0, 1, 1, 1, 1, 0],
        "six_row_changes": changes,
        "family_sha256": manifest["family_sha256"],
        "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "heavy_global_ids": heavy_global,
        "count": 1000,
        "prior_count": 243,
        "new_count": 757,
        "prior_bundle_sha256": sha(old_path),
        "new_source_result_sha256": sha(POOL / "result.json"),
        "source_sha256": sha(__file__),
        "cuts": all_cuts,
        "optimization_calls": 0,
        "scope": (
            "All 1000 planes are conditional on hub graph g1. "
            "Separate from the 353 broad planes."
        ),
    }
    dump(RAW / "all-g1-cuts.json", bundle)
    previous = json.loads((PLAN / "envelope-results.json").read_text())["neighborhoods"][
        "whole-link"
    ]
    assert previous["registry_safe_states"] == 100076
    assert previous["combined_positive"] == 99319 and previous["combined_unexcluded"] == 757
    minimum = min(
        (cut["dual"]["gap"][0] / cut["dual"]["gap"][1], cut["id"], cut["dual"]["gap"])
        for cut in new
    )
    report = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "bundle_path": str((RAW / "all-g1-cuts.json").relative_to(ROOT)),
        "bundle_sha256": sha(RAW / "all-g1-cuts.json"),
        "graph_index": 1,
        "family_sha256": manifest["family_sha256"],
        "prior_planes": 243,
        "new_positive_certificates": 757,
        "total_graph_specific_planes": 1000,
        "finite_whole_link_states": 100076,
        "prior_positive_envelope_states": 99319,
        "remaining_positive_source_certificates": 757,
        "finite_whole_link_exclusion_pending_independent_replay": True,
        "minimum_new_source_gap": minimum[2],
        "minimum_new_source_gap_id": minimum[1],
        "input_files": input_files,
        "optimization_calls": 0,
        "scope": (
            "Exact source arithmetic pending independent replay. Only the fixed-g1 "
            "whole-link neighborhood; no elastic optimum or global covering lower-bound claim."
        ),
    }
    dump(HERE / "result.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "input_files"}))


if __name__ == "__main__":
    main()
