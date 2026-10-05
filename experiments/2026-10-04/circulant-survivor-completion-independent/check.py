# Document:    Independent Circulant Survivor Completion Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e797db630c6ec5bb7be537eac5fd077e0634a86ac2f701fe7f886ffe75557d3c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reconstruct selected conditional models and test launch code with mocks only."""

import contextlib
import copy
import gzip
import importlib.util
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
PRODUCER = BASE / "circulant-survivor-completion-pilot"
CAT = BASE / "circulant-chosen-link-catalog"
ORBIT = BASE / "circulant-all-excess-independent"
HELPER = BASE / "clebsch-affine-link-completion-pilot/run.py"
PROPAGATION_AUDIT = (
    BASE / "circulant-chosen-link-row-propagation-full-runtime-independent/review.json"
)
RUNNER_SHA = "a79a970f10f9ebf3964d41c2d10c0878e3d3f03f46b6cf3dd3138f84652a7bce"
MANIFEST_SHA = "f90070381a196172c3e1f0139774846e70fa247977ddb8d01e431c543c6f7584"
FILES_SHA = "85f22561e7755dd95a5377aeb0b8e2dd3bb7c3ca4c8564c07c1c87fd9b715fc2"
HELPER_SHA = "a98252d012008a3c17d45b553783b564ecb0547509a88535eb37f800d4e2f316"
AUDIT_SHA = "aceba1e0c1280be6154950dfe61e5545ff40035cb5307e3749b1ac97c630f92a"
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
BLOCK_ID = {block: index for index, block in enumerate(BLOCKS)}
SEEDS = tuple(range(2026106701, 2026106705))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    require(len(payload.encode()) < 1_000_000, "small receipt")
    Path(path).write_text(payload)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def selection_check(manifest):
    propagation = read(BASE / "circulant-chosen-link-row-propagation-full/result.json")
    source = ROOT / propagation["survivor_records_path"]
    require(digest(source) == propagation["survivor_records_sha256"], "survivor source hash")
    with gzip.open(source, "rt") as stream:
        records = [json.loads(line) for line in stream]
    require(len(records) == 1096, "full survivor input")
    partials = read(CAT / "partial-catalog.json")
    profiles = read(CAT / "profiles.json")
    fibers = read(CAT / "link-fibers.json")
    orbits = read(ORBIT / "orbits.json")
    by_mask = {mask: orbit["representative_mask"] for orbit in orbits for mask in orbit["members"]}
    require(len(by_mask) == 1300 and len(orbits) == 52, "profile orbit inventory")
    require(sum(len(orbit["members"]) for orbit in orbits) == 1300, "disjoint profile orbits")
    reflection = tuple((-(point - 1)) % 16 + 1 for point in range(1, 17))
    require(reflection == (1, *range(16, 1, -1)), "point-one reflection arithmetic")
    graph = {
        pair
        for pair in combinations(range(1, 17), 2)
        if (pair[1] - pair[0]) % 16 in (1, 3, 8, 13, 15)
    }
    reflected_graph = {tuple(sorted(reflection[v - 1] for v in pair)) for pair in graph}
    require(len(graph) == 40 and graph == reflected_graph, "reflection preserves named pair graph")
    block_map = [BLOCK_ID[tuple(sorted(reflection[v - 1] for v in block))] for block in BLOCKS]
    by_partial = {tuple(row["global_block_ids"]): row["partial_id"] for row in partials}
    by_profile = {tuple(map(tuple, row["excess_triples"])): row["profile_id"] for row in profiles}
    by_pair = {(row["partial_id"], row["profile_id"]): row for row in records}
    require(len(by_pair) == len(records), "unique survivor pairs")
    groups = {}
    for row in records:
        partial, profile = partials[row["partial_id"]], profiles[row["profile_id"]]
        fiber = fibers[partial["excess_link_id"]]
        require(row["profile_id"] in fiber["profile_ids"], "survivor fiber compatibility")
        reflected_partial = tuple(sorted(block_map[i] for i in partial["global_block_ids"]))
        reflected_profile = tuple(
            sorted(
                tuple(sorted(reflection[v - 1] for v in triple))
                for triple in profile["excess_triples"]
            )
        )
        counterpart = by_pair[(by_partial[reflected_partial], by_profile[reflected_profile])]
        require(
            row["selected_count"] == counterpart["selected_count"]
            and row["removed_count"] == counterpart["removed_count"],
            "reflected fixed point size",
        )
        representative = min(row["pair_ordinal"], counterpart["pair_ordinal"])
        groups.setdefault(representative, set()).add(row["pair_ordinal"])
        row.update(
            {
                "class": fiber["class"],
                "free_variables_after_propagation": 3003
                - row["selected_count"]
                - row["removed_count"],
                "profile_orbit_representative_mask": by_mask[profile["choice_mask"]],
                "reflection_representative_pair_ordinal": representative,
                "reflected_pair_ordinal": counterpart["pair_ordinal"],
            }
        )
    classes = sorted({row["class"] for row in records})
    def rank(row):
        return (row["free_variables_after_propagation"], row["pair_ordinal"])
    chosen = [min((row for row in records if row["class"] == kind), key=rank) for kind in classes]
    used_reflections = {row["reflection_representative_pair_ordinal"] for row in chosen}
    used_profiles = {row["profile_orbit_representative_mask"] for row in chosen}
    available = [
        row
        for row in records
        if row["reflection_representative_pair_ordinal"] not in used_reflections
    ]
    novel = [
        row for row in available if row["profile_orbit_representative_mask"] not in used_profiles
    ]
    require(bool(novel), "a new fourth profile orbit is available")
    chosen.append(min(novel, key=rank))
    census = dict(sorted(Counter(row["class"] for row in records).items()))
    require(
        census == {"C4-leaf": 410, "triangle-path2": 658, "triangle-two-leaves": 28}, "class census"
    )
    require(
        len(groups) == 548 and all(len(group) == 2 for group in groups.values()),
        "548 reflection pairs",
    )
    require(
        [row["pair_ordinal"] for row in chosen] == [55433, 48366, 51739, 135193],
        "selected input order",
    )
    require(
        [row["free_variables_after_propagation"] for row in chosen] == [325, 308, 378, 321],
        "ranked free counts",
    )
    require(
        len({row["profile_orbit_representative_mask"] for row in chosen}) == 4,
        "four profile orbits",
    )
    saved = read(PRODUCER / "selection.json")
    require(saved["selected"] == chosen, "full selected records")
    require(
        saved["input_survivor_count"] == 1096 and saved["core_type_counts"] == census,
        "selection census",
    )
    require(
        saved["reflection_orbit_count"] == 548
        and saved["reflection_orbit_size_counts"] == {"2": 548},
        "selection orbit counts",
    )
    require(
        saved["reflection_groups"] == [sorted(groups[k]) for k in sorted(groups)],
        "complete reflection partition",
    )
    require(saved["fourth_case_uses_new_profile_orbit"] is True, "fourth-case new orbit flag")
    for expected, case in zip(chosen, manifest["cases"]):
        require(
            all(case[k] == value for k, value in expected.items()), "manifest selection binding"
        )
    return chosen, partials, profiles, census


