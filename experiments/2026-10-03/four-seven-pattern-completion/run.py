# Document:    Four Sevenfold Double Pattern Block Completion
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Fix all400 double flags to one independently counted pattern; assess completion."""

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

from covering64.core import verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[3]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("cycle", "matching"))
    parser.add_argument("pattern", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lp-seconds", type=float, default=10)
    parser.add_argument("--cp-seconds", type=float, default=120)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    require(all(math.isfinite(t) and t > 0 for t in (args.lp_seconds, args.cp_seconds)),
            "invalid time budget")
    require(args.cp_seconds <= 120 and 1 <= args.workers <= 4, "budget out of range")
    require(not args.output.exists(), "output directory must be new")
    args.output.mkdir(parents=True)
    sources = {}
    for path in (Path(__file__), ROOT / "scripts/four_seven_search.py",
                 ROOT / "scripts/four_seven_double_cuts.py", ROOT / "scripts/four_seven_link_lp.py",
                 ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py"):
        raw = path.read_bytes()
        (args.output / path.name).write_bytes(raw)
        sources[path.name] = hashlib.sha256(raw).hexdigest()
    sys.path.insert(0, str(args.output.resolve()))
    from four_seven_double_cuts import add_double_triple_cuts
    from four_seven_link_lp import exact_certificate, linear_rows, solve_lp
    from four_seven_search import build_model

    raw = args.pattern.read_bytes()
    (args.output / "pattern.txt").write_bytes(raw)
    pattern = [tuple(map(int, line.split())) for line in raw.decode().splitlines() if line.strip()]
    require(len(pattern) == 44 and len(set(pattern)) == 44, "need44 distinct triples")
    require(all(len(t) == 3 and tuple(sorted(set(t))) == t
                and all(1 <= p <= 16 for p in t) for t in pattern), "malformed pattern")
    universe, model, xs, _ = build_model(args.case)
    flags, application = add_double_triple_cuts(universe, model, xs, args.case)
    triple_ranks = {triple: i for i, triple in enumerate(universe.triples)}
    selected = {triple_ranks[t] for t in pattern}
    require(selected.issubset(flags), "pattern has fixed or ineligible triples")
    first_fixed_row = len(model.proto.constraints)
    for tid, flag in flags.items():
        model.add(flag == int(tid in selected))
    require(model.validate() == "", "invalid model")
    require(all(row.has_linear() for row in model.proto.constraints), "nonlinear row")
    rows, width = linear_rows(model)
    model_path = args.output / "model.pbtxt"
    model.export_to_file(str(model_path))
    (args.output / "rows.json.gz").write_bytes(gzip.compress(
        json.dumps({"rows": rows, "width": width}).encode(), mtime=0))
    metadata = {
        "case": args.case, "pattern_sha256": hashlib.sha256(raw).hexdigest(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources, "solver_version": ortools.__version__, "command": sys.argv,
        "lp_seconds_per_stage": args.lp_seconds, "cp_seconds": args.cp_seconds,
        "workers": args.workers, "seed": args.seed, "variables": width, "rows": len(rows),
        "double_application": application, "first_fixed_row": first_fixed_row,
        "fixed_flags": [[tid, flags[tid].index, int(tid in selected)] for tid in flags],
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "scope": "Only full regular64-block four-sevenfold covers in this normalized case "
        "with all400 double flags fixed to this exact44-triple pattern.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    feasible = solve_lp(rows, width, args.lp_seconds)
    result = {"case": args.case, "lp": {k: v for k, v in feasible.items() if k != "weights"},
              "cp": None, "certificate": None, "cover_found": False}
    if feasible["status"] == pywraplp.Solver.INFEASIBLE:
        phase = solve_lp(rows, width, args.lp_seconds, phase_one=True)
        result["phase_one"] = {k: v for k, v in phase.items() if k != "weights"}
        if "weights" in phase:
            result["certificate"] = exact_certificate(rows, width, phase["weights"])
    elif feasible["status"] in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = args.cp_seconds
        solver.parameters.num_search_workers = args.workers
        solver.parameters.random_seed = args.seed
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = False
        (args.output / "parameters.txt").write_text(str(solver.parameters))
        with (args.output / "solver.log").open("w") as log:
            solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
            status = solver.solve(model)
        result["cp"] = {"status": solver.status_name(status), "seconds": solver.wall_time,
                        "response_stats": solver.response_stats()}
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            blocks = [universe.blocks[i] for i, x in enumerate(xs) if solver.value(x)]
            path = args.output / "candidate.txt"
            write_blocks(path, blocks)
            package = verify_cover(blocks)
            standalone = subprocess.run(
                [sys.executable, str(args.output / "check_cover.py"), str(path),
                 "--expected-blocks", "64"], capture_output=True, text=True, check=True,
            )
            checked = json.loads(standalone.stdout)
            require(len(blocks) == 64 and package["valid"] and checked["valid"], "invalid cover")
            require(package["canonical_sha256"] == checked["canonical_sha256"], "hash mismatch")
            result.update(cover_found=True, package=package, standalone=checked)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"case": args.case, "lp": result["lp"], "cp": result["cp"],
                      "certificate": None if result["certificate"] is None else {
                          key: result["certificate"][key] for key in ("gap", "proves_infeasible")},
                      "cover_found": result["cover_found"]}), flush=True)


if __name__ == "__main__":
    main()
