# Document:    Independent Fixed-g1 Presolve Diagnostic Delta Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bind the previously reconstructed model and audit the two parameter deltas."""

import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import sat_parameters_pb2

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "g1-master-presolve-diagnostic"


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parameters(presolve):
    return sat_parameters_pb2.SatParameters(
        max_time_in_seconds=10, num_search_workers=1, random_seed=2026104070,
        randomize_search=True, log_search_progress=True, log_to_stdout=False,
        cp_model_presolve=presolve
    )


def main():
    assert not (HERE / "audit.json").exists()
    manifest = read(SOURCE / "manifest.json")
    assert manifest["source_sha256"] == sha(SOURCE / "run.py")
    for path, expected in manifest["input_files"].items():
        assert sha(ROOT / path) == expected
    prior = read(DAY / "g1-nearest-master/manifest.json")
    gate_path = DAY / "g1-nearest-master-independent/audit.json"
    prior_gate = read(gate_path)
    post_path = DAY / "g1-nearest-master-independent/postcheck.json"
    post = read(post_path)
    assert prior_gate["passed"] and post["passed"]
    assert prior_gate["manifest_sha256"] == sha(DAY / "g1-nearest-master/manifest.json")
    assert post["gate_sha256"] == sha(gate_path)
    assert post["result_sha256"] == sha(DAY / "g1-nearest-master/result.json")
    assert manifest["model_sha256"] == manifest["original_model_sha256"] == prior["master_sha256"]
    assert manifest["model_sha256"] == prior_gate["master_sha256"]
    assert sha(ROOT / manifest["model_path"]) == manifest["model_sha256"]
    original_bytes = (ROOT / prior["master_path"]).read_bytes()
    assert (ROOT / manifest["model_path"]).read_bytes() == original_bytes
    for field in ("graph_index", "family_sha256", "baseline_elastic_objective",
                  "baseline_heavy_global_ids", "ordinary_global_ids", "heavy_global_ids"):
        assert manifest[field] == prior[field]
    assert manifest["budgets"] == {
        "master_calls": 2, "seconds_per_master": 10,
        "lp_calls_per_distinct_accepted_tuple": 1, "seconds_per_lp": 1,
        "maximum_lp_calls": 2, "workers": 1, "master_seed": 2026104070, "lp_seed": 2026104
    }
    assert len(manifest["cases"]) == 2
    checked = []
    for case, (name, presolve) in zip(
        manifest["cases"], (("normal-presolve", True), ("presolve-off", False)), strict=True
    ):
        assert case["name"] == name and case["cp_model_presolve"] is presolve
        assert case["master_seconds"] == 10 and case["worker_count"] == 1
        assert case["seed"] == 2026104070 and case["completion_lp_seconds"] == 1
        assert sha(ROOT / case["parameters_path"]) == case["parameters_sha256"]
        actual = text_format.Parse((ROOT / case["parameters_path"]).read_text(),
                                  sat_parameters_pb2.SatParameters())
        expected = parameters(presolve)
        assert actual.SerializeToString(deterministic=True) == expected.SerializeToString(
            deterministic=True
        )
        checked.append({"name": name, "parameters_sha256": case["parameters_sha256"]})
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": sha(__file__),
        "source_sha256": sha(SOURCE / "run.py"),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "prior_gate_sha256": sha(gate_path), "prior_postcheck_sha256": sha(post_path),
        "model_sha256": manifest["model_sha256"], "identical_checked_model": True,
        "graph_index": 1, "family_sha256": manifest["family_sha256"], "cases": checked,
        "source_review": [
            "Two ten-second calls; same276-variable/1977-row model and fixed objective",
            "Same single worker and seed2026104070; only explicit presolve Boolean differs",
            "All four registry links checked before any LP; rejected links saved",
            "One1-second LP per distinct admitted tuple; duplicates reuse the saved result",
            "No learned cuts or registry nogoods modify either diagnostic model",
            "Numerical zero triggers exact rational recovery attempts and stops diagnostic",
            "UNKNOWN results remain inconclusive",
        ],
        "scope": "Preparation delta gate only; no optimization or global bound.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
