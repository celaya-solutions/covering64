# Document:    Independent Seven Affine Link Completion Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a201c9bb14af825dc4e3af4e0a4a35a2ab8470ad7ae58cfbc2336cbeb5be799b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Full serialized model audit and mocked launcher controls; never solve."""

import contextlib
import importlib.util
import io
import json
import signal
import subprocess
import tempfile
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from unittest.mock import Mock, call, patch

import ortools
from google.protobuf import text_format
from ortools.sat import sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "clebsch-affine-link-completion-pilot"
MANIFEST_SHA = "ea45a44104652ef27307c253849ce89e6d3937ff6e0683ac00167c24677b3d9c"
RUNNER_SHA = "a98252d012008a3c17d45b553783b564ecb0547509a88535eb37f800d4e2f316"
FILES_SHA = "990bf27c5c641a8def312f5f1781ed8c1eaf583666eed9fd77f59f3fa3deea9a"
SUPPORT_REVIEW_SHA = "8c7fd636138ee781dc308ce04c1eee47da63345b0eb3805a611ae794a43ab6a3"
PAIRS = [(0, 10), (40, 13), (4, 7), (18, 3), (16, 3), (16, 8), (60, 3)]
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
RANK = {b: i for i, b in enumerate(BLOCKS)}
CONTAINING = {t: [] for t in TRIPLES}
for index, block in enumerate(BLOCKS):
    for triple in combinations(block, 3):
        CONTAINING[triple].append(index)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def exact(actual, expected, name):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), name)


def linear(row, indices, target, name):
    require(row.has_linear() and not row.name and not row.enforcement_literal, name + " kind")
    require(list(row.linear.vars) == indices, name + " exact variables")
    require(list(row.linear.coeffs) == [1] * len(indices), name + " unit coefficients")
    require(list(row.linear.domain) == [target, target], name + " exact equality")


def check_model(model, point, profile, selected):
    p = model.proto
    require(len(p.variables) == 4368 and len(p.constraints) == 1926, "full model dimensions")
    require(
        not p.name
        and not p.has_objective()
        and not p.has_floating_point_objective()
        and not p.has_solution_hint()
        and not p.has_symmetry()
        and not p.assumptions
        and not p.search_strategy,
        "no hidden restrictions or objective",
    )
    for index, variable in enumerate(p.variables):
        require(
            variable.name == f"block_{index}" and list(variable.domain) == [0, 1],
            "lex binary variables",
        )
    for row_id, triple in enumerate(TRIPLES):
        linear(
            p.constraints[row_id],
            CONTAINING[triple],
            1 + (triple in profile),
            "triple" + str(row_id),
        )
    linear(p.constraints[560], list(range(4368)), 64, "cardinality")
    fixed = [i for i, b in enumerate(BLOCKS) if point in b]
    require(len(fixed) == 1365 and len(selected) == 20 and selected <= set(fixed), "fixed sets")
    for offset, index in enumerate(fixed, 561):
        linear(p.constraints[offset], [index], int(index in selected), "membership" + str(index))
    require(not model.validate(), "OR-Tools syntactic validation")


def damage_controls(model, point, profile, selected):
    controls = []

    def damage(name, change):
        candidate = model.clone()
        change(candidate)
        try:
            check_model(candidate, point, profile, selected)
        except ValueError:
            controls.append(name)
        else:
            raise AssertionError("accepted model damage " + name)

    def set_domain(m):
        m.proto.variables[0].domain[1] = 2

    def duplicate_var(m):
        m.proto.constraints[0].linear.vars[1] = m.proto.constraints[0].linear.vars[0]

    def bad_coefficient(m):
        m.proto.constraints[0].linear.coeffs[0] = 2

    def loose_demand(m):
        m.proto.constraints[0].linear.domain[1] = 2

    def wrong_cardinality(m):
        m.proto.constraints[560].linear.domain[0] = 63

    def flipped_membership(m):
        row = m.proto.constraints[561].linear
        row.domain[0] = row.domain[1] = 1 - row.domain[0]

    def guarded_row(m):
        m.proto.constraints[0].enforcement_literal.append(0)

    damage("nonbinary_variable", set_domain)
    damage("duplicate_triple_incidence", duplicate_var)
    damage("nonunit_coefficient", bad_coefficient)
    damage("weakened_triple_equality", loose_demand)
    damage("wrong_cardinality", wrong_cardinality)
    damage("flipped_fixed_membership", flipped_membership)
    damage("guarded_triple_row", guarded_row)
    damage("extra_restriction", lambda m: m.add(m.get_bool_var_from_proto_index(0) == 0))
    damage("objective", lambda m: m.minimize(m.get_bool_var_from_proto_index(0)))
    damage("hint", lambda m: m.add_hint(m.get_bool_var_from_proto_index(0), 1))
    damage("assumption", lambda m: m.add_assumption(m.get_bool_var_from_proto_index(0)))
    damage(
        "search_strategy",
        lambda m: m.add_decision_strategy(
            [m.get_bool_var_from_proto_index(0)], cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE
        ),
    )
    return controls


