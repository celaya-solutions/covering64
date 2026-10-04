# Document:    Restricted Boolean Template CP Pilot Response Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read back frozen solver artifacts without solving; preserve compact evidence."""

import gzip
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/four-seven-template-cp-restricted-pilots-v1.0.0"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    results = load(RAW / "results.json")
    require(
        [r["case"] for r in results] == ["matching-029", "matching-063"],
        "incomplete pilot inventory",
    )
    require(results == load(HERE / "pilot-results.json"), "durable results differ")
    manifest = load(RAW / "manifest.json")
    audit = load(RAW / "independent-audit.json")
    require(
        audit["passed"] is True and sha(RAW / "manifest.json") == audit["manifest_sha256"],
        "encoding audit does not bind manifest",
    )
    environment = load(RAW / "environment.json")
    require(
        sha(RAW / "run.py") == environment["source_sha256"] == sha(HERE / "run.py"),
        "runner changed",
    )
    archived = []
    for result, seed in zip(results, [2026103801, 2026103802], strict=True):
        case = result["case"]
        folder = RAW / case
        require(load(folder / "result.json") == result, "per-case result differs")
        record = next(r for r in manifest["cases"] if r["case"] == case)
        for field in ["hub_case", "fixed_ids", "source_base_sha256"]:
            require(result[field] == record[field], "restricted scope differs")
        require(
            sha(ROOT / record["model"]) == record["model_sha256"] == result["model_sha256"],
            "model changed",
        )
        for name, field in [
            ("parameters.pbtxt", "parameters_sha256"),
            ("response.pbtxt", "response_sha256"),
            ("solver.log", "log_sha256"),
        ]:
            require(sha(folder / name) == result[field], "raw solver artifact changed")
        parameters = sat_parameters_pb2.SatParameters()
        text_format.Parse((folder / "parameters.pbtxt").read_text(), parameters)
        require(parameters.random_seed == result["seed"] == seed, "wrong seed")
        require(
            parameters.max_time_in_seconds == result["requested_seconds"] == 600, "wrong budget"
        )
        require(parameters.num_search_workers == result["workers"] == 8, "wrong worker count")
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse((folder / "response.pbtxt").read_text(), response)
        require(
            cp_model_pb2.CpSolverStatus.Name(response.status) == result["status"], "wrong status"
        )
        require(response.wall_time == result["wall_seconds"], "wrong reported solver time")
        require(
            response.num_conflicts == result["conflicts"]
            and response.num_branches == result["branches"],
            "wrong reported counters",
        )
        if response.status in [cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL]:
            proto = cp_model_pb2.CpModelProto()
            text_format.Parse((ROOT / record["model"]).read_text(), proto)
            require(len(response.solution) == len(proto.variables), "partial solution")
            values = list(response.solution)
            require(all(v in [0, 1] for v in values), "nonboolean solution")
            for row in proto.constraints:
                require(not row.enforcement_literal, "unexpected conditional row")
                if row.WhichOneof("constraint") == "exactly_one":
                    require(
                        sum(values[i] for i in row.exactly_one.literals) == 1, "one-hot violation"
                    )
                else:
                    require(row.WhichOneof("constraint") == "linear", "unexpected row type")
                    total = sum(
                        values[i] * a
                        for i, a in zip(row.linear.vars, row.linear.coeffs, strict=True)
                    )
                    require(row.linear.domain[0] <= total <= row.linear.domain[1], "row violation")
            require(
                result["witness"] and len(result["checks"]) == 2, "missing witness verification"
            )
            for label, checked in zip(["package", "standalone"], result["checks"], strict=True):
                require(
                    (folder / (label + "-stdout.json")).read_text() == checked["stdout"]
                    and (folder / (label + "-stderr.txt")).read_text() == checked["stderr"],
                    "checker output differs",
                )
                require(
                    checked["exit"] == 0 and json.loads(checked["stdout"])["valid"] is True,
                    "checker rejected witness",
                )
        else:
            require(
                response.status in [cp_model_pb2.UNKNOWN, cp_model_pb2.INFEASIBLE], "bad status"
            )
            require(
                not response.solution and not result["witness"] and not result["checks"],
                "unexpected witness on inconclusive result",
            )
        archived.append(
            {
                "case": case,
                "parameters": (folder / "parameters.pbtxt").read_text(),
                "response": (folder / "response.pbtxt").read_text(),
                "result": result,
            }
        )
    evidence = {
        "environment": environment,
        "manifest": manifest,
        "encoding_audit": audit,
        "responses": archived,
    }
    evidence_path = HERE / "pilot-evidence.json.gz"
    evidence_path.write_bytes(
        gzip.compress(json.dumps(evidence, separators=(",", ":")).encode(), mtime=0)
    )
    report = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "pilot_count": len(results),
        "cases": [
            {
                "case": r["case"],
                "status": r["status"],
                "seed": r["seed"],
                "wall_seconds": r["wall_seconds"],
            }
            for r in results
        ],
        "raw_results_sha256": sha(RAW / "results.json"),
        "evidence_sha256": sha(evidence_path),
        "evidence_bytes": evidence_path.stat().st_size,
        "scope": "Saved solver response and budget verification only. UNKNOWN and uncertified "
        "INFEASIBLE provide no exact exclusion or lower bound.",
    }
    (HERE / "pilot-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
