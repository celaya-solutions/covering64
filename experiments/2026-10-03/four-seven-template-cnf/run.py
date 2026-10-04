# Document:    Bounded Restricted SAT and Independent DRAT Checks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run audited CNFs with native and hard wall limits, file caps, and separate proof checks."""

import hashlib
import itertools
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INDEPENDENT = HERE.parent / "four-seven-template-cnf-independent"
OUTPUT = ROOT / "experiments/scratch/four-seven-template-drat-v1.0.0"
SECONDS = 300
MAX_FILE = 512 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def file_limit():
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE, MAX_FILE))


def bounded(command, prefix):
    began = time.time()
    forced = False
    with (
        prefix.with_suffix(".stdout.log").open("w") as stdout,
        prefix.with_suffix(".stderr.log").open("w") as stderr,
    ):
        process = subprocess.Popen(
            command, cwd=ROOT, stdout=stdout, stderr=stderr, preexec_fn=file_limit
        )
        try:
            code = process.wait(timeout=SECONDS + 30)
        except subprocess.TimeoutExpired:
            forced = True
            process.terminate()
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                code = process.wait(timeout=5)
    return {
        "command": command,
        "exit": code,
        "elapsed_seconds": time.time() - began,
        "started_unix": began,
        "forced_termination": forced,
        "native_time_limit_seconds": SECONDS,
        "hard_wait_seconds": SECONDS + 30,
        "maximum_file_bytes": MAX_FILE,
        "stdout_sha256": sha(prefix.with_suffix(".stdout.log")),
        "stderr_sha256": sha(prefix.with_suffix(".stderr.log")),
    }


