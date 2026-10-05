# Document:    Independent Complete Circulant Profile Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2a440f52bd817aec28a080aa92c37e1adda4267a02cfed8b2b1884173bbac38d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay explicit orbit reduction and every model row; mock the one-call wrapper."""

import contextlib
import importlib.util
import io
import json
import subprocess
import tempfile
from collections import Counter
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
PRODUCER = HERE.parent / "circulant-all-profile-global-pilot"
ENUMERATION = HERE.parent / "circulant-all-excess-profiles"
INDEPENDENT = HERE.parent / "circulant-all-excess-independent"
RAW = ROOT / "experiments/scratch/circulant-all-profile-global-pilot-20261004"
MANIFEST_SHA = "c3a70ac81bc5174807c3ba150e6924d295a3b2730bec8947921f2176bcc67b72"
RUNNER_SHA = "ab89c2a66fa72182b70fa59874f303cfc40dfb9432e2245322116ef7111ec3fb"
AUDIT_SHA = "0ac5ff70de498fd1f399eea6fc7988057d964a53ec0a614c276c0831bc1b3dd9"
README_SHA = "ea63a85509cf43cda34ae96b1bcaace32708f791d59141e6e2480080494e3df5"
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
PAIRS = tuple(combinations(range(1, 17), 2))
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


def exact(actual, expected, message):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), message)


def decode(mask, geometry):
    return frozenset(
        tuple(sorted((p, q, centers[0]))) for p, q, centers in geometry["forced"]
    ) | frozenset(
        tuple(sorted((p, q, centers[(mask >> i) & 1])))
        for i, (p, q, centers) in enumerate(geometry["choices"])
    )


def orbit_replay(geometry, table):
    audit = read(INDEPENDENT / "audit.json")
    require(
        sha(INDEPENDENT / "audit.json") == AUDIT_SHA and audit["passed"] is True,
        "enumeration audit",
    )
    require(sha(INDEPENDENT / "check.py") == audit["checker_sha256"], "enumeration checker binding")
    for name, digest in audit["producer_pins"].items():
        require(sha(ENUMERATION / name) == digest, "enumeration input " + name)
    for name, digest in audit["output_hashes"].items():
        require(sha(INDEPENDENT / name) == digest, "enumeration output " + name)
    masks = read(ENUMERATION / "profiles.json")["choice_masks"]
    require(
        len(masks) == 1300
        and masks == sorted(set(masks))
        and all(type(mask) is int and 0 <= mask < 2**48 for mask in masks),
        "1300 masks",
    )
    edges = {tuple(pair) for pair in geometry["edges"]}
    expected_edges = {pair for pair in PAIRS if (pair[1] - pair[0]) % 16 in (1, 3, 8, 13, 15)}
    require(edges == expected_edges, "named circulant graph")
    profiles = {mask: decode(mask, geometry) for mask in masks}
    require(len(set(profiles.values())) == 1300, "one-to-one profile decoding")
    inverse_profiles = {value: key for key, value in profiles.items()}
    for paths in profiles.values():
        require(
            len(paths) == 80
            and all(sum(pair in edges for pair in combinations(t, 2)) == 2 for t in paths),
            "eighty induced P3 triples",
        )
        loads = Counter(pair for t in paths for pair in combinations(t, 2))
        require(
            all(loads[pair] == (4 if pair in edges else 1) for pair in PAIRS), "exact pair demands"
        )
    maps = [tuple(p) for p in read(INDEPENDENT / "automorphisms.json")["all_maps"]]
    require(len(maps) == len(set(maps)) == 32, "32 distinct maps")
    for mapping in maps:
        require(
            all(type(p) is int for p in mapping) and sorted(mapping) == list(range(1, 17)),
            "graph-map bijection",
        )
        require(
            {tuple(sorted(mapping[p - 1] for p in pair)) for pair in edges} == edges,
            "graph automorphism",
        )
    map_set = set(maps)
    require(tuple(range(1, 17)) in map_set, "identity map")
    require(
        all(tuple(a[b[i] - 1] for i in range(16)) in map_set for a in maps for b in maps),
        "closed map group",
    )
    orbits = read(INDEPENDENT / "orbits.json")
    require(len(orbits) == len(table) == 52, "52 orbit representatives")
    seen = set()
    mapping_witnesses = []
    for orbit, row in zip(orbits, table, strict=True):
        representative = orbit["representative_mask"]
        require(type(representative) is int and representative in profiles, "representative exists")
        images, stabilizer = {}, 0
        for map_index, mapping in enumerate(maps):
            image = frozenset(
                tuple(sorted(mapping[p - 1] for p in t)) for t in profiles[representative]
            )
            require(image in inverse_profiles, "profile action closes")
            mask = inverse_profiles[image]
            images.setdefault(mask, map_index)
            stabilizer += mask == representative
        require(sorted(images) == orbit["members"] and representative == min(images), "exact orbit")
        require(
            orbit["size"] == len(images)
            and orbit["stabilizer_size"] == stabilizer
            and len(images) * stabilizer == 32,
            "orbit-stabilizer count",
        )
        require(not seen.intersection(images), "disjoint orbits")
        seen.update(images)
        exact(
            row,
            {
                "representative_mask": representative,
                "center_bits": [(representative >> i) & 1 for i in range(48)],
            },
            "exact table row",
        )
        mapping_witnesses.extend(
            {"mask": mask, "representative": representative, "map_from_representative": index}
            for mask, index in images.items()
        )
    require(seen == set(masks), "52 images cover all1300 arithmetic profiles")
    return mapping_witnesses


