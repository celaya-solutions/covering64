# Document:    Audited Inversive Pool Sixty-Second Construction Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      1b73be98832ef1cf1389dc2175fb36c7a85e12b0f87f7e16cb6e738e479e6dc2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Solve the independently audited 288-block pool once; preserve the full response."""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

from covering64.core import canonical_text, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL_SHA = "9459e51fb196332ac5a7e555dfde1a95dc195643ff8365b6655bffbcd153bc5e"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "new immutable run directory required")
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(args.audit.read_text())
    require(gate["passed"] and gate["model_sha256"] == MODEL_SHA, "independent model gate")
    model_path, pool_path = ROOT / manifest["model"], ROOT / manifest["pool"]
    require(sha(model_path) == manifest["model_sha256"] == MODEL_SHA and
            sha(pool_path) == manifest["pool_sha256"], "frozen model and pool")
    require(sha(HERE / "build.py") == manifest["builder_sha256"], "frozen builder")
    pool = json.loads(pool_path.read_text())
    model = cp_model.CpModel()
    require(model.proto.parse_text_format(model_path.read_text()) and not model.validate(),
            "parse and validate")
    require(len(model.proto.variables) == 288 and len(model.proto.constraints) == 561,
            "audited dimensions")
    output = args.output.resolve()
    output.mkdir(parents=True)
    for path in (Path(__file__), HERE / "build.py", HERE / "manifest.json", args.audit,
                 model_path, pool_path, ROOT / "scripts/check_cover.py",
                 ROOT / "src/covering64/core.py"):
        (output / path.name).write_bytes(path.read_bytes())
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 2026100371
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (output / "parameters.pbtxt").write_text(str(solver.parameters))
    metadata = dict(started_utc=datetime.now(UTC).isoformat(), seed=2026100371,
                    requested_seconds=60, workers=1, ortools_version=ortools_version,
                    model_sha256=MODEL_SHA, pool_sha256=sha(pool_path),
                    model_audit_sha256=sha(args.audit), runner_sha256=sha(Path(__file__)),
                    source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                            cwd=ROOT, text=True).strip())
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (output / "solver.log").open("w") as log:
        solver.log_callback = lambda message: log.write(message + "\n")
        began = time.monotonic()
        status = solver.solve(model)
        elapsed = time.monotonic() - began
    response = solver.response_proto
    (output / "response.pbtxt").write_text(str(response))
    result = dict(**metadata, finished_utc=datetime.now(UTC).isoformat(),
                  status=solver.status_name(status), elapsed_seconds=elapsed,
                  solver_wall_seconds=solver.wall_time, conflicts=solver.num_conflicts,
                  branches=solver.num_branches, independently_proved_infeasible=False,
                  witness=None, checks=None)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        values = list(response.solution)
        require(len(values) == 288 and all(v in (0, 1) for v in values), "Boolean solution")
        selected = [entry["block"] for entry, value in zip(pool["pool"], values, strict=True)
                    if value]
        require(len(selected) == 64, "solution cardinality")
        package = verify_cover(selected)
        witness = output / "cover64.txt"
        witness.write_text(canonical_text(selected))
        independent_run = subprocess.run(
            [sys.executable, str(ROOT / "scripts/check_cover.py"), str(witness),
             "--v", "16", "--k", "5", "--t", "3"],
            cwd=ROOT, text=True, capture_output=True, check=False, timeout=20)
        independent = json.loads(independent_run.stdout)
        require(package["valid"] and independent["valid"] and independent_run.returncode == 0
                and package["blocks"] == independent["blocks"] == 64, "candidate verification")
        for name, checked in (("package", package), ("standalone", independent)):
            (output / f"{name}.json").write_text(json.dumps(checked, indent=2) + "\n")
        result["witness"] = dict(path=str(witness.relative_to(ROOT)), sha256=sha(witness))
        result["checks"] = dict(package_valid=True, standalone_valid=True)
    result["artifact_sha256"] = {name: sha(output / name) for name in
                                 ("parameters.pbtxt", "response.pbtxt", "solver.log")}
    result["scope"] = ("This 288-block pool only. UNKNOWN is inconclusive; CP-SAT INFEASIBLE "
                       "is not an independently checked theorem. No global lower bound.")
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
