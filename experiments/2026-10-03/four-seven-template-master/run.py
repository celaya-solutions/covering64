# Document:    Heavy Pattern Master Seed Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Solve the relaxed master once. Its outputs are patterns, never covering witnesses."""

import argparse
import gzip
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path

import ortools
from ortools.linear_solver import linear_solver_pb2, pywraplp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/four-seven-template-master-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    meta = json.loads((RAW / "manifest.json").read_text())
    assert audit["passed"] and audit["model_sha256"] == sha(RAW / "model.pb.gz")
    assert meta["model_sha256"] == audit["model_sha256"]
    assert not (RAW / "settings.json").exists(), "refusing to overwrite pilot"
    proto = linear_solver_pb2.MPModelProto()
    proto.ParseFromString(gzip.decompress((RAW / "model.pb.gz").read_bytes()))
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assert solver is not None and solver.LoadModelFromProtoKeepNames(proto) == ""
    roundtrip = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(roundtrip)
    assert proto == roundtrip and solver.SetNumThreads(1)
    seconds, seed = 60, 2026103901
    parameters = f"randomization/randomseedshift = {seed}\nlimits/solutions = 1\n"
    assert solver.SetSolverSpecificParametersAsString(parameters)
    solver.SetTimeLimit(seconds * 1000)
    settings = {"seed": seed, "seconds": seconds, "workers": 1, "parameters": parameters,
                "solver": solver.SolverVersion(), "ortools": ortools.__version__,
                "model_sha256": sha(RAW / "model.pb.gz"),
                "audit_sha256": sha(args.audit), "source_sha256": sha(Path(__file__)),
                "scope": "Heuristic pattern generation with fractional ordinary blocks."}
    (RAW / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    (RAW / "run.py").write_bytes(Path(__file__).read_bytes())
    solver.EnableOutput()
    status = solver.Solve()
    names = {0: "OPTIMAL", 1: "FEASIBLE", 2: "INFEASIBLE", 3: "UNBOUNDED",
             4: "ABNORMAL", 5: "MODEL_INVALID", 6: "NOT_SOLVED"}
    result = {"status": names[status], "solver_wall_milliseconds": solver.WallTime(),
              "nodes": solver.nodes(), "template_seed": None, "covering_witness": None,
              "scope": settings["scope"], "independently_checked_exclusion": False}
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        values = [v.solution_value() for v in solver.variables()]
        assert all(math.isfinite(v) and -1e-6 <= v <= 1 + 1e-6 for v in values)
        assert all(abs(values[i] - round(values[i])) <= 1e-6 for i in meta["integer_variables"])
        residual = 0.0
        for row in proto.constraint:
            value = math.fsum(a * values[i] for i, a in zip(row.var_index, row.coefficient,
                                                          strict=True))
            residual = max(residual, row.lower_bound - value, value - row.upper_bound)
        assert residual <= 1e-6
        primal = RAW / "primal.json.gz"
        primal.write_bytes(gzip.compress(json.dumps([v.hex() for v in values]).encode(), mtime=0))
        selected = [i for i in meta["integer_variables"] if round(values[i]) == 1]
        blocks = list(combinations(range(1, 17), 5))
        assert len(selected) == 28
        catalog_path = ROOT / ("experiments/scratch/four-seven-template-hull-refresh-106-"
                               "20261003/matching/group-catalogs.json.gz")
        catalogs = json.loads(gzip.decompress(catalog_path.read_bytes()))
        patterns = []
        for group in range(4):
            anchor = set(range(4 * group + 1, 4 * group + 4))
            ids = [i for i in selected if anchor <= set(blocks[i])]
            edges = sorted([sorted(set(blocks[i]) - anchor) for i in ids])
            assert len(ids) == 7 and edges in catalogs[group]["templates"]
            patterns.append({"group": group, "block_ids": ids, "edges": edges,
                             "catalog_index": catalogs[group]["templates"].index(edges)})
        result["template_seed"] = {"selected_block_ids": selected, "patterns": patterns,
                                   "primal_sha256": sha(primal),
                                   "max_float_row_residual": residual,
                                   "catalog_sha256": sha(catalog_path)}
    for folder in (HERE, RAW):
        (folder / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
