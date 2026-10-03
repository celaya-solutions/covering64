# Document:    Selected Heavy Triple Hub Cuts and Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Selected hub consequences of regular full covers; partial construction restrictions."""

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks

SELECTED = ((1, 2, 3), (5, 11, 16), (7, 10, 13), (8, 9, 14))
ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "experiments/2026-10-03/first-family-independent/check.py"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def signature(terms, lower, upper, enforcement=()):
    return tuple(sorted(enforcement)), tuple(sorted(terms)), (lower, upper)


def validate_base(universe, model, xs):
    """Require exact heavy flags and regularity before adding conditional hub cuts."""
    require((universe.v, universe.k, universe.t) == (16, 5, 3), "wrong universe")
    require(len(xs) == 4368, "all lexicographic block variables are required")
    names = {v.name: i for i, v in enumerate(model.proto.variables)}
    require(len(names) == len(model.proto.variables), "duplicate variable names")
    for i, x in enumerate(xs):
        require(x.index == i and x.name == f"block_{i}", "wrong block variable order")
        require(tuple(model.proto.variables[i].domain) == (0, 1), "block is not Boolean")
    rows = {
        (tuple(sorted(c.enforcement_literal)), tuple(sorted(zip(c.linear.vars, c.linear.coeffs))),
         tuple(c.linear.domain)) for c in model.proto.constraints if c.has_linear()
    }
    low, high = -9223372036854775808, 9223372036854775807
    for tid, containing in enumerate(universe.containing):
        terms = [(xs[i].index, 1) for i in containing]
        for threshold in (6, 7):
            name = f"heavy{threshold}_{tid}"
            require(name in names, f"missing {name}")
            index = names[name]
            require(tuple(model.proto.variables[index].domain) == (0, 1), "heavy flag not Boolean")
            lower, upper = (6, high) if threshold == 6 else (7, 7)
            require(signature(terms, lower, upper, (index,)) in rows, "missing heavy forward row")
            require(signature(terms, low, threshold - 1, (-index - 1,)) in rows,
                    "missing heavy converse row")
        require(signature(terms, low, 7) in rows, "missing regular multiplicity cap")
    for point in range(1, 17):
        terms = [(i, 1) for i, block in enumerate(universe.blocks) if point in block]
        require(signature(terms, 20, 20) in rows, "missing regular point degree")
    return {name: model.get_int_var_from_proto_index(i) for name, i in names.items()}


def add_selected_hub_cuts(universe, model, xs, selected=SELECTED):
    variables = validate_base(universe, model, xs)
    require(not any(name.startswith("selected_hub_") for name in variables),
            "selected hub cuts already present")
    selected = tuple(tuple(t) for t in selected)
    require(len(set(selected)) == len(selected), "duplicate selected triple")
    for triple in selected:
        require(len(triple) == 3 and tuple(sorted(set(triple))) == triple
                and all(type(p) is int and 1 <= p <= 16 for p in triple), "malformed triple")
    tids = {triple: i for i, triple in enumerate(universe.triples)}
    before = len(model.proto.variables), len(model.proto.constraints)
    hubs = {}
    for triple in selected:
        tid = tids[triple]
        six, seven = variables[f"heavy6_{tid}"], variables[f"heavy7_{tid}"]
        local = []
        for point in range(1, 17):
            if point in triple:
                continue
            count = sum(xs[i] for i in universe.containing[tid] if point in universe.blocks[i])
            hub = model.new_bool_var(f"selected_hub_{tid}_{point}")
            hubs[triple, point] = hub
            local.append(hub)
            model.add(hub <= six)
            model.add(count >= 2).only_enforce_if(hub)
            model.add(count <= 1).only_enforce_if([six, hub.Not()])
            model.add(count <= 3).only_enforce_if(six)
            model.add(count <= 2).only_enforce_if(seven)
        model.add(sum(local) <= 1)
    for point in range(1, 17):
        heavy = [variables[f"heavy6_{i}"] for i, t in enumerate(universe.triples) if point in t]
        selected_hubs = [h for (t, p), h in hubs.items() if p == point]
        model.add(sum(heavy) + sum(selected_hubs) <= 1)
    return {
        "selected_triples": selected,
        "new_variables": len(model.proto.variables) - before[0],
        "new_rows": len(model.proto.constraints) - before[1],
        "scope": "Only selected triples have hub flags; point rows include every heavy triple.",
    }


def selected_hub_hint_values(universe, blocks, selected=SELECTED):
    triples = Counter(t for b in blocks for t in combinations(b, 3))
    quads = Counter(q for b in blocks for q in combinations(b, 4))
    tids = {t: i for i, t in enumerate(universe.triples)}
    return {f"selected_hub_{tids[t]}_{p}": int(
        triples[t] >= 6 and quads[tuple(sorted((*t, p)))] >= 2)
        for t in selected for p in range(1, 17) if p not in t}


def assignment_check(model):
    spec = importlib.util.spec_from_file_location("selected_hub_assignment_audit", AUDIT_PATH)
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(str(model.proto), proto)
    require(list(proto.solution_hint.vars) == list(range(len(proto.variables))),
            "hint is incomplete or unordered")
    audit.verify_assignment(proto, list(proto.solution_hint.values))


