# Document:    H9 H10 Native Reuse Pilot Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      ffa390b429bf252ce348c3720eef072e8090d785cb9fe934ec4e8540b4c62b49
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Pin existing binaries and fresh inputs; run only zero/eight-step input controls."""

import json
import subprocess
import time

from run import BASE, BASE_SHA, BUDGET, HERE, RAW, ROOT, base_module, classify_saved

DAY = HERE.parent
PRIOR = DAY / "native-five-core-record-pilot"
OLD_RAW = ROOT / "experiments/scratch/native-five-core-record-pilot-20261004"
PROOF = DAY / "h9-start-structural-profile/profile.json"
REVIEW = DAY / "h9-start-structural-independent/review.json"
STARTS = [
    (
        2026105901,
        "weak-pair-h9-d23-neutral-queue-runtime-independent/family-a0a737c4010f68fc.txt",
        "a0a737c4010f68fcd5bfba8ccc7c20b4b8d9f06a96bb0086c7a63dbfc43f5ecc",
        (9, 19, 27),
        59,
    ),
    (
        2026105902,
        "native-five-core-record-pilot/seed-2026105602/search-final-weak64.txt",
        "85f6e38a537691442cf6097a68b1364a755ac1ba8312d61adfc88c26abb6a90e",
        (10, 22, 32),
        0,
    ),
]
PINS = {
    PRIOR / "manifest.json": "32d536037298694fea21fa8207efb328851d9ede135cae2c770833863891ee86",
    PRIOR / "result.json": "5c11a6ee25247bc7b3caf707ae05aba8387d2c5c5a8e26642a483397b451c8f3",
    BASE: BASE_SHA,
    DAY / "native-five-core-record-runtime-independent/postcheck.json": (
        "5d79cdfc0820086e14281538398506c674ce9ecb241e1b3b3739b7aabb067862"
    ),
    DAY / "native-five-core-record-pilot-independent/gate.json": (
        "10477409a380ff6fc6a912b6349c7e8e418dcc8b3afab84fe3fab0f5f8eb0e59"
    ),
    DAY / "weak-pair-h9-d23-neutral-queue/result.json": (
        "2dc86eb41830d6647ad8dbc35b8211cb938a70f0f17c04bf68cd3042963c3811"
    ),
    DAY / "weak-pair-h9-d23-neutral-queue-runtime-independent/postcheck.json": (
        "89142fc4522bf21bbf4c34dd06a855113474b54d73b6f793250d207d72ec47f6"
    ),
    DAY / "weak-pair-h9-six-cap-inventory-independent/inventory.json": (
        "de1653eca6de927e511efd316d0893f870e9e8731afc6bd5091a72042c287b55"
    ),
    PROOF: "317797810b797e341ce62992334a8816e46e9051d33d41ab60c8078e0ee15d38",
    DAY / "h9-start-structural-profile/check.py": (
        "368c5def28ae21250f162fb6642fbb947cda6ce165bfc01d655b2c6a1d963b92"
    ),
    REVIEW: "a6ed0173e9e61a700bbe77d3b3599fcdcd34f593f49ef392b2f53721d9cb1c6c",
    DAY / "h9-start-structural-independent/check.py": (
        "03ba2e193809c1e35d32ffc1a75bc840adf8bfc152fdf67ba24b495ee169aefe"
    ),
    OLD_RAW / "search": "079eaf578f1e7b29c4408185e77953b4d337d722e428e12b7c653392e1c2163c",
    OLD_RAW / "control-zero": "6a3c9a15b8a4421f098873e115ac3fd999fe2917659e581c549100a8aef70c0f",
    OLD_RAW / "control-eight": "c04381c2ec6fb18c4441764e52ee25f0e0d4b075691b748e887634230e959515",
    DAY / "weak-pair-h9-six-cap-inventory-independent/proof-binding.json": (
        "c98db57b30c6bc0fe12d64eb7b794d63d7a0906663f5a387858bba9a82fb71d6"
    ),
    DAY / "weak-pair-h9-six-cap-inventory-independent/next-pilot-starts.json": (
        "5ffc16c887a338c8eff63cf38709257b2d9b785baa404920964e5f1d105f46c0"
    ),
}


def main():
    base = base_module()
    sha, dump = base.sha, base.dump
    assert not (HERE / "manifest.json").exists() and not RAW.exists(), "preserve prepared pilot"
    inputs = {str(path.relative_to(ROOT)): digest for path, digest in PINS.items()}
    for path, digest in PINS.items():
        assert sha(path) == digest, f"pinned artifact changed: {path}"
    previous = json.loads((PRIOR / "manifest.json").read_text())
    proof = json.loads(PROOF.read_text())
    review = json.loads(REVIEW.read_text())
    assert proof["passed"] and review["passed"] and review["radius_four_excluded"]
    assert review["certificate_sha256"] == sha(PROOF)
    assert review["initial_sha256"] == proof["initial_sha256"]
    assert review["exact64_named_initial_maximum_overlap"] == 59
    start_receipt = json.loads(
        (DAY / "weak-pair-h9-six-cap-inventory-independent/next-pilot-starts.json").read_text()
    )
    assert start_receipt["passed"] and start_receipt["proof_review_sha256"] == sha(REVIEW)
    sixth = {
        "ids": proof["initial_ids"],
        "threshold": 59,
        "initial_family_sha256": proof["initial_sha256"],
        "certificate_path": str(PROOF.relative_to(ROOT)),
        "certificate_sha256": sha(PROOF),
        "independent_review_path": str(REVIEW.relative_to(ROOT)),
        "independent_review_sha256": sha(REVIEW),
        "application": "Only saved exact64 record/final postclassification; no live filter.",
    }
    assert len(sixth["ids"]) == len(set(sixth["ids"])) == 64
    for group in ("source_files", "input_files", "raw_files"):
        for path, digest in previous[group].items():
            assert path not in inputs or inputs[path] == digest, "conflicting inherited hash"
            inputs[path] = digest
    for path, digest in inputs.items():
        assert sha(ROOT / path) == digest, f"inherited artifact changed: {path}"
    cores = previous["core_rows"]
    incumbent = ROOT / previous["incumbent_path"]
    incumbent_check = base.checked(incumbent, cores)
    assert json.loads(json.dumps(incumbent_check)) == previous["initial_complete"]
    initials = []
    for seed, relative, digest, expected, overlap in STARTS:
        path = DAY / relative
        assert sha(path) == digest
        row = base.checked(path, cores)
        weak = row["weak_metrics"]
        assert (weak["holes"], weak["D2max"], weak["D2sum"]) == expected
        assert row["cap_admissible"] and row["weak_qualified"]
        classified = classify_saved(row, sixth)
        assert classified["weak_six_cap_qualified"]
        assert classified["sixth_named_overlap"] == overlap
        row["seed"] = seed
        initials.append(row)
        inputs[str(path.relative_to(ROOT))] = digest
    RAW.mkdir(parents=True)
    controls = []
    for initial in initials:
        for steps, binary_name in ((0, "control-zero"), (8, "control-eight")):
            directory = RAW / f"control-{initial['seed']}-{steps}"
            directory.mkdir()
            binary = OLD_RAW / binary_name
            command = [
                str(binary),
                str(incumbent),
                str(ROOT / initial["path"]),
                str(initial["seed"]),
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
            receipt = base.validate(
                directory,
                process.stdout,
                process.returncode,
                process.stderr,
                elapsed,
                cores,
                initial["seed"],
                initial,
                steps,
            )
            assert not receipt["success"] and receipt["final"]["iterations"] == steps
            if steps == 8:
                assert receipt["final"]["fallbacks"] == 4
                assert receipt["final"]["min_cardinality"] == 62
            assert {
                row["role"]
                for row in receipt["snapshots"]
                if row["role"] in ("complete", "raw64", "admissible64", "weak64")
            } == {"complete", "raw64", "admissible64", "weak64"}
            initial_classification = classify_saved(initial, sixth)
            assert initial_classification["weak_six_cap_qualified"]
            receipt.update(
                {
                    "seed": initial["seed"],
                    "steps": steps,
                    "command": command,
                    "binary_sha256": sha(binary),
                    "elapsed_seconds": elapsed,
                    "initial_postclassification": initial_classification,
                }
            )
            controls.append(receipt)
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "bounded_control_calls": 4,
            "step_limits": [0, 8],
            "timed_optimization_launched": False,
            "native_search_calls": 0,
            "unchanged_base_runner_sha256": BASE_SHA,
            "controls": controls,
            "runner_sha256": sha(HERE / "run.py"),
            "prepare_sha256": sha(__file__),
            "scope": "Existing sanitizer binaries, new inputs and seeds only; no rebuild.",
        },
    )
    manifest = {
        "document": "H9 H10 Reused Native Pilot Manifest",
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
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path) for path in RAW.rglob("*") if path.is_file()
        },
        "binary_path": previous["binary_path"],
        "binary_sha256": previous["binary_sha256"],
        "incumbent_path": previous["incumbent_path"],
        "initial_complete": incumbent_check,
        "initial_partials": initials,
        "core_rows": cores,
        "core_thresholds": previous["core_thresholds"],
        "sixth_cap": sixth,
        "controls_sha256": sha(HERE / "controls.json"),
        "initial_six_cap_classification": [classify_saved(row, sixth) for row in initials],
        "six_cap_postclassification": "Saved record and final files only; not best over live walk.",
        "postclassification_tie_break": "(holes,D2max,full IDs), D2sum metadata only",
        "historical_comparison": "Frozen driver retains its explicitly scoped old205-family "
        "inventory baseline; new start and six-cap comparisons are separate.",
        "current_qualified_start_rank": [9, 19],
        "weak_live_record_policy_unchanged": True,
        "native_recompilation": False,
        "timed_optimization_launched": False,
        "scope": "Two fresh starts for the frozen five-cap native driver and binary. "
        "All live moves, weights, RNG, cardinalities, record buckets and unconditional "
        "complete-cover stopping are unchanged. Sixth cap is saved-state analysis only.",
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
                "bounded_control_calls": 4,
            }
        )
    )


if __name__ == "__main__":
    main()
