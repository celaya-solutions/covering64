# Document:    Independent Eight Circulant Exact Profile Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      12aa6bee42bf8f67d6ce7f545ef2540da3edf070cc0fdbc1600fc2cdbfb24c2a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Inspect all serialized rows and mock every launcher stop path; no solves."""

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from unittest.mock import Mock, patch

import ortools
from google.protobuf import text_format
from ortools.sat import sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "circulant-exact-profile-pilot"
RAW = ROOT / "experiments/scratch/circulant-exact-profile-pilot-20261004"
ARITHMETIC = HERE.parent / "circulant-pair-graph-screen"
MANIFEST_SHA = "129002dca2ab140a5be66a8879fd7d97fee41f4203ba186d93ca720b335aa7da"
RUNNER_SHA = "68fbd3cd539d9d12589de39bef55ff66605f2d3d9227a86b5ed4773253cae0fc"
ARITHMETIC_REVIEW_SHA = "d83b9a199c51088a3242e9d42c303aa86ee1b5a0b1cd47846577f4bb78e7e928"
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
CARRIERS = {t: [] for t in TRIPLES}
for index, block in enumerate(BLOCKS):
    for triple in combinations(block, 3):
        CARRIERS[triple].append(index)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def exact(actual, expected, name):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), name)


def linear(row, indices, value):
    require(
        row.has_linear() and not row.name and not row.enforcement_literal, "unguarded linear row"
    )
    require(list(row.linear.vars) == indices, "full exact incidence")
    require(list(row.linear.coeffs) == [1] * len(indices), "unit coefficients")
    require(list(row.linear.domain) == [value, value], "exact equality domain")


def model_check(model, excess):
    proto = model.proto
    require(len(proto.variables) == 4368 and len(proto.constraints) == 561, "model dimensions")
    require(
        not proto.name
        and not proto.has_objective()
        and not proto.has_floating_point_objective()
        and not proto.has_solution_hint()
        and not proto.has_symmetry()
        and not proto.assumptions
        and not proto.search_strategy,
        "no hidden restrictions",
    )
    for index, variable in enumerate(proto.variables):
        require(
            variable.name == f"block_{index}" and list(variable.domain) == [0, 1],
            "all4368 lex variables free Boolean",
        )
    linear(proto.constraints[0], list(range(4368)), 64)
    for row_id, triple in enumerate(TRIPLES, 1):
        linear(proto.constraints[row_id], CARRIERS[triple], 1 + (triple in excess))
    require(not model.validate(), "syntactic model validation")


def model_controls(model, excess):
    rejected = []

    def damage(name, mutate):
        candidate = model.clone()
        mutate(candidate)
        try:
            model_check(candidate, excess)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError("accepted model damage " + name)

    def fixed_variable(m):
        m.proto.variables[0].domain[1] = 0

    def nonbinary(m):
        m.proto.variables[0].domain[1] = 2

    def duplicate_incidence(m):
        m.proto.constraints[1].linear.vars[1] = m.proto.constraints[1].linear.vars[0]

    def coefficient(m):
        m.proto.constraints[1].linear.coeffs[0] = 2

    def weak_demand(m):
        m.proto.constraints[1].linear.domain[1] += 1

    def wrong_total(m):
        m.proto.constraints[0].linear.domain[0] = 63

    def guarded(m):
        m.proto.constraints[1].enforcement_literal.append(0)

    damage("fixed_variable", fixed_variable)
    damage("nonbinary_variable", nonbinary)
    damage("duplicate_incidence", duplicate_incidence)
    damage("wrong_coefficient", coefficient)
    damage("weakened_demand", weak_demand)
    damage("wrong_cardinality", wrong_total)
    damage("guarded_row", guarded)
    damage("added_link_restriction", lambda m: m.add(m.get_bool_var_from_proto_index(0) == 0))
    damage("objective", lambda m: m.minimize(m.get_bool_var_from_proto_index(0)))
    damage("hint", lambda m: m.add_hint(m.get_bool_var_from_proto_index(0), 1))
    damage("assumption", lambda m: m.add_assumption(m.get_bool_var_from_proto_index(0)))
    damage(
        "search_strategy",
        lambda m: m.add_decision_strategy(
            [m.get_bool_var_from_proto_index(0)], cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE
        ),
    )
    return rejected


