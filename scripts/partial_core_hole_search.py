#!/usr/bin/env python3
# Document:    Joint Core Escape Partial Cover Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bounded constructive search; the original-core overlap band is not complete."""

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[1]
VERSION = "v1.0.0"
SEED = 2026103991
SECONDS = 180


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def profile(blocks):
    counts = Counter(t for block in blocks for t in combinations(block, 3))
    heavy = sorted((triple, count) for triple, count in counts.items() if count >= 6)
    forbidden = []
    disjoint_five = []
    for group in combinations(heavy, 5):
        if len({p for triple, _ in group for p in triple}) == 15:
            disjoint_five.append(group)
            if sum(count >= 7 for _, count in group) >= 2:
                forbidden.append(group)
    return {
        "heavy_triples": heavy,
        "five_disjoint_heavy_sets": disjoint_five,
        "forbidden_five_heavy_profile": bool(forbidden),
        "forbidden_witnesses": forbidden,
        "interpretation": "Label-invariant screen only; this is not a coverage test.",
    }


def audit(path, core):
    blocks = read_blocks(path)
    if len(blocks) != 64 or len(set(blocks)) != 64:
        raise ValueError("candidate must contain 64 distinct blocks")
    package = verify_cover(blocks)
    run = subprocess.run(
        [sys.executable, "-I", str(ROOT / "scripts/check_cover.py"), str(path),
         "--expected-blocks", "64"], capture_output=True, text=True, check=False,
    )
    independent = json.loads(run.stdout)
    if (run.returncode not in (0, 1) or independent["blocks"] != 64
            or not independent["cardinality_matches"]
            or independent["canonical_sha256"] != package["canonical_sha256"]
            or set(map(tuple, independent["uncovered"])) != set(package["uncovered"])
            or independent["valid"] != package["valid"]):
        raise ValueError("cover verifiers disagree")
    return {
        "package": package, "standalone": independent,
        "original_core_overlap": len(set(blocks) & core),
        "holes": len(package["uncovered"]), "profile": profile(blocks),
        "useful_escape_seed": False,
        "useful_escape_reason": "Requires independent relabeled-core screening before use.",
    }


def make_hint(universe, blocks, core):
    selected = set(blocks)
    counts = Counter(t for block in selected for t in combinations(block, 3))
    ranked = sorted(
        (sum(counts[t] == 1 for t in combinations(block, 3)), block)
        for block in selected & core
    )
    if len(selected & core) != 60:
        raise ValueError("initial seed must contain the complete specified core")
    removed = [block for _, block in ranked[:5]]
    selected.difference_update(removed)
    added = []
    for _ in range(5):
        covered = {t for block in selected for t in combinations(block, 3)}
        block = min(
            (block for block in universe.blocks if block not in selected and block not in core),
            key=lambda block: (-sum(t not in covered for t in combinations(block, 3)), block),
        )
        selected.add(block)
        added.append(block)
    return sorted(selected), {"removed_core_blocks": removed, "added_noncore_blocks": added,
                             "initial_private_loss_ranking": ranked}


def build_model(universe, core, hint):
    model = cp_model.CpModel()
    xs = [model.NewBoolVar(f"block_{i}") for i in range(len(universe.blocks))]
    holes = [model.NewBoolVar(f"missing_{i}") for i in range(len(universe.triples))]
    model.Add(sum(xs) == 64)
    core_ids = [i for i, block in enumerate(universe.blocks) if block in core]
    model.AddLinearConstraint(sum(xs[i] for i in core_ids), 52, 55)
    for tid, flag in enumerate(holes):
        cover = sum(xs[i] for i in universe.containing[tid])
        model.Add(cover == 0).OnlyEnforceIf(flag)
        model.Add(cover >= 1).OnlyEnforceIf(flag.Not())
    model.Minimize(sum(holes))
    selected = set(hint)
    covered = {t for block in selected for t in combinations(block, 3)}
    for block, variable in zip(universe.blocks, xs):
        model.AddHint(variable, int(block in selected))
    for triple, variable in zip(universe.triples, holes):
        model.AddHint(variable, int(triple not in covered))
    if model.Validate():
        raise ValueError(model.Validate())
    return model


