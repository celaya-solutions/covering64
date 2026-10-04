# Document:    Bounded Fixed-Link and Hub-Case Template CP Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run two audited fixed-link and hub-case CP models sequentially with frozen budgets."""

import hashlib
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = ROOT / "experiments/scratch/four-seven-template-cp-restricted-pilots-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def run(meta, seed):
    case = meta["case"]
    folder = OUTPUT / case
    folder.mkdir()
    model_path = ROOT / meta["model"]
    require(sha(model_path) == meta["model_sha256"], "frozen model changed")
    model = cp_model.CpModel()
    model.proto.parse_text_format(model_path.read_text())
    require(not model.validate(), "invalid frozen model")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 600
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    solver.parameters.log_to_response = True
    parameters = folder / "parameters.pbtxt"
    parameters.write_text(str(solver.parameters))
    before = time.time()
    print(
        json.dumps({"event": "launch", "case": case, "seed": seed, "seconds": 600, "workers": 8}),
        flush=True,
    )
    with (folder / "solver.log").open("w") as log:

        def emit(line):
            log.write(line + "\n")
            log.flush()

        solver.log_callback = emit
        status = solver.solve(model)
    response = solver.response_proto
    response_path = folder / "response.pbtxt"
    response_path.write_text(str(response))
    checks = []
    witness = None
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        require(len(response.solution) == len(model.proto.variables), "partial solution")
        witness = folder / "candidate.txt"
        blocks = list(itertools.combinations(range(1, 17), 5))
        chosen = [block for i, block in enumerate(blocks) if response.solution[i] == 1]
        require(len(chosen) == 64, "wrong solution block count")
        witness.write_text("".join(" ".join(map(str, b)) + "\n" for b in chosen))
        for label, prefix in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", [sys.executable, "scripts/check_cover.py"]),
        ]:
            argv = prefix + [str(witness), "--expected-blocks", "64"]
            proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, check=False)
            (folder / (label + "-stdout.json")).write_text(proc.stdout)
            (folder / (label + "-stderr.txt")).write_text(proc.stderr)
            checked = json.loads(proc.stdout)
            require(proc.returncode == 0 and checked["valid"] is True, "candidate rejected")
            checks.append(
                {
                    "command": argv,
                    "exit": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                }
            )
    require(status != cp_model.MODEL_INVALID, "solver rejected model")
    result = {
        "case": case,
        "hub_case": meta["hub_case"],
        "fixed_ids": meta["fixed_ids"],
        "source_base_sha256": meta["source_base_sha256"],
        "status": solver.status_name(status),
        "seed": seed,
        "requested_seconds": 600,
        "workers": 8,
        "wall_seconds": solver.wall_time,
        "elapsed_seconds": time.time() - before,
        "started_unix": before,
        "branches": solver.num_branches,
        "conflicts": solver.num_conflicts,
        "model_sha256": sha(model_path),
        "parameters_sha256": sha(parameters),
        "response_sha256": sha(response_path),
        "log_sha256": sha(folder / "solver.log"),
        "witness": str(witness.relative_to(ROOT)) if witness else None,
        "checks": checks,
        "scope": "A bounded solver observation. UNKNOWN and "
        "uncertified INFEASIBLE cannot establish a theorem or exclusion.",
    }
    save(folder / "result.json", result)
    print(json.dumps({"event": "completed", **result}), flush=True)
    return result


def main():
    require(not OUTPUT.exists(), "refusing to rerun an existing campaign")
    preceding = json.loads(
        (HERE.parent / "four-seven-template-cp-proposal/pilot-audit.json").read_text()
    )
    require(
        preceding["passed"] is True and preceding["pilot_count"] == 2,
        "preceding whole-branch pilot readback incomplete",
    )
    manifest = json.loads((HERE / "manifest.json").read_text())
    audit = json.loads((HERE / "independent-audit.json").read_text())
    require(
        audit["passed"] is True and sha(HERE / "manifest.json") == audit["manifest_sha256"],
        "independent audit does not bind manifest",
    )
    require(sha(HERE / "check_independent.py") == audit["checker_sha256"], "checker changed")
    OUTPUT.mkdir()
    for name in [
        "run.py",
        "build.py",
        "manifest.json",
        "check_independent.py",
        "independent-audit.json",
    ]:
        (OUTPUT / name).write_bytes((HERE / name).read_bytes())
    save(
        OUTPUT / "environment.json",
        {
            "ortools_version": ortools_version,
            "source_sha256": sha(Path(__file__)),
            "python": sys.version,
            "git_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "maximum_concurrent_cp_processes": 1,
            "workers_per_cp_process": 8,
        },
    )
    results = []
    for case, seed in [("matching-029", 2026103801), ("matching-063", 2026103802)]:
        results.append(run(next(c for c in manifest["cases"] if c["case"] == case), seed))
        save(OUTPUT / "results.json", results)
        save(HERE / "pilot-results.json", results)


if __name__ == "__main__":
    main()
