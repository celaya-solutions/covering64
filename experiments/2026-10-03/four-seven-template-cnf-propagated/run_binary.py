# Document:    Bounded Propagated Matching-063 Binary DRAT Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2a0ba7a39c452d9898554bcfa5d25e6aee20992c6bbd033be7f0a824be8dedf9
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
INDEPENDENT = HERE.parent / "four-seven-template-cnf-propagated-independent"
TOOL_DIR = HERE.parent / "four-seven-template-cnf"
OUTPUT = ROOT / "experiments/scratch/four-seven-template-propagated-binary-drat-v1.0.0"
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
    save(folder / "solver-result.json", solved)
    log = (folder / "solver.stdout.log").read_text()
    solution_path = folder / "solution.sol"
    result_lines = log.splitlines() + (
        solution_path.read_text().splitlines() if solution_path.exists() else []
    )
    checked = None
    witness = None
    if solved["exit"] == 20 and not solved["forced_termination"]:
        require("s UNSATISFIABLE" in result_lines and proof.exists(), "missing UNSAT output")
        checked = bounded(
            [str(checker), str(cnf), str(proof), "-i", "-t", str(SECONDS)], folder / "checker"
        )
        checked["verified"] = (
            checked["exit"] == 0
            and not checked["forced_termination"]
            and "s VERIFIED" in (folder / "checker.stdout.log").read_text().splitlines()
        )
        status = "UNSAT_DRAT_VERIFIED" if checked["verified"] else "UNSAT_UNCHECKED"
    elif solved["exit"] == 10 and not solved["forced_termination"]:
        require("s SATISFIABLE" in result_lines, "missing SAT output")
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
        "proof_format": "binary_drat",
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
    tool_meta = json.loads((TOOL_DIR / "tools.json").read_text())
    require(
        audit["passed"] is True and audit["manifest_sha256"] == sha(HERE / "manifest.json"),
        "independent propagation and CNF audit incomplete",
    )
    require(audit["checker_sha256"] == sha(INDEPENDENT / "check.py"), "audit source changed")
    require(manifest["builder_sha256"] == sha(HERE / "build.py"), "propagation source changed")
    require(manifest["encoder_sha256"] == sha(TOOL_DIR / "build.py"), "encoder source changed")
    require(
        tool_meta["passed"] is True
        and tool_meta["source_sha256"] == sha(TOOL_DIR / "prepare_tools.py"),
        "proof tool controls changed",
    )
    paths = {}
    for tool in tool_meta["tools"]:
        path = ROOT / tool["binary"]
        require(sha(path) == tool["binary_sha256"], "proof tool binary changed")
        paths[tool["name"]] = path
    binary = json.loads((HERE / "binary-controls.json").read_text())
    require(binary["passed"] is True, "binary proof controls incomplete")
    require(
        binary["checker_sha256"] == sha(HERE / "prepare_binary_controls.py"),
        "control source changed",
    )
    require(binary["tools_sha256"] == sha(TOOL_DIR / "tools.json"), "binary control tools changed")
    meta = next(m for m in manifest["cases"] if m["case"] == "matching-063")
    require(meta["hub_case"] == [0, 1], "wrong pilot case")
    OUTPUT.mkdir(parents=True)
    for name in [
        "run_binary.py",
        "build.py",
        "manifest.json",
        "binary-controls.json",
        "prepare_binary_controls.py",
    ]:
        (OUTPUT / name).write_bytes((HERE / name).read_bytes())
    for name in ["prepare_tools.py", "tools.json"]:
        (OUTPUT / name).write_bytes((TOOL_DIR / name).read_bytes())
    (OUTPUT / "independent-check.py").write_bytes((INDEPENDENT / "check.py").read_bytes())
    (OUTPUT / "independent-audit.json").write_bytes((INDEPENDENT / "audit.json").read_bytes())
    result = run(meta, paths["cadical"], paths["drat-trim"], 2026104001)
    save(OUTPUT / "results.json", [result])
    save(HERE / "binary-proof-results.json", [result])


if __name__ == "__main__":
    main()