def mock_runner(manifest):
    spec = importlib.util.spec_from_file_location("frozen_affine_runner", PRODUCER / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    require(runner.check_pins() == manifest, "real read-only producer pin validation")
    controls = []
    scenarios = [
        ("normal", [0], [call(timeout=35.0)], [], False, False),
        (
            "term",
            [subprocess.TimeoutExpired("mock", 35), -15],
            [call(timeout=35.0), call(timeout=5.0)],
            [call(12345, signal.SIGTERM)],
            True,
            False,
        ),
        (
            "kill",
            [subprocess.TimeoutExpired("mock", 35), subprocess.TimeoutExpired("mock", 5), -9],
            [call(timeout=35.0), call(timeout=5.0), call()],
            [call(12345, signal.SIGTERM), call(12345, signal.SIGKILL)],
            True,
            True,
        ),
    ]
    for name, answers, waits, signals, fired, killed in scenarios:
        process = Mock(pid=12345)
        process.wait.side_effect = answers
        stdout, stderr = object(), object()
        with (
            patch.object(runner.subprocess, "Popen", return_value=process) as popen,
            patch.object(runner.os, "killpg") as killpg,
        ):
            result = runner.bounded_child(["mock"], stdout, stderr)
        require(process.wait.call_args_list == waits, "watchdog waits")
        require(killpg.call_args_list == signals, "watchdog signals")
        popen.assert_called_once_with(
            ["mock"], cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True
        )
        require(
            result["returncode"] == answers[-1]
            and result["watchdog_fired"] is fired
            and result["kill_required"] is killed,
            "watchdog receipt",
        )
        controls.append(name)
    with tempfile.TemporaryDirectory(prefix="affine-completion-gate-") as temp:
        temp_path = Path(temp)
        receipts = [
            {
                "returncode": i % 2,
                "watchdog_fired": False,
                "kill_required": False,
                "elapsed_seconds": 0.0,
                "watchdog_seconds": 35.0,
                "grace_seconds": 5.0,
            }
            for i in range(7)
        ]
        with (
            patch.object(runner, "HERE", temp_path),
            patch.object(runner, "check_pins", return_value=manifest) as pins,
            patch.object(runner, "sha", return_value="mock-only-hash"),
            patch.object(runner, "dump") as dump,
            patch.object(runner, "bounded_child", side_effect=receipts) as child,
            patch.object(runner.subprocess, "Popen", side_effect=AssertionError("real process")),
            patch.object(cp_model.CpSolver, "solve", side_effect=AssertionError("optimizer")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            runner.run()
            require(
                child.call_count == 7 and pins.call_count == 8 and dump.call_count == 7,
                "exactly seven sequential calls and rechecks",
            )
            require(
                [c.args[0][-2:] for c in child.call_args_list]
                == [["_worker", str(i)] for i in range(1, 8)],
                "case order",
            )
            require(dump.call_args.args[1]["complete"] is True, "final seven-call receipt")
            try:
                runner.run()
            except FileExistsError:
                pass
            else:
                raise AssertionError("relaunch guard failed")
            require(child.call_count == 7, "no relaunch or retry")
        controls.extend(["sequential_seven_calls", "exclusive_relaunch_guard"])
    return controls


def main():
    require(not (HERE / "review.json").exists(), "preserve completed review")
    require(sha(PRODUCER / "manifest.json") == MANIFEST_SHA, "manifest pin")
    require(sha(PRODUCER / "run.py") == RUNNER_SHA, "runner pin")
    require(sha(PRODUCER / "files.json") == FILES_SHA, "files pin")
    for name, digest in read(PRODUCER / "files.json").items():
        require(sha(PRODUCER / name) == digest, "prepared index " + name)
    support_path = HERE.parent / "clebsch-affine-link-support-screen-independent/review.json"
    require(
        sha(support_path) == SUPPORT_REVIEW_SHA and read(support_path)["passed"] is True,
        "independent support screen passed",
    )
    manifest = read(PRODUCER / "manifest.json")
    for group in ("dependencies", "prepared_files"):
        for path, digest in manifest[group].items():
            require(sha(ROOT / path) == digest, "dependency " + path)
    require(
        manifest["source_sha256"] == RUNNER_SHA
        and manifest["ortools_version"] == ortools.__version__ == "9.15.6755",
        "versions",
    )
    required = {
        "variables": 4368,
        "global_exact_triple_rows": 560,
        "cardinality_rows": 1,
        "fixed_membership_rows": 1365,
        "total_rows": 1926,
        "max_calls": 7,
        "total_solver_budget_seconds": 210,
        "retry_or_budget_transfer": False,
        "objective": None,
        "hints": None,
        "propagation_pruning_used_to_restrict_model": False,
        "search_launches_during_preparation": 0,
    }
    for key, value in required.items():
        exact(manifest[key], value, "manifest " + key)
    require(not (PRODUCER / "run-started.json").exists(), "prelaunch gate")
    require(not list(PRODUCER.glob("case-*-output")), "no production outputs")
    cases = manifest["cases"]
    require(len(cases) == 7, "seven cases")
    profiles = read(
        ROOT / "experiments/2026-10-03/independent-geometry/independent-audit-seed-profiles.json"
    )
    maps = read(HERE.parent / "clebsch-point-link-construction/recipe-point-maps.json")
    reports = []
    for number, case in enumerate(cases, 1):
        pair = PAIRS[number - 1]
        require(
            case["case"] == number
            and (case["profile_seed"], case["point"]) == pair
            and case["seed"] == 2026106300 + number,
            "case and seed order",
        )
        require(
            (case["seconds"], case["workers"], case["watchdog_seconds"], case["grace_seconds"])
            == (30.0, 1, 35.0, 5.0),
            "per-case budgets",
        )
        link = next(r for r in maps if (r["profile_seed"], r["point"]) == pair)
        require(
            case["partial_sha256"] == link["partial_canonical_sha256"]
            and case["class"] == link["class"],
            "pinned surviving link",
        )
        partial = [
            tuple(map(int, line.split()))
            for line in (ROOT / case["partial"]).read_text().splitlines()
        ]
        require(
            len(partial) == len(set(partial)) == 20
            and all(
                tuple(sorted(b)) == b and len(b) == len(set(b)) == 5 and case["point"] in b
                for b in partial
            ),
            "partial",
        )
        require(sha(ROOT / case["partial"]) == case["partial_sha256"], "partial bytes")
        profile = {tuple(t) for t in profiles[str(case["profile_seed"])]}
        require(read(ROOT / case["profile"]) == sorted(map(list, profile)), "exact profile copy")
        selected = {RANK[b] for b in partial}
        model = cp_model.CpModel()
        require(model.proto.parse_text_format((ROOT / case["model"]).read_text()), "model parse")
        check_model(model, case["point"], profile, selected)
        params = sat_parameters_pb2.SatParameters()
        text_format.Parse((ROOT / case["parameters"]).read_text(), params)
        fields = {field.name: value for field, value in params.ListFields()}
        exact(
            fields,
            {
                "random_seed": case["seed"],
                "max_time_in_seconds": 30.0,
                "log_search_progress": True,
                "num_search_workers": 1,
                "log_to_stdout": True,
            },
            "only exact five parameter settings",
        )
        counts = Counter(t for b in partial for t in combinations(b, 3))
        residual = [
            {"triple": list(t), "demand": 1 + (t in profile) - counts[t]}
            for t in TRIPLES
            if case["point"] not in t
        ]
        exact(read(ROOT / case["residual"]), residual, "all455 residual rows")
        require(
            sum(r["demand"] for r in residual) == 440 and min(r["demand"] for r in residual) >= 0,
            "remaining44-block incidence total",
        )
        require(case["zero_residual_rows"] == sum(r["demand"] == 0 for r in residual), "zero rows")
        report = read(PRODUCER / f"case-{number}-partial-verification.json")
        require(
            report["package"]["canonical_sha256"]
            == report["standalone"]["canonical_sha256"]
            == case["partial_sha256"],
            "dual receipt hash",
        )
        require(
            report["package"]["covered"] == report["standalone"]["covered_subsets"] == 185
            and len(report["package"]["uncovered"])
            == report["standalone"]["uncovered_count"]
            == 375,
            "partial coverage receipt",
        )
        require(
            report["package"]["valid"] is report["standalone"]["valid"] is False,
            "partial never full cover",
        )
        reports.append(
            {
                "case": number,
                "profile_seed": pair[0],
                "point": pair[1],
                "seed": case["seed"],
                "model_sha256": sha(ROOT / case["model"]),
                "parameters_sha256": sha(ROOT / case["parameters"]),
                "partial_sha256": case["partial_sha256"],
                "all_rows_verified": 1926,
                "free_point_avoiding_variables": 3003,
                "fixed_selected": 20,
            }
        )
        if number == 1:
            damaged = damage_controls(model, case["point"], profile, selected)
    runner_controls = mock_runner(manifest)
    result = {
        "passed": True,
        "decision": "GO",
        "checker_sha256": sha(Path(__file__)),
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": RUNNER_SHA,
        "producer_files_sha256": FILES_SHA,
        "support_review_sha256": SUPPORT_REVIEW_SHA,
        "cases": reports,
        "damaged_models_rejected": damaged,
        "mock_runner_controls": runner_controls,
        "optimizer_calls": 0,
        "real_process_launches": 0,
        "real_signals_sent": 0,
        "scope": (
            "Seven conditional exact64 models only. Full4368 lex binary variables; "
            "560 exact profile triples, one exact64 row,1365 fixed point memberships. "
            "Other3003 variables remain unfixed. No hints, objective, or screen pruning. "
            "Only root may launch the seven sequential30s one-worker calls. "
            "UNKNOWN is inconclusive; solver INFEASIBLE is not a checked theorem."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    gate = {
        key: result[key]
        for key in (
            "passed",
            "decision",
            "manifest_sha256",
            "runner_sha256",
            "support_review_sha256",
            "optimizer_calls",
        )
    }
    gate.update(
        {
            "review_sha256": sha(HERE / "review.json"),
            "max_calls": 7,
            "seconds_per_call": 30,
            "workers": 1,
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