def runner_controls(manifest):
    spec = importlib.util.spec_from_file_location("frozen_circulant_runner", PRODUCER / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    require(runner.SEEDS == list(range(2026106401, 2026106409)), "runner seeds")
    results = []
    for scenario in (
        "normal",
        "term",
        "kill",
        "nonzero",
        "missing",
        "model_invalid",
        "invalid_gate",
        "wrong_gate_manifest",
        "existing_child",
    ):
        with tempfile.TemporaryDirectory(
            prefix="circulant-gate-", dir=ROOT / "experiments/scratch"
        ) as tmp:
            temp = Path(tmp)
            here, raw = temp / "producer", temp / "raw"
            here.mkdir()
            raw.mkdir()
            (here / "manifest.json").write_bytes((PRODUCER / "manifest.json").read_bytes())
            for index in range(8):
                (raw / f"case-{index + 1:02d}").mkdir()
            gate = {
                "passed": True,
                "launch_permitted": scenario != "invalid_gate",
                "manifest_sha256": "0" * 64 if scenario == "wrong_gate_manifest" else MANIFEST_SHA,
            }
            gate_path = temp / "gate.json"
            gate_path.write_text(json.dumps(gate))
            if scenario == "existing_child":
                (raw / "case-01/child-result.json").write_text("{}")
            processes, commands = [], []

            def fake_popen(command, **kwargs):
                index = int(command[-1])
                require(index == len(commands), "ordered sequential calls")
                require(command[-3:-1] == ["--child", "--profile"], "child mode and profile")
                require(
                    kwargs == {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True},
                    "exact subprocess capture",
                )
                commands.append(command)
                code = (
                    -9
                    if scenario == "kill"
                    else -15
                    if scenario == "term"
                    else (1 if scenario == "nonzero" else 0)
                )
                process = Mock(returncode=code)
                answers = [("", "")]
                if scenario == "term":
                    answers.insert(0, subprocess.TimeoutExpired("mock", 35))
                if scenario == "kill":
                    answers = [
                        subprocess.TimeoutExpired("mock", 35),
                        subprocess.TimeoutExpired("mock", 5),
                        ("", ""),
                    ]
                process.communicate.side_effect = answers
                if scenario != "missing":
                    (raw / f"case-{index + 1:02d}/child-result.json").write_text(
                        json.dumps(
                            {
                                "index": index,
                                "seed": 2026106401 + index,
                                "status": "MODEL_INVALID"
                                if scenario == "model_invalid"
                                else "UNKNOWN",
                                "complete64": False,
                                "independent_infeasibility_proof": False,
                            }
                        )
                    )
                processes.append(process)
                return process

            with (
                patch.object(runner, "HERE", here),
                patch.object(runner, "RAW", raw),
                patch.object(runner.subprocess, "Popen", side_effect=fake_popen) as popen,
                patch.object(
                    cp_model.CpSolver, "solve", side_effect=AssertionError("solver called")
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                if scenario in ("invalid_gate", "wrong_gate_manifest", "existing_child"):
                    try:
                        runner.execute(gate_path)
                    except AssertionError:
                        pass
                    else:
                        raise AssertionError("bad precondition admitted " + scenario)
                    require(popen.call_count == 0, "no precondition launch")
                    results.append({"scenario": scenario, "mock_calls": 0, "passed": True})
                    continue
                runner.execute(gate_path)
                expected_calls = 8 if scenario == "normal" else 1
                require(popen.call_count == expected_calls, "correct batch stopping")
                receipt = read(here / "result.json")
                require(receipt["finished_calls"] == expected_calls, "saved completed calls")
                for process in processes:
                    timeouts = [c.kwargs.get("timeout") for c in process.communicate.call_args_list]
                    expected = (
                        [35, 5, None]
                        if scenario == "kill"
                        else ([35, 5] if scenario == "term" else [35])
                    )
                    require(timeouts == expected, "watchdog wait sequence")
                    require(
                        process.terminate.call_count == int(scenario in ("term", "kill")),
                        "termination count",
                    )
                    require(process.kill.call_count == int(scenario == "kill"), "kill count")
                if scenario == "normal":
                    try:
                        runner.execute(gate_path)
                    except AssertionError:
                        pass
                    else:
                        raise AssertionError("relaunch admitted")
                    require(popen.call_count == 8, "no relaunch")
                results.append({"scenario": scenario, "mock_calls": expected_calls, "passed": True})
    return results


def main():
    require(not (HERE / "review.json").exists(), "fresh review")
    require(
        sha(PRODUCER / "manifest.json") == MANIFEST_SHA and sha(PRODUCER / "run.py") == RUNNER_SHA,
        "frozen pilot",
    )
    arithmetic_review = HERE.parent / "circulant-pair-graph-independent/review.json"
    require(
        sha(arithmetic_review) == ARITHMETIC_REVIEW_SHA and read(arithmetic_review)["passed"],
        "independent arithmetic",
    )
    manifest = read(PRODUCER / "manifest.json")
    require(len(manifest["pins"]) == 27, "27 frozen files")
    for relative, digest in manifest["pins"].items():
        require(sha(ROOT / relative) == digest, "pin " + relative)
    required = {
        "variables": 4368,
        "binary_variables": 4368,
        "fixed_variables": 0,
        "rows": 561,
        "cardinality": 64,
        "triple_rows": 560,
        "triple_demand_one": 480,
        "triple_demand_two": 80,
        "hint": None,
        "objective": None,
        "fixed_links": None,
        "fixed_neighborhoods": None,
        "cover_symmetry_constraints": None,
        "calls": 8,
        "sequential": True,
        "workers_per_call": 1,
        "native_seconds_per_call": 30,
        "native_seconds_total_cap": 240,
        "watchdog_seconds_per_call": 35,
        "termination_grace_seconds_per_call": 5,
        "relaunch": False,
        "retries": False,
        "budget_transfer": False,
    }
    for key, value in required.items():
        exact(manifest[key], value, "manifest " + key)
    require(manifest["ortools"] == ortools.__version__ == "9.15.6755", "solver version")
    require(
        not (PRODUCER / "launch.json").exists() and not (PRODUCER / "result.json").exists(),
        "prelaunch review",
    )
    profiles = read(ARITHMETIC / "profiles.json")
    require(len(manifest["cases"]) == len(profiles) == 8, "eight cases")
    reports = []
    for index, case in enumerate(manifest["cases"]):
        exact(case["index"], index, "case index")
        require(
            case["name"] == f"case-{index + 1:02d}" and case["seed"] == 2026106401 + index,
            "case names/seeds",
        )
        exact(case["center_offsets"], profiles[index]["center_offsets"], "profile order")
        require(
            case["point_link_core_type"] == profiles[index]["point_links"][0]["type"],
            "core metadata",
        )
        folder = RAW / case["name"]
        require(not (folder / "child-result.json").exists(), "unlaunched case")
        require(
            sha(folder / "model.pbtxt") == case["model_sha256"]
            and sha(folder / "parameters.pbtxt") == case["parameters_sha256"],
            "case hashes",
        )
        model = cp_model.CpModel()
        require(model.proto.parse_text_format((folder / "model.pbtxt").read_text()), "model parse")
        excess = {tuple(t) for t in profiles[index]["excess_triples"]}
        model_check(model, excess)
        params = sat_parameters_pb2.SatParameters()
        text_format.Parse((folder / "parameters.pbtxt").read_text(), params)
        exact(
            {field.name: value for field, value in params.ListFields()},
            {
                "random_seed": case["seed"],
                "max_time_in_seconds": 30.0,
                "log_search_progress": True,
                "num_search_workers": 1,
                "log_to_stdout": False,
            },
            "only exact five parameter fields",
        )
        reports.append(
            {
                "index": index,
                "seed": case["seed"],
                "model_sha256": case["model_sha256"],
                "parameters_sha256": case["parameters_sha256"],
                "variables": 4368,
                "rows_checked": 561,
                "fixed_variables": 0,
            }
        )
        if index == 0:
            damaged = model_controls(model, excess)
    reflection = []
    family = [{tuple(t) for t in row["excess_triples"]} for row in profiles]
    for index, excess in enumerate(family):
        image = {tuple(sorted(1 + (-(p - 1)) % 16 for p in t)) for t in excess}
        target = family.index(image)
        require(target == 7 - index, "reflection index pairs")
        reflection.append(target)
    controls = runner_controls(manifest)
    output = {
        "passed": True,
        "launch_permitted": True,
        "decision": "GO",
        "checker_sha256": sha(Path(__file__)),
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": RUNNER_SHA,
        "arithmetic_review_sha256": ARITHMETIC_REVIEW_SHA,
        "cases": reports,
        "malformed_models_rejected": damaged,
        "mock_runner_controls": controls,
        "reflection_profile_index_map": reflection,
        "optimizer_calls": 0,
        "real_process_launches": 0,
        "real_signals_sent": 0,
        "scope": (
            "Eight fixed arithmetic excess profiles on a non-Clebsch circulant graph. "
            "All4368 block variables are free Boolean; exact64 and560 exact triple "
            "equations only. No local link, neighborhood, incidence, or block-family "
            "symmetry restriction. Profiles have reflection pairs; no nonisomorphism "
            "claim. Root alone may launch eight sequential30s one-worker calls. "
            "INFEASIBLE without an independent proof is not a theorem."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    gate = {
        key: output[key]
        for key in (
            "passed",
            "launch_permitted",
            "manifest_sha256",
            "runner_sha256",
            "arithmetic_review_sha256",
            "optimizer_calls",
        )
    }
    gate.update(
        {
            "review_sha256": sha(HERE / "review.json"),
            "max_calls": 8,
            "seconds_per_call": 30,
            "workers_per_call": 1,
            "watchdog_seconds": 35,
            "grace_seconds": 5,
        }
    )
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "review_sha256": sha(HERE / "review.json"),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
