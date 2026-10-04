# Document:    Frozen Global Five-Heavy DP Full-Block Model
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      81269285b0df65e74f62a4714bb1259efa610862b1e5375b5691e665b33d1f88
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare the full model and complete checked hint; no optimization entry point."""

import hashlib
import importlib.util
import json
import resource
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path

import ortools
from ortools.sat import sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
BASE = DAY / "three-core-profile-release"
PLAN = DAY / "global-five-heavy-dp-plan"
RAW = ROOT / "experiments/scratch/global-five-heavy-dp-20261004"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def data_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def check_hint(model):
    proto = model.proto
    assert list(proto.solution_hint.vars) == list(range(len(proto.variables)))
    values = list(proto.solution_hint.values)
    for var, value in zip(proto.variables, values, strict=True):
        domain = list(var.domain)
        assert any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2))
    checked = 0
    for row in proto.constraints:
        if all(values[i] if i >= 0 else not values[-i - 1] for i in row.enforcement_literal):
            total = sum(values[i] * coefficient for i, coefficient
                        in zip(row.linear.vars, row.linear.coeffs, strict=True))
            bounds = list(row.linear.domain)
            assert len(bounds) == 2 and bounds[0] <= total <= bounds[1]
            checked += 1
    objective = sum(values[i] * coefficient for i, coefficient
                    in zip(proto.objective.vars, proto.objective.coeffs, strict=True))
    return {"complete_values": len(values), "active_rows_recounted": checked,
            "objective": objective}


def main():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    base = load(BASE / "run.py", "global_dp_base")
    dp = load(PLAN / "check.py", "global_dp_graph")
    previous = read(BASE / "manifest.json")
    gate_path = DAY / "three-core-profile-release-independent/gate.json"
    gate, plan = read(gate_path), read(PLAN / "result.json")
    assert gate["passed"] and gate["manifest_sha256"] == sha(BASE / "manifest.json")
    assert gate["source_sha256"] == sha(BASE / "run.py") == previous["source_sha256"]
    assert plan["passed"] and plan["source_sha256"] == sha(PLAN / "check.py")
    assert plan["optimizer_calls"] == 0
    for relative, digest in plan["input_files"].items():
        assert sha(ROOT / relative) == digest
    case = next(case for case in previous["cases"] if case["name"] == "full-4368")
    assert case["pool"] == list(range(4368)) and case["hint_holes"] == 10
    assert case["hint_core_overlaps"] == [1, 8, 55]
    hint = case["hint"]
    hint_path = ROOT / case["hint_source_path"]
    assert sha(hint_path) == case["hint_sha256"]
    block_rank = {block: index for index, block in enumerate(base.BLOCKS)}
    hint_blocks = [tuple(map(int, line.split()))
                   for line in hint_path.read_text().splitlines() if line.strip()]
    assert len(hint_blocks) == len(set(hint_blocks)) == 64
    assert sorted(block_rank[block] for block in hint_blocks) == hint
    post_path = DAY / "six-hole-strong-core-release-independent/postcheck.json"
    post = read(post_path)
    assert post["passed"]
    assert any(item["ids"] == hint and item["sha256"] == case["hint_sha256"]
               for checked in post["cases"] for item in checked["saved"] + [checked["final"]])
    graph = plan["reachable"]
    for key in ("rows", "states"):
        assert sha(ROOT / graph[key + "_path"]) == graph[key + "_sha256"]
    states = read(ROOT / graph["states_path"])
    packed = (ROOT / graph["rows_path"]).read_bytes()
    rows = list(struct.iter_unpack("<III", packed))
    assert len(states) == 4410 and len(rows) == 99917
    assert states[0] == 0 and len(set(states)) == 4410
    chosen = set(hint)
    counts = [len(chosen.intersection(carriers)) for carriers in base.SUPPORT]
    weights = {dp.mask(triple): 5 * (count >= 6) + (count >= 7)
               for triple, count in zip(base.TRIPLES, counts, strict=True)}
    hint_dp = dp.least_values(states, weights)
    targets = [state for state in states if state.bit_count() == 15]
    assert len(targets) == 16 and max(hint_dp[state] for state in targets) <= 26
    assert sum(count == 0 for count in counts) == 10
    build_started = time.monotonic()
    model, block_variables, _ = base.build_model(list(range(4368)), hint)
    original_variables = [str(var) for var in model.proto.variables]
    original_rows = [str(row) for row in model.proto.constraints]
    original_objective = str(model.proto.objective)
    assert len(original_variables) == 4958 and len(original_rows) == 1188
    six, seven = [], []
    for triple_id, carriers in enumerate(base.SUPPORT):
        count = sum(block_variables[i] for i in carriers)
        a = model.new_bool_var(f"global_triple_{triple_id}_at_least_6")
        b = model.new_bool_var(f"global_triple_{triple_id}_at_least_7")
        model.add(count >= 6).only_enforce_if(a)
        model.add(count <= 5).only_enforce_if(a.Not())
        model.add(count >= 7).only_enforce_if(b)
        model.add(count <= 6).only_enforce_if(b.Not())
        six.append(a)
        seven.append(b)
        model.add_hint(a, int(counts[triple_id] >= 6))
        model.add_hint(b, int(counts[triple_id] >= 7))
    dp_variables = []
    for state in states:
        upper = 26 if state.bit_count() == 15 else 2 * state.bit_count()
        variable = model.new_int_var(0, upper, f"dp_{state:04x}")
        dp_variables.append(variable)
        model.add_hint(variable, hint_dp[state])
    for current, parent, triple_id in rows:
        model.add(dp_variables[current] >= dp_variables[parent]
                  + 5 * six[triple_id] + seven[triple_id])
    build_seconds = time.monotonic() - build_started
    assert len(model.proto.variables) == 10488 and len(model.proto.constraints) == 103345
    assert [str(var) for var in list(model.proto.variables)[:4958]] == original_variables
    assert [str(row) for row in list(model.proto.constraints)[:1188]] == original_rows
    assert str(model.proto.objective) == original_objective
    validate_started = time.monotonic()
    assert not model.validate(), model.validate()
    hint_receipt = check_hint(model)
    assert hint_receipt["objective"] == 651
    validation_seconds = time.monotonic() - validate_started
    RAW.mkdir()
    parameters = sat_parameters_pb2.SatParameters(
        max_time_in_seconds=120, num_search_workers=4, random_seed=2026104104,
        log_search_progress=True, log_to_stdout=False,
    )
    params_path = RAW / "parameters.pbtxt"
    params_path.write_text(str(parameters))
    serialized_started = time.monotonic()
    model_path = RAW / "full-4368-model.pbtxt"
    model_path.write_text(str(model.proto))
    serialization_seconds = time.monotonic() - serialized_started
    for path in (Path(__file__), PLAN / "check.py", BASE / "run.py"):
        target = RAW / "frozen-sources" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    sources = dict(previous["input_files"])
    sources.update(plan["input_files"])
    sources.update({str(path.relative_to(ROOT)): sha(path) for path in (
        Path(__file__), BASE / "run.py", BASE / "manifest.json", gate_path,
        PLAN / "check.py", PLAN / "result.json", hint_path, post_path,
        ROOT / graph["rows_path"], ROOT / graph["states_path"],
    )})
    for relative, digest in sources.items():
        assert sha(ROOT / relative) == digest
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    stats = {
        "model_variables": 10488, "model_rows": 103345, "base_variables": 4958,
        "base_rows": 1188, "global_threshold_booleans": 1120, "threshold_rows": 2240,
        "dp_variables": 4410, "dp_recurrence_rows": 99917, "terminal_caps": 16,
        "named_filters_retained": 3, "all_block_options": 4368,
        "build_seconds": build_seconds, "validation_and_hint_seconds": validation_seconds,
        "serialization_seconds": serialization_seconds,
        "model_pbtxt_bytes": model_path.stat().st_size,
        "process_peak_rss_bytes": rss if sys.platform == "darwin" else 1024 * rss,
        "memory_scope": "Process peak, including imports, model, validation and serialization.",
        "solver_propagation_timing_claim": False, "optimizer_calls": 0,
    }
    dump(HERE / "build-stats.json", stats)
    manifest = {
        "source_sha256": sha(__file__), "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(), "input_files": sources, "ortools_version": ortools.__version__,
        "model_path": str(model_path.relative_to(ROOT)), "model_sha256": sha(model_path),
        "parameters_path": str(params_path.relative_to(ROOT)),
        "parameters_sha256": sha(params_path),
        "build_stats_sha256": sha(HERE / "build-stats.json"),
        "base_variable_prefix_sha256": data_sha(original_variables),
        "base_constraint_prefix_sha256": data_sha(original_rows),
        "base_objective_sha256": data_sha(original_objective),
        "base_prefix_unchanged": True, "hint_source_path": case["hint_source_path"],
        "hint_sha256": case["hint_sha256"], "hint_ids": hint, "hint_holes": 10,
        "hint_core_overlaps": [1, 8, 55], "hint_complete_receipt": hint_receipt,
        "hint_maximum_global_partition_weight": max(hint_dp[state] for state in targets),
        "core_rows": previous["core_rows"], "core_upper_bound": 55,
        "retained_named_partitions": previous["partitions"],
        "global_threshold_variable_start": 4958, "dp_variable_start": 6078,
        "dag": graph, "budget": {"cases": 1, "seconds": 120, "workers": 4,
                                  "seed": 2026104104}, "optimization_calls": 0,
        "scope": "Prepared full4368 model. Existing three-core/named-filter prefix and "
        "65*holes+original-core-overlap objective unchanged. Global exact threshold DP "
        "excludes every forbidden five-disjoint-heavy partition. Independent gate required "
        "before optimization. No covering witness or unrestricted infeasibility claim.",
    }
    dump(HERE / "manifest.json", manifest)
    print(json.dumps({"manifest_sha256": sha(HERE / "manifest.json"),
                      "model_sha256": sha(model_path), "source_sha256": sha(__file__),
                      "hint_maximum_global_partition_weight": manifest[
                          "hint_maximum_global_partition_weight"], **stats}, indent=2))


if __name__ == "__main__":
    main()
