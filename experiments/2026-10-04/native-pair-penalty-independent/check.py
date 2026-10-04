# Document:    Independent Native Pair-Penalty Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "native-pair-penalty"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    manifest = read(SOURCE / "manifest.json")
    assert sha(SOURCE / "manifest.json") == (
        "5589079bf03991d4eca468d5f45444f11427e9ce12e53946bdbd55a6d7745fe2"
    )
    for relative, digest in (manifest["input_files"] | manifest["raw_files"]).items():
        assert sha(ROOT / relative) == digest
    assert sha(SOURCE / "search.cpp") == manifest["source_sha256"]
    assert sha(SOURCE / "run.py") == manifest["runner_sha256"]
    assert sha(ROOT / manifest["binary_path"]) == manifest["binary_sha256"]
    assert sha(SOURCE / "controls.json") == manifest["controls_sha256"]
    assert sha(SOURCE / "native_core_base.cpp") == sha(
        HERE.parent / "native-core-cap-escape-v2/search.cpp"
    )
    for name in ("heuristic_search.cpp", "cores.hpp"):
        assert sha(SOURCE / name) == sha(HERE.parent / "native-core-cap-escape-v2" / name)
    prior = read(HERE.parent / "native-core-cap-escape-independent/gate.json")
    assert prior["passed"]
    proof = read(HERE.parent / "pair-local-necessary-cuts-independent/audit.json")
    assert proof["passed"]
    controls = read(HERE / "control.json")
    assert controls["passed"] and controls["optimizer_calls"] == 0
    assert controls["direct_recounts"] == 901
    assert controls["commits"] > 200 and controls["rollbacks"] > 200
    assert controls["intersection_cases"] == [40] * 5
    assert manifest["budget"] == {
        "runs": 2, "seconds_per_run": 60, "seeds": [2026104401, 2026104402],
        "watchdog_seconds": 75, "termination_grace_seconds": 5,
        "simultaneous_processes": 1, "relaunch": False,
    }
    assert manifest["energy"] == "20H + 5D3 + D4 + 160F"
    assert manifest["mutable_slots"] == 64 and manifest["eligible_blocks"] == 4368
    assert not manifest["fixed_point_degrees"] and not manifest["hard_pair_floor"]
    assert manifest["row_counts"] == {"D3": 1680, "D4": 10920}
    metrics = subprocess.run(
        [str(ROOT / manifest["binary_path"]), "--metrics", str(ROOT / manifest["hint_path"])],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert not metrics.stderr and json.loads(metrics.stdout) == manifest["hint_metrics"]
    assert manifest["hint_metrics"] == {
        "D3": 4, "D4": 0, "core_overlaps": [2, 2, 0], "energy": 140,
        "forbidden": False, "holes": 6, "pair_min": 5,
    }
    report = {
        "passed": True, "optimizer_calls": 0, "checker_sha256": sha(__file__),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "source_sha256": manifest["source_sha256"],
        "runner_sha256": manifest["runner_sha256"],
        "binary_sha256": manifest["binary_sha256"],
        "independent_control_source_sha256": sha(HERE / "control.cpp"),
        "independent_control_sha256": sha(HERE / "control.json"),
        "inherited_core_gate_sha256": sha(
            HERE.parent / "native-core-cap-escape-independent/gate.json"
        ),
        "pair_cut_proof_sha256": sha(
            HERE.parent / "pair-local-necessary-cuts-independent/audit.json"
        ),
        "sanitizers": ["address", "undefined"], "controls": controls,
        "source_review": "Affected pair union includes unchanged pair counts; all changed "
        "triple/quad row-pairs are included. Rejected moves reverse all state updates. "
        "Raw/profile best, soft-score best, zero-deficit best and current are distinct. "
        "All normal/zero/interrupted exits save their status and present records. "
        "One uniform draw per proposal changes the previous seeded stream intentionally.",
        "scope": "Two declared construction runs only. Pair-zero best may be absent. "
        "The guidance is incomplete and fails four necessary single-triple rows. Only "
        "three named core caps are enforced; no all-relabel eligibility claim.",
    }
    (HERE / "gate.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
