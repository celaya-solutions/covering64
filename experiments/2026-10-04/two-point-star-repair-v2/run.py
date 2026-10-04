"""Bounded two-point-star hole repair from the checked D26 partial."""

import argparse
import hashlib
import itertools
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/two-point-star-repair-v2-20261004"
BASE = HERE.parent / "weak-pair-d28-deterministic-descent/center-02.txt"
BASE_SHA = "f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
TRIPLES = list(itertools.combinations(range(1, 17), 3))
RANK = {b: i for i, b in enumerate(BLOCKS)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def family(ids):
    return "".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in ids)


def dual(path):
    results = []
    for prefix in (["uv", "run", "covering64", "verify"],
                   [sys.executable, "scripts/check_cover.py"]):
        process = subprocess.run(
            [*prefix, str(path), "--expected-blocks", "64"], cwd=ROOT,
            capture_output=True, text=True, check=False,
        )
        result = json.loads(process.stdout)
        assert process.returncode == int(not result["valid"])
        assert result["blocks"] == 64
        results.append(result)
    for key in ("valid", "uncovered", "canonical_sha256"):
        assert results[0][key] == results[1][key]
    return results


def build(ids, pivot):
    model = cp_model.CpModel()
    chosen = set(ids)
    variables = []
    for i, block in enumerate(BLOCKS):
        if set(block).isdisjoint(pivot):
            value = int(i in chosen)
            variables.append(model.new_int_var(value, value, f"b_{i}"))
        else:
            variables.append(model.new_bool_var(f"b_{i}"))
    model.add(sum(variables) == 64)
    holes = []
    for j, triple in enumerate(TRIPLES):
        indices = [i for i, block in enumerate(BLOCKS) if set(triple) <= set(block)]
        count = sum(variables[i] for i in indices)
        hole = model.new_bool_var(f"h_{j}")
        model.add(count == 0).only_enforce_if(hole)
        model.add(count >= 1).only_enforce_if(hole.Not())
        holes.append(hole)
        model.add_hint(hole, int(not chosen.intersection(indices)))
    for pair in itertools.combinations(range(1, 17), 2):
        model.add(sum(variables[i] for i, b in enumerate(BLOCKS)
                      if set(pair) <= set(b)) >= 5)
    model.add(sum(holes) <= 12)
    model.minimize(sum(holes))
    for i, variable in enumerate(variables):
        model.add_hint(variable, int(i in chosen))
    assert not model.validate()
    return model


def read_model(path):
    model = cp_model.CpModel()
    assert model.proto.parse_text_format(path.read_text())
    return model


def check_vector(model, values):
    assert all(type(value) is int for value in values)
    proto = model.proto
    assert len(values) == len(proto.variables)
    for value, variable in zip(values, proto.variables):
        domain = list(variable.domain)
        assert any(a <= value <= b for a, b in zip(domain[::2], domain[1::2]))
    for row in proto.constraints:
        active = all(values[e] if e >= 0 else not values[-e - 1]
                     for e in row.enforcement_literal)
        if active:
            assert row.has_linear()
            amount = sum(values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs))
            domain = list(row.linear.domain)
            assert any(a <= amount <= b for a, b in zip(domain[::2], domain[1::2]))


def prepare():
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    assert sha(BASE) == BASE_SHA
    blocks = [tuple(map(int, line.split())) for line in BASE.read_text().splitlines()]
    ids = sorted(RANK[b] for b in blocks)
    assert len(ids) == len(set(ids)) == 64
    checked = dual(BASE)
    assert len(checked[0]["uncovered"]) == 12
    RAW.mkdir(parents=True)
    entries = []
    for number, pivot in enumerate(((6, 14), (1, 9)), 1):
        model = build(ids, pivot)
        path = RAW / f"model-{number}.pbtxt"
        path.write_text(str(model.proto))
        values = [int(i in ids) for i in range(len(BLOCKS))]
        counts = {t: sum(set(t) <= set(BLOCKS[i]) for i in ids) for t in TRIPLES}
        values += [int(counts[t] == 0) for t in TRIPLES]
        check_vector(model, values)
        entries.append({
            "number": number, "pivot": list(pivot), "model": str(path.relative_to(ROOT)),
            "model_sha256": sha(path), "seed": 2026105300 + number,
            "fixed_selected": sum(set(BLOCKS[i]).isdisjoint(pivot) for i in ids),
            "free_blocks": sum(not set(b).isdisjoint(pivot) for b in BLOCKS),
            "variables": len(model.proto.variables), "rows": len(model.proto.constraints),
        })
    dump(HERE / "manifest.json", {
        "source_sha256": sha(__file__), "base_sha256": BASE_SHA,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "ortools_version": ortools.__version__, "entries": entries,
        "seconds": 60, "workers": 4, "watchdog": 80, "grace": 5,
        "search_launches_during_preparation": 0, "baseline_verifiers": checked,
        "scope": "Two fixed local neighborhoods. Outside each two-point star all block "
        "memberships are frozen. Exact 64 and pair floor5; holes are exact. No D3/D4 "
        "or core restrictions. No unrestricted, nonexistence or novelty claim.",
    })