def expected_model(partial, profile):
    expected = cp_model_pb2.CpModelProto()
    for index in range(4368):
        expected.variables.add(name=f"block_{index}", domain=[0, 1])
    carriers = {triple: [] for triple in TRIPLES}
    for index, block in enumerate(BLOCKS):
        for triple in combinations(block, 3):
            carriers[triple].append(index)

    def add(ids, value):
        row = expected.constraints.add().linear
        row.vars.extend(ids)
        row.coeffs.extend([1] * len(ids))
        row.domain.extend([value, value])

    excess = {tuple(triple) for triple in profile["excess_triples"]}
    require(len(excess) == 80, "eighty excess triples")
    for triple in TRIPLES:
        require(len(carriers[triple]) == 78, "all triple carriers")
        add(carriers[triple], 1 + (triple in excess))
    add(list(range(4368)), 64)
    fixed = set(partial["global_block_ids"])
    require(len(fixed) == 20 and fixed <= set(range(1365)), "twenty point-one blocks")
    for index in range(1365):
        add([index], int(index in fixed))
    return expected


def same_model(actual, expected):
    require(actual == expected, "complete exact protobuf equality")


def expected_parameters(seed):
    return sat_parameters_pb2.SatParameters(
        max_time_in_seconds=30.0,
        num_search_workers=1,
        random_seed=seed,
        log_search_progress=True,
        log_to_stdout=True,
    )


