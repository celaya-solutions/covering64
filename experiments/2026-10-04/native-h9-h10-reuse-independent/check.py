# Document:    Independent Native H9 H10 Reuse Pilot Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1f23ffac2250d02004109ae18b369a332652063798499069b94c7b0b2ce671e2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Focused wrapper controls with fake saved reports; no search process launches."""

import ast
import copy
import hashlib
import importlib.util
import json
import tempfile
from itertools import combinations, product
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P = HERE.parent / "native-h9-h10-reuse-pilot"
RAW = ROOT / "experiments/scratch/native-h9-h10-reuse-independent-20261004"
MANIFEST_SHA = "13b26e00b3743ad33cbd94553079d1bb60b6fdf43b5f2bc79dd8ceab1c3f9241"
STARTS = HERE.parent / "weak-pair-h9-six-cap-inventory-independent/next-pilot-starts.json"
STARTS_SHA = "5ffc16c887a338c8eff63cf38709257b2d9b785baa404920964e5f1d105f46c0"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def classify_controls(wrapper, manifest):
    sixth = manifest["sixth_cap"]
    core = sixth["ids"]
    outside = [i for i in range(4368) if i not in core]
    baseline = manifest["initial_partials"][0]
    cases = []
    for size, overlap, five, weak, complete in product(
        [63, 64, 65], [58, 59, 60], [False, True], [False, True], [False, True]
    ):
        row = copy.deepcopy(baseline)
        row["ids"] = sorted(core[:overlap] + outside[: size - overlap])
        row["metrics"]["cardinality"] = size
        row["metrics"]["holes"] = 0 if complete else 9
        row["cap_admissible"] = five
        row["weak_qualified"] = weak
        row["package"]["valid"] = complete
        row["standalone"]["valid"] = complete
        if size != 64:
            row["weak_metrics"] = None
        classified = wrapper.classify_saved(row, sixth)
        expected_sixth = overlap <= 59 if size == 64 else None
        expected_qualified = size == 64 and five and weak and overlap <= 59
        assert classified["sixth_named_cap_applies"] is (size == 64)
        assert classified["sixth_named_cap_pass"] is expected_sixth
        assert classified["weak_six_cap_qualified"] is expected_qualified
        assert classified["complete_at_most64"] is (complete and size <= 64)
        if expected_qualified:
            assert classified["qualified_rank"] == [9, 19]
        else:
            assert classified["qualified_rank"] is None
        cases.append(
            {"size": size, "overlap": overlap, "five": five, "weak": weak, "complete": complete}
        )
    row = copy.deepcopy(baseline)
    before = wrapper.classify_saved(row, sixth)
    row["weak_metrics"]["D2sum"] += 1000
    after = wrapper.classify_saved(row, sixth)
    assert before["qualified_rank"] == after["qualified_rank"]
    for key in ["package", "standalone"]:
        row = copy.deepcopy(baseline)
        row["metrics"]["holes"] = 0
        row["package"]["valid"] = True
        row["standalone"]["valid"] = True
        row[key]["valid"] = False
        assert wrapper.classify_saved(row, sixth)["complete_at_most64"] is False
    baseline65 = wrapper.classify_saved(manifest["initial_complete"], sixth)
    assert baseline65["sixth_named_cap_pass"] is None
    assert baseline65["complete_at_most64"] is False
    return {
        "synthetic_postvalidation_matrix_cases": len(cases),
        "D2sum_rank_invariance": True,
        "both_complete_verifiers_required": True,
        "actual_65_block_baseline_has_no_sixth_cap_verdict": True,
    }


