# Document:    Exact Fixed-g5 Whole-Link Pool Certificates
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1a69181ae81c9a5663df630cea32c6e298e70e53ad1620b1b05e8225031ac755
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Extract exact source certificates from passed saved LPs; never optimize."""

import copy
import gzip
import importlib.util
import json
import subprocess
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
POOL = DAY / "g5-whole-link-pool"
PLAN = DAY / "g5-larger-screen"
OLD = ROOT / "experiments/scratch/g5-larger-screen-20261004"
RAW = ROOT / "experiments/scratch/g5-whole-link-certificates-20261004"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def main():
    assert not RAW.exists() and not (HERE / "result.json").exists()
    branch = load(DAY / "g5-link-continuation/run.py", "g5_certificate_branch")
    helpers = load(DAY / "nearest-heavy-master/run.py", "g5_certificate_helpers")
    exact = load(branch.generator.LP_CORE, "g5_certificate_exact")
    restore = load(PLAN / "restore_bundle.py", "g5_certificate_restore")
    sha = branch.sha
    result, manifest = read(POOL / "result.json"), read(POOL / "manifest.json")
    post_path = DAY / "g5-whole-link-pool-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"] and post["result_sha256"] == sha(POOL / "result.json")
    assert result["manifest_sha256"] == sha(POOL / "manifest.json")
    assert result["source_sha256"] == manifest["source_sha256"] == sha(POOL / "run.py")
    assert result["graph_index"] == manifest["graph_index"] == 5
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    assert not result["numerical_zero"] and not result["exact_fractional_feasibility"]
    records = result["records"]
    assert len(records) == result["evaluated_count"] == result["fresh_evaluations"]
    assert result["cached_evaluations"] == 0 and 0 < len(records) <= 3496
    assert [record["rank"] for record in records] == list(range(len(records)))
    assert all(record["status"] == "OPTIMAL" for record in records)
    assert result["complete_pool"] == (len(records) == 3496)
    assert sha(ROOT / manifest["pool_path"]) == manifest["pool_sha256"]
    expected = json.loads(gzip.decompress((ROOT / manifest["pool_path"]).read_bytes()))[
        "heavy_global_ids"
    ]
    assert len(expected) == len({tuple(ids) for ids in expected}) == 3496
    assert [record["heavy_global_ids"] for record in records] == expected[:len(records)]
    old_path = OLD / "g5-cuts.json"
    old = read(old_path)
    screen_path = DAY / "g5-larger-independent/audit.json"
    screen = read(screen_path)
    assert screen["passed"] and screen["graph_index"] == 5
    assert screen["g5_bundle_sha256"] == sha(OLD / "g5-cuts.json.gz")
    assert old == json.loads(gzip.decompress((OLD / "g5-cuts.json.gz").read_bytes()))
    assert screen["envelope_results_sha256"] == sha(PLAN / "envelope-results.json")
    assert old["count"] == 720 and old["family_sha256"] == manifest["family_sha256"]
    blocks, ordinary, heavy, _, rows, changes = branch.basis()
    heavy_global = [blocks.index(block) for block in heavy]
    lookup = {global_id: local for local, global_id in enumerate(heavy_global)}
    assert manifest["family_sha256"] == branch.data_hash({
        "rows": rows, "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "graph_index": 5,
    })
    assert old["six_row_changes"] == json.loads(json.dumps(changes))
    input_files = {
        str(path.relative_to(ROOT)): sha(path)
        for path in [
            Path(__file__), DAY / "g5-link-continuation/run.py",
            DAY / "nearest-heavy-master/run.py", branch.generator.LP_CORE,
            Path(branch.generator.__file__), PLAN / "restore_bundle.py",
            POOL / "run.py", POOL / "manifest.json", POOL / "result.json",
            post_path, old_path, OLD / "g5-cuts.json.gz", screen_path,
            PLAN / "whole-link-unexcluded.json.gz", PLAN / "envelope-results.json",
            ROOT / manifest["pool_path"], ROOT / manifest["inventory_path"],
        ]
    }
    new = []
    for record in records:
        chosen = [blocks[i] for i in record["heavy_global_ids"]]
        shifted = branch.generator.shifted_rows(rows, heavy, chosen)
        assert branch.data_hash(chosen) == record["heavy_sha256"]
        assert branch.data_hash(shifted) == record["shifted_rows_sha256"]
        assert record["family_sha256"] == manifest["family_sha256"]
        model_path, dual_path = ROOT / record["model_path"], ROOT / record["dual_path"]
        assert sha(model_path) == record["model_sha256"]
        assert json.loads(gzip.decompress(model_path.read_bytes())) == json.loads(
            json.dumps(shifted)
        )
        assert sha(dual_path) == record["dual_sha256"]
        input_files[record["dual_path"]] = record["dual_sha256"]
        fixed = {lookup[i] for i in record["heavy_global_ids"]}
        cut = helpers.derive_cut(
            exact, rows, shifted, read(dual_path), fixed, len(ordinary), len(heavy)
        )
        assert cut is not None and cut["dual"]["proves_infeasible"]
        norm = max(abs(weight) for _, weight in cut["dual"]["weights"])
        assert norm <= cut["denominator"] == 1000000
        cut.update(
            id=f"g5-whole-link-rank{record['rank']:04d}", graph_index=5,
            family_sha256=manifest["family_sha256"],
            source_heavy_global_ids=record["heavy_global_ids"],
            source_heavy_sha256=record["heavy_sha256"],
            source_shifted_rows_sha256=record["shifted_rows_sha256"],
            numerical_dual_path=record["dual_path"],
            numerical_dual_sha256=record["dual_sha256"],
            maximum_signed_row_weight=norm, source_objective=record["objective"],
        )
        new.append(cut)
    all_cuts = old["cuts"] + new
    total = 720 + len(new)
    assert len(all_cuts) == len({cut["id"] for cut in all_cuts}) == total
    assert len({tuple(cut["source_heavy_global_ids"]) for cut in all_cuts}) == total
    assert all(cut["graph_index"] == 5 for cut in all_cuts)
    previous = screen["neighborhoods"]["whole-link"]
    assert previous["registry_safe_states"] == 46436
    assert previous["combined_positive"] == 42940 and previous["combined_unexcluded"] == 3496
    RAW.mkdir()
    (RAW / "extract-frozen.py").write_bytes(Path(__file__).read_bytes())
    bundle = {
        "graph_index": 5, "hub_excesses": [2, 0, 0, 0, 0, 2],
        "six_row_changes": changes, "family_sha256": manifest["family_sha256"],
        "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "heavy_global_ids": heavy_global, "count": total, "prior_count": 720,
        "new_count": len(new), "prior_bundle_sha256": sha(old_path),
        "new_source_result_sha256": sha(POOL / "result.json"),
        "source_sha256": sha(__file__), "cuts": all_cuts, "optimization_calls": 0,
        "scope": "Every plane is conditional on graph g5. The 353 broad planes stay separate.",
    }
    bundle_path = RAW / "all-g5-cuts.json"
    dump(bundle_path, bundle)
    compact = copy.deepcopy(bundle)
    for cut in compact["cuts"]:
        cut["ordinary_coefficients"] = "derived-from-signed-rows"
        cut["coefficients"] = "derived-from-signed-rows"
    archive = {
        "format": "g5-signed-row-compact-v1", "original_sha256": sha(bundle_path),
        "original_bytes": bundle_path.stat().st_size, "unconditional_rows": rows,
        "bundle": compact,
    }
    compact_path = HERE / "all-g5-cuts.compact.json.gz"
    compact_path.write_bytes(gzip.compress(json.dumps(archive).encode(), mtime=0))
    assert restore.restore(compact_path) == bundle_path.read_bytes()
    minimum = min(new, key=lambda cut: Fraction(*cut["dual"]["gap"]))
    report = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "bundle_path": str(bundle_path.relative_to(ROOT)),
        "bundle_sha256": sha(bundle_path), "bundle_bytes": bundle_path.stat().st_size,
        "compact_path": str(compact_path.relative_to(ROOT)),
        "compact_sha256": sha(compact_path), "compact_roundtrip_passed": True,
        "graph_index": 5, "family_sha256": manifest["family_sha256"],
        "prior_planes": 720, "new_positive_certificates": len(new),
        "total_graph_specific_planes": total, "finite_whole_link_states": 46436,
        "prior_positive_envelope_states": 42940,
        "evaluated_positive_source_certificates": len(new),
        "unexamined_pool_states": 3496 - len(new),
        "finite_whole_link_exclusion_pending_independent_replay": len(new) == 3496,
        "minimum_new_source_gap": minimum["dual"]["gap"],
        "minimum_new_source_gap_id": minimum["id"],
        "input_files": input_files, "optimization_calls": 0,
        "scope": "Exact source arithmetic pending independent replay. Only the evaluated "
        "fixed-g5 whole-link states; no elastic optimum or global covering lower-bound claim.",
    }
    dump(HERE / "result.json", report)
    print(json.dumps({key: value for key, value in report.items() if key != "input_files"}))


if __name__ == "__main__":
    main()