def model_damage(actual, expected, parameters, seed):
    rejected = []
    for name in (
        "variable_order",
        "variable_domain",
        "missing_variable",
        "missing_triple_row",
        "wrong_triple_coefficient",
        "wrong_triple_rhs",
        "conditional_triple",
        "wrong_cardinality",
        "missing_membership",
        "flipped_membership",
        "extra_pruning",
        "objective",
        "hint",
    ):
        bad = copy.deepcopy(actual)
        if name == "variable_order":
            bad.variables[0].name = "block_1"
        elif name == "variable_domain":
            bad.variables[1365].domain[1] = 2
        elif name == "missing_variable":
            del bad.variables[4367]
        elif name == "missing_triple_row":
            del bad.constraints[0]
        elif name == "wrong_triple_coefficient":
            bad.constraints[0].linear.coeffs[0] = 2
        elif name == "wrong_triple_rhs":
            bad.constraints[0].linear.domain[1] += 1
        elif name == "conditional_triple":
            bad.constraints[0].enforcement_literal.append(0)
        elif name == "wrong_cardinality":
            bad.constraints[560].linear.domain[0] = 63
        elif name == "missing_membership":
            del bad.constraints[561]
        elif name == "flipped_membership":
            value = 1 - bad.constraints[561].linear.domain[0]
            bad.constraints[561].linear.domain[:] = [value, value]
        elif name == "extra_pruning":
            row = bad.constraints.add().linear
            row.vars.append(1365)
            row.coeffs.append(1)
            row.domain.extend([0, 0])
        elif name == "objective":
            bad.objective.offset = 1
        else:
            bad.solution_hint.vars.append(1365)
            bad.solution_hint.values.append(0)
        try:
            same_model(bad, expected)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError("accepted damaged model: " + name)
    for field, value in (
        ("max_time_in_seconds", 31),
        ("num_search_workers", 2),
        ("random_seed", seed + 1),
        ("log_search_progress", False),
        ("log_to_stdout", False),
    ):
        bad = copy.deepcopy(parameters)
        setattr(bad, field, value)
        require(bad != expected_parameters(seed), "damaged parameters rejected")
        rejected.append("parameter_" + field)
    return rejected


def partial_check(case, partial, profile):
    blocks = [BLOCKS[index] for index in partial["global_block_ids"]]
    canonical = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
    require((ROOT / case["partial"]).read_text() == canonical, "partial canonical text")
    require(
        sha256(canonical.encode()).hexdigest() == partial["partial_canonical_sha256"],
        "partial hash",
    )
    require(read(ROOT / case["profile"]) == profile["excess_triples"], "full saved profile")
    excess = set(map(tuple, profile["excess_triples"]))
    counts = Counter(triple for block in blocks for triple in combinations(block, 3))
    require(
        all(counts[t] == 1 + (t in excess) for t in TRIPLES if 1 in t),
        "all fixed point-one demands",
    )
    residual = [
        {"triple": list(triple), "demand": 1 + (triple in excess) - counts[triple]}
        for triple in TRIPLES
        if 1 not in triple
    ]
    require(read(ROOT / case["residual"]) == residual, "exact residual rows")
    require(
        len(residual) == 455
        and sum(row["demand"] for row in residual) == 440
        and min(row["demand"] for row in residual) >= 0,
        "residual accounting",
    )
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    standalone = module(ROOT / "scripts/check_cover.py", "completion_standalone")
    package = verify_cover(blocks)
    independent = standalone.verify_cover(blocks, expected_blocks=20)
    require(package["blocks"] == independent["blocks"] == 20, "dual partial block count")
    require(package["covered"] == independent["covered_subsets"] == 185, "dual partial coverage")
    require(
        len(package["uncovered"]) == independent["uncovered_count"] == 375, "dual partial holes"
    )
    require(not package["valid"] and not independent["valid"], "partial remains incomplete")
    require(package["canonical_sha256"] == independent["canonical_sha256"], "dual canonical hash")
    saved = read(PRODUCER / f"case-{case['case']}-partial-verification.json")
    require(
        saved == json.loads(json.dumps({"package": package, "standalone": independent})),
        "saved dual receipts",
    )
    return package["canonical_sha256"]


