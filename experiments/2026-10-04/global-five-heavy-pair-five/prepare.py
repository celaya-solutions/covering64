# Document:    Frozen Global Five-Heavy DP Model with Elementary Pair Floors
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4416200c81c61eb408615670161fd2b68fe885878c1faca19f514f179efba528
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Load the frozen parent, append 120 necessary rows, replace its hint; no solve."""

import hashlib
import itertools
import json
import resource
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import ortools
from google.protobuf import text_format
from ortools.sat import sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
BASE = DAY / "global-five-heavy-dp"
INVENTORY = DAY / "pair-five-hint-inventory"
RAW = ROOT / "experiments/scratch/global-five-heavy-pair-five-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
PAIRS = list(itertools.combinations(range(1, 17), 2))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
BLOCK_RANK = {block: index for index, block in enumerate(BLOCKS)}
TRIPLE_RANK = {triple: index for index, triple in enumerate(TRIPLES)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def relative(path):
    return str(path.relative_to(ROOT))


def data_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def mask(triple):
    return sum(1 << (point - 1) for point in triple)


def check_values(model, values):
    assert len(values) == len(model.proto.variables) == 10488
    for variable, value in zip(model.proto.variables, values, strict=True):
        assert type(value) is int
        domain = list(variable.domain)
        assert any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2))
    active = 0
    for row in model.proto.constraints:
        assert row.has_linear()
        if all(values[i] if i >= 0 else not values[-i - 1] for i in row.enforcement_literal):
            value = sum(
                values[i] * coefficient
                for i, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            domain = list(row.linear.domain)
            assert any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2))
            active += 1
    objective = sum(
        values[i] * coefficient
        for i, coefficient in zip(
            model.proto.objective.vars, model.proto.objective.coeffs, strict=True
        )
    )
    return {"complete_values": len(values), "active_rows_recounted": active, "objective": objective}


def main():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    previous = read(BASE / "manifest.json")
    old_gate_path = DAY / "global-five-heavy-dp-independent/gate.json"
    old_post_path = DAY / "global-five-heavy-dp-independent/postcheck.json"
    old_gate, old_post = read(old_gate_path), read(old_post_path)
    assert old_gate["passed"] and old_post["passed"]
    assert old_gate["manifest_sha256"] == sha(BASE / "manifest.json")
    assert old_post["result_sha256"] == sha(BASE / "result.json")
    assert old_post["gate_sha256"] == sha(old_gate_path)
    assert previous["source_sha256"] == sha(BASE / "prepare.py")
    inventory = read(INVENTORY / "result.json")
    assert inventory["passed"] and inventory["optimizer_calls"] == 0
    for key in ("audit_files", "source_files"):
        for name, checksum in inventory[key].items():
            assert sha(ROOT / name) == checksum
    hint = inventory["best"]
    assert hint["eligible"] and hint["holes"] == 6
    assert hint["minimum_pair_count"] == 5 and hint["core_overlaps"] == [2, 2, 0]
    hint_path = ROOT / hint["path"]
    assert sha(hint_path) == hint["sha256"]
    for verifier in inventory["best_verifiers"]:
        assert sha(ROOT / verifier["path"]) == verifier["sha256"]
        checked = read(ROOT / verifier["path"])
        assert checked["blocks"] == 64 and not checked["valid"]
        assert checked["canonical_sha256"] == hint["sha256"]
    blocks = [tuple(map(int, line.split())) for line in hint_path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64 and all(block in BLOCK_RANK for block in blocks)
    ids = sorted(BLOCK_RANK[block] for block in blocks)
    assert ids == hint["ids"]
    chosen = set(ids)
    triple_counts = Counter(t for block in blocks for t in itertools.combinations(block, 3))
    pair_counts = Counter(p for block in blocks for p in itertools.combinations(block, 2))
    point_counts = Counter(point for block in blocks for point in block)
    assert min(pair_counts[pair] for pair in PAIRS) >= 5
    assert sum(triple_counts[t] == 0 for t in TRIPLES) == hint["holes"]
    assert [len(chosen & set(core)) for core in previous["core_rows"]] == [2, 2, 0]
    states_path = ROOT / previous["dag"]["states_path"]
    assert sha(states_path) == previous["dag"]["states_sha256"]
    states = read(states_path)
    assert len(states) == 4410 and states[0] == 0
    weights = {mask(t): 5 * (triple_counts[t] >= 6) + int(triple_counts[t] >= 7) for t in TRIPLES}
    dp_values = {0: 0}
    recurrences = 0
    for state in states[1:]:
        points = [1 << bit for bit in range(16) if state & (1 << bit)]
        terms = []
        for second, third in itertools.combinations(points[1:], 2):
            triple = points[0] | second | third
            parent = state ^ triple
            assert parent in dp_values
            terms.append(dp_values[parent] + weights[triple])
            recurrences += 1
        dp_values[state] = max(terms)
    assert recurrences == 99917
    maximum = max(dp_values[state] for state in states if state.bit_count() == 15)
    assert maximum == hint["maximum_partition_weight"] == 22
    model_path_before = ROOT / previous["model_path"]
    params_path_before = ROOT / previous["parameters_path"]
    assert sha(model_path_before) == previous["model_sha256"]
    assert sha(params_path_before) == previous["parameters_sha256"]
    started = time.monotonic()
    model = cp_model.CpModel()
    assert model.proto.parse_text_format(model_path_before.read_text())
    assert hashlib.sha256(str(model.proto).encode()).hexdigest() == previous["model_sha256"]
    assert len(model.proto.variables) == 10488 and len(model.proto.constraints) == 103345
    original_variables = [str(variable) for variable in model.proto.variables]
    original_rows = [str(row) for row in model.proto.constraints]
    original_objective = str(model.proto.objective)
    variables = [model.get_int_var_from_proto_index(i) for i in range(10488)]
    pair_rows = []
    for pair_id, pair in enumerate(PAIRS):
        support = [i for i, block in enumerate(BLOCKS) if set(pair).issubset(block)]
        assert len(support) == 364
        model.add(sum(variables[i] for i in support) >= 5)
        pair_rows.append(
            {
                "pair_id": pair_id,
                "pair": pair,
                "row": 103345 + pair_id,
                "block_ids": support,
                "lower_bound": 5,
            }
        )
    assert len(model.proto.constraints) == 103465
    assert [str(variable) for variable in model.proto.variables] == original_variables
    assert [str(row) for row in list(model.proto.constraints)[:103345]] == original_rows
    assert str(model.proto.objective) == original_objective
    values = [int(i in chosen) for i in range(4368)]
    values.extend(int(triple_counts[t] == 0) for t in TRIPLES)
    for partition_id, partition in enumerate(previous["retained_named_partitions"]):
        for triple_id, triple in enumerate(partition):
            for threshold in (6, 7):
                index = len(values)
                assert model.proto.variables[index].name == (
                    f"partition_{partition_id}_triple_{triple_id}_at_least_{threshold}"
                )
                values.append(int(triple_counts[tuple(triple)] >= threshold))
    assert len(values) == 4958
    for triple_id, triple in enumerate(TRIPLES):
        for threshold in (6, 7):
            assert model.proto.variables[len(values)].name == (
                f"global_triple_{triple_id}_at_least_{threshold}"
            )
            values.append(int(triple_counts[triple] >= threshold))
    assert len(values) == 6078
    for state in states:
        assert model.proto.variables[len(values)].name == f"dp_{state:04x}"
        values.append(dp_values[state])
    model.clear_hints()
    for variable, value in zip(variables, values, strict=True):
        model.add_hint(variable, value)
    build_seconds = time.monotonic() - started
    started = time.monotonic()
    assert not model.validate(), model.validate()
    assert list(model.proto.solution_hint.vars) == list(range(10488))
    assert list(model.proto.solution_hint.values) == values
    hint_receipt = check_values(model, values)
    assert hint_receipt["objective"] == 392
    validation_seconds = time.monotonic() - started
    params = sat_parameters_pb2.SatParameters()
    text_format.Parse(params_path_before.read_text(), params)
    assert params.random_seed == 2026104104
    params.random_seed = 2026104105
    assert params.max_time_in_seconds == 120 and params.num_search_workers == 4
    RAW.mkdir()
    model_path, params_path = RAW / "full-4368-model.pbtxt", RAW / "parameters.pbtxt"
    started = time.monotonic()
    model_path.write_text(str(model.proto))
    params_path.write_text(str(params))
    serialization_seconds = time.monotonic() - started
    hint_values_path = RAW / "complete-hint-values.json"
    dump(hint_values_path, values)
    frozen_hint = RAW / "hint-six-holes.txt"
    shutil.copy2(hint_path, frozen_hint)
    dump(HERE / "pair-rows.json", pair_rows)
    diagnostics = {
        "path": hint["path"],
        "sha256": hint["sha256"],
        "ids": ids,
        "holes": hint["holes"],
        "core_overlaps": [2, 2, 0],
        "maximum_partition_weight": maximum,
        "point_degrees": [point_counts[p] for p in range(1, 17)],
        "pair_counts": [{"pair": pair, "count": pair_counts[pair]} for pair in PAIRS],
        "triple_counts": [{"triple": triple, "count": triple_counts[triple]} for triple in TRIPLES],
        "pair_histogram": dict(sorted(Counter(pair_counts[p] for p in PAIRS).items())),
        "triple_histogram": dict(sorted(Counter(triple_counts[t] for t in TRIPLES).items())),
    }
    dump(HERE / "hint-diagnostics.json", diagnostics)
    inputs = dict(previous["input_files"])
    for mapping in (inventory["audit_files"], inventory["source_files"]):
        inputs.update(mapping)
    paths = [
        Path(__file__),
        BASE / "manifest.json",
        BASE / "prepare.py",
        BASE / "result.json",
        old_gate_path,
        old_post_path,
        model_path_before,
        params_path_before,
        INVENTORY / "result.json",
        INVENTORY / "check.py",
        INVENTORY / "README.md",
        INVENTORY / "files.json",
        hint_path,
        states_path,
    ]
    paths += [ROOT / row["path"] for row in inventory["best_verifiers"]]
    inputs.update({relative(path): sha(path) for path in paths})
    for name, checksum in inputs.items():
        path = ROOT / name
        assert sha(path) == checksum
        copied = RAW / "frozen-inputs" / name
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copied)
        assert sha(copied) == checksum
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    stats = {
        "model_variables": 10488,
        "model_rows": 103465,
        "parent_rows": 103345,
        "added_pair_rows": 120,
        "build_and_hint_seconds": build_seconds,
        "validation_and_hint_recount_seconds": validation_seconds,
        "serialization_seconds": serialization_seconds,
        "process_peak_rss_bytes": rss if sys.platform == "darwin" else 1024 * rss,
        "model_pbtxt_bytes": model_path.stat().st_size,
        "optimizer_calls": 0,
    }
    dump(HERE / "build-stats.json", stats)
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "ortools_version": ortools.__version__,
        "input_files": inputs,
        "parent_manifest_sha256": sha(BASE / "manifest.json"),
        "parent_model_sha256": previous["model_sha256"],
        "parent_variables_sha256": data_sha(original_variables),
        "parent_rows_sha256": data_sha(original_rows),
        "parent_objective_sha256": data_sha(original_objective),
        "parent_prefix_unchanged": True,
        "model_path": relative(model_path),
        "model_sha256": sha(model_path),
        "parameters_path": relative(params_path),
        "parameters_sha256": sha(params_path),
        "variables": 10488,
        "rows": 103465,
        "pair_row_start": 103345,
        "added_pair_rows": 120,
        "pair_rows_path": relative(HERE / "pair-rows.json"),
        "pair_rows_sha256": sha(HERE / "pair-rows.json"),
        "hint_source_path": hint["path"],
        "hint_sha256": hint["sha256"],
        "hint_ids": ids,
        "hint_holes": 6,
        "hint_core_overlaps": [2, 2, 0],
        "hint_minimum_pair_count": 5,
        "hint_maximum_global_partition_weight": maximum,
        "hint_complete_receipt": hint_receipt,
        "hint_values_path": relative(hint_values_path),
        "hint_values_sha256": sha(hint_values_path),
        "hint_diagnostics_path": relative(HERE / "hint-diagnostics.json"),
        "hint_diagnostics_sha256": sha(HERE / "hint-diagnostics.json"),
        "core_rows": previous["core_rows"],
        "core_upper_bound": 55,
        "retained_named_partitions": previous["retained_named_partitions"],
        "dag": previous["dag"],
        "global_threshold_variable_start": 4958,
        "dp_variable_start": 6078,
        "budget": {"cases": 1, "seconds": 120, "workers": 4, "seed": 2026104105},
        "build_stats_sha256": sha(HERE / "build-stats.json"),
        "optimization_calls": 0,
        "scope": "Preparation only. Frozen parent variables, all 103345 rows and objective "
        "unchanged; only 120 elementary pair>=5 rows and a replaced complete hint. Every valid "
        "64-block cover remains eligible. Independent gate required before optimization.",
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "model_sha256": sha(model_path),
                "parameters_sha256": sha(params_path),
                "source_sha256": sha(__file__),
                "hint_objective": 392,
                **stats,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