def linear(row, variables, coefficients, target):
    require(row.has_linear() and not row.name and not row.enforcement_literal, "unguarded linear")
    require(
        list(row.linear.vars) == variables and list(row.linear.coeffs) == coefficients,
        "exact row expression",
    )
    require(list(row.linear.domain) == [target, target], "equality target")


def check_model(model, geometry, table):
    proto = model.proto
    require(len(proto.variables) == 4416 and len(proto.constraints) == 562, "4416vars562rows")
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
    for index, var in enumerate(proto.variables):
        name = f"block_{index}" if index < 4368 else f"center_choice_{index - 4368}"
        require(var.name == name and list(var.domain) == [0, 1], "free named Boolean variable")
    linear(proto.constraints[0], list(range(4368)), [1] * 4368, 64)
    forced = {tuple(sorted((p, q, centers[0]))) for p, q, centers in geometry["forced"]}
    options = {}
    for bit_index, (a, b, centers) in enumerate(geometry["choices"]):
        require(len(centers) == 2, "two centers per bit")
        for selected_bit, center in enumerate(centers):
            triple = tuple(sorted((a, b, center)))
            require(triple not in forced and triple not in options, "unique triple selector")
            options[triple] = (bit_index, selected_bit)
    require(len(forced) == 32 and len(options) == 96, "forced and conditional rows")
    for row_id, triple in enumerate(TRIPLES, 1):
        indices = list(CARRIERS[triple])
        coefficients = [1] * 78
        target = 2 if triple in forced else 1
        if triple in options:
            bit_index, selected_bit = options[triple]
            coefficient, target = (1, 2) if selected_bit == 0 else (-1, 1)
            indices.append(4368 + bit_index)
            coefficients.append(coefficient)
            for value in (0, 1):
                require(
                    target - coefficient * value == 1 + (value == selected_bit),
                    "bit demand algebra",
                )
        linear(proto.constraints[row_id], indices, coefficients, target)
    row = proto.constraints[561]
    require(
        row.has_table() and not row.name and not row.enforcement_literal, "unguarded allowed table"
    )
    t = row.table
    require(not t.negated and not t.vars and len(t.exprs) == 48, "positive48column table")
    for index, expr in enumerate(t.exprs):
        require(
            list(expr.vars) == [4368 + index] and list(expr.coeffs) == [1] and expr.offset == 0,
            "ordered direct choice-bit column",
        )
    require(
        list(t.values) == [bit for row in table for bit in row["center_bits"]], "all52tablevectors"
    )
    require(not model.validate(), "OR-Tools syntax validation")


def damage_controls(model, geometry, table):
    rejected = []

    def damage(name, mutate):
        bad = model.clone()
        mutate(bad)
        try:
            check_model(bad, geometry, table)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError("accepted damage " + name)

    def fixed_block(m):
        m.proto.variables[0].domain[1] = 0

    def fixed_choice(m):
        m.proto.variables[4368].domain[1] = 0

    def wrong_selector(m):
        row = next(r for r in m.proto.constraints if r.has_linear() and len(r.linear.vars) == 79)
        row.linear.coeffs[78] *= -1

    def table_bit(m):
        m.proto.constraints[561].table.values[0] ^= 1

    def table_column(m):
        m.proto.constraints[561].table.exprs[0].vars[0] += 1

    def table_offset(m):
        m.proto.constraints[561].table.exprs[0].offset = 1

    def table_negated(m):
        m.proto.constraints[561].table.negated = True

    def table_extra(m):
        m.proto.constraints[561].table.values.append(0)

    def guarded_table(m):
        m.proto.constraints[561].enforcement_literal.append(0)

    damage("fixed_cover_block", fixed_block)
    damage("fixed_choice_bit", fixed_choice)
    damage("reversed_selector_sign", wrong_selector)
    damage("changed_table_bit", table_bit)
    damage("wrong_table_column", table_column)
    damage("nonzero_table_offset", table_offset)
    damage("negated_table", table_negated)
    damage("extra_table_cell", table_extra)
    damage("guarded_table", guarded_table)
    damage("extra_link_row", lambda m: m.add(m.get_bool_var_from_proto_index(0) == 0))
    damage("objective", lambda m: m.minimize(m.get_bool_var_from_proto_index(0)))
    damage("hint", lambda m: m.add_hint(m.get_bool_var_from_proto_index(0), 1))
    damage("assumption", lambda m: m.add_assumption(m.get_bool_var_from_proto_index(0)))
    return rejected


