# Document:    Affine Circle Incidence Relaxation Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      710fbd94dd91dc06e18f3c1b5aa74746b10b8d4630fafce358cbc0213e3639e2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run the approved60-second necessary-relaxation pilot after an independent gate."""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

from covering64.core import verify_cover, write_blocks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-circle-incidence-relaxation-20261003"
PILOT = RAW / "pilot"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(args.gate.read_text())
    model_path = ROOT / manifest["model"]
    assert gate["passed"] and gate["model_sha256"] == manifest["model_sha256"] == digest(model_path)
    assert manifest["pool_sha256"] == digest(RAW / "pool.json")
    assert manifest["builder_sha256"] == digest(HERE / "build.py") == digest(RAW / "build.py")
    assert not PILOT.exists(), "preserve previous pilot"
    model = cp_model.CpModel()
    assert model.proto.parse_text_format(model_path.read_text()) and not model.validate()
    PILOT.mkdir()
    (PILOT / "run.py").write_bytes(Path(__file__).read_bytes())
    (PILOT / "gate.json").write_bytes(args.gate.read_bytes())
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 2026103984
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (PILOT / "parameters.pbtxt").write_text(str(solver.parameters))
    with (PILOT / "solver.log").open("w") as log:
        solver.log_callback = lambda message: (log.write(message + "\n"), log.flush())
        status = solver.solve(model)
    (PILOT / "response.pbtxt").write_text(str(solver.response_proto))
    result = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "status": solver.status_name(status),
        "seed": 2026103984,
        "requested_seconds": 60,
        "workers": 1,
        "solver_wall_seconds": solver.wall_time,
        "conflicts": solver.num_conflicts,
        "branches": solver.num_branches,
        "ortools_version": ortools.__version__,
        "model_sha256": digest(model_path),
        "pool_sha256": digest(RAW / "pool.json"),
        "gate_sha256": digest(args.gate),
        "runner_sha256": digest(Path(__file__)),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "candidate": None,
        "independently_proved_infeasible": False,
        "scope": manifest["scope"],
        "global_lower_bound_claim": False,
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        values = list(solver.response_proto.solution)
        proto = cp_model_pb2.CpModelProto()
        text_format.Parse(model_path.read_text(), proto)
        assert len(values) == 288 and all(x in (0, 1) for x in values)
        for row in proto.constraints:
            assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
            activity = sum(
                values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            assert row.linear.domain[0] <= activity <= row.linear.domain[1]
        data = json.loads((RAW / "pool.json").read_text())
        selected = [tuple(row["block"]) for row, x in zip(data["pool"], values, strict=True) if x]
        omitted = [
            tuple(row["block"])
            for row, x in zip(data["pool"], values, strict=True)
            if not x and row["kind"] == "circle"
        ]
        extensions = [b for b in selected if b not in map(tuple, data["circles"])]
        assert len(selected) == len(set(selected)) == 64
        assert len(extensions) - len(omitted) == 16
        write_blocks(PILOT / "candidate.txt", selected)
        write_blocks(PILOT / "omitted-circles.txt", omitted)
        package = verify_cover(selected)
        standalone_run = subprocess.run(
            [
                sys.executable,
                "scripts/check_cover.py",
                str(PILOT / "candidate.txt"),
                "--expected-blocks",
                "64",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert standalone_run.returncode in (0, 1)
        standalone = json.loads(standalone_run.stdout)
        assert package["valid"] == standalone["valid"]
        assert package["blocks"] == standalone["blocks"] == 64
        assert [list(t) for t in package["uncovered"]] == standalone["uncovered"]
        assert package["canonical_sha256"] == standalone["canonical_sha256"]
        save(PILOT / "package.json", package)
        save(PILOT / "standalone.json", standalone)
        result["candidate"] = {
            "blocks": 64,
            "extensions": len(extensions),
            "omitted_circles": len(omitted),
            "covers_all_triples": package["valid"],
            "missing_triples": len(package["uncovered"]),
            "witness_sha256": digest(PILOT / "candidate.txt"),
            "omitted_circles_sha256": digest(PILOT / "omitted-circles.txt"),
        }
    else:
        assert status in (cp_model.UNKNOWN, cp_model.INFEASIBLE)
        assert not solver.response_proto.solution
    result["artifact_sha256"] = {p.name: digest(p) for p in sorted(PILOT.iterdir()) if p.is_file()}
    save(HERE / "result.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
