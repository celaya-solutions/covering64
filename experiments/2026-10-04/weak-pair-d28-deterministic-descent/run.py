# Document:    Bounded Deterministic Weak-Pair Descent Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1c8525cc2f4d255c5992f882a27821847135c32e7eeeb1d15bf08ea1507c04ea
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reuse frozen one/two-swap scans under a gated, four-round deterministic wrapper."""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "experiments/scratch/weak-pair-d28-deterministic-descent-run-20261004"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    require(not path.exists(), f"preserve existing file: {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, path)


def load_recorder(path):
    spec = importlib.util.spec_from_file_location("frozen_recorder_" + path.parent.name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rank(state):
    return state["metrics"]["holes"], state["metrics"]["D2max"]


def verify_family(ids, recorder, cores):
    inspected = recorder.inspect_family(ids, cores)
    require(recorder.legal(inspected["metrics"]), "candidate fails fixed weak/core rows")
    blocks = [recorder.BLOCKS[i] for i in sorted(ids)]
    text = recorder.family_text(ids)
    package = recorder.verify_cover(blocks)
    standalone = recorder.STANDALONE.verify_cover(
        recorder.STANDALONE.parse_witness(text), expected_blocks=64
    )
    require(
        package["canonical_sha256"] == standalone["canonical_sha256"] == inspected["sha256"],
        "candidate canonical hash disagreement",
    )
    require(
        sorted(map(tuple, package["uncovered"])) == sorted(map(tuple, standalone["uncovered"])),
        "hole list disagreement",
    )
    cover = inspected["metrics"]["holes"] == 0
    require(package["valid"] is cover and standalone["valid"] is cover, "cover verdict")
    return json.loads(
        json.dumps(
            {
                "ids": sorted(ids),
                **inspected,
                "cover_found": cover,
                "verification": {"package": package, "standalone": standalone},
            }
        )
    )


def choose(initial, outcomes):
    require(
        len(outcomes) == 2 and all(o["complete"] and o["passed"] for o in outcomes),
        "both completed shells required for choice",
    )
    candidates = [state for outcome in outcomes for state in outcome["best_ties"]]
    require(all(rank(state) < rank(initial) for state in candidates), "nonstrict candidate")
    if not candidates:
        return None
    best = min(rank(state) for state in candidates)
    return min(
        (state for state in candidates if rank(state) == best),
        key=lambda state: tuple(state["ids"]),
    )


def run_campaign(initial, execute_shell, record_round):
    current, rounds, observed_covers = initial, [], []
    for number in range(1, 5):
        center = current
        outcomes = []
        for shell in ("one", "two"):
            outcome = execute_shell(number, shell, center)
            outcomes.append(outcome)
            observed_covers.extend(outcome["observed_covers"])
            if not outcome["passed"] or not outcome["complete"]:
                row = {
                    "round": number,
                    "center_sha256": center["sha256"],
                    "center_metrics": center["metrics"],
                    "shells": outcomes,
                    "complete": False,
                    "selected": None,
                    "stop_reason": "incomplete",
                    "cover_found": bool(observed_covers),
                    "local_closure": False,
                }
                record_round(row)
                rounds.append(row)
                return {
                    "rounds": rounds,
                    "final_center": current,
                    "stop_reason": "incomplete",
                    "observed_covers": observed_covers,
                    "local_closure": False,
                }
            if outcome["observed_covers"] and len(outcomes) == 1:
                row = {
                    "round": number,
                    "center_sha256": center["sha256"],
                    "center_metrics": center["metrics"],
                    "shells": outcomes,
                    "complete": False,
                    "selected": None,
                    "stop_reason": "cover_observed",
                    "cover_found": True,
                    "local_closure": False,
                }
                record_round(row)
                rounds.append(row)
                return {
                    "rounds": rounds,
                    "final_center": current,
                    "stop_reason": "cover_observed",
                    "observed_covers": observed_covers,
                    "local_closure": False,
                }
        winner = choose(center, outcomes)
        reason = (
            "no_strict_improvement"
            if winner is None
            else "cover"
            if winner["cover_found"]
            else "round_limit"
            if number == 4
            else None
        )
        row = {
            "round": number,
            "center_sha256": center["sha256"],
            "center_metrics": center["metrics"],
            "shells": outcomes,
            "complete": True,
            "selected": winner,
            "stop_reason": reason,
            "cover_found": bool(observed_covers),
            "local_closure": winner is None,
        }
        record_round(row)
        rounds.append(row)
        if winner is not None:
            current = winner
        if reason:
            return {
                "rounds": rounds,
                "final_center": current,
                "stop_reason": reason,
                "observed_covers": observed_covers,
                "local_closure": winner is None,
            }
    raise AssertionError("four-round bound")


def strict_grammar(stdout):
    events = [json.loads(line) for line in stdout.splitlines()]
    require(len(events) >= 2, "missing terminal events")
    require(all(isinstance(row, dict) for row in events), "nonobject event")
    require(
        events[0].get("event") == "start" and events[-1].get("event") == "final",
        "bad terminal event grammar",
    )
    require(all(row.get("event") == "improvement" for row in events[1:-1]), "unknown middle event")
    for row in events[1:]:
        value = row.get("seconds")
        require(
            type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "invalid event time",
        )


def execute_shell(number, shell, center, manifest, recorder):
    directory = RUN / f"round-{number:02d}-{shell}"
    directory.mkdir()
    center_path = directory / "center.txt"
    center_path.write_text(recorder.family_text(center["ids"]))
    require(sha(center_path) == center["sha256"], "round center changed")
    binary = ROOT / manifest["shells"][shell]["binary_path"]
    require(sha(binary) == manifest["shells"][shell]["binary_sha256"], "binary changed")
    prefix = directory / "scan"
    command = [str(binary), str(center_path), "120", str(prefix)]
    watchdog = {
        "deadline_seconds": 135,
        "grace_seconds": 5,
        "fired": False,
        "terminate_sent": False,
        "kill_sent": False,
        "relaunch": False,
    }
    started = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        stdout, stderr = process.communicate(timeout=135)
    except subprocess.TimeoutExpired:
        watchdog["fired"] = watchdog["terminate_sent"] = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            watchdog["kill_sent"] = True
            process.kill()
            stdout, stderr = process.communicate()
    elapsed = time.monotonic() - started
    (directory / "stdout.jsonl").write_text(stdout)
    (directory / "stderr.txt").write_text(stderr)
    validation, error = None, None
    try:
        require(not watchdog["fired"], "watchdog fired")
        strict_grammar(stdout)
        validation = recorder.validate(
            prefix, stdout, process.returncode, stderr, elapsed, center, manifest["core_rows"]
        )
    except (AssertionError, ValueError, KeyError, IndexError, TypeError, OSError) as exception:
        error = f"{type(exception).__name__}: {exception}"

    raw_rows = []
    if validation is not None:
        raw_rows = validation["audited_families"]
    else:
        for line in stdout.splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row.get("event") == "improvement":
                raw_rows.append(row)
        try:
            rows = json.loads(Path(str(prefix) + "-ties.json").read_text())
            if isinstance(rows, list):
                raw_rows.extend(rows)
        except (OSError, json.JSONDecodeError):
            pass
    candidates, rejected = {}, []
    original = set(center["ids"])
    (directory / "candidates").mkdir()
    for index, row in enumerate(raw_rows):
        try:
            outgoing, incoming = row["outgoing"], row["incoming"]
            outgoing = [outgoing] if shell == "one" else outgoing
            incoming = [incoming] if shell == "one" else incoming
            size = 1 if shell == "one" else 2
            require(isinstance(outgoing, list) and isinstance(incoming, list), "bad swap lists")
            require(
                len(outgoing) == len(set(outgoing)) == len(incoming) == len(set(incoming)) == size,
                "bad swap sizes",
            )
            require(
                all(type(i) is int and 0 <= i < 4368 for i in outgoing + incoming), "bad swap IDs"
            )
            require(
                set(outgoing) <= original and not set(incoming) & original,
                "swap differs from original center",
            )
            state = verify_family(
                (original - set(outgoing)) | set(incoming), recorder, manifest["core_rows"]
            )
            require(state["metrics"] == row["metrics"], "recorded candidate metrics damaged")
            if "sha256" in row:
                require(state["sha256"] == row["sha256"], "recorded candidate hash damaged")
            digest = state["sha256"]
            if digest not in candidates:
                witness = directory / "candidates" / f"{digest}.txt"
                witness.write_text(recorder.family_text(state["ids"]))
                receipt = witness.with_suffix(".json")
                dump(receipt, state)
                candidates[digest] = {k: v for k, v in state.items() if k != "verification"}
                candidates[digest].update(
                    {
                        "witness_path": str(witness.relative_to(ROOT)),
                        "receipt_path": str(receipt.relative_to(ROOT)),
                        "receipt_sha256": sha(receipt),
                    }
                )
        except (AssertionError, ValueError, KeyError, IndexError, TypeError) as exception:
            rejected.append({"row": index, "error": f"{type(exception).__name__}: {exception}"})
    if validation is not None and rejected:
        error = "Fresh candidate archive rejected a validated row"
        validation = None
    best_ties = (
        [] if validation is None else [candidates[row["sha256"]] for row in validation["best_ties"]]
    )
    if validation is not None:
        dump(directory / "candidate-audit.json", validation)
    outcome = {
        "round": number,
        "shell": shell,
        "center_sha256": center["sha256"],
        "center_metrics": center["metrics"],
        "command": command,
        "binary_sha256": manifest["shells"][shell]["binary_sha256"],
        "recorder_sha256": manifest["shells"][shell]["recorder_sha256"],
        "passed": validation is not None,
        "complete": validation is not None and validation["final"]["complete"],
        "validation_error": error,
        "watchdog": watchdog,
        "returncode": process.returncode,
        "elapsed_seconds": elapsed,
        "relaunch": False,
        "budget_transfer": False,
        "final": None if validation is None else validation["final"],
        "best_ties": best_ties,
        "saved_candidates": list(candidates.values()),
        "rejected_candidate_records": rejected,
        "observed_covers": [state for state in candidates.values() if state["cover_found"]],
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path)
            for path in sorted(directory.rglob("*"))
            if path.is_file()
        },
    }
    dump(directory / "shell-result.json", outcome)
    outcome["shell_result_path"] = str((directory / "shell-result.json").relative_to(ROOT))
    outcome["shell_result_sha256"] = sha(directory / "shell-result.json")
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--gate-sha256", required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    require(not RUN.exists() and not (HERE / "result.json").exists(), "campaign already exists")
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(args.gate) == args.gate_sha256, "gate hash mismatch")
    gate = json.loads(args.gate.read_text())
    require(gate.get("passed") is True and gate.get("decision") == "GO", "independent GO required")
    expected = {
        "manifest_sha256": sha(HERE / "manifest.json"),
        "runner_sha256": sha(__file__),
        "initial_sha256": manifest["initial"]["sha256"],
        **{
            f"{kind}_binary_sha256": manifest["shells"][kind]["binary_sha256"]
            for kind in ("one", "two")
        },
    }
    for key, value in expected.items():
        require(gate.get(key) == value, f"gate binding mismatch: {key}")
    for group in ("input_files", "sources", "raw_files", "files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, f"frozen input changed: {relative}")
    recorders = {
        kind: load_recorder(ROOT / spec["recorder_path"])
        for kind, spec in manifest["shells"].items()
    }
    initial = verify_family(manifest["initial"]["ids"], recorders["one"], manifest["core_rows"])
    require(initial == manifest["initial"], "initial profile changed")
    RUN.mkdir(parents=True)
    dump(
        RUN / "start.json",
        {"gate_path": str(args.gate.resolve()), "gate_sha256": args.gate_sha256, **expected},
    )

    def persist_round(row):
        if row["selected"] is not None:
            winner = row["selected"]
            checked = verify_family(winner["ids"], recorders["one"], manifest["core_rows"])
            require(checked["sha256"] == winner["sha256"], "selected center changed")
            path = HERE / f"center-{row['round']:02d}.txt"
            with path.open("x") as handle:
                handle.write(recorders["one"].family_text(winner["ids"]))
            dump(HERE / f"center-{row['round']:02d}-verification.json", checked)
        dump(HERE / f"round-{row['round']:02d}.json", row)

    result = run_campaign(
        initial,
        lambda n, kind, center: execute_shell(n, kind, center, manifest, recorders[kind]),
        persist_round,
    )
    result.update(
        {
            "manifest_sha256": expected["manifest_sha256"],
            "gate_sha256": args.gate_sha256,
            "runner_sha256": sha(__file__),
            "shell_launches": sum(len(row["shells"]) for row in result["rounds"]),
            "relaunch": False,
            "budget_transfer": False,
            "cover_found": bool(result["observed_covers"]),
            "scope": manifest["scope"],
            "raw_files": {
                str(path.relative_to(ROOT)): sha(path)
                for path in sorted(RUN.rglob("*"))
                if path.is_file()
            },
        }
    )
    dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                "stop_reason": result["stop_reason"],
                "cover_found": result["cover_found"],
                "rounds": len(result["rounds"]),
                "shell_launches": result["shell_launches"],
                "final_center_metrics": result["final_center"]["metrics"],
                "result_sha256": sha(HERE / "result.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
