# Document:    Gated SQS Union Symmetry Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      570d65ee798306992ae712422a73f45b154ea204e92ee66ece4336f65976426b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run the single authorized180-second pilot only after a separate model gate."""

import argparse
import hashlib
import json
import platform
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
RAW = ROOT / "experiments/scratch/sqs-union-symmetry-pilot-20261003"
PILOT = RAW / "pilot-2026104011"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=Path, required=True)
    args = parser.parse_args()
    gate = json.loads(args.gate.read_text())
    manifest = json.loads((HERE / "model-manifest.json").read_text())
    model_path = ROOT / manifest["model_path"]
    pool_path = ROOT / manifest["pool_path"]
    assert gate["passed"] and gate["model_sha256"] == manifest["model_sha256"] == digest(model_path)
    assert manifest["pool_sha256"] == digest(pool_path)
    assert gate["pool_sha256"] == digest(pool_path)
    assert gate["source_sha256"] == digest(args.gate.parent / "check.py")
    for relative, expected_hash in gate["verified_inputs"].items():
        path = (ROOT / relative).resolve()
        assert path.is_relative_to(ROOT) and digest(path) == expected_hash
    assert (
        manifest["builder_sha256"]
        == digest(HERE / "build_model.py")
        == digest(RAW / "build_model.py")
    )
    for relative, expected_hash in manifest["verified_inputs"].items():
        path = (ROOT / relative).resolve()
        assert path.is_relative_to(ROOT) and digest(path) == expected_hash
    assert manifest["base_model_sha256"] == digest(ROOT / manifest["base_model_path"])
    assert manifest["certificate_sha256"] == digest(ROOT / manifest["certificate_path"])
    assert manifest["certificate_audit_sha256"] == digest(ROOT / manifest["certificate_audit_path"])
    certificate_audit = json.loads((ROOT / manifest["certificate_audit_path"]).read_text())
    assert (
        certificate_audit["passed"]
        and certificate_audit["certificate_sha256"] == manifest["certificate_sha256"]
    )
    assert certificate_audit["pool_sha256"] == digest(pool_path)
    assert ortools.__version__ == manifest["ortools_version"] == "9.15.6755"
    assert manifest["proposed_pilot"] == {
        "seed": 2026104011,
        "seconds": 180,
        "workers": 1,
        "status": "not_run",
    }
    assert not PILOT.exists(), "single pilot only; preserve existing run"
    assert not (HERE / "pilot-result.json").exists(), "preserve recorded result"
    model = cp_model.CpModel()
    assert model.proto.parse_text_format(model_path.read_text()) and not model.validate()
    assert len(model.proto.variables) == 1744 and len(model.proto.constraints) == 562
    PILOT.mkdir()
    (PILOT / "run_pilot.py").write_bytes(Path(__file__).read_bytes())
    (PILOT / "independent-gate.json").write_bytes(args.gate.read_bytes())
    solver = cp_model.CpSolver()
    solver.parameters.random_seed = 2026104011
    solver.parameters.max_time_in_seconds = 180
    solver.parameters.num_search_workers = 1
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    (PILOT / "parameters.pbtxt").write_text(str(solver.parameters))
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "runner_sha256": digest(Path(__file__)),
        "model_sha256": digest(model_path),
        "pool_sha256": digest(pool_path),
        "base_model_sha256": manifest["base_model_sha256"],
        "certificate_sha256": manifest["certificate_sha256"],
        "certificate_audit_sha256": manifest["certificate_audit_sha256"],
        "gate_sha256": digest(args.gate),
        "manifest_sha256": digest(HERE / "model-manifest.json"),
        "ortools_version": ortools.__version__,
        "python_version": platform.python_version(),
        "seed": 2026104011,
        "requested_seconds": 180,
        "workers": 1,
    }
    save(PILOT / "start.json", start)
    with (PILOT / "solver.log").open("w") as log:
        solver.log_callback = lambda message: (log.write(message + "\n"), log.flush())
        status = solver.solve(model)
    (PILOT / "response.pbtxt").write_text(str(solver.response_proto))
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "status": solver.status_name(status),
        "solver_wall_seconds": solver.wall_time,
        "conflicts": solver.num_conflicts,
        "branches": solver.num_branches,
        "witness": None,
        "independently_proved_infeasible": False,
        "global_lower_bound_claim": False,
        "scope": manifest["scope"],
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        values = list(solver.response_proto.solution)
        assert len(values) == 1744 and all(value in (0, 1) for value in values)
        proto = cp_model_pb2.CpModelProto()
        text_format.Parse(model_path.read_text(), proto)
        for constraint in proto.constraints:
            assert (
                constraint.WhichOneof("constraint") == "linear"
                and not constraint.enforcement_literal
            )
            row = constraint.linear
            activity = sum(
                values[i] * coefficient for i, coefficient in zip(row.vars, row.coeffs, strict=True)
            )
            assert row.domain[0] <= activity <= row.domain[1]
        pool = json.loads(pool_path.read_text())["pool"]
        selected = [tuple(row["block"]) for row, value in zip(pool, values, strict=True) if value]
        assert len(selected) == len(set(selected)) == 64
        witness_path = PILOT / "cover64.txt"
        write_blocks(witness_path, selected)
        package = verify_cover(selected)
        save(PILOT / "package.json", package)
        standalone_run = subprocess.run(
            [
                sys.executable,
                "scripts/check_cover.py",
                str(witness_path),
                "--expected-blocks",
                "64",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert standalone_run.returncode in (0, 1)
        standalone = json.loads(standalone_run.stdout)
        save(PILOT / "standalone.json", standalone)
        assert package["valid"] and standalone["valid"] and standalone_run.returncode == 0
        assert package["blocks"] == standalone["blocks"] == 64
        assert package["canonical_sha256"] == standalone["canonical_sha256"]
        result["witness"] = {
            "path": str(witness_path.relative_to(ROOT)),
            "sha256": digest(witness_path),
            "blocks": 64,
            "both_verifiers_passed": True,
        }
    else:
        assert status in (cp_model.UNKNOWN, cp_model.INFEASIBLE)
        assert not solver.response_proto.solution
    result["artifact_sha256"] = {
        path.name: digest(path) for path in sorted(PILOT.iterdir()) if path.is_file()
    }
    save(HERE / "pilot-result.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