def prepare(args):
    raw, compact = args.raw.resolve(), args.compact.resolve()
    if (compact / "metadata.json").exists():
        raise ValueError("refusing to overwrite a frozen experiment")
    raw.mkdir(parents=True, exist_ok=True)
    compact.mkdir(parents=True, exist_ok=True)
    certificate = json.loads(gzip.decompress(args.core.read_bytes()))
    core = set(map(tuple, certificate["core_blocks"]))
    if len(core) != 60:
        raise ValueError("core must contain 60 distinct blocks")
    universe = Universe.build()
    initial = read_blocks(args.input)
    write_blocks(compact / "input.txt", initial)
    write_blocks(compact / "core.txt", sorted(core))
    input_audit = audit(compact / "input.txt", core)
    if input_audit["holes"] != 3 or input_audit["original_core_overlap"] != 60:
        raise ValueError("expected verified three-hole input retaining the core")
    hint, initialization = make_hint(universe, initial, core)
    write_blocks(compact / "hint.txt", hint)
    hint_audit = audit(compact / "hint.txt", core)
    if hint_audit["original_core_overlap"] != 55:
        raise ValueError("hint does not meet the construction band")
    model = build_model(universe, core, hint)
    model.ExportToFile(str(raw / "model.pbtxt"))
    (raw / "source_snapshot.py").write_bytes(Path(__file__).read_bytes())
    dump(compact / "input-audit.json", input_audit)
    dump(compact / "hint-audit.json", hint_audit)
    dump(compact / "initialization.json", initialization)
    metadata = {
        "version": VERSION, "seed": SEED, "seconds": SECONDS, "workers": 1,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": sha(__file__), "model_sha256": sha(raw / "model.pbtxt"),
        "input_sha256": sha(compact / "input.txt"), "hint_sha256": sha(compact / "hint.txt"),
        "core_sha256": sha(compact / "core.txt"), "certificate_sha256": sha(args.core),
        "solver": "OR-Tools CP-SAT", "solver_version": ortools.__version__,
        "raw_directory": str(raw), "compact_directory": str(compact),
        "variables": {"lex_ordered_blocks": 4368, "exact_missing_indicators": 560},
        "core_overlap_band": [52, 55], "selected_blocks": 64,
        "hint_holes": hint_audit["holes"], "hint_core_overlap": 55,
        "scope": "Constructive original-label core band only; not a complete restriction.",
        "no_additional_assumptions": ["degrees", "regularity", "rotations", "hole ceiling"],
    }
    dump(compact / "metadata.json", metadata)
    print(json.dumps(metadata), flush=True)


class SaveSolutions(cp_model.CpSolverSolutionCallback):
    def __init__(self, model, universe, core, compact):
        super().__init__()
        self.model, self.universe, self.core, self.compact = model, universe, core, compact
        self.saved = []

    def on_solution_callback(self):
        blocks = [block for i, block in enumerate(self.universe.blocks)
                  if self.Value(self.model.GetBoolVarFromProtoIndex(i))]
        holes = int(round(self.ObjectiveValue()))
        path = self.compact / f"solution-{len(self.saved):03d}-h{holes}.txt"
        write_blocks(path, blocks)
        checked = audit(path, self.core)
        if checked["holes"] != holes or not 52 <= checked["original_core_overlap"] <= 55:
            raise ValueError("solver solution disagrees with independent counts")
        dump(path.with_suffix(".audit.json"), checked)
        row = {"path": path.name, "sha256": sha(path), "holes": holes,
               "core_overlap": checked["original_core_overlap"], "seconds": self.WallTime(),
               "forbidden_profile": checked["profile"]["forbidden_five_heavy_profile"]}
        self.saved.append(row)
        print(json.dumps({"event": "solution", **row}), flush=True)
        if checked["package"]["valid"]:
            self.StopSearch()


def run(args):
    compact = args.compact.resolve()
    metadata = json.loads((compact / "metadata.json").read_text())
    raw = Path(metadata["raw_directory"])
    if (sha(__file__) != metadata["source_sha256"]
            or sha(raw / "source_snapshot.py") != metadata["source_sha256"]
            or sha(raw / "model.pbtxt") != metadata["model_sha256"]
            or sha(compact / "hint.txt") != metadata["hint_sha256"]
            or sha(compact / "core.txt") != metadata["core_sha256"]):
        raise ValueError("frozen source, model, or inputs changed")
    gate_sha = sha(args.gate)
    if (raw / "run-started.json").exists():
        raise ValueError("this frozen experiment has already been started")
    model = cp_model.CpModel()
    if not model.Proto().parse_text_format((raw / "model.pbtxt").read_text()):
        raise ValueError("failed to parse frozen model")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = SECONDS
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = SEED
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    callback = SaveSolutions(model, Universe.build(), set(read_blocks(compact / "core.txt")),
                             compact)
    dump(raw / "run-started.json", {"gate": str(args.gate.resolve()), "gate_sha256": gate_sha,
                                   "seed": SEED, "seconds": SECONDS, "workers": 1})
    start = time.monotonic()
    with (raw / "solver.log").open("w") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        status = solver.Solve(model, callback)
    result = {"status": solver.StatusName(status), "solver_seconds": solver.WallTime(),
              "elapsed_seconds": time.monotonic() - start, "saved": callback.saved,
              "objective_bound": solver.BestObjectiveBound(),
              "response_stats": solver.ResponseStats(), "gate_sha256": gate_sha,
              "scope": metadata["scope"], "useful_escape_seed_claim": False}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result["best_holes"] = int(round(solver.ObjectiveValue()))
    dump(compact / "result.json", result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--core", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--compact", type=Path, required=True)
    p = sub.add_parser("run")
    p.add_argument("--compact", type=Path, required=True)
    p.add_argument("--gate", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
    else:
        run(args)


if __name__ == "__main__":
    main()
