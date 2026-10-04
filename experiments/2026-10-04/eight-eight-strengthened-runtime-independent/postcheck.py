# Document:    Strengthened Eight by Eight Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6e66451859e0492a390776fa3606e22244171552b16fd7cb4cc64ae885dcf4e8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read frozen runtime records only; never rerun search."""

import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model_helper

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "eight-eight-strengthened"
PRE = HERE.parent / "eight-eight-strengthened-independent"
RAW = ROOT / "experiments/scratch/eight-eight-strengthened-20261004"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    manifest = read(PRODUCER / "manifest.json")
    result = read(PRODUCER / "result.json")
    gate = read(PRE / "gate.json")
    assert (
        sha(PRODUCER / "result.json")
        == "df522b51d617839d16dc39e0b5924873f9f5c95c771860ad1df64aedf30febb9"
    )
    assert result["manifest_sha256"] == gate["manifest_sha256"] == sha(PRODUCER / "manifest.json")
    assert result["gate_sha256"] == sha(PRE / "gate.json")
    assert gate["passed"] and gate["decision"] == "GO"
    assert gate["model_audit_sha256"] == sha(ROOT / gate["model_audit_path"])
    assert gate["runner_audit_sha256"] == sha(ROOT / gate["runner_audit_path"])
    assert gate["readme_sha256"] == sha(PRE / "README.md")
    assert manifest["source_sha256"] == gate["producer_sha256"] == sha(PRODUCER / "run.py")
    common = HERE.parent / "two-point-star-repair-v2/run.py"
    assert manifest["common_sha256"] == sha(common)
    assert gate["proof_files"] == manifest["proof_files"]
    for path, digest in manifest["proof_files"].items():
        assert sha(ROOT / path) == digest
    assert not result["cover_found"] and result["relaunch"] is False
    assert len(result["runs"]) == len(manifest["entries"]) == 3
    assert sorted(p.name for p in RAW.glob("run-*")) == ["run-1", "run-2", "run-3"]
    assert {str(p.relative_to(ROOT)): sha(p) for p in RAW.rglob("*") if p.is_file()} == result[
        "raw_files"
    ]
    rows = []
    previous_result_mtime = None
    for entry, row in zip(manifest["entries"], result["runs"]):
        number = entry["number"]
        folder = RAW / f"run-{number}"
        assert row["number"] == number and row["kinds"] == entry["kinds"]
        assert row["command"][1:] == [str(PRODUCER / "run.py"), "--child", str(number)]
        assert Path(row["command"][0]).is_file()
        for field in ("model", "groups"):
            assert sha(ROOT / entry[field]) == entry[f"{field}_sha256"]
        params = text_format.Parse(
            (folder / "parameters.pbtxt").read_text(), sat_parameters_pb2.SatParameters()
        )
        expected = sat_parameters_pb2.SatParameters(
            max_time_in_seconds=120,
            num_search_workers=4,
            random_seed=2026105500 + number,
            log_search_progress=True,
        )
        assert params == expected
        outcome = read(folder / "outcome.json")
        response_text = (folder / "response.pbtxt").read_text()
        response = text_format.Parse(response_text, cp_model_pb2.CpSolverResponse())
        native_response = cp_model_helper.CpSolverResponse()
        assert native_response.parse_text_format(response_text)
        assert response.status == native_response.status == cp_model_pb2.UNKNOWN
        assert list(response.solution) == list(native_response.solution) == []
        assert outcome == row["outcome"] and outcome["status"] == "UNKNOWN"
        assert outcome["callbacks"] == 0 and outcome["wall_seconds"] == response.wall_time
        assert abs(native_response.wall_time - response.wall_time) < 1e-9
        assert 120 <= response.wall_time < 125
        assert response.wall_time <= row["elapsed_seconds"] < manifest["watchdog"]
        assert row["returncode"] == 0 and not row["watchdog_fired"]
        assert row["saved"] == [] and not row["cover_found"]
        assert not list(folder.glob("callback-*")) and not (folder / "final-vector.json").exists()
        assert not list(folder.glob("*.txt")) and not list(folder.glob("*.tmp"))
        assert (folder / "stderr.log").read_text() == ""
        log = (folder / "stdout.log").read_text()
        assert log.count("Starting CP-SAT solver v9.15.6755") == 1
        assert log.count("CpSolverResponse summary:") == 1
        assert "status: UNKNOWN" in log
        assert f"random_seed: {entry['seed']}" in log
        assert "max_time_in_seconds: 120" in log and "num_search_workers: 4" in log
        saved = read(PRODUCER / f"run-{number}-result.json")
        assert saved == row
        params_mtime = (folder / "parameters.pbtxt").stat().st_mtime_ns
        if previous_result_mtime is not None:
            assert previous_result_mtime <= params_mtime
        previous_result_mtime = (PRODUCER / f"run-{number}-result.json").stat().st_mtime_ns
        rows.append(
            {
                "number": number,
                "kinds": entry["kinds"],
                "seed": entry["seed"],
                "status": "UNKNOWN",
                "callbacks": 0,
                "solution_length": 0,
                "wall_seconds": response.wall_time,
                "elapsed_seconds": row["elapsed_seconds"],
                "parameters_exact": True,
                "native_and_standard_response_match": True,
                "stdout_sha256": sha(folder / "stdout.log"),
                "response_sha256": sha(folder / "response.pbtxt"),
                "no_candidate_files": True,
                "sequential_file_order_consistent": True,
            }
        )
    assert not (PRODUCER / "cover.txt").exists()
    receipt = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "producer_result_sha256": sha(PRODUCER / "result.json"),
        "manifest_sha256": sha(PRODUCER / "manifest.json"),
        "pre_run_gate_sha256": sha(PRE / "gate.json"),
        "all_raw_files_hash_checked": len(result["raw_files"]),
        "runs": rows,
        "cover_found": False,
        "search_reruns": 0,
        "sequence_evidence": "Audited sequential runner plus result-before-next-parameters mtimes",
        "scope": (
            "Three bounded UNKNOWN restricted recipe outcomes; "
            "no feasibility or nonexistence conclusion"
        ),
    }
    (HERE / "postcheck.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "runs": 3,
                "search_reruns": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