def check_candidate(blocks, path):
    write_blocks(path, blocks)
    package = verify_cover(blocks)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_cover.py"), str(path),
         "--expected-blocks", "64"], capture_output=True, text=True,
    )
    require(proc.returncode in (0, 1), "standalone verifier failed")
    standalone = json.loads(proc.stdout)
    require(len(blocks) == 64 and package["canonical_sha256"] == standalone["canonical_sha256"]
            and len(package["uncovered"]) == standalone["uncovered_count"], "checkers disagree")
    require(Counter(p for b in blocks for p in b) == Counter({p: 20 for p in range(1, 17)}),
            "candidate is not regular")
    return {"package": package, "standalone": standalone}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--seed", type=int, default=2026102801)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    require(math.isfinite(args.seconds) and 0 < args.seconds <= 300, "invalid time budget")
    require(1 <= args.workers <= 4, "invalid worker count")
    args.output.mkdir(parents=True, exist_ok=True)
    old = json.loads((args.input_run / "metadata.json").read_text())
    raw = (args.input_run / "model.pbtxt").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == old["model_sha256"], "input model hash mismatch")
    candidate = args.input_run / "initial.txt"
    require(hashlib.sha256(candidate.read_bytes()).hexdigest() == old["hint_sha256"],
            "input witness hash mismatch")
    blocks = read_blocks(candidate)
    checked = check_candidate(blocks, args.output / "initial.txt")
    universe = Universe.build()
    model = cp_model.CpModel()
    require(model.proto.parse_text_format(raw.decode()), "model parse failed")
    original_hint = list(model.proto.solution_hint.values)
    assignment_check(model)
    xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
    application = add_selected_hub_cuts(universe, model, xs)
    extra = selected_hub_hint_values(universe, blocks)
    for i in range(len(original_hint), len(model.proto.variables)):
        model.add_hint(model.get_int_var_from_proto_index(i), extra[model.proto.variables[i].name])
    assignment_check(model)
    model_path = args.output / "model.pbtxt"
    model.export_to_file(str(model_path))
    sources = {}
    for name, digest in old["sources"].items():
        source = (args.input_run / name).read_bytes()
        require(hashlib.sha256(source).hexdigest() == digest, "input source hash mismatch")
        (args.output / name).write_bytes(source)
        sources[name] = digest
    for path in (Path(__file__), AUDIT_PATH, ROOT / "scripts/check_cover.py",
                 ROOT / "src/covering64/core.py"):
        target = args.output / ("assignment-audit.py" if path == AUDIT_PATH else path.name)
        target.write_bytes(path.read_bytes())
        sources[target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
    metadata = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources, "input_run": str(args.input_run), "input_metadata": old,
        "input_model_sha256": old["model_sha256"],
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "hint_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        "application": application, "auxiliary_hints": extra,
        "variables": len(model.proto.variables), "constraints": len(model.proto.constraints),
        "complete_hint_values": len(model.proto.solution_hint.values),
        "hint_validation": "Every domain and active row evaluated with integer arithmetic",
        "initial": checked, "solver_version": ortools.__version__,
        "seed": args.seed, "seconds": args.seconds, "workers": args.workers,
        "command": sys.argv, "scope": "Selected-heavy hub restrictions in a regular partial model.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    prepared = {"prepared": True, **application, "variables": metadata["variables"],
                "constraints": metadata["constraints"]}
    print(json.dumps(prepared), flush=True)
    if args.prepare_only:
        return
    holes = [model.get_int_var_from_proto_index(i) for i in range(4368, 4928)]

    class Capture(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__()
            self.records = []
            self.best = len(checked["package"]["uncovered"]) + 1

        def on_solution_callback(self):
            missing = sum(self.value(x) for x in holes)
            if missing >= self.best:
                return
            witness = [b for i, b in enumerate(universe.blocks) if self.value(xs[i])]
            report = check_candidate(witness, args.output / f"candidate-h{missing}.txt")
            require(report["standalone"]["uncovered_count"] == missing, "objective mismatch")
            self.best = missing
            self.records.append({"missing": missing, "seconds": self.wall_time, "checks": report})
            (args.output / "improvements.json").write_text(
                json.dumps(self.records, indent=2) + "\n")
            print(json.dumps({"missing": missing, "seconds": self.wall_time}), flush=True)

    capture = Capture()
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (args.output / "solver-parameters.txt").write_text(str(solver.parameters))
    with (args.output / "solver.log").open("w") as stream:
        solver.log_callback = lambda line: stream.write(line + "\n")
        status = solver.solve(model, capture)
    result = {"status": solver.status_name(status), "seconds": solver.wall_time,
              "best_missing": min(capture.best, len(checked["package"]["uncovered"])),
              "improvements": capture.records, "response_stats": solver.response_stats(),
              "cover_found": any(r["missing"] == 0 for r in capture.records)}
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "seconds", "best_missing", "cover_found")}))


if __name__ == "__main__":
    main()
