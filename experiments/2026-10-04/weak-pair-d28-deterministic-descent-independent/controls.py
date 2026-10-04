# Document:    Independent Deterministic Descent Finite Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      75cd495ef956b627d3c90d4848a2232c5cbd32c2542064eb71d95ccbc6f4490a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Pure orchestration fixtures and recorded-output fake processes; no optimizer launches."""

import copy
import json
import math
import subprocess
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-d28-descent-independent-20261004"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def expect_failure(callback, label):
    try:
        callback()
    except (ValueError, AssertionError, TypeError, KeyError, IndexError):
        return label
    raise ValueError("accepted damaged control: " + label)


def abstract_state(holes=12, deficit=28, ids=None, tag="base", cover=False):
    return {
        "ids": [1, 2] if ids is None else ids,
        "sha256": tag,
        "metrics": {"holes": holes, "D2max": deficit},
        "cover_found": cover,
    }


def abstract_outcome(states=None, complete=True, passed=True, covers=None):
    states = [] if states is None else states
    return {
        "best_ties": states,
        "complete": complete,
        "passed": passed,
        "observed_covers": (
            [state for state in states if state["cover_found"]] if covers is None else covers
        ),
    }


def pure_controls(runner):
    initial = abstract_state()
    tests = []

    def campaign(name, execute, expected_reason, expected_calls, final_tag, closure=False):
        calls, rows = [], []

        def tracked(number, shell, center):
            calls.append((number, shell, center["sha256"]))
            return execute(number, shell, center)

        result = runner.run_campaign(copy.deepcopy(initial), tracked, rows.append)
        require(result["stop_reason"] == expected_reason, name + " reason")
        require(len(calls) == expected_calls, name + " call count")
        require(result["final_center"]["sha256"] == final_tag, name + " adopted center")
        require(result["local_closure"] is closure, name + " local closure")
        require(result["rounds"] == rows, name + " recorded rounds")
        for index in range(0, len(calls) - 1, 2):
            one, two = calls[index : index + 2]
            require(one[1] == "one" and two[1] == "two", name + " shell order")
            require(one[0] == two[0] and one[2] == two[2], name + " same round center")
        tests.append({"name": name, "calls": calls, "stop_reason": result["stop_reason"]})
        return result

    campaign(
        "no improvement", lambda *_: abstract_outcome(), "no_strict_improvement", 2, "base", True
    )
    for shell in ("one", "two"):
        for passed in (False, True):

            def incomplete(_number, kind, _center, target=shell, valid=passed):
                return abstract_outcome(
                    [abstract_state(deficit=27, tag="unadopted")],
                    complete=kind != target,
                    passed=valid if kind == target else True,
                )

            campaign(
                f"{shell} incomplete passed={passed}",
                incomplete,
                "incomplete",
                1 if shell == "one" else 2,
                "base",
            )
    for shell in ("one", "two"):

        def cover(_number, kind, _center, target=shell):
            return abstract_outcome(
                covers=[abstract_state(0, 0, tag="synthetic-cover", cover=True)]
                if kind == target
                else [],
                complete=kind != target,
            )

        result = campaign(
            shell + " incomplete cover", cover, "incomplete", 1 if shell == "one" else 2, "base"
        )
        require(len(result["observed_covers"]) == 1, "incomplete cover was lost")
    result = campaign(
        "complete first shell cover",
        lambda *_: abstract_outcome([abstract_state(0, 0, tag="synthetic-cover", cover=True)]),
        "cover_observed",
        1,
        "base",
    )
    require(not result["rounds"][0]["complete"], "one-shell cover round mislabeled complete")

    def cover_second(_number, shell, _center):
        return abstract_outcome(
            [abstract_state(0, 0, tag="synthetic-cover", cover=True)] if shell == "two" else []
        )

    campaign("complete both cover", cover_second, "cover", 2, "synthetic-cover")

    def four_rounds(number, _shell, _center):
        return abstract_outcome([abstract_state(deficit=28 - number, tag=f"round-{number}")])

    result = campaign("four round cap", four_rounds, "round_limit", 8, "round-4")
    require(len(result["rounds"]) == 4, "wrong round cap")
    a = abstract_state(deficit=27, ids=[9, 10], tag="one")
    b = abstract_state(deficit=27, ids=[1, 20], tag="two")

    def tie_then_stop(number, shell, _center):
        return abstract_outcome([a if shell == "one" else b] if number == 1 else [])

    campaign(
        "full family lex tie then stop", tie_then_stop, "no_strict_improvement", 4, "two", True
    )
    winner = runner.choose(initial, [abstract_outcome([a]), abstract_outcome([b])])
    require(winner["sha256"] == "two", "tie choice follows shell order")
    lower_h = abstract_state(11, 999, [99, 100], "lower-hole")
    winner = runner.choose(initial, [abstract_outcome([a]), abstract_outcome([lower_h])])
    require(winner["sha256"] == "lower-hole", "holes must outrank deficit")
    require(
        runner.choose(initial, [abstract_outcome(), abstract_outcome()]) is None, "empty choice"
    )
    rejects = []
    for name, outcomes in (
        ("one shell", [abstract_outcome([a])]),
        ("three shells", [abstract_outcome([a])] * 3),
        ("incomplete choice", [abstract_outcome([a]), abstract_outcome([b], False)]),
        ("failed choice", [abstract_outcome([a]), abstract_outcome([b], passed=False)]),
        ("equal-rank choice", [abstract_outcome([initial]), abstract_outcome()]),
        ("worse-rank choice", [abstract_outcome([abstract_state(deficit=29)]), abstract_outcome()]),
    ):
        rejects.append(expect_failure(lambda o=outcomes: runner.choose(initial, o), name))
    return {"synthetic_states_only": True, "campaigns": tests, "choice_rejections": rejects}


