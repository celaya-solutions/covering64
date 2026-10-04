# Document:    Raw H6 Native Reuse Pilot Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f24570553c7b63ca89b482b7f5beb938ec6e098ffa15e801b309d97814038777
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Pin one raw start; run only the authorized frozen zero/eight-step controls."""

import copy
import json
import subprocess
import time
from unittest.mock import patch

import run as wrapper
from run import BASE, BASE_SHA, BUDGET, HERE, RAW, ROOT, base_module, classify_saved

DAY = HERE.parent
PRIOR = DAY / "native-five-core-record-pilot"
OLD_RAW = ROOT / "experiments/scratch/native-five-core-record-pilot-20261004"
START = DAY / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
START_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
WEAK_FIXTURE = (
    DAY / "weak-pair-h9-d23-neutral-queue-runtime-independent/family-a0a737c4010f68fc.txt"
)
PINS = {
    PRIOR / "manifest.json": "32d536037298694fea21fa8207efb328851d9ede135cae2c770833863891ee86",
    BASE: BASE_SHA,
    START: START_SHA,
    WEAK_FIXTURE: "a0a737c4010f68fcd5bfba8ccc7c20b4b8d9f06a96bb0086c7a63dbfc43f5ecc",
    DAY / "h9-start-structural-profile/profile.json": (
        "317797810b797e341ce62992334a8816e46e9051d33d41ab60c8078e0ee15d38"
    ),
    DAY / "h9-start-structural-independent/review.json": (
        "a6ed0173e9e61a700bbe77d3b3599fcdcd34f593f49ef392b2f53721d9cb1c6c"
    ),
    DAY / "native-h9-h10-reuse-runtime-independent/postcheck.json": (
        "d3c7b5a61d8c689b0299030a83247480537f741e2161570a2fe698259a9b358a"
    ),
    DAY / "native-h9-h10-reuse-runtime-independent/raw-h6-first-run-independent.json": (
        "5c3e29456812491ac13e2dacdf1352848c141cc2722fc6fc24acfe53ce10a4f0"
    ),
    OLD_RAW / "search": "079eaf578f1e7b29c4408185e77953b4d337d722e428e12b7c653392e1c2163c",
    OLD_RAW / "control-zero": "6a3c9a15b8a4421f098873e115ac3fd999fe2917659e581c549100a8aef70c0f",
    OLD_RAW / "control-eight": "c04381c2ec6fb18c4441764e52ee25f0e0d4b075691b748e887634230e959515",
}


def main():
    base = base_module()
    sha, dump = base.sha, base.dump
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    assert BUDGET == {
        "max_runs": 1,
        "seconds_per_run": 300,
        "seeds": [2026106101],
        "watchdog_seconds": 315,
        "termination_grace_seconds": 5,
        "simultaneous_processes": 1,
        "stop_after_first_complete_at_most_64": True,
        "unused_budget_reallocated": False,
        "relaunch": False,
    }
    inputs = {str(path.relative_to(ROOT)): digest for path, digest in PINS.items()}
    previous = json.loads((PRIOR / "manifest.json").read_text())
    for group in ("source_files", "input_files", "raw_files"):
        for path, digest in previous[group].items():
            assert path not in inputs or inputs[path] == digest
            inputs[path] = digest
    for path, digest in inputs.items():
        assert sha(ROOT / path) == digest, path
    proof_path = DAY / "h9-start-structural-profile/profile.json"
    review_path = DAY / "h9-start-structural-independent/review.json"
    proof, review = json.loads(proof_path.read_text()), json.loads(review_path.read_text())
    assert proof["passed"] and review["passed"] and review["radius_four_excluded"]
    assert review["certificate_sha256"] == sha(proof_path)
    assert review["initial_sha256"] == proof["initial_sha256"]
    assert review["exact64_named_initial_maximum_overlap"] == 59
    sixth = {
        "ids": proof["initial_ids"],
        "threshold": 59,
        "initial_family_sha256": proof["initial_sha256"],
        "certificate_path": str(proof_path.relative_to(ROOT)),
        "certificate_sha256": sha(proof_path),
        "independent_review_path": str(review_path.relative_to(ROOT)),
        "independent_review_sha256": sha(review_path),
        "application": "Saved exact64 records/finals only; no new live filter.",
    }
    assert len(sixth["ids"]) == len(set(sixth["ids"])) == 64
    cores = previous["core_rows"]
    incumbent = ROOT / previous["incumbent_path"]
    complete = base.checked(incumbent, cores)
    assert json.loads(json.dumps(complete)) == previous["initial_complete"]
    initial = base.checked(START, cores)
    assert initial["sha256"] == START_SHA and initial["cap_admissible"]
    assert initial["weak_qualified"] is False
    weak = initial["weak_metrics"]
    assert (
        weak["holes"],
        weak["minimum_pair_count"],
        weak["D2max"],
        weak["D2sum"],
        weak["D3"],
        weak["D4"],
    ) == (6, 4, 14, 498, 80, 72)
    assert initial["metrics"] == {"cardinality": 64, "holes": 6, "core_overlaps": [0, 2, 2, 1, 0]}
    initial["seed"] = 2026106101
    raw_class = classify_saved(initial, sixth)
    assert raw_class["sixth_named_overlap"] == 0 and raw_class["six_named_caps_pass"]
    assert raw_class["weak_six_cap_qualified"] is False and raw_class["qualified_rank"] is None
    complete_class = classify_saved(complete, sixth)
    assert complete_class["sixth_named_cap_pass"] is None
    assert (
        complete_class["metrics"]["cardinality"] == 65 and not complete_class["complete_at_most64"]
    )
    weak_fixture = base.checked(WEAK_FIXTURE, cores)
    assert classify_saved(weak_fixture, sixth)["weak_six_cap_qualified"]

    RAW.mkdir(parents=True)
    controls = []
    for steps, binary_name in ((0, "control-zero"), (8, "control-eight")):
        directory = RAW / f"control-2026106101-{steps}"
        directory.mkdir()
        binary = OLD_RAW / binary_name
        command = [
            str(binary),
            str(incumbent),
            str(START),
            "2026106101",
            "300",
            str(directory / "search"),
        ]
        started = time.monotonic()
        process = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, check=False, timeout=30
        )
        elapsed = time.monotonic() - started
        (directory / "stdout.jsonl").write_text(process.stdout)
        (directory / "stderr.txt").write_text(process.stderr)
        checked = base.validate(
            directory,
            process.stdout,
            process.returncode,
            process.stderr,
            elapsed,
            cores,
            2026106101,
            initial,
            steps,
        )
        assert not checked["success"] and checked["final"]["iterations"] == steps
        events = [json.loads(line) for line in process.stdout.splitlines()]
        first = [e for e in events if e["event"] == "record" and e["mutations"] == 0]
        assert [e["role"] for e in first] == ["complete", "raw64", "admissible64"]
        if steps == 0:
            assert checked["final"]["weak64"] is None and checked["final"]["weak_D2max"] is None
            assert not (directory / "search-final-weak64.txt").exists()
        if steps == 8:
            assert checked["final"]["fallbacks"] == 4 and checked["final"]["min_cardinality"] == 62
        checked.update(
            {
                "steps": steps,
                "seed": 2026106101,
                "command": command,
                "binary_sha256": sha(binary),
                "elapsed_seconds": elapsed,
                "initial_weak_bucket_present": False,
            }
        )
        controls.append(checked)

    # Metadata fixtures test classification only; they are not native discoveries.
    classifier_controls = []
    temporary_manifest = {
        "initial_partials": [initial],
        "initial_complete": complete,
        "sixth_cap": sixth,
    }
    for name, snapshots in [
        ("no_weak_saved", controls[0]["snapshots"]),
        (
            "later_first_weak_fixture",
            [*controls[0]["snapshots"], {**weak_fixture, "role": "weak64"}],
        ),
    ]:
        folder = RAW / ("classifier-fixture-" + name)
        folder.mkdir()
        dump(folder / "manifest.json", temporary_manifest)
        dump(
            folder / "result.json",
            {
                "manifest_sha256": sha(folder / "manifest.json"),
                "runs": [{"validation_passed": True, "seed": 2026106101, "snapshots": snapshots}],
            },
        )
        with patch.object(wrapper, "HERE", folder):
            wrapper.write_saved_classification(base, temporary_manifest)
        classified = json.loads((folder / "saved-six-cap-classification.json").read_text())
        assert classified["initial_eligible_fallbacks"] == []
        assert len(classified["initial_raw_fallbacks"]) == 1
        assert classified["initial_raw_fallbacks"][0]["sha256"] == START_SHA
        assert classified["initial_raw_fallbacks"][0]["weak_six_cap_qualified"] is False
        assert classified["complete_incumbent_fallback"]["sha256"] == complete["sha256"]
        assert classified["complete_incumbent_fallback"]["sixth_named_cap_pass"] is None
        best = classified["best_saved_weak_six_cap_family"]
        assert (best is None) == (name == "no_weak_saved")
        if best is not None:
            assert best["sha256"] == weak_fixture["sha256"] and best["qualified_rank"] == [9, 19]
        assert classified["reference_count"] == len(snapshots)
        classifier_controls.append(
            {
                "case": name,
                "passed": True,
                "synthetic_assembly": True,
                "report_sha256": sha(folder / "saved-six-cap-classification.json"),
            }
        )
    # Both fifth/sixth cap verdicts are subordinate to an independently valid complete family.
    synthetic_complete = copy.deepcopy(initial)
    synthetic_complete["metrics"]["holes"] = 0
    synthetic_complete["package"]["valid"] = synthetic_complete["standalone"]["valid"] = True
    synthetic_complete["cap_admissible"] = False
    assert classify_saved(synthetic_complete, sixth)["complete_at_most64"] is True
    classifier_controls.append(
        {
            "case": "complete_before_caps_metadata_only",
            "passed": True,
            "synthetic_metadata_not_a_witness": True,
        }
    )
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "bounded_control_calls": 2,
            "step_limits": [0, 8],
            "timed_optimization_launched": False,
            "native_search_calls": 0,
            "unchanged_base_runner_sha256": BASE_SHA,
            "controls": controls,
            "classifier_controls": classifier_controls,
            "runner_sha256": sha(HERE / "run.py"),
            "prepare_sha256": sha(__file__),
            "scope": "Two existing zero/eight-step control binaries only; "
            "classifier fixtures are synthetic assemblies.",
        },
    )
    manifest = {
        "document": "Raw H6 Reused Native Pilot Manifest",
        "version": "v1.0.0",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "status": "PREPARED_NOT_RUN",
        "budget": BUDGET,
        "base_runner_path": str(BASE.relative_to(ROOT)),
        "base_runner_sha256": BASE_SHA,
        "prior_manifest_sha256": sha(PRIOR / "manifest.json"),
        "source_files": {
            str((HERE / name).relative_to(ROOT)): sha(HERE / name)
            for name in ("run.py", "prepare.py")
        },
        "input_files": {
            **inputs,
            **{
                str((HERE / name).relative_to(ROOT)): sha(HERE / name)
                for name in ("README.md", "controls.json")
            },
        },
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in RAW.rglob("*") if p.is_file()},
        "binary_path": previous["binary_path"],
        "binary_sha256": previous["binary_sha256"],
        "incumbent_path": previous["incumbent_path"],
        "initial_complete": complete,
        "initial_partials": [initial],
        "core_rows": cores,
        "core_thresholds": previous["core_thresholds"],
        "sixth_cap": sixth,
        "controls_sha256": sha(HERE / "controls.json"),
        "initial_six_cap_classification": [raw_class],
        "initial_weak_bucket_present": False,
        "initial_raw_fallback_sha256": START_SHA,
        "initial_eligible_weak_fallback_count": 0,
        "initial_raw_start_holes": 6,
        "historical_best_qualified_rank": [9, 19],
        "complete_incumbent_is_separate": True,
        "six_cap_postclassification": "Saved records/finals only; "
        "best qualified saved family may be null.",
        "historical_comparison": "Unchanged driver retains the old205-family baseline. "
        "Raw H6 and current known H9/D19 comparisons are separate.",
        "weak_live_record_policy_unchanged": True,
        "native_recompilation": False,
        "timed_optimization_launched": False,
        "scope": "One fresh raw-H6 start, weak-ineligible initially. Unchanged binary/driver/"
        "live moves/weights/RNG/objective/five-cap record policy. Sixth cap only classifies "
        "saved exact64 states; it does not recover omitted live states.",
    }
    for key in (
        "all_blocks",
        "triples",
        "labels",
        "block_order",
        "cost",
        "ranking",
        "tabu_tenure",
        "novelty_residue_threshold",
        "no_eligible_fallback",
        "decay",
        "trajectory_incumbent65",
        "source_algorithm",
        "upstream_revision",
        "initialization",
        "records",
        "core_policy",
        "weak_record_policy",
        "weak_record_hole_ceiling",
        "weak_record_ranking",
        "D2sum_role",
        "reused_kernel_hashes",
    ):
        manifest[key] = previous[key]
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "controls_sha256": sha(HERE / "controls.json"),
                "native_search_calls": 0,
                "bounded_control_calls": 2,
            }
        )
    )


if __name__ == "__main__":
    main()
