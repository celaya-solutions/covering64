# Document:    Inversive Pool Pilot Result Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      13fa79d151baa3b5406e54422a388011908d016a0c4c0c2ccf673f7a7df6ff85
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read frozen solver evidence without a solver invocation."""

import copy
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/inversive-plane-pool-pilot-20261003"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(result):
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(result["model_sha256"] == manifest["model_sha256"] ==
            sha(ROOT / manifest["model"]), "model hash")
    require(result["pool_sha256"] == manifest["pool_sha256"] ==
            sha(ROOT / manifest["pool"]), "pool hash")
    require(result["runner_sha256"] == sha(HERE / "run.py") == sha(RAW / "run.py"), "runner")
    for name, digest in result["artifact_sha256"].items():
        require(sha(RAW / name) == digest, "artifact hash")
    parameters = sat_parameters_pb2.SatParameters()
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse((RAW / "parameters.pbtxt").read_text(), parameters)
    text_format.Parse((RAW / "response.pbtxt").read_text(), response)
    require(parameters.random_seed == result["seed"] == 2026100371, "seed")
    require(parameters.max_time_in_seconds == result["requested_seconds"] == 60 and
            parameters.num_search_workers == result["workers"] == 1, "budget/workers")
    require(cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"], "status")
    require(response.wall_time == result["solver_wall_seconds"] and
            response.num_conflicts == result["conflicts"] and
            response.num_branches == result["branches"], "response counters")
    require(result["status"] == "UNKNOWN" and not response.solution and
            result["witness"] is None and result["checks"] is None and
            result["independently_proved_infeasible"] is False, "inconclusive classification")


def main():
    result = json.loads((HERE / "result.json").read_text())
    require(result == json.loads((RAW / "result.json").read_text()), "result copies")
    inspect(result)
    controls = []
    for field, value in (("status", "INFEASIBLE"), ("requested_seconds", 61), ("workers", 2),
                         ("seed", 1), ("branches", -1), ("model_sha256", "0"),
                         ("independently_proved_infeasible", True)):
        damaged = copy.deepcopy(result)
        damaged[field] = value
        try:
            inspect(damaged)
        except ValueError:
            controls.append(dict(field=field, rejected=True))
        else:
            raise ValueError("damaged result accepted")
    audit = dict(passed=True, checker_sha256=sha(Path(__file__)),
                 result_sha256=sha(HERE / "result.json"), status="UNKNOWN", solver_calls=0,
                 damaged_controls=controls, scope="Frozen restricted solver result readback only.")
    (HERE / "readback-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