def mock_runner(manifest):
    spec = importlib.util.spec_from_file_location("global_profile_runner", PRODUCER / "run.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    require(runner.SEED == 2026106501, "runner seed")
    results = []
    for scenario in (
        "normal",
        "term",
        "kill",
        "nonzero",
        "missing_child",
        "bad_gate",
        "wrong_manifest",
        "existing_child",
    ):
        with tempfile.TemporaryDirectory(
            prefix="global-profile-gate-", dir=ROOT / "experiments/scratch"
        ) as tmp:
            temp = Path(tmp)
            here, raw = temp / "producer", temp / "raw"
            here.mkdir()
            raw.mkdir()
            (here / "manifest.json").write_bytes((PRODUCER / "manifest.json").read_bytes())
            gate = {
                "passed": True,
                "launch_permitted": scenario != "bad_gate",
                "manifest_sha256": "0" * 64 if scenario == "wrong_manifest" else MANIFEST_SHA,
            }
            gate_path = temp / "gate.json"
            gate_path.write_text(json.dumps(gate))
            if scenario == "existing_child":
                (raw / "child-result.json").write_text("{}")
            process = Mock(
                returncode=(
                    -9
                    if scenario == "kill"
                    else -15
                    if scenario == "term"
                    else 1
                    if scenario == "nonzero"
                    else 0
                )
            )
            answers = [("", "")]
            if scenario == "term":
                answers = [subprocess.TimeoutExpired("mock", 310), ("", "")]
            if scenario == "kill":
                answers = [
                    subprocess.TimeoutExpired("mock", 310),
                    subprocess.TimeoutExpired("mock", 5),
                    ("", ""),
                ]
            process.communicate.side_effect = answers

            def fake_popen(command, **kwargs):
                require(command[-1] == "--child" and len(command) == 3, "one exact child")
                require(
                    kwargs == {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True},
                    "captured child streams",
                )
                if scenario != "missing_child":
                    (raw / "child-result.json").write_text(json.dumps({"status": "UNKNOWN"}))
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
                if scenario in ("bad_gate", "wrong_manifest", "existing_child"):
                    try:
                        runner.execute(gate_path)
                    except AssertionError:
                        pass
                    else:
                        raise AssertionError("invalid launch accepted")
                    require(popen.call_count == 0, "no invalid launch")
                else:
                    runner.execute(gate_path)
                    require(popen.call_count == 1, "one launch only")
                    expected = (
                        [310, 5, None]
                        if scenario == "kill"
                        else ([310, 5] if scenario == "term" else [310])
                    )
                    require(
                        [c.kwargs.get("timeout") for c in process.communicate.call_args_list]
                        == expected,
                        "watchdog waits",
                    )
                    require(
                        process.terminate.call_count == int(scenario in ("term", "kill"))
                        and process.kill.call_count == int(scenario == "kill"),
                        "termination calls",
                    )
                    receipt = read(here / "result.json")
                    require(
                        receipt["returncode"] == process.returncode
                        and receipt["watchdog"] is (scenario in ("term", "kill")),
                        "saved receipt",
                    )
                    if scenario == "normal":
                        try:
                            runner.execute(gate_path)
                        except AssertionError:
                            pass
                        else:
                            raise AssertionError("relaunch accepted")
                        require(popen.call_count == 1, "no second call")
                results.append(
                    {"scenario": scenario, "mock_calls": popen.call_count, "passed": True}
                )
    return results


def main():
    require(not (HERE / "review.json").exists(), "fresh model audit")
    require(
        sha(PRODUCER / "manifest.json") == MANIFEST_SHA and sha(PRODUCER / "run.py") == RUNNER_SHA,
        "frozen producer",
    )
    require(sha(PRODUCER / "README.md") == README_SHA, "safe reduction explanation")
    manifest = read(PRODUCER / "manifest.json")
    require(len(manifest["pins"]) == 15, "all15 pins")
    for relative, digest in manifest["pins"].items():
        require(sha(ROOT / relative) == digest, "input pin " + relative)
    required = {
        "variables": 4416,
        "binary_variables": 4416,
        "block_variables": 4368,
        "choice_variables": 48,
        "fixed_variables": 0,
        "rows": 562,
        "cardinality_rows": 1,
        "triple_rows": 560,
        "forced_demand_two_triples": 32,
        "conditional_triples": 96,
        "fixed_demand_one_triples": 432,
        "table_rows": 1,
        "table_columns": 48,
        "allowed_table_vectors": 52,
        "excess_profiles": 1300,
        "excess_profile_representatives": 52,
        "graph_automorphisms": 32,
        "graph_steps_mod16": [1, 3, 8, 13, 15],
        "hint": None,
        "objective": None,
        "fixed_blocks": None,
        "fixed_links": None,
        "fixed_neighborhoods": None,
        "cover_invariance_constraints": None,
        "cover_orbits_classified": False,
        "calls": 1,
        "native_seconds": 300,
        "workers": 4,
        "seed": 2026106501,
        "watchdog_seconds": 310,
        "termination_grace_seconds": 5,
        "relaunch": False,
        "retries": False,
        "budget_transfer": False,
    }
    for key, value in required.items():
        exact(manifest[key], value, "manifest " + key)
    require(manifest["ortools"] == ortools.__version__ == "9.15.6755", "solver version")
    require(
        not (PRODUCER / "launch.json").exists()
        and not (PRODUCER / "result.json").exists()
        and not (RAW / "child-result.json").exists(),
        "prelaunch gate",
    )
    geometry = read(ENUMERATION / "geometry.json")
    table = read(PRODUCER / "allowed-profile-table.json")
    mappings = orbit_replay(geometry, table)
    model = cp_model.CpModel()
    require(model.proto.parse_text_format((RAW / "model.pbtxt").read_text()), "model parse")
    check_model(model, geometry, table)
    params = sat_parameters_pb2.SatParameters()
    text_format.Parse((RAW / "parameters.pbtxt").read_text(), params)
    exact(
        {field.name: value for field, value in params.ListFields()},
        {
            "random_seed": 2026106501,
            "max_time_in_seconds": 300.0,
            "log_search_progress": True,
            "num_search_workers": 4,
            "log_to_stdout": False,
        },
        "parameters",
    )
    damaged, controls = damage_controls(model, geometry, table), mock_runner(manifest)
    mapping_path = HERE / "profile-orbit-maps.json"
    mapping_path.write_text(
        json.dumps(sorted(mappings, key=lambda r: r["mask"]), indent=2, sort_keys=True) + "\n"
    )
    receipt = {
        "passed": True,
        "launch_permitted": True,
        "decision": "GO",
        "checker_sha256": sha(Path(__file__)),
        "manifest_sha256": MANIFEST_SHA,
        "runner_sha256": RUNNER_SHA,
        "producer_readme_sha256": README_SHA,
        "enumeration_independent_audit_sha256": AUDIT_SHA,
        "profile_orbit_maps_sha256": sha(mapping_path),
        "profiles_replayed": 1300,
        "explicit_maps_checked": 32,
        "orbits_replayed": 52,
        "model_sha256": sha(RAW / "model.pbtxt"),
        "parameters_sha256": sha(RAW / "parameters.pbtxt"),
        "table_sha256": sha(PRODUCER / "allowed-profile-table.json"),
        "model_variables": 4416,
        "free_cover_block_variables": 4368,
        "choice_bits": 48,
        "linear_rows": 561,
        "table_rows": 1,
        "malformed_models_rejected": damaged,
        "mock_runner_controls": controls,
        "optimizer_calls": 0,
        "real_process_launches": 0,
        "real_signals_sent": 0,
        "scope": (
            "Complete excess-profile representative reduction for the named circulant "
            "pair graph, using the independently enumerated1300 profiles and32 "
            "explicit graph automorphisms. Relabeling blocks with the profile is "
            "bijective; no cover invariance is assumed. No claim about other pair "
            "graphs or unrestricted existence. Root alone may launch one300s "
            "four-worker call. Solver INFEASIBLE is not a checked theorem."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    gate = {
        key: receipt[key]
        for key in (
            "passed",
            "launch_permitted",
            "manifest_sha256",
            "runner_sha256",
            "model_sha256",
            "optimizer_calls",
        )
    }
    gate.update(
        {
            "review_sha256": sha(HERE / "review.json"),
            "max_calls": 1,
            "seconds": 300,
            "workers": 4,
            "seed": 2026106501,
            "watchdog_seconds": 310,
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
