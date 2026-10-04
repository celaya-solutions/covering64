#!/usr/bin/env python3
# Document:    Bounded Point Star Repair Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Full block domain within four conditional retained-block neighborhoods."""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/point-star-repair-20261004"
SOURCE = ROOT / "experiments/2026-10-03/heuristic-tabu-2026100301-deficit-3.txt"
RUNS = [(2, 2026104001), (2, 2026104002), (15, 2026104003), (15, 2026104004)]
SCOPE = ("All 4368 lexicographic blocks are variables; outside-star incumbent blocks "
         "are fixed. Results concern only these retained-block neighborhoods. "
         "Focused scheduling is new locally, not a new reachable neighborhood.")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def audit(path):
    blocks = read_blocks(path)
    if len(blocks) != 64 or len(set(blocks)) != 64:
        raise ValueError("expected 64 distinct blocks")
    package = verify_cover(blocks)
    checked = subprocess.run(
        [sys.executable, "-I", str(ROOT / "scripts/check_cover.py"), str(path),
         "--expected-blocks", "64"], capture_output=True, text=True, check=False,
    )
    standalone = json.loads(checked.stdout)
    # Direct fresh unions also check callback objective independently of caches.
    holes = sorted(set(combinations(range(1, 17), 3)) -
                   {t for block in blocks for t in combinations(block, 3)})
    if (checked.returncode not in (0, 1) or checked.stderr
            or standalone["blocks"] != 64 or not standalone["cardinality_matches"]
            or standalone["canonical_sha256"] != package["canonical_sha256"]
            or standalone["valid"] != package["valid"]
            or sorted(map(tuple, standalone["uncovered"])) != holes
            or sorted(map(tuple, package["uncovered"])) != holes):
        raise ValueError("independent coverage counts disagree")
    return {"package": package, "standalone": standalone, "holes": len(holes)}