class Collector(cp_model.CpSolverSolutionCallback):
    def __init__(self, model, output):
        super().__init__()
        self.variables = [model.get_int_var_from_proto_index(i)
                          for i in range(len(model.proto.variables))]
        self.output = output
        self.count = 0

    def on_solution_callback(self):
        self.count += 1
        values = [self.value(v) for v in self.variables]
        dump(self.output / f"callback-{self.count:03d}.json", {"values": values})
        if sum(values[len(BLOCKS):]) == 0:
            self.stop_search()


def child(number):
    manifest = json.loads((HERE / "manifest.json").read_text())
    entry = manifest["entries"][number - 1]
    model = read_model(ROOT / entry["model"])
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = manifest["seconds"]
    solver.parameters.num_search_workers = manifest["workers"]
    solver.parameters.random_seed = entry["seed"]
    solver.parameters.log_search_progress = True
    output = RAW / f"run-{number}"
    (output / "parameters.pbtxt").write_text(str(solver.parameters))
    collector = Collector(model, output)
    status = solver.solve(model, collector)
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        dump(output / "final-vector.json", {"values": list(solver.response_proto.solution)})
    (output / "response.pbtxt").write_text(str(solver.response_proto))
    dump(output / "outcome.json", {
        "status": solver.status_name(status), "wall_seconds": solver.wall_time,
        "callbacks": collector.count, "objective": solver.objective_value,
        "bound": solver.best_objective_bound,
    })


def execute(gate_path):
    gate = json.loads(gate_path.read_text())
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert gate["decision"] == "GO" and gate["passed"] is True
    assert gate["manifest_sha256"] == sha(manifest_path)
    assert manifest["source_sha256"] == sha(__file__)
    assert sha(BASE) == BASE_SHA
    assert not (HERE / "result.json").exists()
    assert not any(RAW.glob("run-*"))
    for entry in manifest["entries"]:
        assert sha(ROOT / entry["model"]) == entry["model_sha256"]
    runs = []
    for entry in manifest["entries"]:
        number = entry["number"]
        output = RAW / f"run-{number}"
        output.mkdir()
        command = [sys.executable, str(Path(__file__).resolve()), "--child", str(number)]
        started = time.monotonic()
        timeout = False
        with (output / "stdout.log").open("w") as out, (output / "stderr.log").open("w") as err:
            process = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err)
            try:
                process.wait(timeout=manifest["watchdog"])
            except subprocess.TimeoutExpired:
                timeout = True
                process.terminate()
                try:
                    process.wait(timeout=manifest["grace"])
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        model = read_model(ROOT / entry["model"])
        saved = []
        vectors = sorted(output.glob("callback-*.json"))
        if (output / "final-vector.json").exists():
            vectors.append(output / "final-vector.json")
        for vector_path in vectors:
            values = json.loads(vector_path.read_text())["values"]
            check_vector(model, values)
            ids = [i for i, v in enumerate(values[:len(BLOCKS)]) if v]
            witness = output / (vector_path.stem + ".txt")
            witness.write_text(family(ids))
            checks = dual(witness)
            holes = len(checks[0]["uncovered"])
            assert holes == sum(values[len(BLOCKS):])
            saved.append({"vector": str(vector_path.relative_to(ROOT)),
                          "witness": str(witness.relative_to(ROOT)), "holes": holes,
                          "sha256": sha(witness), "verifiers": checks})
            if holes == 0:
                (HERE / "cover.txt").write_text(witness.read_text())
        outcome_path = output / "outcome.json"
        outcome = json.loads(outcome_path.read_text()) if outcome_path.exists() else None
        row = {"number": number, "pivot": entry["pivot"], "command": command,
               "returncode": process.returncode, "watchdog_fired": timeout,
               "elapsed_seconds": time.monotonic() - started, "outcome": outcome,
               "saved": saved, "cover_found": any(v["holes"] == 0 for v in saved)}
        dump(HERE / f"run-{number}-result.json", row)
        runs.append(row)
        if row["cover_found"] or timeout or process.returncode != 0 or outcome is None:
            break
    result = {"manifest_sha256": sha(manifest_path), "gate_sha256": sha(gate_path),
              "runs": runs, "relaunch": False,
              "cover_found": any(r["cover_found"] for r in runs),
              "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.rglob("*"))
                            if p.is_file()}, "scope": manifest["scope"]}
    dump(HERE / "result.json", result)
    print(json.dumps({"cover_found": result["cover_found"], "result_sha256":
                      sha(HERE / "result.json"), "runs": len(runs)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--child", type=int, choices=(1, 2))
    group.add_argument("--execute", type=Path, metavar="GATE")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.child:
        child(args.child)
    else:
        execute(args.execute)
