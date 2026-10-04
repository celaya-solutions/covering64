# Document:    Independent Continued Fixed-g1 Master Delta Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay the diagnostic cut and nogood, then reconstruct the full continued master."""

import ast
import importlib.util
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "g1-nearest-master-continuation"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load(DAY / "g1-nearest-master-independent/check.py", "independent_g1_master_delta")
exact = load(DAY / "g1-whole-link-certificates-independent/check.py", "independent_g1_delta_cut")
ind, read = base.ind, base.read


def encoded(proto):
    return proto.SerializeToString(deterministic=True)


def main():
    assert not (HERE / "audit.json").exists()
    manifest = read(SOURCE / "manifest.json")
    additions = read(SOURCE / "diagnostic-additions.json")
    assert manifest["source_sha256"] == ind.sha(SOURCE / "run.py")
    for collection in (manifest["input_files"], additions["input_files"]):
        for path, expected in collection.items():
            assert ind.sha(ROOT / path) == expected
    prior = read(DAY / "g1-nearest-master/manifest.json")
    prior_gate_path = DAY / "g1-nearest-master-independent/audit.json"
    prior_gate = read(prior_gate_path)
    assert prior_gate["passed"] and prior_gate["manifest_sha256"] == ind.sha(
        DAY / "g1-nearest-master/manifest.json"
    )
    for field in ("graph_index", "hub_excesses", "hub_pair_targets", "family_sha256",
                  "six_row_changes", "heavy_global_ids", "ordinary_global_ids",
                  "unconditional_rows_sha256", "baseline_heavy_global_ids",
                  "baseline_elastic_objective", "baseline_record", "objective"):
        assert manifest[field] == prior[field]
    blocks, anchors, ordinary, heavy, rows = ind.basis()
    gids = [blocks.index(block) for block in heavy]
    assert gids == manifest["heavy_global_ids"]
    support_o = [[r for r, row in enumerate(rows) if i in row[0]] for i in range(len(ordinary))]
    support_h = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(len(heavy))]
    cut, nogood = additions["cut"], additions["nogood"]
    assert additions["family_sha256"] == manifest["family_sha256"]
    assert additions["graph_index"] == manifest["graph_index"] == 1
    gap = exact.verify_cut(cut, rows, support_o, support_h, gids, manifest["family_sha256"])
    assert [gap.numerator, gap.denominator] == [337849, 25000]
    diagnostic_path = DAY / "g1-master-presolve-diagnostic/result.json"
    diagnostic = read(diagnostic_path)
    post_path = DAY / "g1-master-presolve-diagnostic-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"] and post["result_sha256"] == ind.sha(diagnostic_path)
    rejected, accepted = diagnostic["cases"]
    assert rejected["name"] == "normal-presolve" and accepted["name"] == "presolve-off"
    assert cut["source_heavy_global_ids"] == accepted["heavy_global_ids"]
    for label in ("heavy_sha256", "shifted_rows_sha256"):
        assert cut[f"source_{label}"] == accepted[label]
    assert cut["numerical_dual_path"] == accepted["dual_path"]
    assert cut["numerical_dual_sha256"] == accepted["dual_sha256"]
    assert ind.sha(ROOT / accepted["dual_path"]) == cut["numerical_dual_sha256"]
    assert cut["source_objective"] == accepted["lp"]["objective"] == 13.514017967610794
    base.validate_nogood(nogood, blocks, anchors, gids)
    assert nogood["heavy_global_ids"] == [10, 11, 15, 27, 35, 46, 69]
    assert nogood["registry"]["representative"] == "cycle-028"
    assert nogood["anchor_group_zero_based"] == 0
    assert set(nogood["heavy_global_ids"]) <= set(rejected["heavy_global_ids"])
    rejection_path = ROOT / (
        "experiments/scratch/g1-master-presolve-diagnostic-20261004/normal-presolve/registry.json"
    )
    assert ind.sha(rejection_path) == rejected["registry_sha256"]
    receipt = read(rejection_path)
    assert nogood["registry"] == receipt["links"][0]
    assert ind.validate_receipt(tuple(blocks[i] for i in rejected["heavy_global_ids"]), receipt)
    initial_nogoods = read(ROOT / manifest["nogoods_path"])
    assert initial_nogoods == read(ROOT / prior["nogoods_path"]) + [nogood]
    assert ind.sha(ROOT / manifest["nogoods_path"]) == manifest["nogoods_sha256"]
    certificate = read(DAY / "g1-whole-link-certificates-independent/audit.json")
    conditional = read(ROOT / certificate["bundle_path"])["cuts"] + [cut]
    broad = read(base.PLAN / "broad-cuts-reference.json")["cuts"]
    expected = base.master(heavy, anchors, gids, broad + conditional, initial_nogoods,
                           manifest["baseline_heavy_global_ids"])
    actual = text_format.Parse((ROOT / manifest["master_path"]).read_text(),
                              cp_model_pb2.CpModelProto())
    assert encoded(actual) == encoded(expected)
    assert ind.sha(ROOT / manifest["master_path"]) == manifest["master_sha256"]
    assert len(actual.variables) == 276 and len(actual.constraints) == 1979
    old = text_format.Parse((ROOT / prior["master_path"]).read_text(), cp_model_pb2.CpModelProto())
    assert manifest["previous_model_sha256"] == prior["master_sha256"]
    delta = Counter(map(encoded, actual.constraints)) - Counter(map(encoded, old.constraints))
    removed = Counter(map(encoded, old.constraints)) - Counter(map(encoded, actual.constraints))
    assert not removed and sum(delta.values()) == 2
    assert manifest["delta"] == {"conditional_g1_cuts": 1, "g1_registry_nogoods": 1}
    assert len(conditional) == manifest["conditional_g1_cut_count"] == 1001
    assert len(initial_nogoods) == manifest["initial_registry_nogoods"] == 20
    params = text_format.Parse((ROOT / manifest["parameters_path"]).read_text(),
                              sat_parameters_pb2.SatParameters())
    assert ind.sha(ROOT / manifest["parameters_path"]) == manifest["parameters_sha256"]
    assert params == sat_parameters_pb2.SatParameters(
        max_time_in_seconds=5, num_search_workers=1, random_seed=2026104070,
        randomize_search=True, cp_model_presolve=False, log_search_progress=True,
        log_to_stdout=False
    )
    assert manifest["budget"] == {
        "admitted_lps": 50, "master_proposals": 100, "each_master_seconds": 5,
        "each_lp_seconds": 1, "combined_solver_seconds": 120, "wall_seconds": 160,
        "workers": 1, "seed": 2026104070, "cp_model_presolve": False,
        "unknown_policy": "Record UNKNOWN then continue with the next deterministic seed."
    }
    old_tree, new_tree = ast.parse((DAY / "g1-nearest-master/run.py").read_text()), ast.parse(
        (SOURCE / "run.py").read_text()
    )
    old_defs = {n.name: n for n in old_tree.body if isinstance(n, ast.FunctionDef)}
    new_defs = {n.name: n for n in new_tree.body if isinstance(n, ast.FunctionDef)}
    for name in ("load", "dump", "link_nogood", "build"):
        assert ast.dump(old_defs[name]) == ast.dump(new_defs[name])
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": ind.sha(__file__),
        "source_sha256": ind.sha(SOURCE / "run.py"),
        "manifest_sha256": ind.sha(SOURCE / "manifest.json"),
        "additions_sha256": ind.sha(SOURCE / "diagnostic-additions.json"),
        "prior_gate_sha256": ind.sha(prior_gate_path),
        "diagnostic_postcheck_sha256": ind.sha(post_path),
        "master_sha256": manifest["master_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "model_variables": 276, "model_rows": 1979, "removed_rows": 0, "added_rows": 2,
        "exact_diagnostic_gap": [gap.numerator, gap.denominator],
        "registry_nogood_ids": nogood["heavy_global_ids"],
        "source_review": [
            "Original master rows and fixed baseline objective preserved; no radius",
            "New diagnostic exact cut and cycle-028 nogood remain graph-one only",
            "UNKNOWN records are saved and continue at the next deterministic seed",
            "One worker, five seconds per master, one second per accepted LP",
            "Caps50 admitted LPs/100 proposals/120solver/160wall",
            "Pre-master guards113.8solver/151wall; pre-LP guards118.9solver/156wall",
            "Registry precedes LP and dynamic cuts/nogoods use fixed graph-one rows",
            "Numerical zero and unresolved exact separation stop the run",
        ],
        "scope": "Independent preparation and one exact fixed-g1 separation; no global bound.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
