# Document:    Deterministic Descent Wrapper Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2e29d04d70f3ebf85a2cd82d12e11b80126c330fc0c485fccb283ad3a0dc451e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Synthetic campaign/process controls only; no search binary or solver invocation."""

import importlib.util
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def load_runner():
    spec = importlib.util.spec_from_file_location("descent_control_runner", HERE / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def state(tag, deficit=28, holes=12, first=0):
    return {
        "sha256": tag,
        "ids": list(range(first, first + 64)),
        "metrics": {"holes": holes, "D2max": deficit},
        "cover_found": holes == 0,
    }


def outcome(candidates=(), complete=True, passed=True, covers=()):
    return {
        "best_ties": list(candidates),
        "complete": complete,
        "passed": passed,
        "observed_covers": list(covers),
    }


def campaign_cases(runner):
    baseline = state("baseline")
    a, b = state("larger", 27, first=10), state("smaller", 27, first=1)
    cover = state("synthetic-cover", 0, 0)
    specs = [
        (
            "cross-shell-full-family-tie-choice",
            [outcome([a]), outcome([b]), outcome(), outcome()],
            "no_strict_improvement",
            4,
            "smaller",
        ),
        (
            "one-shell-wins-lower-rank",
            [outcome([state("one-wins", 26)]), outcome([b]), outcome(), outcome()],
            "no_strict_improvement",
            4,
            "one-wins",
        ),
        ("unchanged-complete-stop", [outcome(), outcome()], "no_strict_improvement", 2, "baseline"),
        ("first-incomplete-no-adoption", [outcome([a], False)], "incomplete", 1, "baseline"),
        (
            "second-incomplete-no-adoption",
            [outcome([a]), outcome([b], False)],
            "incomplete",
            2,
            "baseline",
        ),
        ("invalid-terminal-no-adoption", [outcome([a], False, False)], "incomplete", 1, "baseline"),
        (
            "early-cover-no-round-optimum",
            [outcome([cover], covers=[cover])],
            "cover_observed",
            1,
            "baseline",
        ),
        (
            "incomplete-cover-retained",
            [outcome([cover], False, covers=[cover])],
            "incomplete",
            1,
            "baseline",
        ),
    ]
    rows = []
    for name, replies, reason, count, final in specs:
        calls, recorded = [], []

        def execute(number, shell, center):
            calls.append((number, shell, center["sha256"]))
            return replies[len(calls) - 1]

        result = runner.run_campaign(baseline, execute, recorded.append)
        assert result["stop_reason"] == reason and len(calls) == count
        assert result["final_center"]["sha256"] == final and recorded == result["rounds"]
        for number in range(1, 5):
            centers = [c[2] for c in calls if c[0] == number]
            assert len(set(centers)) <= 1
        if "incomplete" in name or "invalid" in name or "early-cover" in name:
            assert recorded[0]["selected"] is None and not result["local_closure"]
        if "cover" in name:
            assert len(result["observed_covers"]) == 1
        rows.append(
            {
                "case": name,
                "passed": True,
                "shell_calls": count,
                "stop_reason": reason,
                "synthetic_final": final,
            }
        )
    calls, recorded = [], []

    def improving(number, shell, center):
        calls.append((number, shell, center["sha256"]))
        return outcome([state(f"round-{number}", 28 - number)])

    result = runner.run_campaign(baseline, improving, recorded.append)
    assert len(calls) == 8 and len(recorded) == 4 and result["stop_reason"] == "round_limit"
    assert result["final_center"]["sha256"] == "round-4"
    assert [row[0] for row in calls] == [1, 1, 2, 2, 3, 3, 4, 4]
    assert all(calls[i][2] == calls[i + 1][2] for i in (0, 2, 4, 6))
    rows.append({"case": "four-round-bound", "passed": True, "shell_calls": 8})
    return rows


def grammar_cases(runner):
    good = '{"event":"start"}\n{"event":"final","seconds":0}\n'
    runner.strict_grammar(good)
    bad = [
        good.replace('{"event":"start"}', "null"),
        good.replace('{"event":"start"}', "[]"),
        good.replace('{"event":"final","seconds":0}', '{"event":"final","seconds":NaN}'),
        good.replace('"seconds":0', '"seconds":true'),
        '{"event":"start"}\n{"event":"unknown","seconds":0}\n{"event":"final","seconds":0}\n',
        '{"event":"start"}\n',
        '{"event":"start"}\n{"event":"final"',
    ]
    for text in bad:
        try:
            runner.strict_grammar(text)
        except ValueError:
            pass
        else:
            raise AssertionError("malformed grammar accepted")
    return {"passed": True, "positive_controls": 1, "negative_controls": len(bad)}


def fake_process_case(runner, timeouts):
    with tempfile.TemporaryDirectory(prefix="descent-fake-") as directory:
        root = Path(directory)
        run = root / "run"
        run.mkdir()
        binary = root / "synthetic-binary"
        binary.write_text("never executed\n")
        text = "synthetic center only\n"
        center = state("unused")
        center["sha256"] = runner.hashlib.sha256(text.encode()).hexdigest()
        manifest = {
            "shells": {
                "one": {
                    "binary_path": binary.name,
                    "binary_sha256": runner.sha(binary),
                    "recorder_sha256": "synthetic-recorder",
                }
            },
            "core_rows": [],
        }
        recorder = SimpleNamespace(family_text=lambda ids: text)
        calls = {"launch": 0, "communicate": 0, "terminate": 0, "kill": 0}

        class FakeProcess:
            returncode = -9 if timeouts == 2 else -15 if timeouts else 1

            def __init__(self, command, **kwargs):
                calls["launch"] += 1
                assert command[2] == "120" and kwargs["cwd"] == root

            def communicate(self, timeout=None):
                calls["communicate"] += 1
                if calls["communicate"] <= timeouts:
                    raise runner.subprocess.TimeoutExpired("fake", timeout)
                return 'null\n{"event":"final","seconds":0}\n', "synthetic stderr\n"

            def terminate(self):
                calls["terminate"] += 1

            def kill(self):
                calls["kill"] += 1

        with (
            patch.object(runner, "ROOT", root),
            patch.object(runner, "RUN", run),
            patch.object(runner.subprocess, "Popen", FakeProcess),
        ):
            result = runner.execute_shell(1, "one", center, manifest, recorder)
        assert not result["passed"] and not result["complete"] and result["validation_error"]
        assert calls["launch"] == 1 and calls["terminate"] == int(timeouts > 0)
        assert calls["kill"] == int(timeouts > 1) and not result["relaunch"]
        assert not result["budget_transfer"] and result["observed_covers"] == []
        assert (run / "round-01-one/stdout.jsonl").read_text().startswith("null\n")
        assert (run / "round-01-one/stderr.txt").read_text() == "synthetic stderr\n"
        assert all(
            runner.sha(root / path) == digest for path, digest in result["raw_files"].items()
        )
        return {"timeouts": timeouts, "passed": True, "calls": calls, "raw_output_preserved": True}


def main():
    runner = load_runner()
    rows = campaign_cases(runner)
    grammar = grammar_cases(runner)
    processes = [fake_process_case(runner, n) for n in (0, 1, 2)]
    result = {
        "passed": True,
        "search_launches": 0,
        "solver_launches": 0,
        "real_process_launches": 0,
        "runner_sha256": runner.sha(HERE / "run.py"),
        "source_sha256": runner.sha(Path(__file__)),
        "campaign_cases": rows,
        "grammar": grammar,
        "fake_process_cases": processes,
        "scope": "Synthetic wrapper controls only. These are not candidate witnesses, "
        "scan results, or mathematical cover/feasibility claims.",
    }
    runner.dump(HERE / "controls.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "search_launches": 0,
                "campaign_cases": len(rows),
                "receipt_sha256": runner.sha(HERE / "controls.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
