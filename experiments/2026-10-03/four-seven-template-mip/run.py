# Document:    Mixed Integer Matching Template Hull Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      665dc2a4cd3d580a1c2e6b25708c9d2ed13b38330616356138244c6db9a80976
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Prepare or solve the audited hull with continuous template selectors."""

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import ortools
from ortools.linear_solver import linear_solver_pb2, pywraplp

from covering64.core import Universe, verify_cover, write_blocks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HULL = ROOT / "experiments/scratch/four-seven-template-hull-refresh-106-20261003/matching"
AUDIT = HERE.parent / "four-seven-template-hull-refresh/independent-audit.json"
MATRIX_SHA256 = "ee2072837ae28bcce599c60975995a5c88b3fc3eb635352abc089b3eb6d78bab"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def prepare(output):
    require(not output.exists(), "output directory must be new")
    audit = read(AUDIT)
    require(audit["passed"], "passing independent matrix audit required")
    entry = next(row for row in audit["cases"] if row["case"] == "matching")
    require(sha(HULL / "extended-rows.json.gz") == entry["matrix_sha256"] == MATRIX_SHA256,
            "frozen audited matrix required")
    matrix = read(HULL / "extended-rows.json.gz")
    require(matrix["width"] == 55528 and len(matrix["rows"]) == 4550, "matrix dimensions")
    solver = pywraplp.Solver.CreateSolver("SCIP")
    require(solver is not None, "SCIP unavailable")
    variables = [solver.IntVar(0, 1, f"x{i}") if i < 4768 else
                 solver.NumVar(0, 1, f"x{i}") for i in range(matrix["width"])]
    for index, (ids, values, lower, upper) in enumerate(matrix["rows"]):
        row = solver.RowConstraint(-solver.infinity() if lower is None else lower,
                                   solver.infinity() if upper is None else upper, f"row_{index}")
        for column, value in zip(ids, values, strict=True):
            row.SetCoefficient(variables[column], value)
    solver.Objective().SetMinimization()
    proto = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(proto)
    output.mkdir(parents=True)
    raw = proto.SerializeToString(deterministic=True)
    (output / "model.pb.gz").write_bytes(gzip.compress(raw, mtime=0))
    (output / "run.py").write_bytes(Path(__file__).read_bytes())
    (output / "matrix.json.gz").write_bytes((HULL / "extended-rows.json.gz").read_bytes())
    metadata = {"source_sha256": sha(Path(__file__)), "matrix_sha256": MATRIX_SHA256,
                "model_sha256": sha(output / "model.pb.gz"),
                "independent_matrix_audit_sha256": sha(AUDIT),
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "ortools_version": ortools.__version__, "solver": solver.SolverVersion(),
                "variables": 55528, "boolean_variables": 4768, "continuous_selectors": 50760,
                "rows": 4550, "objective": "constant zero feasibility",
                "scope": "Whole normalized matching four-sevenfold branch; no fixed first link."}
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata), flush=True)


def solve(folder, audit_path, seconds, seed):
    require(math.isfinite(seconds) and seconds > 0 and 0 <= seed < 2147483647, "budget or seed")
    metadata = read(folder / "metadata.json")
    require(sha(folder / "run.py") == metadata["source_sha256"] == sha(Path(__file__)),
            "source snapshot changed")
    require(sha(folder / "model.pb.gz") == metadata["model_sha256"], "model snapshot changed")
    audit = read(audit_path)
    require(audit["passed"] and audit["model_sha256"] == metadata["model_sha256"] and
            audit["matrix_sha256"] == MATRIX_SHA256, "independent MIP model audit required")
    require(not (folder / "result.json").exists() and not (folder / "solve-metadata.json").exists(),
            "refusing to overwrite a prior run")
    proto = linear_solver_pb2.MPModelProto()
    proto.ParseFromString(gzip.decompress((folder / "model.pb.gz").read_bytes()))
    solver = pywraplp.Solver.CreateSolver("SCIP")
    error = solver.LoadModelFromProtoKeepNames(proto)
    require(error == "", "model load failed: " + error)
    reconstructed = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(reconstructed)
    require(reconstructed == proto, "SCIP import changed model")
    require(solver.SetNumThreads(1), "single-thread setting rejected")
    solver.SetTimeLimit(int(seconds * 1000))
    parameters = f"randomization/randomseedshift = {seed}\nlimits/solutions = 1\n"
    require(solver.SetSolverSpecificParametersAsString(parameters), "SCIP parameters rejected")
    settings = {"seconds": seconds, "seed": seed, "threads": 1, "parameters": parameters,
                "solver": solver.SolverVersion(), "model_sha256": metadata["model_sha256"],
                "independent_model_audit_sha256": sha(audit_path)}
    (folder / "solve-metadata.json").write_text(json.dumps(settings, indent=2) + "\n")
    solver.EnableOutput()
    status = solver.Solve()
    names = {0: "OPTIMAL", 1: "FEASIBLE", 2: "INFEASIBLE", 3: "UNBOUNDED",
             4: "ABNORMAL", 5: "MODEL_INVALID", 6: "NOT_SOLVED"}
    result = {"status": names.get(status, str(status)), "wall_milliseconds": solver.WallTime(),
              "nodes": solver.nodes(), "candidate": None, "independently_proved_infeasible": False,
              "scope": metadata["scope"]}
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        variables = solver.variables()
        blocks = [block for block, variable in zip(Universe.build().blocks, variables[:4368],
                                                   strict=True) if variable.solution_value() > 0.5]
        path = folder / "candidate.txt"
        write_blocks(path, blocks)
        package = verify_cover(blocks)
        independent = subprocess.run([sys.executable, str(ROOT / "scripts/check_cover.py"),
                                      str(path), "--expected-blocks", "64"],
                                     capture_output=True, text=True, cwd=ROOT, check=False)
        (folder / "independent-check.stdout").write_text(independent.stdout)
        (folder / "independent-check.stderr").write_text(independent.stderr)
        result["candidate"] = {"sha256": sha(path), "blocks": len(blocks), "package": package,
                               "independent_returncode": independent.returncode}
        require(len(blocks) == 64 and package["valid"] and independent.returncode == 0,
                "numerical candidate failed required exact covering checks")
    (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "solve"))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--seconds", type=float, default=300)
    parser.add_argument("--seed", type=int, default=2026100301)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.folder)
    else:
        require(args.audit is not None, "independent model audit is required")
        solve(args.folder, args.audit, args.seconds, args.seed)


if __name__ == "__main__":
    main()
