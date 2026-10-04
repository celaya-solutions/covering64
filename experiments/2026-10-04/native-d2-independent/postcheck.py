# Document:    Independent Native D2 Pilot Outcome Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3785a2ebc2ca385ea1655199ca27221cf24252e65b2ad8ed4f96a04754a51f2a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import json
import subprocess

from check import HERE, ROOT, SOURCE, read, recount, sha


def main():
    gate = read(HERE / "gate.json")
    manifest = read(SOURCE / "manifest.json")
    result = read(SOURCE / "result.json")
    assert gate["passed"]
    assert result["gate_sha256"] == sha(HERE / "gate.json")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == sha(SOURCE / "manifest.json")
    assert result["binary_sha256"] == gate["binary_sha256"] == sha(ROOT / manifest["binary_path"])
    for path, digest in (manifest["input_files"] | manifest["raw_files"]).items():
        assert sha(ROOT / path) == digest, path
    assert result["optimizer_calls"] == len(result["cases"]) in (1, 2)
    assert not result["global_lower_bound_claim"] and not result["unused_budget_reallocated"]
    seeds = manifest["budget"]["seeds"]
    assert [row["seed"] for row in result["cases"]] == seeds[: len(result["cases"])]
    cache = {}
    saved = []
    verifications = 0
    summaries = []
    for index, case in enumerate(result["cases"]):
        assert case["validation_error"] is None and case["exit_code"] in (0, 1)
        assert not case["watchdog"]["fired"] and not case["watchdog"]["relaunch"]
        assert case["wall_seconds"] < 76
        hint = manifest["hints"][index]
        assert case["command"] == [
            str(ROOT / manifest["binary_path"]),
            str(ROOT / hint["path"]),
            str(case["seed"]),
            "60",
            str(SOURCE / f"seed-{case['seed']}" / "search"),
        ]
        for path, digest in case["raw_files"].items():
            assert sha(ROOT / path) == digest
        log = next(ROOT / p for p in case["raw_files"] if p.endswith("stdout.jsonl"))
        events = [json.loads(line) for line in log.read_text().splitlines()]
        assert events[0] == {"event": "start", "seed": case["seed"], "budget": 60}
        records = [event for event in events if event["event"] == "record"]
        assert [event["serial"] for event in records] == list(range(1, len(records) + 1))
        observed = {}
        for number, row in enumerate(case["snapshots"]):
            path = ROOT / row["path"]
            assert sha(path) == row["sha256"]
            metrics = recount(path, manifest["core_rows"])
            assert row["metrics"] == metrics
            assert all(value <= 55 for value in metrics["core_overlaps"])
            if row["role"] in ("raw", "final_raw"):
                assert not metrics["forbidden"]
            if row["role"] in ("qualified", "final_qualified"):
                assert metrics["D2max"] == metrics["D2sum"] == metrics["D3"] == metrics["D4"] == 0
                assert metrics["pair_min"] >= 5 and not metrics["forbidden"]
            if row["sha256"] not in cache:
                receipts = []
                for name, command in (
                    ("package", ["uv", "run", "covering64", "verify"]),
                    ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
                ):
                    checked = subprocess.run(
                        command + [str(path), "--expected-blocks", "64"],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    assert checked.returncode == int(metrics["holes"] != 0) and not checked.stderr
                    payload = json.loads(checked.stdout)
                    assert payload["blocks"] == 64 and payload["valid"] == (metrics["holes"] == 0)
                    key = "covered" if name == "package" else "covered_subsets"
                    assert payload[key] == 560 - metrics["holes"]
                    receipt = HERE / f"seed-{case['seed']}-state-{number:03d}-{name}.json"
                    receipt.write_text(checked.stdout)
                    receipts.append(
                        {
                            "path": str(receipt.relative_to(ROOT)),
                            "sha256": sha(receipt),
                            "canonical_sha256": payload["canonical_sha256"],
                        }
                    )
                    verifications += 1
                assert receipts[0]["canonical_sha256"] == receipts[1]["canonical_sha256"]
                cache[row["sha256"]] = receipts
            observed[path.name] = metrics
            saved.append(
                {
                    "seed": case["seed"],
                    "role": row["role"],
                    "path": row["path"],
                    "sha256": row["sha256"],
                    "metrics": metrics,
                    "verifiers": cache[row["sha256"]],
                }
            )
        last = {}
        for event in records:
            role = event["role"]
            assert role in ("raw", "primary", "qualified")
            assert event["metrics"] == observed[f"search-record-{event['serial']}-{role}.txt"]
            metrics = event["metrics"]
            key = (metrics["D2max"], metrics["holes"]) if role == "primary" else (metrics["holes"],)
            assert role not in last or key < last[role][0]
            last[role] = (key, metrics)
        assert {"raw", "primary"} <= set(last)
        final = events[-1]
        assert 0 <= final["seconds"] <= case["wall_seconds"] + 1
        assert 0 <= final["core_rejections"] <= final["iterations"]
        for role in ("current", "raw", "primary", "qualified"):
            if final[role] is None:
                assert role == "qualified" and role not in last
            else:
                assert final[role] == observed[f"search-final-{role}.txt"]
                if role != "current":
                    assert final[role] == last[role][1]
        if case["exit_code"] == 0:
            assert index == len(result["cases"]) - 1
            assert sum(event["role"] == "qualified" for event in records) == 1
            assert records[-1]["role"] == "qualified"
            assert records[-1]["iterations"] == final["iterations"]
            assert final["current"] == final["primary"] == final["qualified"]
            assert final["current"]["D2max"] == 0
            want = "cover_found" if final["current"]["holes"] == 0 else "qualified_hint_found"
            assert final["event"] == result["stop_reason"] == want
        else:
            assert final["event"] == "finished" and final["seconds"] >= 59
            assert final["current"]["D2max"] > 0 and "qualified" not in last
        summaries.append(
            {
                "seed": case["seed"],
                "wall_seconds": case["wall_seconds"],
                "native_seconds": final["seconds"],
                "iterations": final["iterations"],
                "status": final["event"],
                "primary": final["primary"],
                "raw": final["raw"],
                "current": final["current"],
                "qualified": final["qualified"],
            }
        )
    if result["cases"][-1]["exit_code"] == 1:
        assert len(result["cases"]) == 2 and result["stop_reason"] == "budget_exhausted"
    expected_skips = [
        {"seed": seed, "reason": result["stop_reason"]} for seed in seeds[len(result["cases"]) :]
    ]
    assert result["skipped_runs"] == expected_skips
    report = {
        "passed": True,
        "optimizer_calls_by_audit": 0,
        "declared_optimizer_calls": result["optimizer_calls"],
        "checker_sha256": sha(__file__),
        "gate_sha256": sha(HERE / "gate.json"),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "result_sha256": sha(SOURCE / "result.json"),
        "stop_reason": result["stop_reason"],
        "skipped_runs": result["skipped_runs"],
        "summaries": summaries,
        "saved_states": saved,
        "unique_states": len(cache),
        "dual_verifier_calls": verifications,
        "scope": "Direct recount and dual verification of all saved states and first-zero pilot "
        "stopping behavior. Bounded construction outcomes do not establish infeasibility or "
        "a global lower bound. Positive-hole qualified states are partial hints, not covers.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "unique_states": len(cache),
                "dual_verifier_calls": verifications,
                "stop_reason": result["stop_reason"],
                "summaries": summaries,
            }
        )
    )


if __name__ == "__main__":
    main()
