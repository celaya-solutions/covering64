#!/usr/bin/env python3
# Document:    Exact Search of Certified Residual Kernels
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Batch exact repairs using independently checked rational dual reductions."""

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover, write_blocks

SPEC = importlib.util.spec_from_file_location(
    "kernel_lns", Path(__file__).with_name("lns_search.py"))
LNS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LNS)


def solve_kernel(universe, retained, certificate, target, seconds, seed=0, output=None):
    retained = list(retained)
    if (len(set(retained)) != len(retained)
            or any(type(i) is not int or not 0 <= i < len(universe.blocks) for i in retained)):
        raise ValueError("invalid retained block IDs")
    if type(target) is not int or target < len(retained):
        raise ValueError("target is below retained count")
    if isinstance(seconds, bool) or not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be finite and positive")
    covered = {t for i in retained for t in universe.coverage[i]}
    missing = sorted(set(range(len(universe.triples))) - covered)
    candidates = sorted({i for t in missing for i in universe.containing[t]} - set(retained))
    budget = target - len(retained)
    bound = Fraction(*certificate["lower_bound"])
    # Validate every rational capacity even when the bound itself excludes the budget.
    allowed, upper, reduction = LNS.dual_restrictions(
        universe, certificate, max(budget, math.ceil(bound)), candidates, missing)
    result = {"retained_ids": sorted(retained), "replacement_limit": budget,
              "certificate": certificate, "candidate_count": len(allowed),
              "seed": seed, "seconds": seconds, "witness": None,
              "scope": "only this retained-block neighborhood; no global infeasibility claim"}
    if bound > budget:
        result.update(status="LP_CERTIFIED_INFEASIBLE", solver_seconds=0.0)
        return result
    result["reduction"] = reduction
    model = cp_model.CpModel()
    variables = {i: model.NewBoolVar(f"block_{i}") for i in allowed}
    for triple in missing:
        terms = [variables[i] for i in universe.containing[triple] if i in variables]
        model.Add(sum(terms) >= 1)
        if triple in upper:
            model.Add(sum(terms) <= upper[triple])
    model.Add(sum(variables.values()) <= budget)
    if output:
        output.mkdir(parents=True, exist_ok=True)
        model.ExportToFile(str(output / "model.pbtxt"))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed % 2_147_483_647
    solver.parameters.log_search_progress = bool(output)
    solver.parameters.log_to_stdout = False
    if output:
        with (output / "solver.log").open("w") as stream:
            solver.log_callback = lambda text: (stream.write(text + "\n"), stream.flush())
            status = solver.Solve(model)
    else:
        status = solver.Solve(model)
    result.update(status=solver.StatusName(status), solver_seconds=solver.WallTime(),
                  response_stats=solver.ResponseStats())
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        selected = sorted(set(retained) | {i for i in allowed if solver.Value(variables[i])})
        witness = [universe.blocks[i] for i in selected]
        checked = verify_cover(witness, universe.v, universe.k, universe.t)
        if not checked["valid"] or len(witness) > target:
            raise RuntimeError("kernel candidate failed package verification")
        result.update(witness=witness, verification=checked)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds-per-case", type=float, default=30)
    parser.add_argument("--seed", type=int, default=2026100800)
    args = parser.parse_args(argv)
    raw = args.candidates.read_bytes()
    data = json.loads(gzip.decompress(raw) if args.candidates.suffix == ".gz" else raw)
    args.output.mkdir(parents=True, exist_ok=True)
    for source in [Path(__file__), Path(__file__).with_name("lns_search.py")]:
        (args.output / f"source-{source.name}").write_bytes(source.read_bytes())
    metadata = {
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "lns_sha256": hashlib.sha256(
            Path(__file__).with_name("lns_search.py").read_bytes()).hexdigest(),
        "input_sha256": hashlib.sha256(raw).hexdigest(), "solver_version": ortools.__version__,
        "workers": 1, "seed": args.seed, "seconds_per_case": args.seconds_per_case,
        "cases": len(data["candidates"]), "scope": "only the supplied retained-block neighborhoods",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    universe = Universe.build()
    results = []
    for number, case in enumerate(data["candidates"]):
        retained = case["retained_block_ids"]
        explicit = list(map(tuple, case["retained_core_blocks"]))
        if [universe.blocks[i] for i in sorted(retained)] != explicit:
            raise ValueError("retained blocks do not agree with their lexicographic IDs")
        certificate = {"weights": [[t, n, case["denominator"]] for t, n in case["weights"]],
                       "lower_bound": case.get("exact_lower_bound", case.get("lower_bound"))}
        folder = args.output / f"case-{number:03}"
        result = solve_kernel(universe, retained, certificate, 64, args.seconds_per_case,
                              args.seed + number, folder)
        if ("allowed_block_ids" in case and "reduction" in result
                and result["reduction"]["candidate_ids"] != case["allowed_block_ids"]):
            raise ValueError("independent candidate pruning disagrees with source artifact")
        result["removed_core_positions"] = case["removed"]
        if result["witness"]:
            path = folder / "cover.txt"
            write_blocks(path, result["witness"])
            run = subprocess.run([sys.executable, "scripts/check_cover.py", str(path)],
                                 capture_output=True, text=True, check=True)
            result["standalone_verification"] = json.loads(run.stdout)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append({"case": number, "status": result["status"],
                        "candidate_count": result["candidate_count"],
                        "solver_seconds": result["solver_seconds"]})
        print(json.dumps(results[-1]), flush=True)
        (args.output / "summary.json").write_text(json.dumps(results, indent=2) + "\n")
        if result["witness"]:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
