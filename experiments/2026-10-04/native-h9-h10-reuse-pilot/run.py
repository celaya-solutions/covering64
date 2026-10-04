# Document:    H9 H10 Reused Native Pilot and Saved Six Cap Classifier
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      17504f9cd022ca134aa1d39bf50f737819346f6acc1b41ad0a363c6af5485e5f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Delegate to the frozen five-cap driver, then classify only its saved records."""

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/native-h9-h10-reuse-pilot-20261004"
BASE = HERE.parent / "native-five-core-record-pilot/run.py"
BASE_SHA = "c0052cbf52dc40eb3547d40df7c619e8187698e932541180d7101a3133f03ba3"
BUDGET = {
    "max_runs": 2,
    "seconds_per_run": 300,
    "seeds": [2026105901, 2026105902],
    "watchdog_seconds": 315,
    "termination_grace_seconds": 5,
    "simultaneous_processes": 1,
    "stop_after_first_complete_at_most_64": True,
    "unused_budget_reallocated": False,
    "relaunch": False,
}


def base_module():
    spec = importlib.util.spec_from_file_location("unchanged_five_cap_driver", BASE)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    assert base.sha(BASE) == BASE_SHA, "frozen driver changed"
    # Only output locations and the declared fresh seed list change.
    base.HERE = HERE
    base.RAW = RAW
    base.BUDGET = BUDGET
    return base


def classify_saved(row, sixth):
    overlap = len(set(row["ids"]) & set(sixth["ids"]))
    exact64 = row["metrics"]["cardinality"] == 64
    sixth_pass = overlap <= sixth["threshold"] if exact64 else None
    six_pass = bool(row["cap_admissible"] and sixth_pass)
    qualified = row["weak_qualified"] and six_pass
    weak = row["weak_metrics"]
    return {
        "path": row["path"],
        "sha256": row["sha256"],
        "role": row.get("role", "initial"),
        "ids": row["ids"],
        "metrics": row["metrics"],
        "weak_metrics": weak,
        "sixth_named_overlap": overlap,
        "sixth_named_cap_applies": exact64,
        "sixth_named_cap_pass": sixth_pass,
        "six_named_caps_pass": six_pass,
        "weak_six_cap_qualified": qualified,
        "qualified_rank": [weak["holes"], weak["D2max"]] if qualified else None,
        "complete_at_most64": row["metrics"]["holes"] == 0
        and row["metrics"]["cardinality"] <= 64
        and row["package"]["valid"]
        and row["standalone"]["valid"],
    }


def write_saved_classification(base, manifest):
    producer_path = HERE / "result.json"
    producer = json.loads(producer_path.read_text())
    assert producer["manifest_sha256"] == base.sha(HERE / "manifest.json")
    assert all(run["validation_passed"] for run in producer["runs"])
    initial_fallbacks = []
    for initial in manifest["initial_partials"]:
        assert base.sha(ROOT / initial["path"]) == initial["sha256"], "initial witness changed"
        classified = classify_saved(initial, manifest["sixth_cap"])
        assert classified["weak_six_cap_qualified"], "initial eligible fallback lost"
        initial_fallbacks.append({"seed": initial["seed"], **classified})
    references = []
    for run in producer["runs"]:
        for row in run["snapshots"]:
            assert base.sha(ROOT / row["path"]) == row["sha256"], "saved witness changed"
            references.append({"seed": run["seed"], **classify_saved(row, manifest["sixth_cap"])})
    families = {}
    for row in references:
        if row["sha256"] in families:
            old = families[row["sha256"]]
            assert old["ids"] == row["ids"] and old["metrics"] == row["metrics"]
        else:
            families[row["sha256"]] = row
    qualified = [row for row in families.values() if row["weak_six_cap_qualified"]]
    best = (
        min(qualified, key=lambda row: (*row["qualified_rank"], tuple(row["ids"])))
        if qualified
        else None
    )
    output = {
        "passed": True,
        "producer_result_sha256": base.sha(producer_path),
        "manifest_sha256": base.sha(HERE / "manifest.json"),
        "classifier_sha256": base.sha(__file__),
        "sixth_cap_proof_sha256": manifest["sixth_cap"]["independent_review_sha256"],
        "initial_eligible_fallbacks": initial_fallbacks,
        "initial_fallback_scope": "Both preserved input witnesses, including an unlaunched "
        "second start after an early cover. These are not counted as native saved references.",
        "references": references,
        "distinct_families": list(families.values()),
        "reference_count": len(references),
        "distinct_family_count": len(families),
        "weak_six_cap_distinct_count": len(qualified),
        "best_saved_weak_six_cap_family": best,
        "complete_at_most64": any(row["complete_at_most64"] for row in references),
        "scope": "Postclassification of saved record and final files only. No claim to "
        "the best six-cap state in the live walk. Live five-cap buckets and "
        "unconditional complete-family bucket are unchanged. Named images only.",
    }
    base.dump(HERE / "saved-six-cap-classification.json", output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--gate-sha256", required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    base = base_module()
    assert base.sha(args.gate) == args.gate_sha256, "gate changed"
    gate = json.loads(args.gate.read_text())
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert gate.get("passed") is True and gate.get("decision") == "GO", "independent GO required"
    for key, expected in {
        "manifest_sha256": base.sha(HERE / "manifest.json"),
        "runner_sha256": base.sha(__file__),
        "base_runner_sha256": BASE_SHA,
        "binary_sha256": manifest["binary_sha256"],
        "initial_sha256s": [row["sha256"] for row in manifest["initial_partials"]],
    }.items():
        assert gate.get(key) == expected, f"gate binding {key}"
    assert not (HERE / "saved-six-cap-classification.json").exists(), "already classified"
    base.main(args.gate.resolve())
    write_saved_classification(base, manifest)


if __name__ == "__main__":
    main()
