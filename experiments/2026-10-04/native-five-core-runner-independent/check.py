# Document:    Independent Five-Core Python Runner Delta Review
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f2a11d365f6415f3055495f93981fc6c9deb7075d8a662acb491667d01d34b25
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay frozen zero/eight-step outputs and test process guards with fakes only."""

import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PRODUCER = ROOT / "experiments/2026-10-04/native-five-core-record-pilot"
RAW = ROOT / "experiments/scratch/native-five-core-record-pilot-20261004"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    manifest_path = PRODUCER / "manifest.json"
    assert sha(manifest_path) == "32d536037298694fea21fa8207efb328851d9ede135cae2c770833863891ee86"
    assert sha(PRODUCER / "run.py") == (
        "c0052cbf52dc40eb3547d40df7c619e8187698e932541180d7101a3133f03ba3"
    )
    manifest = json.loads(manifest_path.read_text())
    spec = importlib.util.spec_from_file_location("five_core_runner", PRODUCER / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    assert runner.BUDGET == manifest["budget"]
    for relative, expected in (
        manifest["source_files"] | manifest["input_files"] | manifest["raw_files"]
    ).items():
        assert sha(ROOT / relative) == expected
    controls = []
    for initial in manifest["initial_partials"]:
        seed = initial["seed"]
        for steps in (0, 8):
            directory = RAW / f"control-{seed}-{steps}"
            stdout = (directory / "stdout.jsonl").read_text()
            stderr = (directory / "stderr.txt").read_text()
            result = runner.validate(
                directory,
                stdout,
                1,
                stderr,
                300,
                manifest["core_rows"],
                seed,
                initial,
                steps,
            )
            assert not result["success"]
            roles = [r["role"] for r in result["snapshots"] if not r["role"].startswith("final_")]
            expected = ["complete", "raw64"]
            if seed == 2026105602:
                expected += ["admissible64", "weak64"]
            assert roles[: len(expected)] == expected
            controls.append(
                {
                    "seed": seed,
                    "steps": steps,
                    "initial_roles": expected,
                    "snapshots": len(result["snapshots"]),
                    "passed": True,
                }
            )
    damages = []
    initial = manifest["initial_partials"][1]
    directory = RAW / "control-2026105602-0"
    clean = [json.loads(line) for line in (directory / "stdout.jsonl").read_text().splitlines()]
    for kind in ("weak_D2", "initial_role", "seed", "final_weak_D2"):
        events = json.loads(json.dumps(clean))
        if kind == "weak_D2":
            next(e for e in events if e.get("role") == "weak64")["weak_D2max"] += 1
        elif kind == "initial_role":
            next(e for e in events if e.get("role") == "weak64")["role"] = "raw64"
        elif kind == "seed":
            events[0]["seed"] += 1
        else:
            events[-1]["weak_D2max"] += 1
        try:
            runner.validate(
                directory,
                "\n".join(map(json.dumps, events)),
                1,
                "",
                300,
                manifest["core_rows"],
                initial["seed"],
                initial,
                0,
            )
        except (AssertionError, FileNotFoundError):
            damages.append(kind)
        else:
            raise AssertionError(f"damaged recorder output accepted: {kind}")

    original_popen = runner.subprocess.Popen
    original_execute = runner.execute_bounded
    original_validate = runner.validate
    cases = []
    scratch = ROOT / "experiments/scratch/native-five-core-runner-independent-20261004"
    scratch.mkdir(exist_ok=True)
    try:

        def forbidden(*args, **kwargs):
            raise AssertionError("real process launch attempted during fake control")

        runner.subprocess.Popen = forbidden
        for kind, expected_calls in (
            ("two_normal", 2),
            ("cover_stop", 1),
            ("watchdog_stop", 1),
            ("invalid_stop", 1),
            ("abnormal_stop", 1),
            ("failed_gate", 0),
            ("wrong_manifest", 0),
            ("wrong_source", 0),
            ("wrong_budget", 0),
            ("prior_start", 0),
            ("prior_result", 0),
        ):
            with tempfile.TemporaryDirectory(prefix=f"{kind}-", dir=scratch) as temp:
                base = Path(temp)
                runner.HERE = base / "producer"
                runner.RAW = base / "raw"
                runner.HERE.mkdir()
                runner.RAW.mkdir()
                changed = json.loads(json.dumps(manifest))
                if kind == "wrong_source":
                    key = next(iter(changed["source_files"]))
                    changed["source_files"][key] = "0" * 64
                if kind == "wrong_budget":
                    changed["budget"]["seconds_per_run"] = 301
                dump(runner.HERE / "manifest.json", changed)
                gate = {
                    "passed": kind != "failed_gate",
                    "manifest_sha256": sha(runner.HERE / "manifest.json"),
                }
                if kind == "wrong_manifest":
                    gate["manifest_sha256"] = "0" * 64
                dump(base / "gate.json", gate)
                if kind == "prior_start":
                    dump(runner.RAW / "start.json", {})
                if kind == "prior_result":
                    dump(runner.HERE / "result.json", {})
                commands = []

                def fake_execute(command):
                    commands.append(command)
                    index = len(commands) - 1
                    expected = changed["initial_partials"][index]
                    assert command[2] == str(ROOT / expected["path"])
                    assert command[3:5] == [str(expected["seed"]), "300"]
                    rc = 0 if kind == "cover_stop" else 2 if kind == "abnormal_stop" else 1
                    return rc, "", "", {"fired": kind == "watchdog_stop"}, 1

                def fake_validate(*args, **kwargs):
                    if kind == "invalid_stop":
                        raise ValueError("deliberately invalid saved output")
                    return {"success": kind == "cover_stop"}

                runner.execute_bounded = fake_execute
                runner.validate = fake_validate
                rejected = False
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        runner.main(base / "gate.json")
                except AssertionError:
                    rejected = True
                assert len(commands) == expected_calls, kind
                assert rejected == (expected_calls == 0 or kind == "invalid_stop"), kind
                cases.append({"case": kind, "fake_calls": len(commands), "passed": True})

        watchdogs = []
        for mode in ("normal", "terminate", "kill"):
            calls = []

            class FakeProcess:
                returncode = 1

                def communicate(self, timeout=None):
                    calls.append(["communicate", timeout])
                    if mode != "normal" and timeout == 315:
                        raise subprocess.TimeoutExpired("fake", timeout)
                    if mode == "kill" and timeout == 5:
                        raise subprocess.TimeoutExpired("fake", timeout)
                    return "fake stdout", ""

                def terminate(self):
                    calls.append(["terminate"])

                def kill(self):
                    calls.append(["kill"])

            runner.subprocess.Popen = lambda *args, **kwargs: FakeProcess()
            rc, stdout, stderr, flags, elapsed = original_execute(["fake"])
            assert flags["fired"] == (mode != "normal")
            assert flags["terminate_sent"] == (mode != "normal")
            assert flags["kill_sent"] == (mode == "kill")
            assert flags["relaunch"] is False
            watchdogs.append({"mode": mode, "calls": calls, "flags": flags, "passed": True})
    finally:
        runner.subprocess.Popen = original_popen
        runner.execute_bounded = original_execute
        runner.validate = original_validate
    receipt = {
        "passed": True,
        "decision": "GO",
        "scope": "Python runner and recorder delta only; native policy review is separate.",
        "manifest_sha256": sha(manifest_path),
        "runner_sha256": sha(PRODUCER / "run.py"),
        "checker_sha256": sha(Path(__file__)),
        "saved_controls_replayed": controls,
        "damaged_outputs_rejected": damages,
        "fake_runner_cases": cases,
        "fake_watchdog_cases": watchdogs,
        "optimizer_launches": 0,
        "native_requeries": 0,
        "qualification_is_historical": True,
    }
    dump(OUT / "review.json", receipt)
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(OUT / "review.json"),
                "controls": len(controls),
                "fake_runner_cases": len(cases),
            }
        )
    )


if __name__ == "__main__":
    main()
