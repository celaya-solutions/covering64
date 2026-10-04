# Document:    Pinned SAT Solver and Independent Proof Checker Provenance
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze already-built public tool revisions and verify positive/negative checker controls."""

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/proof-tools-20261003"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    records = []
    for name, revision, executable in [
        ("cadical", "c60730422e758ef1cebe7aeddf2dda31c996bf04", "build/cadical"),
        ("drat-trim", "2e3b2dc0ecf938addbd779d42877b6ed69d9a985", "drat-trim"),
    ]:
        folder = RAW / name
        current = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=folder, text=True
        ).strip()
        require(current == revision, "public source revision changed")
        subprocess.run(
            ["git", "diff", "--exit-code", "HEAD"], cwd=folder, check=True, capture_output=True
        )
        archive = RAW / (name + "-source.tar.gz")
        subprocess.run(
            ["git", "archive", "--format=tar.gz", "--output", str(archive), "HEAD"],
            cwd=folder,
            check=True,
        )
        records.append(
            {
                "name": name,
                "git_revision": revision,
                "repository": "https://github.com/"
                + ("arminbiere/cadical.git" if name == "cadical" else "marijnheule/drat-trim.git"),
                "source_archive": str(archive.relative_to(ROOT)),
                "source_archive_sha256": sha(archive),
                "binary": str((folder / executable).relative_to(ROOT)),
                "binary_sha256": sha(folder / executable),
                "build_log_sha256": sha(folder / "build.log"),
                "build_commands": ["./configure", "make -j4"]
                if name == "cadical"
                else ["make -j2"],
            }
        )
    solver = ROOT / records[0]["binary"]
    checker = ROOT / records[1]["binary"]
    controls = RAW / "controls"
    controls.mkdir(exist_ok=True)
    cnf = controls / "unsat.cnf"
    cnf.write_text("p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0\n")
    proof = controls / "unsat.drat"
    command = [str(solver), "--no-binary", "--seed=2026103901", "-t", "5", str(cnf), str(proof)]
    solve = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
    (controls / "solver.log").write_text(solve.stdout + solve.stderr)
    require(solve.returncode == 20 and "s UNSATISFIABLE" in solve.stdout, "solver control failed")
    empty = controls / "empty.drat"
    empty.write_text("")
    sat = controls / "sat.cnf"
    sat.write_text("p cnf 2 1\n1 2 0\n")
    checks = []
    for name, formula, trace, valid in [
        ("valid", cnf, proof, True),
        ("empty-proof", cnf, empty, False),
        ("wrong-satisfiable-model", sat, proof, False),
    ]:
        argv = [str(checker), str(formula), str(trace), "-t", "5"]
        process = subprocess.run(argv, capture_output=True, text=True, timeout=10, check=False)
        passed = process.returncode == 0 and "s VERIFIED" in process.stdout.splitlines()
        require(passed == valid, "checker control has wrong outcome")
        log = controls / (name + ".log")
        log.write_text(process.stdout + process.stderr)
        checks.append(
            {
                "name": name,
                "command": argv,
                "exit": process.returncode,
                "verified": passed,
                "log_sha256": sha(log),
                "stdout": process.stdout,
                "stderr": process.stderr,
            }
        )
    report = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "tools": records,
        "solver_version": subprocess.check_output([str(solver), "--version"], text=True).strip(),
        "solver_build": subprocess.check_output([str(solver), "--build"], text=True),
        "control_solver_command": command,
        "controls": checks,
        "scope": "Pinned public tools and tiny positive/negative controls only; "
        "no research proof yet.",
    }
    for target in [HERE / "tools.json", RAW / "tools.json"]:
        target.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {"passed": True, "solver_version": report["solver_version"], "controls": len(checks)}
        )
    )


if __name__ == "__main__":
    main()