def prepare():
    if (HERE / "metadata.json").exists():
        raise ValueError("prepared pilot already exists")
    RAW.mkdir(parents=True, exist_ok=True)
    universe = Universe.build()
    original = set(read_blocks(SOURCE))
    ids = {b: i for i, b in enumerate(universe.blocks)}
    selected = {ids[b] for b in original}
    if len(selected) != 64:
        raise ValueError("bad seed")
    write_blocks(HERE / "initial.txt", sorted(original))
    dump(HERE / "initial.audit.json", audit(HERE / "initial.txt"))
    models = []
    covered = {t for b in original for t in combinations(b, 3)}
    for point in (2, 15):
        removed = sorted(i for i in selected if point in universe.blocks[i])
        retained = sorted(selected - set(removed))
        model = cp_model.CpModel()
        xs = [model.NewBoolVar(f"block_{i}") for i in range(4368)]
        holes = [model.NewBoolVar(f"missing_{i}") for i in range(560)]
        model.Add(sum(xs) == 64)
        for i in retained:
            model.Add(xs[i] == 1)
        for tid, flag in enumerate(holes):
            count = sum(xs[i] for i in universe.containing[tid])
            model.Add(count == 0).OnlyEnforceIf(flag)
            model.Add(count >= 1).OnlyEnforceIf(flag.Not())
        weight = len(removed) + 1
        model.Minimize(weight * sum(holes) + sum(xs[i] for i in removed))
        for i, x in enumerate(xs):
            model.AddHint(x, int(i in selected))
        for t, h in zip(universe.triples, holes):
            model.AddHint(h, int(t not in covered))
        if model.Validate():
            raise ValueError(model.Validate())
        path = RAW / f"point-{point}.pbtxt"
        model.ExportToFile(str(path))
        models.append({"point": point, "removed_ids": removed,
                       "retained_ids": retained, "weight": weight,
                       "model_file": str(path), "model_sha256": sha(path)})
    (RAW / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    dependencies = ["src/covering64/core.py", "scripts/check_cover.py",
                    "scripts/partial_core_hole_search.py"]
    dump(HERE / "metadata.json", {
        "scope": SCOPE, "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dependencies": {p: sha(ROOT / p) for p in dependencies},
        "initial_sha256": sha(HERE / "initial.txt"),
        "ortools": ortools.__version__, "python": sys.version,
        "runs": [{"point": p, "seed": s, "seconds": 30, "workers": 1}
                 for p, s in RUNS], "models": models,
    })
    print("Prepared two models; no optimization has run.", flush=True)


class SaveSolutions(cp_model.CpSolverSolutionCallback):
    def __init__(self, model, universe, spec, folder, initial):
        super().__init__()
        self.model, self.universe, self.spec = model, universe, spec
        self.folder, self.initial, self.saved = folder, initial, []

    def on_solution_callback(self):
        chosen = {i for i in range(4368)
                  if self.Value(self.model.GetBoolVarFromProtoIndex(i))}
        blocks = [self.universe.blocks[i] for i in sorted(chosen)]
        path = self.folder / f"solution-{len(self.saved):03d}.txt"
        write_blocks(path, blocks)
        checked = audit(path)
        old_count = len(chosen & set(self.spec["removed_ids"]))
        score = self.spec["weight"] * checked["holes"] + old_count
        if (not set(self.spec["retained_ids"]) <= chosen
                or round(self.ObjectiveValue()) != score):
            raise ValueError("candidate violates retained blocks or exact objective")
        row = {"path": str(path.relative_to(HERE)), "sha256": sha(path),
               "holes": checked["holes"], "objective": score,
               "old_removed_blocks_reselected": old_count,
               "seconds": self.WallTime(),
               "deleted_from_initial": sorted(self.initial - chosen),
               "added_to_initial": sorted(chosen - self.initial)}
        dump(path.with_suffix(".audit.json"), checked)
        self.saved.append(row)
        print(json.dumps({"event": "solution", **row}), flush=True)
        if checked["holes"] == 0:
            self.StopSearch()


def run():
    metadata = json.loads((HERE / "metadata.json").read_text())
    gate = json.loads((HERE / "gate.json").read_text())
    if gate.get("passed") is not True:
        raise ValueError("independent gate is not passing")
    if sha(__file__) != metadata["source_sha256"]:
        raise ValueError("runner changed after preparation")
    if sha(RAW / "source_snapshot.py") != metadata["source_sha256"]:
        raise ValueError("snapshot changed")
    if sha(HERE / "initial.txt") != metadata["initial_sha256"]:
        raise ValueError("initial witness changed")
    for path, digest in metadata["dependencies"].items():
        if sha(ROOT / path) != digest:
            raise ValueError("dependency changed")
    if gate["metadata_sha256"] != sha(HERE / "metadata.json"):
        raise ValueError("gate does not bind this metadata")
    universe = Universe.build()
    original = set(read_blocks(HERE / "initial.txt"))
    initial = {i for i, block in enumerate(universe.blocks) if block in original}
    spec_loader = importlib.util.spec_from_file_location(
        "profile_helper", ROOT / "scripts/partial_core_hole_search.py")
    helper = importlib.util.module_from_spec(spec_loader)
    spec_loader.loader.exec_module(helper)
    results = []
    for item in metadata["runs"]:
        point, seed = item["point"], item["seed"]
        spec = next(s for s in metadata["models"] if s["point"] == point)
        if sha(spec["model_file"]) != spec["model_sha256"]:
            raise ValueError("model changed")
        folder = HERE / f"p{point}-seed{seed}"
        folder.mkdir()
        model = cp_model.CpModel()
        if not model.Proto().parse_text_format(Path(spec["model_file"]).read_text()):
            raise ValueError("model parse failed")
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = seed
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = False
        callback = SaveSolutions(model, universe, spec, folder, initial)
        started = time.monotonic()
        log_path = RAW / f"p{point}-seed{seed}.log"
        with log_path.open("w") as log:
            solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
            status = solver.Solve(model, callback)
        for saved in callback.saved:
            saved["profile"] = helper.profile(read_blocks(HERE / saved["path"]))
        result = {**item, "status": solver.StatusName(status),
                  "solver_seconds": solver.WallTime(),
                  "elapsed_seconds": time.monotonic() - started,
                  "objective_bound": solver.BestObjectiveBound(),
                  "response_stats": solver.ResponseStats(), "saved": callback.saved,
                  "log_sha256": sha(log_path),
                  "best_holes": min((s["holes"] for s in callback.saved), default=None)}
        dump(folder / "result.json", result)
        results.append(result)
        print(json.dumps({k: v for k, v in result.items()
                          if k not in ("saved", "response_stats")}), flush=True)
        if result["best_holes"] == 0:
            break
    dump(HERE / "summary.json", {"scope": SCOPE, "runs": results,
                               "gate_sha256": sha(HERE / "gate.json"),
                               "metadata_sha256": sha(HERE / "metadata.json")})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "run"))
    args = parser.parse_args()
    prepare() if args.action == "prepare" else run()