def watchdog_controls(helper):
    reports = []
    for name, waits, kill_errors, signals, watchdog, killed in (
        ("normal", [0], None, [], False, False),
        (
            "term",
            [subprocess.TimeoutExpired("synthetic", 35), -15],
            None,
            [signal.SIGTERM],
            True,
            False,
        ),
        (
            "kill",
            [
                subprocess.TimeoutExpired("synthetic", 35),
                subprocess.TimeoutExpired("synthetic", 5),
                -9,
            ],
            None,
            [signal.SIGTERM, signal.SIGKILL],
            True,
            True,
        ),
        (
            "term_exit_race",
            [subprocess.TimeoutExpired("synthetic", 35), 0],
            [ProcessLookupError()],
            [signal.SIGTERM],
            True,
            False,
        ),
        (
            "kill_exit_race",
            [
                subprocess.TimeoutExpired("synthetic", 35),
                subprocess.TimeoutExpired("synthetic", 5),
                0,
            ],
            [None, ProcessLookupError()],
            [signal.SIGTERM, signal.SIGKILL],
            True,
            True,
        ),
    ):
        process = Mock(pid=717171)
        process.wait.side_effect = waits
        with (
            patch.object(helper.subprocess, "Popen", return_value=process) as popen,
            patch.object(helper.os, "killpg", side_effect=kill_errors) as kill,
            patch.object(helper.time, "monotonic", side_effect=[0, 1]),
        ):
            result = helper.bounded_child(["mocked-worker"], io.BytesIO(), io.BytesIO())
        require(
            popen.call_count == 1 and popen.call_args.kwargs["start_new_session"] is True,
            "one isolated child",
        )
        require(process.wait.call_args_list[0].kwargs == {"timeout": 35.0}, "35-second watchdog")
        if watchdog:
            require(process.wait.call_args_list[1].kwargs == {"timeout": 5.0}, "five-second grace")
        require(
            [call.args for call in kill.call_args_list] == [(process.pid, sig) for sig in signals],
            "group signal path",
        )
        require(
            result["watchdog_fired"] == watchdog and result["kill_required"] == killed,
            "watchdog flags",
        )
        require(result["returncode"] == waits[-1], "child return code")
        reports.append({"scenario": name, **result})
    return reports


