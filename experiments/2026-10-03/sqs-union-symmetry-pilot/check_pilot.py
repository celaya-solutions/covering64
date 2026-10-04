# Document:    SQS Union Symmetry Pilot Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      8f81ea070a91f9dcf94c7c03ff8bc3789bf09a4636d12df480caee95111751f6
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit the frozen pilot response and independently recount any witness."""

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
RAW = ROOT / "experiments/scratch/sqs-union-symmetry-pilot-20261003"
PILOT = RAW / "pilot-2026104011"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(result):
    manifest = json.loads((HERE / "model-manifest.json").read_text())
    assert result["manifest_sha256"] == digest(HERE / "model-manifest.json")
    assert (
        result["model_sha256"] == manifest["model_sha256"] == digest(ROOT / manifest["model_path"])
    )
    assert result["pool_sha256"] == manifest["pool_sha256"] == digest(ROOT / manifest["pool_path"])
    for relative, expected in manifest["verified_inputs"].items():
        assert digest(ROOT / relative) == expected
    for prefix in ("base_model", "certificate", "certificate_audit"):
        assert (
            result[f"{prefix}_sha256"]
            == manifest[f"{prefix}_sha256"]
            == digest(ROOT / manifest[f"{prefix}_path"])
        )
    assert (
        result["runner_sha256"] == digest(HERE / "run_pilot.py") == digest(PILOT / "run_pilot.py")
    )
    assert result["gate_sha256"] == digest(PILOT / "independent-gate.json")
    gate = json.loads((PILOT / "independent-gate.json").read_text())
    assert gate["passed"] and gate["model_sha256"] == result["model_sha256"]
    for relative, expected in gate["verified_inputs"].items():
        assert digest(ROOT / relative) == expected
    start = json.loads((PILOT / "start.json").read_text())
    assert all(result[key] == value for key, value in start.items())
    assert set(result["artifact_sha256"]) == {
        path.name for path in PILOT.iterdir() if path.is_file()
    }
    for name, expected in result["artifact_sha256"].items():
        assert digest(PILOT / name) == expected
    parameters = sat_parameters_pb2.SatParameters()
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse((PILOT / "parameters.pbtxt").read_text(), parameters)
    text_format.Parse((PILOT / "response.pbtxt").read_text(), response)
    assert parameters.random_seed == result["seed"] == 2026104011
    assert parameters.max_time_in_seconds == result["requested_seconds"] == 180
    assert parameters.num_search_workers == result["workers"] == 1
    assert cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"]
    assert response.wall_time == result["solver_wall_seconds"]
    assert (
        response.num_conflicts == result["conflicts"]
        and response.num_branches == result["branches"]
    )
    assert result["independently_proved_infeasible"] is False
    assert result["global_lower_bound_claim"] is False and result["scope"] == manifest["scope"]
    if result["status"] in ("OPTIMAL", "FEASIBLE"):
        model = cp_model_pb2.CpModelProto()
        text_format.Parse((ROOT / manifest["model_path"]).read_text(), model)
        values = list(response.solution)
        assert len(values) == 1744 and all(value in (0, 1) for value in values)
        for constraint in model.constraints:
            assert (
                constraint.WhichOneof("constraint") == "linear"
                and not constraint.enforcement_literal
            )
            row = constraint.linear
            activity = sum(
                values[i] * coefficient for i, coefficient in zip(row.vars, row.coeffs, strict=True)
            )
            assert row.domain[0] <= activity <= row.domain[1]
        pool = json.loads((ROOT / manifest["pool_path"]).read_text())["pool"]
        selected = [tuple(row["block"]) for row, value in zip(pool, values, strict=True) if value]
        witness_path = ROOT / result["witness"]["path"]
        assert list(read_blocks(witness_path)) == selected
        assert digest(witness_path) == result["witness"]["sha256"]
        assert result["witness"]["blocks"] == len(selected) == len(set(selected)) == 64
        assert result["witness"]["both_verifiers_passed"] is True
        package = verify_cover(selected)
        assert package["valid"] and package["blocks"] == 64
        run = subprocess.run(
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
            check=True,
        )
        standalone = json.loads(run.stdout)
        assert standalone["valid"] and standalone["blocks"] == 64
        assert package["canonical_sha256"] == standalone["canonical_sha256"]
    else:
        assert result["status"] in ("UNKNOWN", "INFEASIBLE") and not response.solution
        assert result["witness"] is None


def main():
    result = json.loads((HERE / "pilot-result.json").read_text())
    inspect(result)
    mutations = [
        ("model_sha256", "0" * 64),
        ("pool_sha256", "0" * 64),
        ("runner_sha256", "0" * 64),
        ("seed", 1),
        ("requested_seconds", 179),
        ("workers", 2),
        ("status", "UNKNOWN" if result["status"] != "UNKNOWN" else "FEASIBLE"),
        ("conflicts", result["conflicts"] + 1),
        ("independently_proved_infeasible", True),
        ("global_lower_bound_claim", True),
        ("artifact_sha256", {}),
        ("witness", None if result["witness"] is not None else {"blocks": 64}),
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
        "model_sha256": result["model_sha256"],
        "checker_sha256": digest(Path(__file__)),
        "result_sha256": digest(HERE / "pilot-result.json"),
        "damaged_results_rejected": len(mutations),
        "witness": result["witness"],
        "independently_proved_infeasible": False,
        "global_lower_bound_claim": False,
    }
    (HERE / "pilot-readback.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
