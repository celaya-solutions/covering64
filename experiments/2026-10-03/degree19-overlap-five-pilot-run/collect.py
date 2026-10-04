# Document:    Four Overlap Five Pilot Evidence Collection
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check completed solver responses and preserve compact frozen pilot evidence."""

import gzip
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/degree19-overlap-five-pilot-run-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    metadata = json.loads((RAW / "metadata.json").read_text())
    for name, digest in metadata["sources"].items():
        assert sha(RAW / name) == digest
    lp = json.loads((HERE / "lp-audit.json").read_text())
    assert lp["passed"] and lp["metadata_sha256"] == sha(RAW / "metadata.json")
    survivors = {row["id"] for row in lp["models"] if not row["excluded"]}
    selection = json.loads((RAW / "cp-selection.json").read_text())
    assert set(selection["cases"]) == survivors and len(selection["cases"]) == len(survivors)
    assert selection["seconds"] == 300 and selection["workers"] == 2
    assert selection["maximum_simultaneous_jobs"] == 2
    processes = json.loads((RAW / "cp-process-results.json").read_text())
    assert {row["id"] for row in processes} == survivors and len(processes) == len(survivors)
    assert all(row["returncode"] == 0 for row in processes)
    cp_results = []
    for item in metadata["models"]:
        if item["id"] not in survivors:
            continue
        folder = RAW / item["id"]
        summary = json.loads((folder / "cp-summary.json").read_text())
        parameters = text_format.Parse((folder / "cp-parameters.pbtxt").read_text(),
                                       sat_parameters_pb2.SatParameters())
        response = text_format.Parse((folder / "cp-response.pbtxt").read_text(),
                                     cp_model_pb2.CpSolverResponse())
        assert parameters.max_time_in_seconds == 300 and parameters.num_search_workers == 2
        assert parameters.random_seed == item["seed"] == summary["seed"]
        assert summary["status"] == cp_model_pb2.CpSolverStatus.Name(response.status)
        assert abs(summary["wall_seconds"] - response.wall_time) < 1e-9
        assert summary["model_sha256"] == item["model_sha256"] == sha(folder / "model.pbtxt")
        assert summary["response_sha256"] == sha(folder / "cp-response.pbtxt")
        assert summary["parameters_sha256"] == sha(folder / "cp-parameters.pbtxt")
        if summary["status"] in ("FEASIBLE", "OPTIMAL"):
            checked = json.loads((folder / "cp-verification.json").read_text())
            assert checked["verified_cover"] and checked["exact_model_rows_satisfied"]
            assert checked["package"]["valid"] and checked["standalone"]["valid"]
            assert checked["standalone_returncode"] == 0
            assert len(checked["selected_ids"]) == len(set(checked["selected_ids"])) == 64
        cp_results.append(summary)
    hashes = {str(path.relative_to(RAW)): sha(path) for path in sorted(RAW.rglob("*"))
              if path.is_file() and "__pycache__" not in path.parts}
    proof_folder = HERE.parent / "degree19-overlap-five-certificate-replay"
    proof = json.loads((proof_folder / "pilot-000.json").read_text())
    assert proof["valid"] and proof["matrix_sha256"] == sha(RAW / "pilot-000/lp-rows.json.gz")
    assert proof["certificate_sha256"] == sha(RAW / "pilot-000/certificate.json")
    evidence = {"metadata": metadata, "lp_audit": lp, "cp_results": cp_results,
                "cp_processes": processes, "cp_selection": selection,
                "independent_certificate_replay": proof,
                "certificate": json.loads((RAW / "pilot-000/certificate.json").read_text()),
                "sources": {name: (RAW / name).read_text() for name in metadata["sources"]
                            if name.endswith(".py")},
                "primal_values": {name: json.loads(gzip.decompress(
                    (RAW / name / "feasibility.json.gz").read_bytes()))["values"]
                    for name in sorted(survivors)},
                "raw_artifact_sha256": hashes, "collector_sha256": sha(Path(__file__))}
    encoded = gzip.compress((json.dumps(evidence) + "\n").encode(), mtime=0)
    (HERE / "evidence.json.gz").write_bytes(encoded)
    result = {"passed": True, "lp_excluded": [r["id"] for r in lp["models"] if r["excluded"]],
              "cp_results": cp_results,
              "verified_covers": [r["id"] for r in cp_results if r["verified_cover"]],
              "evidence_sha256": sha(HERE / "evidence.json.gz"), "evidence_bytes": len(encoded),
              "collector_sha256": sha(Path(__file__)),
              "scope": "Four explicit ordered unions only. UNKNOWN is inconclusive and "
                       "CP-SAT INFEASIBLE alone is not an independently checked theorem."}
    (HERE / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