def wrapper_control(runner, manifest, scenario):
    calls = []
    with tempfile.TemporaryDirectory(prefix="independent-completion-wrapper-") as directory:
        folder = Path(directory)
        save(folder / "manifest.json", manifest)
        checks = 0

        def pins():
            nonlocal checks
            checks += 1
            if scenario == "changed_pin" and checks == 3:
                raise AssertionError("mocked changed dependency")
            return manifest

        def child(command, stdout, stderr):
            number = int(command[-1])
            calls.append(number)
            stdout.write(b"mocked stdout\n")
            stderr.write(b"")
            failed = scenario == "first_watchdog" and number == 1
            if not failed:
                destination = folder / f"case-{number}-output"
                destination.mkdir()
                save(destination / "result.json", {"synthetic": True, "case": number})
            return {
                "returncode": -9 if failed else 0,
                "watchdog_fired": failed,
                "kill_required": failed,
                "watchdog_seconds": 35.0,
                "grace_seconds": 5.0,
            }

        utility = SimpleNamespace(bounded_child=Mock(side_effect=child))
        with (
            patch.object(runner, "HERE", folder),
            patch.object(runner, "check_pins", side_effect=pins),
            patch.object(runner, "helper", return_value=utility),
            patch.object(runner.subprocess, "Popen", side_effect=AssertionError("no real child")),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            try:
                runner.run()
            except AssertionError:
                require(scenario == "changed_pin", "only changed pin may abort")
            else:
                require(scenario != "changed_pin", "changed pin must abort")
            expected = [1] if scenario == "changed_pin" else [1, 2, 3, 4]
            require(calls == expected, "four ordered calls with no retry or transfer")
            try:
                runner.run()
            except (AssertionError, FileExistsError):
                pass
            else:
                raise AssertionError("repeated launch accepted")
            require(calls == expected, "repeat did not launch")
        runtime = read(folder / "runtime.json")
        require([row["case"] for row in runtime["calls"]] == calls, "runtime prefix")
        require(runtime["complete"] == (len(calls) == 4), "runtime complete flag")
        launch = read(folder / "run-started.json")
        require(
            launch["max_calls"] == 4 and launch["supervisor_pid"] == os.getpid(),
            "launch limit and parent",
        )
        for row in runtime["calls"]:
            number = row["case"]
            for label in ("stdout", "stderr"):
                require(
                    row[label + "_sha256"] == digest(folder / f"case-{number}-{label}.log"),
                    "log pin",
                )
        return {"scenario": scenario, "mocked_calls": calls, "repeat_rejected": True}


def worker_controls(runner, helper, manifest):
    reports = []
    for status in (runner.cp_model.UNKNOWN, runner.cp_model.INFEASIBLE):
        with tempfile.TemporaryDirectory(prefix="independent-completion-worker-") as directory:
            folder = Path(directory)
            save(folder / "manifest.json", manifest)
            save(
                folder / "run-started.json",
                {
                    "supervisor_pid": os.getppid(),
                    "manifest_sha256": digest(folder / "manifest.json"),
                },
            )
            fake_solver = SimpleNamespace(
                parameters=helper.parameters(SEEDS[0]),
                solve=Mock(return_value=status),
                status_name=Mock(
                    return_value="UNKNOWN" if status == runner.cp_model.UNKNOWN else "INFEASIBLE"
                ),
                wall_time=0.0,
                num_branches=0,
                num_conflicts=0,
                response_stats=Mock(return_value="synthetic response"),
                value=Mock(side_effect=AssertionError("no candidate values expected")),
            )
            with (
                patch.object(runner, "HERE", folder),
                patch.object(runner, "check_pins", return_value=manifest),
                patch.object(runner, "helper", return_value=helper),
                patch.object(runner.cp_model, "CpSolver", return_value=fake_solver),
                patch.object(
                    runner.subprocess, "Popen", side_effect=AssertionError("no real child")
                ),
            ):
                runner.worker(1)
            require(fake_solver.solve.call_count == 1, "one mocked solve")
            result = read(folder / "case-1-output/result.json")
            require(
                result["witness"] is None
                and result["proof_generated"] is False
                and result["global_nonexistence_claim"] is False,
                "no unsupported witness or proof claim",
            )
            require(
                result["status"] == fake_solver.status_name.return_value, "native status preserved"
            )
            require(result["seed"] == SEEDS[0] and result["point"] == 1, "worker identity")
            require(
                result["model_sha256"] == digest(ROOT / manifest["cases"][0]["model"]),
                "model receipt",
            )
            reports.append(
                {
                    "status": result["status"],
                    "mocked_solves": 1,
                    "witness": None,
                    "independent_infeasibility_proof": False,
                }
            )
    return reports


def main():
    for path, expected in (
        (PRODUCER / "run.py", RUNNER_SHA),
        (PRODUCER / "manifest.json", MANIFEST_SHA),
        (PRODUCER / "files.json", FILES_SHA),
        (HELPER, HELPER_SHA),
        (PROPAGATION_AUDIT, AUDIT_SHA),
    ):
        require(digest(path) == expected, "frozen gate input")
    manifest = read(PRODUCER / "manifest.json")
    require(
        manifest["source_sha256"] == RUNNER_SHA
        and manifest["ortools_version"] == ortools.__version__,
        "runner and solver version",
    )
    for field in ("dependencies", "prepared_files"):
        for path, expected in manifest[field].items():
            require(digest(ROOT / path) == expected, "frozen file: " + path)
    require(
        str(PROPAGATION_AUDIT.relative_to(ROOT)) in manifest["dependencies"],
        "accepted full audit dependency",
    )
    for field, expected in {
        "variables": 4368,
        "global_exact_triple_rows": 560,
        "cardinality_rows": 1,
        "fixed_membership_rows": 1365,
        "total_rows": 1926,
        "max_calls": 4,
        "total_solver_budget_seconds": 120,
        "retry_or_budget_transfer": False,
        "objective": None,
        "hints": None,
        "cover_invariance": None,
        "propagation_pruning_used_to_restrict_model": False,
    }.items():
        require(manifest[field] == expected, "exact model scope: " + field)
    chosen, partials, profiles, census = selection_check(manifest)
    reports = []
    for number, (case, selected, seed) in enumerate(zip(manifest["cases"], chosen, SEEDS), 1):
        require(case["case"] == number and case["seed"] == seed, "case and seed order")
        require(
            (case["seconds"], case["workers"], case["watchdog_seconds"], case["grace_seconds"])
            == (30.0, 1, 35.0, 5.0),
            "frozen per-call budgets",
        )
        expected = expected_model(partials[case["partial_id"]], profiles[case["profile_id"]])
        actual = text_format.Parse((ROOT / case["model"]).read_text(), cp_model_pb2.CpModelProto())
        same_model(actual, expected)
        parameters = text_format.Parse(
            (ROOT / case["parameters"]).read_text(), sat_parameters_pb2.SatParameters()
        )
        require(parameters == expected_parameters(seed), "exact solver parameters")
        witness_hash = partial_check(
            case, partials[case["partial_id"]], profiles[case["profile_id"]]
        )
        damages = model_damage(actual, expected, parameters, seed)
        reports.append(
            {
                "case": number,
                "pair_ordinal": selected["pair_ordinal"],
                "class": selected["class"],
                "variables": 4368,
                "rows": 1926,
                "initial_free_variables": 3003,
                "model_sha256": digest(ROOT / case["model"]),
                "parameters_sha256": digest(ROOT / case["parameters"]),
                "partial_canonical_sha256": witness_hash,
                "damaged_controls_rejected": damages,
            }
        )
    runner, helper = (
        module(PRODUCER / "run.py", "mocked_completion_runner"),
        module(HELPER, "mocked_completion_helper"),
    )
    require(runner.check_pins() == manifest, "read-only pin guard")
    watchdogs = watchdog_controls(helper)
    wrappers = [
        wrapper_control(runner, manifest, scenario)
        for scenario in ("normal", "first_watchdog", "changed_pin")
    ]
    workers = worker_controls(runner, helper, manifest)
    receipt = {
        "passed": True,
        "checker_sha256": digest(Path(__file__)),
        "runner_sha256": RUNNER_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "producer_files_sha256": FILES_SHA,
        "accepted_propagation_audit_sha256": AUDIT_SHA,
        "helper_sha256": HELPER_SHA,
        "dependency_pins_checked": len(manifest["dependencies"]),
        "prepared_pins_checked": len(manifest["prepared_files"]),
        "selection_class_census": census,
        "reflection_orbits": 548,
        "selected_pair_ordinals": [row["pair_ordinal"] for row in chosen],
        "four_distinct_profile_orbits": True,
        "cases": reports,
        "watchdog_controls": watchdogs,
        "wrapper_controls": wrappers,
        "worker_controls": workers,
        "real_optimizer_calls": 0,
        "real_process_launches": 0,
        "real_signals": 0,
        "scope": "Four conditional exact64 models with a fixed point-one partial "
        "and fixed excess profile; "
        "propagation counts only select cases. No exhaustion or global nonexistence claim.",
    }
    save(HERE / "review.json", receipt)
    save(
        HERE / "gate.json",
        {
            "decision": "HOLD",
            "reason": "Root deferred this batch pending new parity-certificate review.",
            "runner_sha256": RUNNER_SHA,
            "manifest_sha256": MANIFEST_SHA,
            "independent_review_sha256": digest(HERE / "review.json"),
            "maximum_calls": 0,
            "planned_maximum_calls": 4,
            "per_call_seconds": 30,
            "workers_per_call": 1,
            "total_solver_budget_seconds": 120,
            "watchdog_seconds": 35,
            "grace_seconds": 5,
            "seeds": SEEDS,
            "retry_or_budget_transfer": False,
            "scope": receipt["scope"],
        },
    )
    print(
        json.dumps(
            {
                "passed": True,
                "decision": "HOLD",
                "models": 4,
                "review_sha256": digest(HERE / "review.json"),
                "gate_sha256": digest(HERE / "gate.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
