# Document:    Independent Raw H6 Native Reuse Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      0141a61646c64f3ead5b3c05a4a261b1d9e7f77a22413fd636f03b1cc5e46f4e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay existing bounded controls; independently check nullable weak records."""

import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "native-raw-h6-reuse-pilot"
RAW = ROOT / "experiments/scratch/native-raw-h6-reuse-pilot-20261004"
MANIFEST_SHA = "6d497a1b7081c1891ea61de71103254c2b439474abe5c58780080f743f487712"
RUNNER_SHA = "82f1d4e312433b5170af8bf24d8dbc8edc4a6162d863a7513353d7b0ad0bb98b"
BASE_SHA = "c0052cbf52dc40eb3547d40df7c619e8187698e932541180d7101a3133f03ba3"
BINARY_SHA = "079eaf578f1e7b29c4408185e77953b4d337d722e428e12b7c653392e1c2163c"
START_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
PROFILE = HERE.parent / "h6-two-point-star-warm-repair-runtime-independent/check.py"
PROFILE_SHA = "a035d956213ba49806c1b8769b31661adad06246560b2c540ad729ff855f4af5"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = set(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert sha(PRODUCER / "manifest.json") == MANIFEST_SHA
    assert sha(PRODUCER / "run.py") == RUNNER_SHA and sha(PROFILE) == PROFILE_SHA
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    pins = {}
    for group in ("source_files", "input_files", "raw_files"):
        for name, digest in manifest[group].items():
            assert name not in pins or pins[name] == digest
            pins[name] = digest
    for name, digest in pins.items():
        assert sha(ROOT / name) == digest, name
    assert sha(ROOT / manifest["binary_path"]) == BINARY_SHA
    assert sha(ROOT / manifest["base_runner_path"]) == BASE_SHA
    wrapper = load(PRODUCER / "run.py", "independent_raw_h6_wrapper")
    base = wrapper.base_module()
    pristine = load(ROOT / manifest["base_runner_path"], "independent_pristine_native")
    for name in ("execute_bounded", "checked", "validate", "main"):
        assert getattr(base, name).__code__ == getattr(pristine, name).__code__
    assert base.HERE == PRODUCER and base.RAW == RAW
    expected_budget = {
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
    assert wrapper.BUDGET == base.BUDGET == manifest["budget"] == expected_budget
    assert len(manifest["initial_partials"]) == 1
    initial = manifest["initial_partials"][0]
    assert initial["sha256"] == START_SHA and initial["seed"] == 2026106101
    assert initial["weak_qualified"] is False and initial["cap_admissible"] is True
    profile = load(PROFILE, "independent_raw_h6_profile")
    cache = {}

    def inspect(path):
        digest = sha(path)
        if digest in cache:
            return cache[digest]
        blocks = [tuple(map(int, line.split())) for line in Path(path).read_text().splitlines()]
        assert blocks == sorted(set(blocks)) and all(b in BLOCKS for b in blocks)
        ids = [BLOCKS.index(b) for b in blocks]
        holes = len(TRIPLES - {t for b in blocks for t in itertools.combinations(b, 3)})
        overlaps = [len(set(ids).intersection(core)) for core in manifest["core_rows"]]
        package = verify_cover(blocks)
        process = subprocess.run(
            [
                sys.executable,
                "scripts/check_cover.py",
                str(path),
                "--expected-blocks",
                str(len(blocks)),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        standalone = json.loads(process.stdout)
        assert not process.stderr and process.returncode == int(holes != 0)
        assert package["valid"] == standalone["valid"] == (holes == 0)
        assert len(package["uncovered"]) == standalone["uncovered_count"] == holes
        assert standalone["blocks"] == len(blocks) and standalone["cardinality_matches"]
        row = {
            "sha256": digest,
            "ids": ids,
            "metrics": {"cardinality": len(blocks), "holes": holes, "core_overlaps": overlaps},
            "classification": profile.classify(ids, manifest) if len(blocks) == 64 else None,
            "package": package,
            "standalone": standalone,
        }
        cache[digest] = row
        return row

    raw_initial = inspect(ROOT / initial["path"])
    assert raw_initial["metrics"] == initial["metrics"]
    p = raw_initial["classification"]
    assert (p["holes"], p["minimum_pair_count"], p["D2max"], p["D2sum"], p["D3"], p["D4"]) == (
        6,
        4,
        14,
        498,
        80,
        72,
    )
    assert not p["weak_qualified"] and p["six_named_caps_pass"]
    complete = inspect(ROOT / manifest["incumbent_path"])
    assert complete["metrics"]["cardinality"] == 65 and complete["metrics"]["holes"] == 0
    assert complete["classification"] is None
    control_reports = []
    for steps in (0, 8):
        folder = RAW / f"control-2026106101-{steps}"
        events = [json.loads(line) for line in (folder / "stdout.jsonl").read_text().splitlines()]
        assert not (folder / "stderr.txt").read_text()
        assert events[0] == {
            "event": "start",
            "seed": 2026106101,
            "budget": 300,
            "mode": "control",
            "control_step_limit": steps,
        }
        records = [event for event in events if event["event"] == "record"]
        assert [r["serial"] for r in records] == list(range(1, len(records) + 1))
        initial_records = [r for r in records if r["mutations"] == 0]
        assert [r["role"] for r in initial_records] == ["complete", "raw64", "admissible64"]
        assert all(r["step"] == 0 for r in initial_records)
        roles = {name: [] for name in ("complete", "raw64", "admissible64", "weak64")}
        for event in records:
            row = inspect(folder / f"search-record-{event['serial']}-{event['role']}.txt")
            assert row["metrics"] == event["metrics"]
            role = event["role"]
            if role == "complete":
                assert row["metrics"]["holes"] == 0
            else:
                assert row["metrics"]["cardinality"] == 64
                if role == "admissible64":
                    assert all(
                        a <= b for a, b in zip(row["metrics"]["core_overlaps"], [55] * 4 + [56])
                    )
                if role == "weak64":
                    assert row["classification"]["weak_qualified"]
                    assert event["weak_D2max"] == row["classification"]["D2max"]
            roles[role].append(row)
        assert roles["complete"][0]["sha256"] == complete["sha256"]
        assert roles["raw64"][0]["sha256"] == roles["admissible64"][0]["sha256"] == START_SHA
        terminal = events[-1]
        assert terminal["event"] == "finished" and terminal["iterations"] == steps
        for role in ("current", "complete", "raw64", "admissible64", "weak64"):
            path = folder / f"search-final-{role}.txt"
            if role != "current" and not roles[role]:
                assert terminal[role] is None and not path.exists()
            else:
                row = inspect(path)
                assert row["metrics"] == terminal[role]
                if role != "current":
                    assert row["sha256"] == roles[role][-1]["sha256"]
        assert terminal["weak64"] is None and terminal["weak_D2max"] is None
        assert not roles["weak64"]
        traces = [e for e in events if e["event"] == "trace"]
        assert [e["step"] for e in traces] == list(range(steps))
        assert all(e["fallback"] for e in traces[:4])
        assert sum(terminal["action_counts"]) == steps
        if steps == 0:
            assert terminal["mutations"] == terminal["weight_updates"] == 0
        else:
            assert terminal["fallbacks"] == 4 and terminal["min_cardinality"] == 62
        control_reports.append(
            {
                "steps": steps,
                "initial_roles": [r["role"] for r in initial_records],
                "weak_initial_and_final_absent": True,
                "terminal": terminal,
            }
        )

    watchdog_controls = []
    for name, responses in (
        ("normal", [("", "")]),
        ("terminate", [None, ("", "")]),
        ("kill", [None, None, ("", "")]),
    ):
        events = []

        class Process:
            returncode = 1

            def communicate(self, timeout=None):
                events.append(["communicate", timeout])
                answer = responses.pop(0)
                if answer is None:
                    raise subprocess.TimeoutExpired("mock only", timeout)
                return answer

            def terminate(self):
                events.append(["terminate"])

            def kill(self):
                events.append(["kill"])

        with patch.object(base.subprocess, "Popen", return_value=Process()) as mocked:
            _, _, _, watchdog, _ = base.execute_bounded(["not-a-native-launch"])
            assert mocked.call_count == 1
        assert watchdog["fired"] == (name != "normal") and not watchdog["relaunch"]
        assert (
            events
            == {
                "normal": [["communicate", 315]],
                "terminate": [["communicate", 315], ["terminate"], ["communicate", 5]],
                "kill": [
                    ["communicate", 315],
                    ["terminate"],
                    ["communicate", 5],
                    ["kill"],
                    ["communicate", None],
                ],
            }[name]
        )
        watchdog_controls.append({"case": name, "events": events})

    weak_path = (
        HERE.parent
        / "weak-pair-h9-d23-neutral-queue-runtime-independent/family-a0a737c4010f68fc.txt"
    )
    weak_checked = inspect(weak_path)
    assert weak_checked["classification"]["weak_six_cap_qualified"]
    base_rows = [
        base.checked(ROOT / manifest["incumbent_path"], manifest["core_rows"]),
        base.checked(ROOT / initial["path"], manifest["core_rows"]),
    ]
    weak_row = base.checked(weak_path, manifest["core_rows"])
    classifier_cases = []
    with tempfile.TemporaryDirectory(
        prefix="raw-h6-gate-", dir=ROOT / "experiments/scratch"
    ) as temp:
        temp = Path(temp)
        for name, snapshots in (
            ("no_weak", base_rows),
            ("later_first_weak", [*base_rows, weak_row]),
        ):
            folder = temp / name
            folder.mkdir()
            (folder / "manifest.json").write_bytes((PRODUCER / "manifest.json").read_bytes())
            dump(
                folder / "result.json",
                {
                    "manifest_sha256": MANIFEST_SHA,
                    "runs": [
                        {"seed": 2026106101, "validation_passed": True, "snapshots": snapshots}
                    ],
                },
            )
            with patch.object(wrapper, "HERE", folder):
                wrapper.write_saved_classification(base, manifest)
            classified = json.loads((folder / "saved-six-cap-classification.json").read_text())
            assert classified["initial_eligible_fallbacks"] == []
            assert classified["initial_raw_fallbacks"][0]["sha256"] == START_SHA
            assert classified["initial_raw_fallbacks"][0]["weak_qualified"] is False
            assert classified["complete_incumbent_fallback"]["metrics"]["cardinality"] == 65
            assert classified["complete_incumbent_fallback"]["sixth_named_cap_pass"] is None
            assert classified["reference_count"] == len(snapshots)
            best = classified["best_saved_weak_six_cap_family"]
            assert (best is None) == (name == "no_weak")
            if best:
                assert best["sha256"] == weak_checked["sha256"] and best["qualified_rank"] == [
                    9,
                    19,
                ]
            classifier_cases.append({"name": name, "passed": True, "synthetic_metadata_only": True})
    assert not (RAW / "start.json").exists() and not (PRODUCER / "result.json").exists()
    report = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "checker_sha256": sha(__file__),
        "pins_verified": len(pins),
        "budget": expected_budget,
        "initial": raw_initial,
        "separate_complete65": complete,
        "control_replays": control_reports,
        "watchdog_controls": watchdog_controls,
        "classifier_cases": classifier_cases,
        "real_native_launches": 0,
        "scope": "Raw H6 remains weak-ineligible. Initial weak bucket and best saved "
        "weak family may be absent; later first weak record is allowed. Complete65 is "
        "separate. Sixth cap only postclassifies saved exact64 records. Frozen live "
        "walk, weights, RNG, objective, and five-cap policy remain unchanged.",
    }
    dump(HERE / "review.json", report)
    dump(
        HERE / "gate.json",
        {
            "decision": "GO",
            "passed": True,
            "manifest_sha256": MANIFEST_SHA,
            "runner_sha256": RUNNER_SHA,
            "base_runner_sha256": BASE_SHA,
            "binary_sha256": BINARY_SHA,
            "initial_sha256s": [START_SHA],
            "review_sha256": sha(HERE / "review.json"),
            "scope": report["scope"],
            "real_native_launches_during_review": 0,
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "review_sha256": sha(HERE / "review.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