def grammar_controls(runner):
    start, final = {"event": "start"}, {"event": "final", "seconds": 1.0}
    accepted, rejected = [], []
    for name, events in (
        ("no improvements", [start, final]),
        ("one improvement", [start, {"event": "improvement", "seconds": 0.5}, final]),
    ):
        runner.strict_grammar("\n".join(map(json.dumps, events)))
        accepted.append(name)
    for name, events in (
        ("missing final", [start]),
        ("wrong start", [final, final]),
        ("wrong final", [start, start]),
        ("unknown middle", [start, {"event": "debug", "seconds": 0.2}, final]),
        ("null event", [None, final]),
        ("list event", [start, [], final]),
        ("integer event", [start, 1]),
        ("boolean time", [start, {"event": "final", "seconds": True}]),
        ("NaN time", [start, {"event": "final", "seconds": math.nan}]),
        ("infinite time", [start, {"event": "final", "seconds": math.inf}]),
        ("negative time", [start, {"event": "final", "seconds": -1}]),
        ("missing time", [start, {"event": "final"}]),
    ):
        data = "\n".join(map(json.dumps, events))
        rejected.append(expect_failure(lambda d=data: runner.strict_grammar(d), name))
    rejected.append(expect_failure(lambda: runner.strict_grammar("{bad json"), "invalid JSON"))
    return {"accepted": accepted, "rejected": rejected}


