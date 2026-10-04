# Document:    Gated Frozen Global Five-Heavy DP Execution
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      9c3477f5bf5a759376dae33fab89b0d783bdd13bf623c3c296d8f780c2d990ad
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Load the serialized model and run exactly once after a separately bound gate."""

import argparse
import hashlib
import importlib.util
import itertools
import json
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/global-five-heavy-dp-run-20261004"
OUTPUT = HERE / "full-4368"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    assert not Path(path).exists()
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def load_frozen(manifest):
    model_path = ROOT / manifest["model_path"]
    parameter_path = ROOT / manifest["parameters_path"]
    assert sha(model_path) == manifest["model_sha256"]
    assert sha(parameter_path) == manifest["parameters_sha256"]
    assert manifest["ortools_version"] == ortools.__version__
    model = cp_model.CpModel()
    assert model.proto.parse_text_format(model_path.read_text())
    assert hashlib.sha256(str(model.proto).encode()).hexdigest() == manifest["model_sha256"]
    assert not model.validate(), model.validate()
    assert len(model.proto.variables) == 10488 and len(model.proto.constraints) == 103345
    solver = cp_model.CpSolver()
    assert solver.parameters.parse_text_format(parameter_path.read_text())
    assert hashlib.sha256((str(solver.parameters) + "\n").encode()).hexdigest() == (
        manifest["parameters_sha256"]
    )
    assert solver.parameters.max_time_in_seconds == 120
    assert solver.parameters.num_search_workers == 4
    assert solver.parameters.random_seed == 2026104104
    assert not solver.parameters.log_to_stdout
    return model, solver


def save_state(ids, missing, objective, values, label, manifest, dp):
    assert len(ids) == len(set(ids)) == 64 and ids == sorted(ids)
    assert all(type(i) is int and 0 <= i < 4368 for i in ids)
    chosen = set(ids)
    counts = Counter(triple for i in ids for triple in itertools.combinations(BLOCKS[i], 3))
    recounted = [i for i, triple in enumerate(TRIPLES) if counts[triple] == 0]
    assert missing == recounted
    overlaps = [len(chosen & set(core)) for core in manifest["core_rows"]]
    assert max(overlaps) <= 55 and objective == 65 * len(missing) + overlaps[0]
    states = dp[1]
    weights = {dp[0].mask(t): 5 * (counts[t] >= 6) + (counts[t] >= 7) for t in TRIPLES}
    least = dp[0].least_values(states, weights)
    maximum = max(least[state] for state in states if state.bit_count() == 15)
    assert maximum <= 26
    path = OUTPUT / f"{label}-h{len(missing)}-c{overlaps[0]}.txt"
    vector_path = RAW / f"{label}-values.json"
    assert not path.exists()
    path.write_text("".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in ids))
    dump(vector_path, values)
    return {
        "label": label, "ids": ids, "holes": len(missing), "hole_triple_ids": missing,
        "composite_objective": objective, "core_overlaps": overlaps,
        "global_partition_maximum": maximum, "path": str(path.relative_to(ROOT)),
        "sha256": sha(path), "values_path": str(vector_path.relative_to(ROOT)),
        "values_sha256": sha(vector_path),
    }


class SaveStates(cp_model.CpSolverSolutionCallback):
    def __init__(self, model, manifest, dp, emit):
        super().__init__()
        self.variables = [model.get_int_var_from_proto_index(i) for i in range(10488)]
        self.manifest, self.dp, self.emit = manifest, dp, emit
        self.best, self.records, self.seen = None, [], set()
        self.zero = False

    def on_solution_callback(self):
        objective = int(round(self.objective_value))
        if self.best is not None and objective > self.best:
            return
        values = [self.value(variable) for variable in self.variables]
        ids = [i for i in range(4368) if values[i]]
        missing = [i for i in range(560) if values[4368 + i]]
        key = tuple(ids)
        if key in self.seen and objective == self.best:
            if not missing:
                self.zero = True
                self.stop_search()
            return
        kind = "improvement" if self.best is None or objective < self.best else "callback_tie"
        record = save_state(ids, missing, objective, values,
                            f"callback-{len(self.records):03d}", self.manifest, self.dp)
        record["kind"] = kind
        record["callback_seconds"] = self.wall_time
        self.records.append(record)
        self.seen.add(key)
        self.best = objective
        with (RAW / "callback-records.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")
        self.emit({"event": kind, "objective": objective, "holes": len(missing),
                   "callback_seconds": self.wall_time, "path": record["path"]})
        if not missing:
            self.zero = True
            self.stop_search()


def run(gate_path):
    manifest_path = HERE / "manifest.json"
    manifest, gate = read(manifest_path), read(gate_path)
    assert gate["passed"] and gate["manifest_sha256"] == sha(manifest_path)
    assert gate["source_sha256"] == manifest["source_sha256"] == sha(HERE / "prepare.py")
    assert gate["runner_source_sha256"] == sha(__file__)
    assert gate["model_sha256"] == manifest["model_sha256"]
    assert gate["parameters_sha256"] == manifest["parameters_sha256"]
    for relative, expected in manifest["input_files"].items():
        assert sha(ROOT / relative) == expected
    assert not RAW.exists() and not OUTPUT.exists() and not (HERE / "result.json").exists()
    model, solver = load_frozen(manifest)
    proof_source = HERE.parent / "global-five-heavy-dp-plan/check.py"
    spec = importlib.util.spec_from_file_location("frozen_dp_counter", proof_source)
    dp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dp)
    states = read(ROOT / manifest["dag"]["states_path"])
    RAW.mkdir()
    OUTPUT.mkdir()
    snapshots = {
        "execute.py": Path(__file__), "prepare.py": HERE / "prepare.py",
        "manifest.json": manifest_path, "gate.json": gate_path,
        "model.pbtxt": ROOT / manifest["model_path"],
        "parameters.pbtxt": ROOT / manifest["parameters_path"],
    }
    for name, source in snapshots.items():
        (RAW / name).write_bytes(source.read_bytes())
        assert sha(RAW / name) == sha(source)

    def emit(value):
        text = json.dumps(value)
        with (RAW / "stdout.log").open("a") as stream:
            stream.write(text + "\n")
        print(text, flush=True)

    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(), "runner_source_sha256": sha(__file__),
        "manifest_sha256": sha(manifest_path), "gate_sha256": sha(gate_path),
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "budget": manifest["budget"], "ortools_version": ortools.__version__,
    }
    dump(RAW / "start.json", start)
    emit({"event": "start", **start})
    callback = SaveStates(model, manifest, (dp, states), emit)
    with (RAW / "solver.log").open("w") as log:
        def write_log(message):
            log.write(message)
            log.flush()

        solver.log_callback = write_log
        before = time.monotonic()
        status = solver.solve(model, callback)
        elapsed = time.monotonic() - before
    (RAW / "response.pbtxt").write_text(str(solver.response_proto))
    (RAW / "used-parameters.pbtxt").write_text(str(solver.parameters) + "\n")
    assert sha(RAW / "used-parameters.pbtxt") == manifest["parameters_sha256"]
    final = None
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        values = list(solver.response_proto.solution)
        assert len(values) == 10488
        ids = [i for i in range(4368) if values[i]]
        missing = [i for i in range(560) if values[4368 + i]]
        final = save_state(ids, missing, int(round(solver.objective_value)), values,
                           "final-response", manifest, (dp, states))
        final["ties_callback_best"] = final["composite_objective"] == callback.best
        final["matches_saved_callback_ids"] = any(final["ids"] == row["ids"]
                                                 for row in callback.records)
    verified_zero = []
    zeros = {row["path"]: row for row in callback.records + ([final] if final else [])
             if row["holes"] == 0}
    for path in zeros:
        receipts = []
        for prefix in (["uv", "run", "covering64", "verify"],
                       ["uv", "run", "python", "scripts/check_cover.py"]):
            checked = subprocess.run(prefix + [str(ROOT / path), "--expected-blocks", "64"],
                                     cwd=ROOT, capture_output=True, text=True, check=True)
            receipt = json.loads(checked.stdout)
            assert receipt["valid"]
            receipts.append(receipt)
        assert receipts[0]["canonical_sha256"] == receipts[1]["canonical_sha256"]
        verified_zero.append({"path": path, "verifiers": receipts})
    result = {
        **start, "status": solver.status_name(status), "seconds": elapsed,
        "reported_seconds": solver.wall_time, "objective_bound": solver.best_objective_bound,
        "best_composite_objective": callback.best, "records": callback.records,
        "final": final, "stopped_on_zero": callback.zero,
        "verified_zero_candidates": verified_zero, "covering_witness": bool(verified_zero),
        "optimization_calls": 1, "global_lower_bound_claim": False,
        "scope": "One frozen full4368 run. All callback improvements and distinct callback "
        "ties plus the native final state are saved. UNKNOWN/timeouts are inconclusive; "
        "native infeasibility is not an independently checked theorem.",
    }
    emit({"event": "finished", "status": result["status"], "seconds": elapsed,
          "best_objective": callback.best, "final_holes": final["holes"] if final else None,
          "records": len(callback.records), "stopped_on_zero": callback.zero})
    result["raw_files"] = {
        path.name: {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
        for path in sorted(RAW.iterdir()) if path.is_file()
    }
    dump(HERE / "result.json", result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=Path, required=True)
    run(parser.parse_args().gate)
