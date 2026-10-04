# Document:    Four Case First-Link Integer Search Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Load the frozen audited lifted base and append exactly seven fixed-block rows."""

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import verify_cover, write_blocks

ROOT = Path(__file__).resolve().parents[3]
SEEDS = {"cycle-069": 2026103101, "cycle-111": 2026103102,
         "matching-029": 2026103103, "matching-030": 2026103104}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("primal_run", type=Path)
    parser.add_argument("representative", choices=tuple(SEEDS))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output must be new")
    args.output.mkdir(parents=True)
    results_path = args.primal_run / "results.json.gz"
    results = json.loads(gzip.decompress(results_path.read_bytes()))
    matches = [item for item in results if item["id"] == args.representative]
    require(len(matches) == 1, "representative must be unique")
    entry = matches[0]
    require(entry["lp"]["numerically_valid"] and len(set(entry["fixed_ids"])) == 7,
            "invalid LP entry or fixed link")
    case = entry["case"]
    base_path = args.primal_run / f"input-{case}-base.pbtxt"
    source_metadata = json.loads((args.primal_run / "metadata.json").read_text())
    require(digest(base_path) == source_metadata["inputs"][f"{case}-base.pbtxt"],
            "base model hash mismatch")
    shutil.copyfile(base_path, args.output / "base.pbtxt")
    sources = {}
    for path in (Path(__file__), ROOT / "scripts/check_cover.py", ROOT / "src/covering64/core.py"):
        shutil.copyfile(path, args.output / path.name)
        sources[path.name] = digest(path)
    model = cp_model.CpModel()
    require(model.proto.parse_text_format(base_path.read_text()), "base model parse failure")
    require(len(model.proto.variables) == 4768 and len(model.proto.constraints) == 4270,
            "unexpected lifted base size")
    require(model.validate() == "", "base model invalid")
    blocks = list(combinations(range(1, 17), 5))
    xs = [model.get_bool_var_from_proto_index(i) for i in range(4368)]
    require(all(model.proto.variables[i].name == f"block_{i}" for i in range(4368)),
            "block order mismatch")
    require(all(blocks[i][:3] == (1, 2, 3) for i in entry["fixed_ids"]), "not first-heavy link")
    for i in entry["fixed_ids"]:
        model.add(xs[i] == 1)
    require(model.validate() == "", "fixed-link model invalid")
    model_path = args.output / "model.pbtxt"
    model.export_to_file(str(model_path))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = SEEDS[args.representative]
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (args.output / "parameters.txt").write_text(str(solver.parameters))
    metadata = {
        "id": args.representative, "case": case, "fixed_ids": entry["fixed_ids"],
        "fixed_blocks": [blocks[i] for i in entry["fixed_ids"]],
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources, "solver_version": ortools.__version__, "command": sys.argv,
        "base_sha256": digest(base_path), "model_sha256": digest(model_path),
        "primal_results_sha256": digest(results_path), "primal_run": str(args.primal_run),
        "seconds": 60, "workers": 2, "seed": SEEDS[args.representative],
        "variables": len(model.proto.variables), "rows": len(model.proto.constraints),
        "hints_added": False, "new_constraints": "Exactly seven block_i ==1 rows",
        "scope": "One fixed first-heavy-link case of the audited lifted normalized regular "
        "four-sevenfold64-block branch. No new feature cuts or fixed double-triple pattern. "
        "UNKNOWN is inconclusive; INFEASIBLE alone is not an independently checked theorem.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        status = solver.solve(model)
    result = {"id": args.representative, "status": solver.status_name(status),
              "seconds": solver.wall_time, "response_stats": solver.response_stats(),
              "cover_found": False}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        candidate = [blocks[i] for i, x in enumerate(xs) if solver.value(x)]
        path = args.output / "candidate.txt"
        write_blocks(path, candidate)
        package = verify_cover(candidate)
        run = subprocess.run([sys.executable, str(args.output / "check_cover.py"), str(path),
                              "--expected-blocks", "64"], capture_output=True, text=True)
        require(run.returncode == 0, "standalone verifier rejected extracted cover")
        standalone = json.loads(run.stdout)
        require(len(candidate) == 64 and package["valid"] and standalone["valid"], "invalid cover")
        require(package["canonical_sha256"] == standalone["canonical_sha256"], "hash mismatch")
        result.update(cover_found=True, package=package, standalone=standalone)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "response_stats"}),
          flush=True)


if __name__ == "__main__":
    main()
