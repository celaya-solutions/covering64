# Document:    Clebsch Recipe Fractional Feasibility Prescreen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      376768375bf0c6eaff3b3c3b51026cec227396f368e58b654b356dd93888fec9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""A bounded fractional diagnostic; infeasible statuses are not proof certificates."""

import hashlib
import importlib.util
import itertools
import json
import platform
import subprocess
import time
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SEEDS = [0, 1, 9, 40, 19, 8, 4, 18, 16, 12, 3, 10, 11, 26, 60, 25]
PROFILE_SOURCE = ROOT / "scripts/independent_clebsch_profiles.py"
ORBIT_SOURCE = ROOT / "experiments/2026-10-03/independent-geometry/profile-orbits/certificate.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    out = HERE / "output"
    out.mkdir(exist_ok=False)
    spec = importlib.util.spec_from_file_location("clebsch_profiles", PROFILE_SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    triple_index = {t: i for i, t in enumerate(triples)}
    containing = [[] for _ in triples]
    for i, block in enumerate(blocks):
        for triple in itertools.combinations(block, 3):
            containing[triple_index[triple]].append(i)
    assert len(blocks) == 4368 and len(triples) == 560
    assert all(len(row) == 78 for row in containing)
    report = {
        "scope": "Fractional x in [0,1] with exact recipe triple demands. No binary search.",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(Path(__file__)),
        "profile_source_sha256": sha(PROFILE_SOURCE),
        "orbit_certificate_sha256": sha(ORBIT_SOURCE),
        "python": platform.python_version(),
        "ortools": ortools.__version__,
        "profile_seeds": SEEDS,
        "per_profile_limit_ms": 5000,
        "rows": [],
    }
    statuses = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE_UNCERTIFIED",
        pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
        pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
    }
    for seed in SEEDS:
        profile = {tuple(t) for t in module.make_profile(seed)}
        assert len(profile) == 80 and profile <= set(triples)
        demands = [1 + int(t in profile) for t in triples]
        solver = pywraplp.Solver.CreateSolver("GLOP")
        assert solver is not None
        solver.SetTimeLimit(5000)
        variables = [solver.NumVar(0, 1, f"block_{i}") for i in range(4368)]
        for i, demand in enumerate(demands):
            row = solver.Constraint(demand, demand, f"triple_{i}")
            for block_id in containing[i]:
                row.SetCoefficient(variables[block_id], 1)
        start = time.monotonic()
        status = solver.Solve()
        item = {
            "profile_seed": seed,
            "status": statuses.get(status, str(status)),
            "elapsed_seconds": time.monotonic() - start,
            "solver_version": solver.SolverVersion(),
            "profile": sorted(profile),
            "columns": solver.NumVariables(),
            "rows": solver.NumConstraints(),
        }
        if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
            values = [v.solution_value() for v in variables]
            item.update({
                "max_row_residual": max(
                    abs(sum(values[j] for j in row) - demand)
                    for row, demand in zip(containing, demands, strict=True)
                ),
                "max_bound_violation": max(max(-x, x - 1, 0) for x in values),
                "sum_values": sum(values),
                "fractional_columns": sum(abs(x - round(x)) > 1e-7 for x in values),
                "positive_columns": sum(x > 1e-8 for x in values),
            })
            vector = out / f"profile-{seed}-vector.json"
            vector.write_text(json.dumps(values) + "\n")
            item["vector_sha256"] = sha(vector)
        report["rows"].append(item)
        (out / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        summary = {k: item[k] for k in ("profile_seed", "status", "elapsed_seconds")}
        print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
