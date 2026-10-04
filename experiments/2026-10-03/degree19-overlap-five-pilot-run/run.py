# Document:    Bounded Four Model Overlap Five Pilot Campaign
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Freeze audited models, run bounded LP stages, then explicitly selected CP pilots."""

import argparse
import concurrent.futures
import gzip
import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / "experiments/scratch/degree19-overlap-five-pilots-v1.0.1"
BLOCKS = list(combinations(range(1, 17), 5))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def write_gzip(path, value):
    path.write_bytes(gzip.compress((json.dumps(value) + "\n").encode(), mtime=0))


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def inspect_candidate(output, folder, selected, rows, origin):
    selected = sorted(selected)
    blocks = [BLOCKS[i] for i in selected]
    path = folder / f"{origin}-candidate.txt"
    path.write_text("".join(" ".join(map(str, block)) + "\n" for block in blocks))
    core = load_module(output / "core.py", f"frozen_core_{origin.replace('-', '_')}")
    package = core.verify_cover(blocks)
    command = [sys.executable, str(output / "check_cover.py"), str(path), "--expected-blocks", "64"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    standalone = json.loads(completed.stdout)
    values = [int(i in set(selected)) for i in range(4368)]
    valid_rows = all((lower is None or sum(values[i] * c for i, c in zip(ids, coeffs)) >= lower)
                     and (upper is None or sum(values[i] * c for i, c in zip(ids, coeffs)) <= upper)
                     for ids, coeffs, lower, upper in rows)
    verified = len(selected) == len(set(selected)) == 64 and valid_rows and package["valid"]
    verified = verified and standalone["valid"] and completed.returncode == 0
    verified = verified and package["canonical_sha256"] == standalone["canonical_sha256"]
    result = {"verified_cover": bool(verified), "exact_model_rows_satisfied": valid_rows,
              "selected_ids": selected, "package": package, "standalone": standalone,
              "standalone_command": command, "standalone_returncode": completed.returncode,
              "stdout": completed.stdout, "stderr": completed.stderr,
              "candidate_sha256": sha(path)}
    write(folder / f"{origin}-verification.json", result)
    return result


def lp_stage(rows, width, seconds, phase_one):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    limit_ms = max(1, int(seconds * 1000))
    solver.set_time_limit(limit_ms)
    variables = [solver.NumVar(0, 1, f"block_{i}") for i in range(width)]
    constraints = []
    for number, (ids, coeffs, lower, upper) in enumerate(rows):
        row = solver.Constraint(-solver.infinity() if lower is None else lower,
                                solver.infinity() if upper is None else upper)
        for i, coefficient in zip(ids, coeffs):
            row.SetCoefficient(variables[i], coefficient)
        if phase_one:
            for label, bound, sign in (("lo", lower, 1), ("hi", upper, -1)):
                if bound is not None:
                    slack = solver.NumVar(0, solver.infinity(), f"{label}_{number}")
                    row.SetCoefficient(slack, sign)
                    solver.Objective().SetCoefficient(slack, 1)
        constraints.append(row)
    solver.Objective().SetMinimization()
    start = time.monotonic()
    status = solver.Solve()
    elapsed = time.monotonic() - start
    labels = ("OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNBOUNDED", "ABNORMAL",
              "MODEL_INVALID", "NOT_SOLVED")
    result = {"status": status, "status_name": labels[status], "phase_one": phase_one,
              "requested_limit_ms": limit_ms, "solve_seconds": elapsed,
              "solver_wall_ms": solver.wall_time(), "solver_version": solver.SolverVersion()}
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        result.update(objective=solver.Objective().Value(),
                      values=[variable.solution_value() for variable in variables],
                      weights=[row.dual_value() for row in constraints])
    return result


def certificate(rows, width, weights):
    denominator = 1000000
    assert len(weights) == len(rows) and all(math.isfinite(weight) for weight in weights)
    integers = [round(weight * denominator) for weight in weights]
    columns, rhs = [0] * width, 0
    for (ids, coeffs, lower, upper), weight in zip(rows, integers):
        if weight:
            bound = lower if weight > 0 else upper
            assert bound is not None
            rhs += weight * bound
            for i, coefficient in zip(ids, coeffs):
                columns[i] += weight * coefficient
    box_max = sum(max(0, value) for value in columns)
    gap = Fraction(rhs - box_max, denominator)
    return {"denominator": denominator, "weights": [[i, weight] for i, weight in enumerate(integers)
                                                     if weight], "rhs_numerator": rhs,
            "box_max_numerator": box_max, "gap": [gap.numerator, gap.denominator],
            "checked_columns": width, "proves_infeasible": gap > 0}


def prepare_and_lp(output):
    assert not output.exists(), "output must be new"
    output.mkdir(parents=True)
    audit_path = ROOT / "experiments/2026-10-03/degree19-overlap-five-independent/pilot-audit.json"
    audit = json.loads(audit_path.read_text())
    assert audit["passed"] and audit["manifest_sha256"] == sha(ORIGINAL / "manifest.json")
    source_paths = {
        "run.py": Path(__file__), "check_cover.py": ROOT / "scripts/check_cover.py",
        "core.py": ROOT / "src/covering64/core.py",
        "raw_certificate_checker.py": ROOT /
        "experiments/2026-10-03/four-seven-link-lp-independent/check.py",
        "pilot_model_checker.py": audit_path.with_name("check_pilots.py"),
        "pilot-audit.json": audit_path,
        "input-manifest.json": ORIGINAL / "manifest.json",
        "factorization.json.gz": ORIGINAL / "factorization.json.gz",
    }
    for name, path in source_paths.items():
        shutil.copyfile(path, output / name)
    records = []
    for number, record in enumerate(audit["models"]):
        name = record["id"]
        folder = output / name
        folder.mkdir()
        for filename, field in (("model.pbtxt", "model_sha256"),
                                ("lp-rows.json.gz", "lp_rows_sha256")):
            original = ORIGINAL / name / filename
            assert sha(original) == record[field]
            shutil.copyfile(original, folder / filename)
        records.append({"id": name, "seed": 2026103401 + number,
                        "model_sha256": sha(folder / "model.pbtxt"),
                        "lp_rows_sha256": sha(folder / "lp-rows.json.gz")})
    metadata = {"sources": {name: sha(output / name) for name in source_paths}, "models": records,
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "ortools_version": ortools.__version__, "python_version": sys.version,
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "lp_solver_seconds_total_per_model": 15, "cp_seconds_per_model": 300,
                "cp_workers": 2, "maximum_simultaneous_cp_jobs": 2,
                "scope": "Four explicit ordered 33-block unions only; not all 4578210 classes."}
    write(output / "metadata.json", metadata)
    results = []
    for record in records:
        folder = output / record["id"]
        data = json.loads(gzip.decompress((folder / "lp-rows.json.gz").read_bytes()))
        rows, width = data["rows"], data["width"]
        feasibility = lp_stage(rows, width, 15.0, False)
        write_gzip(folder / "feasibility.json.gz", feasibility)
        result = {"id": record["id"], "feasibility_status": feasibility["status_name"],
                  "solve_seconds_total": feasibility["solve_seconds"],
                  "certificate_pending_independent_check": False, "verified_cover": False}
        if "values" in feasibility:
            values = feasibility["values"]
            result["fractional_variables"] = sum(1e-7 < value < 1 - 1e-7 for value in values)
            if all(min(abs(value), abs(value - 1)) <= 1e-7 for value in values):
                checked = inspect_candidate(output, folder,
                                            [i for i, value in enumerate(values) if value > 0.5],
                                            rows, "lp")
                result["verified_cover"] = checked["verified_cover"]
        remaining = 15.0 - feasibility["solve_seconds"]
        if feasibility["status"] == pywraplp.Solver.INFEASIBLE and remaining >= 0.001:
            phase = lp_stage(rows, width, remaining, True)
            write_gzip(folder / "phase-one.json.gz", phase)
            result["phase_one_status"] = phase["status_name"]
            result["solve_seconds_total"] += phase["solve_seconds"]
            if "weights" in phase:
                exact = certificate(rows, width, phase["weights"])
                write(folder / "certificate.json", exact)
                result["certificate_pending_independent_check"] = exact["proves_infeasible"]
                result["certificate_gap"] = exact["gap"]
        write(folder / "lp-summary.json", result)
        results.append(result)
        write(output / "lp-results.json", results)
        print(json.dumps(result), flush=True)


def cp_case(output, name):
    metadata = json.loads((output / "metadata.json").read_text())
    record = next(record for record in metadata["models"] if record["id"] == name)
    folder = output / name
    assert sha(folder / "model.pbtxt") == record["model_sha256"]
    assert not (folder / "cp-summary.json").exists(), "CP result already exists"
    model = cp_model.CpModel()
    assert model.proto.parse_text_format((folder / "model.pbtxt").read_text())
    assert model.validate() == ""
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers = 2
    solver.parameters.random_seed = record["seed"]
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (folder / "cp-parameters.pbtxt").write_text(str(solver.parameters))
    with (folder / "cp-search.log").open("w") as log:
        def log_line(line):
            log.write(line + "\n")
            log.flush()
        solver.log_callback = log_line
        status = solver.solve(model)
    (folder / "cp-response.pbtxt").write_text(str(solver.response_proto))
    (folder / "cp-statistics.txt").write_text(solver.response_stats())
    result = {"id": name, "status": solver.status_name(status), "seed": record["seed"],
              "wall_seconds": solver.wall_time, "branches": solver.num_branches,
              "conflicts": solver.num_conflicts, "verified_cover": False,
              "model_sha256": sha(folder / "model.pbtxt"),
              "parameters_sha256": sha(folder / "cp-parameters.pbtxt"),
              "response_sha256": sha(folder / "cp-response.pbtxt")}
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        selected = [i for i in range(4368) if solver.value(model.get_bool_var_from_proto_index(i))]
        rows = json.loads(gzip.decompress((folder / "lp-rows.json.gz").read_bytes()))["rows"]
        checked = inspect_candidate(output, folder, selected, rows, "cp")
        result["verified_cover"] = checked["verified_cover"]
        assert result["verified_cover"], "integer solver candidate failed verification"
    write(folder / "cp-summary.json", result)
    print(json.dumps(result), flush=True)


def cp_campaign(output, names):
    metadata = json.loads((output / "metadata.json").read_text())
    assert len(names) == len(set(names)) and set(names) <= {r["id"] for r in metadata["models"]}
    assert sha(output / "run.py") == metadata["sources"]["run.py"]
    write(output / "cp-selection.json", {"cases": names, "seconds": 300, "workers": 2,
                                         "maximum_simultaneous_jobs": 2})

    def run(name):
        command = [sys.executable, str(output / "run.py"), "cp-case", str(output), "--case", name]
        with (output / name / "cp-process.log").open("w") as log:
            completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=False)
        result = {"id": name, "command": command, "returncode": completed.returncode}
        write(output / name / "cp-process.json", result)
        print(json.dumps(result), flush=True)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, names))
    write(output / "cp-process-results.json", results)
    assert all(result["returncode"] == 0 for result in results), "CP process failed; inspect logs"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare-lp", "cp-case", "cp"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--ids", nargs="+")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.mode == "prepare-lp":
        prepare_and_lp(output)
    elif args.mode == "cp-case":
        cp_case(output, args.case)
    else:
        assert args.ids, "explicit survivor IDs required after independent certificate review"
        cp_campaign(output, args.ids)


if __name__ == "__main__":
    main()