def report_controls(wrapper, manifest):
    original_here = wrapper.HERE
    results = []
    fake_base = SimpleNamespace(sha=sha, dump=dump)
    RAW.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="saved-", dir=RAW) as directory:
        temporary = Path(directory)
        wrapper.HERE = temporary
        dump(temporary / "manifest.json", manifest)
        first, second = copy.deepcopy(manifest["initial_partials"])

        def replay(snapshots, changed=None, passed=True):
            output = temporary / "saved-six-cap-classification.json"
            output.unlink(missing_ok=True)
            producer = {
                "manifest_sha256": sha(temporary / "manifest.json"),
                "runs": [
                    {"seed": first["seed"], "validation_passed": passed, "snapshots": snapshots}
                ],
                "skipped_seeds": [second["seed"]],
            }
            dump(temporary / "result.json", producer)
            wrapper.write_saved_classification(fake_base, manifest if changed is None else changed)
            return read(output)

        result = replay([])
        assert len(result["initial_eligible_fallbacks"]) == 2
        assert result["reference_count"] == 0 and result["best_saved_weak_six_cap_family"] is None
        assert {r["seed"] for r in result["initial_eligible_fallbacks"]} == {2026105901, 2026105902}
        results.append("both fallbacks preserved with no saved references")

        result = replay([first, copy.deepcopy(first), second])
        assert result["reference_count"] == 3 and result["distinct_family_count"] == 2
        assert result["weak_six_cap_distinct_count"] == 2
        assert result["best_saved_weak_six_cap_family"]["sha256"] == first["sha256"]
        assert len(result["initial_eligible_fallbacks"]) == 2
        results.append("saved references deduplicated; best rank and unlaunched fallback preserved")

        # Synthetic post-validation rows exercise selection; they are not cover witnesses.
        better = copy.deepcopy(second)
        better["weak_metrics"]["holes"] = 8
        better["weak_metrics"]["D2max"] = 99
        result = replay([first, better])
        assert result["best_saved_weak_six_cap_family"]["sha256"] == second["sha256"]
        results.append("holes precede D2max in saved-record selection")

        tied = copy.deepcopy(second)
        tied["weak_metrics"]["holes"] = 9
        tied["weak_metrics"]["D2max"] = 19
        tied["weak_metrics"]["D2sum"] = -999
        result = replay([first, tied])
        expected = min([first, tied], key=lambda row: tuple(row["ids"]))
        assert result["best_saved_weak_six_cap_family"]["sha256"] == expected["sha256"]
        results.append("full IDs break equal-rank ties; D2sum is not a tie-break")

        cases = []
        bad_initial = copy.deepcopy(manifest)
        bad_initial["initial_partials"][1]["sha256"] = "0" * 64
        cases.append(("unlaunched fallback hash changed", [first], bad_initial, True))
        bad_initial = copy.deepcopy(manifest)
        bad_initial["initial_partials"][1]["weak_qualified"] = False
        cases.append(("unlaunched fallback eligibility lost", [first], bad_initial, True))
        bad = copy.deepcopy(first)
        bad["sha256"] = "0" * 64
        cases.append(("saved witness hash changed", [bad], None, True))
        bad = copy.deepcopy(first)
        bad["metrics"]["holes"] += 1
        cases.append(("duplicate hash has different metrics", [first, bad], None, True))
        cases.append(("native validation failed", [first], None, False))
        for name, snapshots, changed, passed in cases:
            try:
                replay(snapshots, changed, passed)
            except AssertionError:
                results.append(name + ": rejected")
            else:
                raise AssertionError("accepted " + name)
    wrapper.HERE = original_here
    return results


