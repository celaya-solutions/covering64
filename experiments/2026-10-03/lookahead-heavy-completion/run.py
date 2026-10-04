# Document:    Bounded Hub-Unrestricted Fixed-Heavy Completion Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b391da36376b82c2d318887efddd052730e895d5bd819ed264255ca0cfcc50c4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INDEPENDENT = HERE.parent / "native-ten-hole-completion-independent"
OUTPUT = ROOT / "experiments/scratch/lookahead-heavy-completion-pilot-v1.0.0"
SEED = 2026104401


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def child():
    manifest = json.loads((OUTPUT / "manifest.json").read_text())
    model_path = ROOT / manifest["model"]
    require(sha(model_path) == manifest["model_sha256"], "model changed")
    model = cp_model.CpModel()
    model.proto.parse_text_format(model_path.read_text())
    require(not model.validate(), "invalid model")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = SEED
    solver.parameters.log_search_progress = True
    (OUTPUT / "parameters.pbtxt").write_text(str(solver.parameters))
    began = time.time()
    status = solver.solve(model)
    elapsed = time.time() - began
    response = solver.response_proto
    (OUTPUT / "response.pbtxt").write_text(str(response))
    witness = None
    if status in [cp_model.FEASIBLE, cp_model.OPTIMAL]:
        blocks = sorted(manifest["heavy_blocks"] + [
            b for i, b in enumerate(manifest["ordinary_blocks"]) if response.solution[i] == 1
        ])
        require(len(blocks) == 64, "wrong candidate block count")
        witness = OUTPUT / "candidate.txt"
        witness.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
    save(
        OUTPUT / "child-result.json",
        {
            "status": solver.status_name(status),
            "elapsed_seconds": elapsed,
            "native_wall_time": solver.wall_time,
            "response_sha256": sha(OUTPUT / "response.pbtxt"),
            "witness": str(witness.relative_to(ROOT)) if witness else None,
        },
    )


def main():
    require(not OUTPUT.exists(), "fresh pilot directory required")
    manifest = json.loads((HERE / "manifest.json").read_text())
    audit = json.loads((INDEPENDENT / "audit.json").read_text())
    require(
        audit["passed"] and audit["model_sha256"] == manifest["model_sha256"]
        and audit["witness_sha256"] == manifest["source_seed_sha256"],
        "gate incomplete",
    )
    require(audit["checker_sha256"] == sha(INDEPENDENT / "check.py"), "gate checker changed")
    require(manifest["builder_sha256"] == sha(HERE / "build.py"), "builder changed")
    require(sha(ROOT / manifest["model"]) == manifest["model_sha256"], "prepared model changed")
    OUTPUT.mkdir(parents=True)
    for name in [
        "run.py",
        "build.py",
        "manifest.json",
    ]:
        (OUTPUT / name).write_bytes((HERE / name).read_bytes())
    (OUTPUT / "independent-check.py").write_bytes((INDEPENDENT / "check.py").read_bytes())
    (OUTPUT / "independent-audit.json").write_bytes((INDEPENDENT / "audit.json").read_bytes())
    command = [sys.executable, str(HERE / "run.py"), "--child"]
    began = time.time()
    forced = False
    with (OUTPUT / "stdout.log").open("w") as stdout, (OUTPUT / "stderr.log").open("w") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        try:
            code = process.wait(timeout=90)
        except subprocess.TimeoutExpired:
            forced = True
            process.terminate()
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                code = process.wait(timeout=5)
    saved = OUTPUT / "child-result.json"
    result = (
        json.loads(saved.read_text())
        if saved.exists()
        else {"status": "INTERRUPTED", "witness": None}
    )
    checks = []
    if result["witness"]:
        for label, prefix in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", [sys.executable, "scripts/check_cover.py"]),
        ]:
            argv = prefix + [str(ROOT / result["witness"]), "--expected-blocks", "64"]
            checked = subprocess.run(
                argv, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False
            )
            (OUTPUT / (label + ".json")).write_text(checked.stdout)
            require(
                checked.returncode == 0 and json.loads(checked.stdout)["valid"] is True,
                "candidate failed verifier",
            )
            checks.append({"command": argv, "exit": checked.returncode, "stdout": checked.stdout})
    result.update(
        command=command,
        exit=code,
        forced_termination=forced,
        wrapper_elapsed_seconds=time.time() - began,
        seed=SEED,
        native_time_limit_seconds=60,
        hard_wait_seconds=90,
        workers=1,
        ortools_version=ortools_version,
        model_sha256=manifest["model_sha256"],
        manifest_sha256=sha(HERE / "manifest.json"),
        runner_sha256=sha(HERE / "run.py"),
        gate_sha256=sha(INDEPENDENT / "audit.json"),
        stdout_sha256=sha(OUTPUT / "stdout.log"),
        stderr_sha256=sha(OUTPUT / "stderr.log"),
        witness_checks=checks,
        scope="Only this fixed 28-heavy-block completion. "
        "UNKNOWN or unchecked CP-SAT INFEASIBLE makes no exclusion.",
    )
    save(OUTPUT / "result.json", result)
    save(HERE / "pilot-result.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "seconds": result["wrapper_elapsed_seconds"],
                "witness": result["witness"],
            }
        )
    )


if __name__ == "__main__":
    child() if "--child" in sys.argv else main()