def candidate(folder):
    text = (folder / "solution.sol").read_text()
    assignment = {}
    for line in text.splitlines():
        if line.startswith("v "):
            for token in line[2:].split():
                literal = int(token)
                if literal:
                    require(
                        abs(literal) not in assignment or assignment[abs(literal)] == (literal > 0),
                        "inconsistent SAT assignment",
                    )
                    assignment[abs(literal)] = literal > 0
    require(all(i in assignment for i in range(1, 4369)), "missing block assignments")
    blocks = [b for i, b in enumerate(itertools.combinations(range(1, 17), 5), 1) if assignment[i]]
    require(len(blocks) == 64, "SAT candidate has wrong block count")
    witness = folder / "candidate.txt"
    witness.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
    checks = []
    for label, prefix in [
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", [sys.executable, "scripts/check_cover.py"]),
    ]:
        command = prefix + [str(witness), "--expected-blocks", "64"]
        p = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False
        )
        (folder / (label + "-stdout.json")).write_text(p.stdout)
        (folder / (label + "-stderr.txt")).write_text(p.stderr)
        require(
            p.returncode == 0 and json.loads(p.stdout)["valid"] is True, "candidate failed verifier"
        )
        checks.append(
            {"command": command, "exit": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
        )
    return {"path": str(witness.relative_to(ROOT)), "sha256": sha(witness), "checks": checks}


def run(meta, solver, checker, seed):
    folder = OUTPUT / meta["case"]
    folder.mkdir()
    cnf = ROOT / meta["cnf"]
    require(sha(cnf) == meta["cnf_sha256"], "audited CNF changed")
    proof = folder / "proof.drat"
    command = [
        str(solver),
        "--no-binary",
        f"--seed={seed}",
        "-t",
        str(SECONDS),
        "-w",
        str(folder / "solution.sol"),
        str(cnf),
        str(proof),
    ]
    save(
        folder / "launch.json",
        {
            "case": meta["case"],
            "seed": seed,
            "command": command,
            "cnf_sha256": sha(cnf),
            "solver_sha256": sha(solver),
            "checker_sha256": sha(checker),
        },
    )
    print(
        json.dumps(
            {
                "event": "launch",
                "case": meta["case"],
                "seed": seed,
                "solver_seconds": SECONDS,
                "file_cap_bytes": MAX_FILE,
            }
        ),
        flush=True,
    )
    solved = bounded(command, folder / "solver")
    log = (folder / "solver.stdout.log").read_text()
    checked = None
    witness = None
    if solved["exit"] == 20 and not solved["forced_termination"]:
        require("s UNSATISFIABLE" in log.splitlines() and proof.exists(), "missing UNSAT output")
        checked = bounded(
            [str(checker), str(cnf), str(proof), "-t", str(SECONDS)], folder / "checker"
        )
        checked["verified"] = (
            checked["exit"] == 0
            and not checked["forced_termination"]
            and "s VERIFIED" in (folder / "checker.stdout.log").read_text().splitlines()
        )
        status = "UNSAT_DRAT_VERIFIED" if checked["verified"] else "UNSAT_UNCHECKED"
    elif solved["exit"] == 10 and not solved["forced_termination"]:
        require("s SATISFIABLE" in log.splitlines(), "missing SAT output")
        witness = candidate(folder)
        status = "SAT_CANDIDATE_VERIFIED"
    else:
        status = "INCONCLUSIVE"
    result = {
        "case": meta["case"],
        "hub_case": meta["hub_case"],
        "fixed_ids": meta["fixed_ids"],
        "status": status,
        "seed": seed,
        "cnf_sha256": sha(cnf),
        "solver": solved,
        "proof": str(proof.relative_to(ROOT)) if proof.exists() else None,
        "proof_sha256": sha(proof) if proof.exists() else None,
        "proof_bytes": proof.stat().st_size if proof.exists() else 0,
        "checker": checked,
        "witness": witness,
        "scope": "Only this audited restricted CP projection. Incomplete or unchecked proofs "
        "make no exclusion; any combined first-link exclusion needs the other five proofs.",
    }
    save(folder / "result.json", result)
    print(
        json.dumps(
            {
                "event": "completed",
                "case": meta["case"],
                "status": status,
                "solver_seconds": solved["elapsed_seconds"],
                "proof_bytes": result["proof_bytes"],
            }
        ),
        flush=True,
    )
    return result


def main():
    require(not OUTPUT.exists(), "new proof campaign required")
    manifest = json.loads((HERE / "manifest.json").read_text())
    audit = json.loads((INDEPENDENT / "audit.json").read_text())
    tools = json.loads((HERE / "tools.json").read_text())
    require(
        audit["passed"] is True and audit["manifest_sha256"] == sha(HERE / "manifest.json"),
        "CNF translation audit incomplete",
    )
    require(
        audit["checker_sha256"] == sha(INDEPENDENT / "check.py"), "CNF audit source changed"
    )
    require(
        tools["passed"] is True and tools["source_sha256"] == sha(HERE / "prepare_tools.py"),
        "tool controls changed",
    )
    paths = {}
    for tool in tools["tools"]:
        path = ROOT / tool["binary"]
        require(sha(path) == tool["binary_sha256"], "proof tool binary changed")
        paths[tool["name"]] = path
    OUTPUT.mkdir(parents=True)
    for name in [
        "run.py",
        "build.py",
        "manifest.json",
        "prepare_tools.py",
        "tools.json",
    ]:
        (OUTPUT / name).write_bytes((HERE / name).read_bytes())
    (OUTPUT / "independent-check.py").write_bytes((INDEPENDENT / "check.py").read_bytes())
    (OUTPUT / "independent-audit.json").write_bytes((INDEPENDENT / "audit.json").read_bytes())
    results = []
    for meta, seed in zip(manifest["cases"], [2026103901, 2026103902], strict=True):
        results.append(run(meta, paths["cadical"], paths["drat-trim"], seed))
        save(OUTPUT / "results.json", results)
        save(HERE / "proof-results.json", results)
        if results[-1]["witness"]:
            break


if __name__ == "__main__":
    main()
