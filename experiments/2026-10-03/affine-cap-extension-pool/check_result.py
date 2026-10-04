# Document:    Affine Cap Pool Pilot Result Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      398365eda73cd254983338c588e00310817344230caf366ec3e18d3ca44076f6
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check frozen response, parameters and any solution without calling a solver."""

import copy
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

from covering64.core import read_blocks, verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-cap-extension-pool-pilot-20261003"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(result):
    manifest = json.loads((HERE / "manifest.json").read_text())
    entry = next(x for x in manifest["models"] if x["name"] == "incidence-cuts")
    require(result["model_sha256"] == entry["sha256"] == sha(ROOT / entry["path"]), "model")
    require(result["pool_sha256"] == manifest["pool_sha256"] ==
            sha(ROOT / manifest["pool"]), "pool")
    require(result["runner_sha256"] == sha(HERE / "run.py") == sha(RAW / "run.py"), "runner")
    for name, digest in result["artifact_sha256"].items():
        require(sha(RAW / name) == digest, "artifact hash")
    parameters = sat_parameters_pb2.SatParameters()
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse((RAW / "parameters.pbtxt").read_text(), parameters)
    text_format.Parse((RAW / "response.pbtxt").read_text(), response)
    require(parameters.random_seed == result["seed"] == 2026103971, "seed")
    require(parameters.max_time_in_seconds == result["requested_seconds"] == 300 and
            parameters.num_search_workers == result["workers"] == 8, "budget/workers")
    require(cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"], "status")
    require(response.wall_time == result["solver_wall_seconds"] and
            response.num_conflicts == result["conflicts"] and
            response.num_branches == result["branches"], "response counters")
    require(result["independently_proved_infeasible"] is False, "no independent negative proof")
    if result["status"] in ("OPTIMAL", "FEASIBLE"):
        model = cp_model_pb2.CpModelProto()
        text_format.Parse((ROOT / entry["path"]).read_text(), model)
        values = list(response.solution)
        require(len(values) == 528 and all(v in (0, 1) for v in values), "Boolean solution")
        for row in model.constraints:
            require(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal,
                    "plain linear constraints")
            activity = sum(values[i] * c for i, c in
                           zip(row.linear.vars, row.linear.coeffs, strict=True))
            require(row.linear.domain[0] <= activity <= row.linear.domain[1], "solution row")
        pool = json.loads((ROOT / manifest["pool"]).read_text())
        selected = sorted(tuple(row["block"]) for row, value in
                          zip(pool["pool"], values, strict=True) if value)
        require(len(selected) == 64 and verify_cover(selected)["valid"], "response cover")
        witness = ROOT / result["witness"]["path"]
        require(sha(witness) == result["witness"]["sha256"] and
                list(read_blocks(witness)) == selected, "response matches saved witness")
        for name in ("package", "standalone"):
            report = json.loads((RAW / f"{name}.json").read_text())
            require(report["valid"] and report["blocks"] == 64, "saved covering check")
    else:
        require(result["status"] in ("UNKNOWN", "INFEASIBLE") and not response.solution and
                result["witness"] is None and result["checks"] is None, "no witness")


def main():
    result = json.loads((HERE / "result.json").read_text())
    require(result == json.loads((RAW / "result.json").read_text()), "result copies")
    inspect(result)
    controls = []
    other = "INFEASIBLE" if result["status"] == "UNKNOWN" else "UNKNOWN"
    for field, value in (("status", other), ("requested_seconds", 301), ("workers", 7),
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
                 result_sha256=sha(HERE / "result.json"), status=result["status"], solver_calls=0,
                 damaged_controls=controls, scope="Frozen restricted solver result readback only.")
    (HERE / "readback-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
