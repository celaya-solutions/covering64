# Document:    Affine Circle Relaxation Pilot Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      71cda7de0ebab924b279db7868381a3b6b2d1bf6f7689c1e563547cd888e2792
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check saved solver response, parameters, artifacts, and any noncover candidate."""

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-circle-incidence-relaxation-20261003"
PILOT = RAW / "pilot"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(result):
    manifest = json.loads((HERE / "manifest.json").read_text())
    assert result["model_sha256"] == manifest["model_sha256"] == digest(ROOT / manifest["model"])
    assert result["pool_sha256"] == manifest["pool_sha256"] == digest(RAW / "pool.json")
    assert result["runner_sha256"] == digest(HERE / "run.py") == digest(PILOT / "run.py")
    assert (
        result["gate_sha256"]
        == digest(PILOT / "gate.json")
        == digest(HERE / "independent-audit.json")
    )
    assert set(result["artifact_sha256"]) == {p.name for p in PILOT.iterdir() if p.is_file()}
    for name, value in result["artifact_sha256"].items():
        assert value == digest(PILOT / name)
    parameters = sat_parameters_pb2.SatParameters()
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse((PILOT / "parameters.pbtxt").read_text(), parameters)
    text_format.Parse((PILOT / "response.pbtxt").read_text(), response)
    assert parameters.random_seed == result["seed"] == 2026103984
    assert parameters.max_time_in_seconds == result["requested_seconds"] == 60
    assert parameters.num_search_workers == result["workers"] == 1
    assert cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"]
    assert response.wall_time == result["solver_wall_seconds"]
    assert (
        response.num_conflicts == result["conflicts"]
        and response.num_branches == result["branches"]
    )
    assert result["independently_proved_infeasible"] is False
    assert result["global_lower_bound_claim"] is False
    if result["status"] in ("OPTIMAL", "FEASIBLE"):
        model = cp_model_pb2.CpModelProto()
        text_format.Parse((ROOT / manifest["model"]).read_text(), model)
        values = list(response.solution)
        assert len(values) == 288 and all(x in (0, 1) for x in values)
        for row in model.constraints:
            assert row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
            activity = sum(
                values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            assert row.linear.domain[0] <= activity <= row.linear.domain[1]
        pool = json.loads((RAW / "pool.json").read_text())["pool"]
        selected = [tuple(row["block"]) for row, x in zip(pool, values, strict=True) if x]
        omitted = [
            tuple(row["block"])
            for row, x in zip(pool, values, strict=True)
            if not x and row["kind"] == "circle"
        ]
        extensions = sum(
            row["kind"] == "extension" and x for row, x in zip(pool, values, strict=True)
        )
        assert list(read_blocks(PILOT / "candidate.txt")) == selected
        assert list(read_blocks(PILOT / "omitted-circles.txt")) == omitted
        assert len(selected) == len(set(selected)) == 64
        package = verify_cover(selected)
        run = subprocess.run(
            [
                sys.executable,
                "scripts/check_cover.py",
                str(PILOT / "candidate.txt"),
                "--expected-blocks",
                "64",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        assert run.returncode in (0, 1)
        standalone = json.loads(run.stdout)
        assert package["valid"] == standalone["valid"]
        assert [list(t) for t in package["uncovered"]] == standalone["uncovered"]
        assert result["candidate"] == {
            "blocks": 64,
            "extensions": extensions,
            "omitted_circles": len(omitted),
            "covers_all_triples": package["valid"],
            "missing_triples": len(package["uncovered"]),
            "witness_sha256": digest(PILOT / "candidate.txt"),
            "omitted_circles_sha256": digest(PILOT / "omitted-circles.txt"),
        }
    else:
        assert result["status"] in ("UNKNOWN", "INFEASIBLE") and not response.solution
        assert result["candidate"] is None


def main():
    result = json.loads((HERE / "result.json").read_text())
    inspect(result)
    mutations = [
        ("model_sha256", "0" * 64),
        ("seed", 1),
        ("requested_seconds", 59),
        ("workers", 2),
        ("status", "UNKNOWN" if result["status"] != "UNKNOWN" else "FEASIBLE"),
        ("independently_proved_infeasible", True),
        ("global_lower_bound_claim", True),
        ("candidate", None if result["candidate"] is not None else {"covers_all_triples": True}),
        ("artifact_sha256", {}),
    ]
    for key, value in mutations:
        damaged = copy.deepcopy(result)
        damaged[key] = value
        try:
            inspect(damaged)
        except (AssertionError, ValueError, KeyError):
            continue
        raise AssertionError("damaged result accepted")
    report = {
        "passed": True,
        "status": result["status"],
        "damaged_results_rejected": len(mutations),
        "checker_sha256": digest(Path(__file__)),
        "result_sha256": digest(HERE / "result.json"),
        "model_sha256": result["model_sha256"],
        "candidate": result["candidate"],
        "global_lower_bound_claim": False,
    }
    (HERE / "readback.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