def process_controls(runner, manifest):
    require(not RAW.exists(), "preserve independent raw controls")
    RAW.mkdir(parents=True)
    previous_run, previous_subprocess, previous_time = runner.RUN, runner.subprocess, runner.time
    controls, launches = [], 0
    try:
        cases = [
            ("valid-one", "one", "valid"),
            ("valid-two", "two", "valid"),
            ("terminate-timeout", "two", "terminate"),
            ("kill-timeout", "two", "kill"),
            ("duplicate-ties", "two", "duplicates"),
            ("damaged-candidate", "two", "damaged"),
            ("nonobject-event", "one", "nonobject"),
            ("unknown-event", "one", "unknown"),
            ("missing-final", "two", "missing-final"),
        ]
        for name, shell, kind in cases:
            fixture_name = "weak-pair-swap-scan" if shell == "one" else "weak-pair-two-swap-scan-v2"
            producer = HERE.parent / fixture_name
            fixture_manifest = json.loads((producer / "manifest.json").read_text())
            fixture_raw = ROOT / ("experiments/scratch/" + fixture_name + "-20261004")
            source_stdout = (fixture_raw / "stdout.jsonl").read_text()
            source_ties = json.loads((fixture_raw / "scan-ties.json").read_text())
            events = [json.loads(line) for line in source_stdout.splitlines()]
            if kind == "duplicates":
                source_ties.append(copy.deepcopy(source_ties[0]))
            elif kind == "damaged":
                events[1]["metrics"]["holes"] = 0
                source_ties[0]["metrics"]["holes"] = 0
            elif kind == "nonobject":
                events.insert(1, None)
            elif kind == "unknown":
                events.insert(1, {"event": "unknown", "seconds": 0.001})
            elif kind == "missing-final":
                events.pop()
            stdout = "\n".join(map(json.dumps, events)) + "\n"
            recorder = runner.load_recorder(ROOT / manifest["shells"][shell]["recorder_path"])
            center = runner.verify_family(
                fixture_manifest["initial"]["ids"], recorder, manifest["core_rows"]
            )
            work = RAW / name
            work.mkdir()
            runner.RUN = work
            calls = []
            fake = SimpleNamespace(returncode=0, terminated=False, killed=False)

            def communicate(timeout=None):
                calls.append(timeout)
                if kind in ("terminate", "kill") and len(calls) == 1:
                    raise subprocess.TimeoutExpired("fake-process", timeout)
                if kind == "kill" and len(calls) == 2:
                    raise subprocess.TimeoutExpired("fake-process", timeout)
                return stdout, ""

            def terminate():
                fake.terminated = True
                fake.returncode = -15

            def kill():
                fake.killed = True
                fake.returncode = -9

            fake.communicate, fake.terminate, fake.kill = communicate, terminate, kill

            def popen(command, **_kwargs):
                nonlocal launches
                launches += 1
                require(command[2] == "120", "native seconds changed")
                require(
                    Path(command[1]).read_text() == recorder.family_text(center["ids"]),
                    "wrong center",
                )
                Path(command[3] + "-ties.json").write_text(json.dumps(source_ties) + "\n")
                return fake

            runner.subprocess = SimpleNamespace(
                Popen=popen, PIPE=subprocess.PIPE, TimeoutExpired=subprocess.TimeoutExpired
            )
            clock = iter([0.0, 141.0 if kind == "kill" else 136.0 if kind == "terminate" else 10.0])
            runner.time = SimpleNamespace(monotonic=lambda: next(clock))
            before = launches
            result = runner.execute_shell(1, shell, center, manifest, recorder)
            require(launches - before == 1, "fake process relaunched")
            require(
                result["relaunch"] is False and result["budget_transfer"] is False,
                "transfer/relaunch",
            )
            require(result["complete"] is (kind == "valid"), "completion label " + name)
            require(result["passed"] is (kind == "valid"), "validation label " + name)
            require(not result["observed_covers"], "damaged fixture became a cover")
            hashes = [state["sha256"] for state in result["saved_candidates"]]
            require(len(hashes) == len(set(hashes)), "canonical candidate alias")
            require(len(hashes) == (5 if kind == "damaged" else 6), "saved candidate count " + name)
            expected_calls = (
                [135, 5, None] if kind == "kill" else [135, 5] if kind == "terminate" else [135]
            )
            require(calls == expected_calls, "watchdog call sequence " + name)
            require(fake.terminated is (kind in ("terminate", "kill")), "terminate count")
            require(fake.killed is (kind == "kill"), "kill count")
            require(
                (work / ("round-01-" + shell) / "stdout.jsonl").read_text() == stdout,
                "raw stdout lost",
            )
            require(
                (work / ("round-01-" + shell) / "shell-result.json").exists(),
                "terminal receipt lost",
            )
            for state in result["saved_candidates"]:
                require(
                    runner.sha(ROOT / state["witness_path"]) == state["sha256"],
                    "saved witness changed",
                )
                require(
                    runner.sha(ROOT / state["receipt_path"]) == state["receipt_sha256"],
                    "receipt changed",
                )
            controls.append(
                {
                    "name": name,
                    "fake_process_calls": calls,
                    "saved_families": len(hashes),
                    "passed": result["passed"],
                    "complete": result["complete"],
                    "rejected_candidates": len(result["rejected_candidate_records"]),
                }
            )
    finally:
        runner.RUN, runner.subprocess, runner.time = (
            previous_run,
            previous_subprocess,
            previous_time,
        )
    return {"controls": controls, "fake_process_launches": launches, "optimizer_launches": 0}
