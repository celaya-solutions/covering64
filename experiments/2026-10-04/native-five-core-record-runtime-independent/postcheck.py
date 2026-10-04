# Document:    Five Core Record Pilot Independent Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e032c4902d45dacfbd776ed7e561ebfd0a1b5444877db75760038debeb3ab828
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount saved families and replay logged mutations without running any optimizer."""

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime
from pathlib import Path

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "native-five-core-record-pilot"
RAW = ROOT / "experiments/scratch/native-five-core-record-pilot-20261004"
MANIFEST_SHA = "32d536037298694fea21fa8207efb328851d9ede135cae2c770833863891ee86"
GATE_SHA = "10477409a380ff6fc6a912b6349c7e8e418dcc8b3afab84fe3fab0f5f8eb0e59"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


OLD_PATH = HERE.parent / "native-variable-partial-start-independent/postcheck.py"
ORACLE_PATH = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
assert sha(OLD_PATH) == "1a6a4515434a79a7fe7b3d5597d44134130e8f8643586c7e0c0559dc37c89b20"
assert sha(ORACLE_PATH) == "7fc14c0e2078894a03cc8945c94cb8f9987e79f4780d49558d311e83f0d0ba92"
OLD = load(OLD_PATH, "prior_partial_runtime_helpers")
ORACLE = load(ORACLE_PATH, "independent_full_inclusion_counts")
STANDALONE = load(ROOT / "scripts/check_cover.py", "standalone_five_core_runtime")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--result-sha256", required=True)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    manifest, result = read(PRODUCER / "manifest.json"), read(PRODUCER / "result.json")
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(PRODUCER / "result.json") == args.result_sha256
    assert sha(args.gate) == GATE_SHA
    gate = read(args.gate)
    assert gate["passed"] is True and gate["decision"] == "GO"
    assert gate["manifest_sha256"] == result["manifest_sha256"] == MANIFEST_SHA
    assert result["gate_sha256"] == sha(args.gate)
    assert (
        result["budget"]
        == manifest["budget"]
        == {
            "max_runs": 2,
            "relaunch": False,
            "seconds_per_run": 300,
            "seeds": [2026105601, 2026105602],
            "watchdog_seconds": 315,
            "termination_grace_seconds": 5,
            "simultaneous_processes": 1,
            "stop_after_first_complete_at_most_64": True,
            "unused_budget_reallocated": False,
        }
    )
    assert manifest["core_thresholds"] == [55, 55, 55, 55, 56]
    assert manifest["weak_record_ranking"] == ["holes", "D2max"]
    assert manifest["weak_record_hole_ceiling"] == 11
    assert 1 <= len(result["runs"]) <= 2
    assert [r["seed"] for r in result["runs"]] == manifest["budget"]["seeds"][: len(result["runs"])]
    assert result["skipped_seeds"] == manifest["budget"]["seeds"][len(result["runs"]) :]
    campaign_complete = (
        len(result["runs"]) == 2
        or result["runs"][-1]["success"]
        or result["runs"][-1]["watchdog"]["fired"]
    )
    assert campaign_complete or args.partial, "second run has not completed"
    for group in ("source_files", "input_files", "raw_files"):
        for path, digest in manifest[group].items():
            assert sha(ROOT / path) == digest, path
    assert sha(ROOT / manifest["binary_path"]) == manifest["binary_sha256"]
    start = read(RAW / "start.json")
    assert start["gate_sha256"] == GATE_SHA
    assert start["manifest_sha256"] == MANIFEST_SHA and start["budget"] == manifest["budget"]
    assert sha(RAW / "frozen-sources/gate.json") == GATE_SHA
    assert sha(RAW / "frozen-sources/manifest.json") == MANIFEST_SHA
    for relative, expected in manifest["source_files"].items():
        assert sha(RAW / "frozen-sources" / Path(relative).name) == expected
    cores = manifest["core_rows"]
    inventory_path = HERE.parent / "h11-common-core-saved-inventory-independent/inventory.json"
    assert sha(inventory_path) == "720e1856a16aaf32b3fbf456a37e644d626a849aa0ae5e3bd7b989bd6680cece"
    inventory = read(inventory_path)
    known = {r["sha256"] for r in inventory["families"]}
    baseline = min(
        (r["metrics"]["holes"], r["metrics"]["D2max"])
        for r in inventory["families"]
        if r["all_checks_pass"]
    )
    assert baseline == (11, 27)
    family_cache, files = {}, {}

    def check(path, expected):
        blocks = OLD.parse(path.read_text())
        ids = [OLD.RANK[b] for b in blocks]
        digest = sha(path)
        actual = OLD.metrics(ids, cores)
        assert actual == expected, path
        if digest not in family_cache:
            package = verify_cover(blocks)
            standalone = STANDALONE.verify_cover(blocks, expected_blocks=len(blocks))
            assert package["valid"] == standalone["valid"] == (actual["holes"] == 0)
            assert sorted(map(tuple, package["uncovered"])) == sorted(
                map(tuple, standalone["uncovered"])
            )
            assert package["canonical_sha256"] == standalone["canonical_sha256"] == digest
            weak = ORACLE.analyze(ids, cores[:4])["metrics"] if len(ids) == 64 else None
            if weak is not None:
                weak["cardinality"] = len(ids)
            caps = len(ids) == 64 and all(
                a <= b for a, b in zip(actual["core_overlaps"], [55] * 4 + [56])
            )
            qualified = bool(
                caps
                and actual["holes"] <= 11
                and weak["minimum_pair_count"] >= 5
                and weak["D3"] == weak["D4"] == 0
            )
            family_cache[digest] = {
                "sha256": digest,
                "ids": ids,
                "metrics": actual,
                "weak_metrics": weak,
                "five_caps_pass": caps,
                "weak_qualified": qualified,
                "package": package,
                "standalone": standalone,
                "hash_in_historical_inventory": digest in known,
                "qualified_rank_improvement": qualified
                and (actual["holes"], weak["D2max"]) < baseline,
            }
        files[str(path.relative_to(ROOT))] = digest
        return family_cache[digest]

    summaries = []
    previous_time, previous_elapsed = None, None
    for run in result["runs"]:
        assert run["validation_passed"]
        seed = run["seed"]
        initial = next(r for r in manifest["initial_partials"] if r["seed"] == seed)
        directory = PRODUCER / f"seed-{seed}"
        assert run["command"] == [
            str(ROOT / manifest["binary_path"]),
            str(ROOT / manifest["incumbent_path"]),
            str(ROOT / initial["path"]),
            str(seed),
            "300",
            str(directory / "search"),
        ]
        started = datetime.fromisoformat(run["started_utc"])
        assert started >= datetime.fromisoformat(start["started_utc"])
        assert 0 <= run["elapsed_seconds"] <= 315 + 5 + 15
        assert set(run["watchdog"]) == {"fired", "terminate_sent", "kill_sent", "relaunch"}
        assert all(type(value) is bool for value in run["watchdog"].values())
        assert run["watchdog"]["relaunch"] is False
        assert run["watchdog"]["terminate_sent"] == run["watchdog"]["fired"]
        assert not run["watchdog"]["kill_sent"] or run["watchdog"]["fired"]
        if previous_time is not None:
            assert (started - previous_time).total_seconds() >= previous_elapsed - 1
        previous_time, previous_elapsed = started, run["elapsed_seconds"]
        for key in ("stdout", "stderr"):
            suffix = "stdout.jsonl" if key == "stdout" else "stderr.txt"
            assert run[key]["path"] == str((RAW / f"seed-{seed}-{suffix}").relative_to(ROOT))
            assert sha(ROOT / run[key]["path"]) == run[key]["sha256"]
            files[run[key]["path"]] = run[key]["sha256"]
        assert (ROOT / run["stderr"]["path"]).read_text() == ""
        events = [
            json.loads(line) for line in (ROOT / run["stdout"]["path"]).read_text().splitlines()
        ]
        assert events[0] == {
            "event": "start",
            "seed": seed,
            "budget": 300,
            "mode": "search",
            "control_step_limit": None,
        }
        final = events[-1]
        assert final == run["final"]
        records = [e for e in events if e["event"] == "record"]
        assert all(
            e["event"] in ("start", "record", "trace", "finished", "cover_found", "interrupted")
            for e in events
        )
        assert sum(e["event"] == "start" for e in events) == 1
        assert sum(e["event"] in ("finished", "cover_found", "interrupted") for e in events) == 1
        assert [e["serial"] for e in records] == list(range(1, len(records) + 1))
        buckets = {name: [] for name in ("complete", "raw64", "admissible64", "weak64")}
        for event in records:
            role = event["role"]
            path = directory / f"search-record-{event['serial']}-{role}.txt"
            family = check(path, event["metrics"])
            if role == "complete":
                assert family["metrics"]["holes"] == 0
                rank = (family["metrics"]["cardinality"],)
            elif role == "weak64":
                assert family["weak_qualified"]
                assert event["weak_D2max"] == family["weak_metrics"]["D2max"]
                rank = (family["metrics"]["holes"], family["weak_metrics"]["D2max"])
            else:
                assert family["metrics"]["cardinality"] == 64
                if role == "admissible64":
                    assert family["five_caps_pass"]
                rank = (family["metrics"]["holes"],)
            if buckets[role]:
                assert rank < buckets[role][-1]["rank"]
            buckets[role].append({"sha256": family["sha256"], "rank": rank})
        expected_initial = ["complete", "raw64"] + (
            ["admissible64", "weak64"] if seed == 2026105602 else []
        )
        assert [e["role"] for e in records[: len(expected_initial)]] == expected_initial
        assert all(e["mutations"] == e["step"] == 0 for e in records[: len(expected_initial)])
        assert buckets["complete"][0]["rank"] == (65,)
        assert (
            buckets["complete"][0]["sha256"] == manifest["input_files"][manifest["incumbent_path"]]
        )
        for event in records[len(expected_initial) :]:
            assert type(event["step"]) is int and 0 <= event["step"] <= final["iterations"]
            assert type(event["mutations"]) is int and 0 < event["mutations"] <= final["mutations"]
        for role in expected_initial[1:]:
            assert buckets[role][0]["sha256"] == initial["sha256"]
        expected_files = {f"search-record-{e['serial']}-{e['role']}.txt" for e in records}
        snapshot_expectations = [
            (directory / f"search-record-{e['serial']}-{e['role']}.txt", e["role"]) for e in records
        ]
        for role in ("current", *buckets):
            path = directory / f"search-final-{role}.txt"
            if role != "current" and not buckets[role]:
                assert final[role] is None and not path.exists()
                continue
            family = check(path, final[role])
            snapshot_expectations.append((path, "final_" + role))
            expected_files.add(path.name)
            if role != "current":
                assert family["sha256"] == buckets[role][-1]["sha256"]
            reported = run["final_rows"][role]
            assert reported["sha256"] == family["sha256"] and reported["role"] == "final_" + role
        assert len(run["snapshots"]) == len(snapshot_expectations)
        for snapshot, (path, role) in zip(run["snapshots"], snapshot_expectations):
            family = family_cache[sha(path)]
            assert snapshot["path"] == str(path.relative_to(ROOT))
            assert snapshot["sha256"] == family["sha256"] and snapshot["role"] == role
            assert snapshot["ids"] == family["ids"]
            assert snapshot["metrics"] == family["metrics"]
            assert snapshot["weak_metrics"] == family["weak_metrics"]
            assert snapshot["cap_admissible"] == family["five_caps_pass"]
            assert snapshot["weak_qualified"] == family["weak_qualified"]
            weak = family["weak_metrics"]
            assert snapshot["historical_comparison"] == {
                "scope": "Frozen finite saved-family inventory at H<=11; no isomorphism claim",
                "in_inventory_scope": family["metrics"]["cardinality"] == 64
                and family["metrics"]["holes"] <= 11,
                "hash_in_inventory": family["sha256"] in known,
                "holes": family["metrics"]["holes"],
                "D2max": None if weak is None else weak["D2max"],
                "D2sum": None if weak is None else weak["D2sum"],
                "qualified_baseline_rank": list(baseline),
                "qualified_rank_improvement": family["qualified_rank_improvement"],
            }
        assert {p.name for p in directory.glob("*.txt")} == expected_files
        assert final["weak_D2max"] == (
            None if not buckets["weak64"] else buckets["weak64"][-1]["rank"][1]
        )
        live = set(initial["ids"])
        traces = [e for e in events if e["event"] == "trace"]
        assert all(e["fallback"] for e in traces[:4])
        assert [e["step"] for e in traces] == list(range(min(32, final["iterations"])))
        for trace in traces:
            OLD.validate_trace_shape(trace)
            target = set(OLD.TRIPLES[trace["target"]])
            assert not any(target.issubset(OLD.BLOCKS[i]) for i in live)
            assert trace["incoming"] not in live
            for removed in trace["removed"]:
                if removed >= 0:
                    assert removed in live
                    live.remove(removed)
            if trace["action"] in ("add_only", "swap"):
                live.add(trace["incoming"])
            assert OLD.metrics(sorted(live), cores) == trace["metrics"]
            assert trace["weights_updated"] == (trace["action"] == "add_only")
        success = final["current"]["holes"] == 0 and final["current"]["cardinality"] <= 64
        assert run["success"] == success == (run["returncode"] == 0)
        assert final["event"] == (
            "cover_found" if success else "finished" if run["returncode"] == 1 else "interrupted"
        )
        for key in ("iterations", "mutations", "weight_updates", "fallbacks", "novelties"):
            assert type(final[key]) is int and final[key] >= 0
        assert all(type(value) is int and value >= 0 for value in final["action_counts"])
        assert sum(final["action_counts"]) == final["iterations"]
        assert final["max_cardinality"] == 64 and 0 < final["min_cardinality"] <= 64
        assert 0 <= final["seconds"] <= run["elapsed_seconds"] + 1
        if not success and not run["watchdog"]["fired"]:
            assert run["returncode"] == 1 and 300 <= final["seconds"] < 315
        summaries.append(
            {
                "seed": seed,
                "success": success,
                "buckets": buckets,
                "trace_mutations_replayed": len(traces),
                "snapshot_references_checked": len(snapshot_expectations),
                "started_utc": run["started_utc"],
                "elapsed_seconds": run["elapsed_seconds"],
                "returncode": run["returncode"],
                "watchdog": run["watchdog"],
                "final": final,
            }
        )
    output_path = HERE / (
        "postcheck.json" if campaign_complete else "partial-postcheck-seed5601.json"
    )
    assert not output_path.exists(), "preserve runtime receipt"
    qualified = [f for f in family_cache.values() if f["weak_qualified"]]
    receipt = {
        "passed": True,
        "campaign_complete": campaign_complete,
        "source_sha256": sha(Path(__file__)),
        "producer_result_sha256": args.result_sha256,
        "manifest_sha256": MANIFEST_SHA,
        "gate_sha256": sha(args.gate),
        "prior_runtime_helpers_sha256": sha(OLD_PATH),
        "independent_oracle_sha256": sha(ORACLE_PATH),
        "historical_inventory_sha256": sha(inventory_path),
        "package_verifier_sha256": sha(ROOT / "src/covering64/core.py"),
        "standalone_verifier_sha256": sha(ROOT / "scripts/check_cover.py"),
        "trace_damage_controls": OLD.trace_shape_controls(),
        "families": list(family_cache.values()),
        "distinct_families": len(family_cache),
        "saved_family_references": sum(r["snapshot_references_checked"] for r in summaries),
        "best_qualified_rank": min(
            (f["metrics"]["holes"], f["weak_metrics"]["D2max"]) for f in qualified
        ),
        "new_qualified_family_hashes": [
            f["sha256"] for f in qualified if not f["hash_in_historical_inventory"]
        ],
        "files": files,
        "runs": summaries,
        "cover_found": any(r["success"] for r in summaries),
        "optimizer_launches": 0,
        "native_requeries": 0,
        "raw_files": {
            str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.rglob("*")) if p.is_file()
        },
        "scope": (
            "Saved-state recount and logged mutation replay only; "
            "no global or all-relabel conclusion"
        ),
    }
    output_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    assert output_path.stat().st_size < 1_000_000, "tracked receipt is too large"
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(output_path),
                "campaign_complete": campaign_complete,
                "best_qualified_rank": receipt["best_qualified_rank"],
                "distinct_families": len(family_cache),
                "optimizer_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