def main():
    manifest = read(P / "manifest.json")
    assert sha(P / "manifest.json") == MANIFEST_SHA
    pins = {}
    for group in ["source_files", "input_files", "raw_files"]:
        for path, digest in manifest[group].items():
            assert sha(ROOT / path) == digest, path
            pins[path] = digest
    assert sha(ROOT / manifest["binary_path"]) == manifest["binary_sha256"]
    expected_budget = {
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
    assert manifest["budget"] == expected_budget
    prior = read(HERE.parent / "native-five-core-record-pilot/manifest.json")
    prior_gate_path = HERE.parent / "native-five-core-record-pilot-independent/gate.json"
    prior_gate = read(prior_gate_path)
    assert prior_gate["passed"] and prior_gate["decision"] == "GO"
    assert prior_gate["manifest_sha256"] == manifest["prior_manifest_sha256"]
    assert manifest["binary_sha256"] == prior["binary_sha256"]
    for key in [
        "core_rows",
        "core_thresholds",
        "weak_record_policy",
        "weak_record_ranking",
        "weak_record_hole_ceiling",
    ]:
        assert manifest[key] == prior[key]
    assert manifest["core_thresholds"] == [55, 55, 55, 55, 56]
    assert manifest["native_recompilation"] is False

    assert sha(STARTS) == STARTS_SHA
    independent_starts = read(STARTS)
    assert independent_starts["passed"]
    profile = read(ROOT / manifest["sixth_cap"]["certificate_path"])
    proof_path = ROOT / manifest["sixth_cap"]["independent_review_path"]
    assert sha(proof_path) == manifest["sixth_cap"]["independent_review_sha256"]
    assert read(proof_path)["passed"]
    assert (
        sha(ROOT / manifest["sixth_cap"]["certificate_path"])
        == manifest["sixth_cap"]["certificate_sha256"]
    )
    assert manifest["sixth_cap"]["threshold"] == 59
    assert manifest["sixth_cap"]["ids"] == profile["initial_ids"]
    assert manifest["sixth_cap"]["initial_family_sha256"] == profile["initial_sha256"]
    assert independent_starts["proof_review_sha256"] == sha(proof_path)
    universe = list(combinations(range(1, 17), 5))
    for initial, trusted in zip(
        manifest["initial_partials"], independent_starts["starts"], strict=True
    ):
        assert initial["seed"] == trusted["seed"]
        assert initial["sha256"] == trusted["sha256"] == sha(ROOT / initial["path"])
        assert initial["weak_metrics"]["cardinality"] == trusted["cardinality"] == 64
        assert {k: v for k, v in initial["weak_metrics"].items() if k != "cardinality"} == trusted[
            "metrics"
        ]
        assert initial["weak_qualified"] and initial["cap_admissible"]
        blocks = [
            tuple(map(int, s.split())) for s in (ROOT / initial["path"]).read_text().splitlines()
        ]
        assert len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks)
        assert [universe[i] for i in initial["ids"]] == blocks
        overlaps = [len(set(initial["ids"]) & set(core)) for core in manifest["core_rows"]]
        sixth = len(set(initial["ids"]) & set(manifest["sixth_cap"]["ids"]))
        assert overlaps[4] == trusted["fifth_core_overlap"]
        assert sixth == trusted["sixth_core_overlap"]
        assert all(n <= cap for n, cap in zip(overlaps, manifest["core_thresholds"], strict=True))
        assert sixth <= 59

    spec = importlib.util.spec_from_file_location("independent_reuse_wrapper", P / "run.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    assert wrapper.BUDGET == expected_budget
    assert wrapper.BASE_SHA == manifest["base_runner_sha256"] == sha(wrapper.BASE)
    base = wrapper.base_module()
    assert base.HERE == P and base.RAW == wrapper.RAW and base.BUDGET == expected_budget
    tree = ast.parse((P / "run.py").read_text())
    loader = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "base_module"
    )
    modified_base_attributes = [
        target.attr
        for n in ast.walk(loader)
        if isinstance(n, ast.Assign)
        for target in n.targets
        if isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name)
        and target.value.id == "base"
    ]
    assert modified_base_attributes == ["HERE", "RAW", "BUDGET"]
    main_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    assert ast.unparse(main_node.body[-2]) == "base.main(args.gate.resolve())"
    assert ast.unparse(main_node.body[-1]) == "write_saved_classification(base, manifest)"
    for initial, expected in zip(
        manifest["initial_partials"], manifest["initial_six_cap_classification"], strict=True
    ):
        assert wrapper.classify_saved(initial, manifest["sixth_cap"]) == expected

    result = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": sha(P / "run.py"),
        "source_sha256": sha(__file__),
        "base_runner_sha256": manifest["base_runner_sha256"],
        "binary_sha256": manifest["binary_sha256"],
        "unique_pins_checked": len(pins),
        "inherited_gate_sha256": sha(prior_gate_path),
        "starts_receipt_sha256": STARTS_SHA,
        "sixth_proof_review_sha256": sha(proof_path),
        "initial_sha256s": [r["sha256"] for r in manifest["initial_partials"]],
        "budget": expected_budget,
        "base_mutations": modified_base_attributes,
        "classification_runs_only_after_unchanged_base_main": True,
        "classifier_controls": classify_controls(wrapper, manifest),
        "saved_report_controls": report_controls(wrapper, manifest),
        "optimizer_launches": 0,
        "native_process_launches": 0,
        "scope": (
            "Focused wrapper review. Original native kernel, recorder and dual validator "
            "are reused by frozen hashes. Sixth cap postclassifies saved exact64 records only; "
            "no best-six-cap-live-state claim."
        ),
    }
    dump(HERE / "checks.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "pins": len(pins),
                "matrix_cases": result["classifier_controls"][
                    "synthetic_postvalidation_matrix_cases"
                ],
                "report_cases": len(result["saved_report_controls"]),
            }
        )
    )


if __name__ == "__main__":
    main()
