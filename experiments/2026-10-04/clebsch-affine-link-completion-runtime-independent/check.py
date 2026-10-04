# Document:    Independent Seven Affine Completion Runtime Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      307085ed67877a4d0c2073517aba89d3b6777f3615589be223ce1495cf876b86
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Saved runtime receipts and log replay only; no solver or subprocess imports."""

import copy
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "clebsch-affine-link-completion-pilot"
GATE = HERE.parent / "clebsch-affine-link-completion-independent"
RUNTIME_SHA = "07721cefc0937da1220f54a2a10ef2fc72103e475c112cf0d03e4de83f6637c2"
ROOT_LAUNCH_SHA = "918edcdf7b222f4749a515948429ec6d0d8051ee30aef28223e3e8c48081675c"
GATE_SHA = "c91675846eaeec6101a0e8cccbf7fc6d09dde9f7e84e743ef97f77e35ec748f4"
REVIEW_SHA = "49e26e1d136e4541cc138c22bd75ab5789f577e8dc292df1d2b9d3e1d9a7b827"
MANIFEST_SHA = "ea45a44104652ef27307c253849ce89e6d3937ff6e0683ac00167c24677b3d9c"
RUNNER_SHA = "a98252d012008a3c17d45b553783b564ecb0547509a88535eb37f800d4e2f316"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def exact(actual, expected, label):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), label)


def seconds(value, maximum, label):
    require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum, label)


def check_case(case, run, result, stdout, stderr, output_files, manifest):
    number = case["case"]
    require(type(run["case"]) is int and run["case"] == number, "runtime case")
    exact(run["returncode"], 0, "worker returncode")
    require(run["watchdog_fired"] is run["kill_required"] is False, "no watchdog or kill")
    exact([run["watchdog_seconds"], run["grace_seconds"]], [35.0, 5.0], "watchdog budgets")
    seconds(run["elapsed_seconds"], 40, "process elapsed")
    exact(output_files, ["result.json"], "no candidate/value/verifier outputs")
    for key in ("case", "profile_seed", "point", "seed"):
        exact(result[key], case[key], "result " + key)
    require(result["status"] == "INFEASIBLE", "terminal status")
    require(
        result["witness"] is None
        and result["proof_generated"] is False
        and result["global_nonexistence_claim"] is False,
        "no witness/proof/global claim",
    )
    require(result["manifest_sha256"] == MANIFEST_SHA, "result manifest")
    require(result["model_sha256"] == manifest["prepared_files"][case["model"]], "result model")
    require(
        result["parameters_sha256"] == manifest["prepared_files"][case["parameters"]],
        "result parameters",
    )
    require(result["source_revision"] == manifest["source_revision"], "result source revision")
    require(
        result["ortools_version"] == manifest["ortools_version"] == "9.15.6755", "solver version"
    )
    require(result["python_version"] == manifest["python_version"], "Python version")
    require(result["scope"] == "This exact pinned partial and fixed excess profile only.", "scope")
    require(
        result["status_note"]
        == "UNKNOWN is inconclusive; INFEASIBLE lacks an independent proof certificate.",
        "caveat",
    )
    exact(result["branches"], 0, "no branches")
    exact(result["conflicts"], 0, "no search conflicts")
    seconds(result["elapsed_seconds"], run["elapsed_seconds"], "solve wrapper elapsed")
    seconds(result["solver_wall_time_seconds"], result["elapsed_seconds"], "solver walltime")
    require(stderr == "", "empty stderr")
    require(stdout.count("Starting CP-SAT solver v9.15.6755") == 1, "one solver start")
    require(stdout.count("CpSolverResponse summary:") == 1, "one terminal response")
    require(
        stdout.count("Starting presolve") == 1 and "Problem closed by presolve." in stdout,
        "presolve closure",
    )
    parameter_line = re.findall(r"^Parameters: (.*)$", stdout, re.M)
    require(len(parameter_line) == 1, "one parameters line")
    require(
        parameter_line[0]
        == (
            f"random_seed: {case['seed']} max_time_in_seconds: 30 log_search_progress: true "
            "num_search_workers: 1 log_to_stdout: true"
        ),
        "logged exact parameters",
    )
    require(
        "#Variables: 4'368" in stdout
        and "- 4'368 Booleans in [0,1]" in stdout
        and "#kLinear1: 1'365" in stdout
        and "#kLinearN: 561" in stdout
        and "#terms: 48'048" in stdout,
        "logged exact model dimensions",
    )
    fingerprint = re.findall(r"model_fingerprint: (0x[0-9a-f]+)", stdout)
    require(len(fingerprint) == 1, "one model fingerprint")
    response = stdout[stdout.index("CpSolverResponse summary:") :].strip()
    require(response == result["response_stats"].strip(), "log and response text agree")
    fields = {}
    for line in response.splitlines()[1:]:
        key, value = line.split(": ", 1)
        require(key not in fields, "unique response field")
        fields[key] = value
    require(
        fields["status"] == "INFEASIBLE" and fields["objective"] == fields["best_bound"] == "NA",
        "response no objective/solution",
    )
    for key in (
        "integers",
        "booleans",
        "conflicts",
        "branches",
        "propagations",
        "integer_propagations",
        "restarts",
        "lp_iterations",
    ):
        require(fields[key] == "0", "response no-search count " + key)
    require(
        math.isclose(
            float(fields["walltime"]),
            result["solver_wall_time_seconds"],
            rel_tol=1e-9,
            abs_tol=1e-12,
        ),
        "response walltime at printed precision",
    )
    require(
        float(fields["deterministic_time"]) >= 0 and float(fields["gap_integral"]) == 0,
        "response effort and no objective gap",
    )
    return {
        "case": number,
        "profile_seed": case["profile_seed"],
        "point": case["point"],
        "seed": case["seed"],
        "status": "INFEASIBLE",
        "model_fingerprint": fingerprint[0],
        "solver_wall_time_seconds": result["solver_wall_time_seconds"],
        "solve_wrapper_seconds": result["elapsed_seconds"],
        "process_elapsed_seconds": run["elapsed_seconds"],
        "returncode": 0,
        "presolve_closed": True,
        "witness": None,
        "proof_generated": False,
        "independently_checked_nonexistence": False,
    }


def damage_controls(args):
    case, run, result, stdout, stderr, files, manifest = args
    rejected = []

    def reject(label, changed):
        try:
            check_case(*changed)
        except (ValueError, KeyError):
            rejected.append(label)
        else:
            raise AssertionError("accepted runtime damage " + label)

    for key, value in [
        ("status", "FEASIBLE"),
        ("seed", 2026106302),
        ("proof_generated", True),
        ("model_sha256", "0" * 64),
        ("parameters_sha256", "0" * 64),
        ("witness", {"path": "fake.txt"}),
        ("branches", True),
        ("solver_wall_time_seconds", 31.0),
        ("response_stats", "truncated"),
    ]:
        changed = copy.deepcopy(result)
        changed[key] = value
        reject("result_" + key, (case, run, changed, stdout, stderr, files, manifest))
    changed = copy.deepcopy(run)
    changed["watchdog_fired"] = True
    reject("false_watchdog", (case, changed, result, stdout, stderr, files, manifest))
    changed = copy.deepcopy(run)
    changed["returncode"] = 1
    reject("wrong_worker_exit", (case, changed, result, stdout, stderr, files, manifest))
    reject(
        "extra_solver_start",
        (
            case,
            run,
            result,
            "Starting CP-SAT solver v9.15.6755\n" + stdout,
            stderr,
            files,
            manifest,
        ),
    )
    reject(
        "wrong_log_seed",
        (case, run, result, stdout.replace("2026106301", "2026106302"), stderr, files, manifest),
    )
    reject(
        "truncated_log",
        (case, run, result, stdout.split("CpSolverResponse")[0], stderr, files, manifest),
    )
    reject("nonempty_stderr", (case, run, result, stdout, "error", files, manifest))
    reject(
        "unexpected_candidate",
        (case, run, result, stdout, stderr, ["result.json", "witness.txt"], manifest),
    )
    return rejected


def main():
    require(not (HERE / "review.json").exists(), "preserve independent receipt")
    for path, digest in [
        (PRODUCER / "runtime.json", RUNTIME_SHA),
        (PRODUCER / "root-launch.json", ROOT_LAUNCH_SHA),
        (GATE / "gate.json", GATE_SHA),
        (GATE / "review.json", REVIEW_SHA),
        (PRODUCER / "manifest.json", MANIFEST_SHA),
        (PRODUCER / "run.py", RUNNER_SHA),
    ]:
        require(sha(path) == digest, "frozen runtime binding: " + path.name)
    manifest = read(PRODUCER / "manifest.json")
    pinned_files = {}
    for group in ("dependencies", "prepared_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, "prepared dependency " + relative)
            pinned_files[relative] = digest
    require(len(pinned_files) == 54, "all54 preparation pins")
    gate = read(GATE / "gate.json")
    require(
        gate["decision"] == "GO"
        and gate["passed"] is True
        and gate["review_sha256"] == REVIEW_SHA
        and gate["manifest_sha256"] == MANIFEST_SHA
        and gate["runner_sha256"] == RUNNER_SHA,
        "independent launch gate",
    )
    launch = read(PRODUCER / "root-launch.json")
    require(
        launch["gate_sha256"] == GATE_SHA
        and launch["manifest_sha256"] == MANIFEST_SHA
        and launch["source_revision"] == manifest["source_revision"],
        "root launch binding",
    )
    exact(
        [launch["calls_max"], launch["seconds_each"], launch["root_pin_checks"]],
        [7, 30, 54],
        "root launch budgets/pins",
    )
    seconds(launch["started_unix"], 10**12, "recorded launch timestamp")
    exact(
        read(PRODUCER / "run-started.json"),
        {"manifest_sha256": MANIFEST_SHA, "max_calls": 7},
        "exclusive run marker",
    )
    runtime = read(PRODUCER / "runtime.json")
    require(
        runtime["manifest_sha256"] == MANIFEST_SHA and runtime["complete"] is True,
        "runtime campaign completed",
    )
    calls = runtime["calls"]
    require(len(calls) == len(manifest["cases"]) == 7, "exactly seven receipts")
    require([r["case"] for r in calls] == list(range(1, 8)), "ordered receipts")
    directories = sorted(p.name for p in PRODUCER.glob("case-*-output"))
    require(directories == [f"case-{i}-output" for i in range(1, 8)], "exact seven output dirs")
    saved = {}
    summaries = []
    first_args = None
    for case, run in zip(manifest["cases"], calls, strict=True):
        number = case["case"]
        result_path = PRODUCER / f"case-{number}-output/result.json"
        stdout_path = PRODUCER / f"case-{number}-stdout.log"
        stderr_path = PRODUCER / f"case-{number}-stderr.log"
        for path, digest in [
            (result_path, run["result_sha256"]),
            (stdout_path, run["stdout_sha256"]),
            (stderr_path, run["stderr_sha256"]),
        ]:
            require(sha(path) == digest, "runtime file hash " + path.name)
            saved[str(path.relative_to(ROOT))] = digest
        result = read(result_path)
        args = (
            case,
            run,
            result,
            stdout_path.read_text(),
            stderr_path.read_text(),
            sorted(p.name for p in result_path.parent.iterdir()),
            manifest,
        )
        summaries.append(check_case(*args))
        if first_args is None:
            first_args = args
    controls = damage_controls(first_args)
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "runtime_sha256": RUNTIME_SHA,
        "root_launch_sha256": ROOT_LAUNCH_SHA,
        "run_started_sha256": sha(PRODUCER / "run-started.json"),
        "gate_sha256": GATE_SHA,
        "model_gate_review_sha256": REVIEW_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": RUNNER_SHA,
        "prepared_pins_checked": len(pinned_files),
        "prepared_files": pinned_files,
        "runtime_files": saved,
        "cases": summaries,
        "solver_status_counts": {"INFEASIBLE": 7},
        "worker_exit_codes": [0] * 7,
        "solver_wall_seconds_total": sum(r["solver_wall_time_seconds"] for r in summaries),
        "process_elapsed_seconds_total": sum(r["process_elapsed_seconds"] for r in summaries),
        "candidate_count": 0,
        "proof_certificates_checked": 0,
        "real_process_launches": 0,
        "optimizer_calls": 0,
        "damaged_controls_rejected": controls,
        "scope": (
            "Saved results and logs agree with seven conditional frozen models. "
            "All seven CP-SAT statuses are INFEASIBLE after presolve, with no witnesses. "
            "No independent nonexistence certificate is present. The ordered calls "
            "and frozen sequential runner support the recorded launch order; receipts "
            "do not include separate per-child absolute start timestamps. "
            "No statement about other links, profiles, or unrestricted existence."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(HERE / "review.json"),
                "solver_wall_seconds_total": receipt["solver_wall_seconds_total"],
                "process_seconds_total": receipt["process_elapsed_seconds_total"],
                "damaged_controls": len(controls),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
