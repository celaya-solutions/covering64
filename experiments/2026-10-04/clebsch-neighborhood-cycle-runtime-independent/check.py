# Document:    Independent Clebsch Cycle Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      58ccaec3f1675c49121d3259396070f1f5d85e15e1af387ba341e0b2dc023352
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check saved runtime evidence without importing the producer or solving."""

import copy
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "clebsch-neighborhood-cycle-pilot"
GATE = HERE.parent / "clebsch-neighborhood-cycle-independent/gate.json"
RAW = ROOT / "experiments/scratch/clebsch-neighborhood-cycle-pilot-20261004"
MANIFEST_SHA = "909498955fe3f595465c364f97dd5b938ff333f23ccbf027ec611a4d472fc968"
GATE_SHA = "3b3eb88b04923e69b31404dcc4fe942e09c41936cd7fc88502a7015284f05891"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_result(result, child, response):
    assert result["returncode"] == 0
    assert all(result[key] is False for key in ("watchdog", "terminated", "killed"))
    assert result["manifest_sha256"] == MANIFEST_SHA
    assert result["gate_sha256"] == GATE_SHA
    assert result["child"] == child
    assert child["status"] == "INFEASIBLE"
    assert child["complete64"] is False
    assert child["independent_infeasibility_proof"] is False
    assert "package" not in child and "standalone" not in child
    assert response.status == cp_model_pb2.INFEASIBLE
    assert not response.solution and not response.additional_solutions
    assert response.wall_time == child["native_wall_time"]
    assert 0 < response.wall_time <= child["elapsed_seconds"] <= result["elapsed_seconds"] < 35


def main():
    manifest_path = PRODUCER / "manifest.json"
    result_path = PRODUCER / "result.json"
    launch_path = PRODUCER / "launch.json"
    assert sha(manifest_path) == MANIFEST_SHA and sha(GATE) == GATE_SHA
    manifest = json.loads(manifest_path.read_text())
    result = json.loads(result_path.read_text())
    launch = json.loads(launch_path.read_text())
    for path, digest in manifest["pins"].items():
        assert sha(ROOT / path) == digest, path
    for path, digest in result["raw_files"].items():
        assert sha(ROOT / path) == digest, path
    assert {Path(path).name for path in result["raw_files"]} == {
        "model.pbtxt",
        "parameters.pbtxt",
        "solver.log",
        "response.pbtxt",
        "child-result.json",
        "stdout.log",
        "stderr.log",
    }
    assert set(result["raw_files"]) == {
        str(path.relative_to(ROOT)) for path in RAW.iterdir() if path.is_file()
    }
    assert launch["manifest_sha256"] == MANIFEST_SHA
    assert launch["gate_sha256"] == GATE_SHA
    assert launch["command"][1:] == [str(PRODUCER / "run.py"), "--child"]
    assert not (PRODUCER / "witness.txt").exists() and not (RAW / "vector.json").exists()
    assert (RAW / "stderr.log").read_text() == ""
    assert (RAW / "stdout.log").read_text() == ""
    child = json.loads((RAW / "child-result.json").read_text())
    response = text_format.Parse(
        (RAW / "response.pbtxt").read_text(), cp_model_pb2.CpSolverResponse()
    )
    check_result(result, child, response)
    log = (RAW / "solver.log").read_text()
    for required in (
        "Starting CP-SAT solver v" + manifest["ortools"],
        "random_seed: 2026106201",
        "max_time_in_seconds: 30",
        "num_search_workers: 1",
        "INFEASIBLE: 'during probing'",
        "Problem closed by presolve.",
        "status: INFEASIBLE",
        "walltime: 0.015652",
    ):
        assert required in log, required
    controls = {}
    for name in (
        "returncode",
        "watchdog",
        "complete64",
        "proof_claim",
        "response_status",
        "response_solution",
        "native_wall_time",
    ):
        damaged_result, damaged_child, damaged_response = (
            copy.deepcopy(result),
            copy.deepcopy(child),
            copy.deepcopy(response),
        )
        if name == "returncode":
            damaged_result["returncode"] = 1
        elif name == "watchdog":
            damaged_result["watchdog"] = True
        elif name == "complete64":
            damaged_child["complete64"] = True
        elif name == "proof_claim":
            damaged_child["independent_infeasibility_proof"] = True
        elif name == "response_status":
            damaged_response.status = cp_model_pb2.FEASIBLE
        elif name == "response_solution":
            damaged_response.solution.append(1)
        else:
            damaged_child["native_wall_time"] = 31
        damaged_result["child"] = damaged_child
        try:
            check_result(damaged_result, damaged_child, damaged_response)
        except AssertionError:
            controls[name] = "rejected"
        else:
            raise AssertionError("damaged result accepted: " + name)
    audit = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "gate_sha256": GATE_SHA,
        "result_sha256": sha(result_path),
        "launch_sha256": sha(launch_path),
        "checker_sha256": sha(Path(__file__)),
        "manifest_pins_checked": len(manifest["pins"]),
        "runtime_files_checked": len(result["raw_files"]),
        "status": child["status"],
        "native_seconds": response.wall_time,
        "solve_elapsed_seconds": child["elapsed_seconds"],
        "wrapper_seconds": result["elapsed_seconds"],
        "returncode": result["returncode"],
        "watchdog": False,
        "witness_exists": False,
        "vector_exists": False,
        "complete64": False,
        "independent_infeasibility_proof": False,
        "scope": "Solver result only for the fixed sixteen neighborhoods plus cycle recipe.",
        "damage_controls": controls,
        "optimizer_calls": 0,
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "result_sha256": sha(result_path),
                "wrapper_seconds": result["elapsed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
