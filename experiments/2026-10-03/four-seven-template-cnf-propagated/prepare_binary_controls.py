# Document:    Pinned Binary DRAT Positive and Negative Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      f56434119b6155f6fffdcea8c4ecad03eda694d98e5c77adbf7146ead7b81c4d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import resource
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOL_DIR = HERE.parent / "four-seven-template-cnf"
RAW = ROOT / "experiments/scratch/four-seven-template-binary-controls-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (512 * 1024 * 1024,) * 2)


def run(command, prefix):
    p = subprocess.run(command, capture_output=True, timeout=15, preexec_fn=limits, check=False)
    prefix.with_suffix(".stdout.log").write_bytes(p.stdout)
    prefix.with_suffix(".stderr.log").write_bytes(p.stderr)
    return {
        "command": command,
        "exit": p.returncode,
        "stdout_sha256": sha(prefix.with_suffix(".stdout.log")),
        "stderr_sha256": sha(prefix.with_suffix(".stderr.log")),
        "verified": "s VERIFIED" in p.stdout.decode().splitlines(),
    }


def main():
    require(not RAW.exists(), "new binary controls required")
    tools = json.loads((TOOL_DIR / "tools.json").read_text())
    require(tools["passed"], "prior tool checks failed")
    paths = {}
    for t in tools["tools"]:
        paths[t["name"]] = ROOT / t["binary"]
        require(sha(paths[t["name"]]) == t["binary_sha256"], "binary changed")
    RAW.mkdir(parents=True)
    (RAW / "unsat.cnf").write_text("p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0\n")
    (RAW / "sat.cnf").write_text("p cnf 2 1\n1 2 0\n")
    (RAW / "empty.drat").write_bytes(b"")
    solver = run(
        [
            str(paths["cadical"]),
            "--seed=2026104001",
            "-t",
            "5",
            str(RAW / "unsat.cnf"),
            str(RAW / "unsat.drat"),
        ],
        RAW / "solver",
    )
    require(
        solver["exit"] == 20 and (RAW / "unsat.drat").stat().st_size > 0, "binary solver control"
    )
    checks = []
    for name, cnf, proof, expected in [
        ("valid", "unsat.cnf", "unsat.drat", True),
        ("empty", "unsat.cnf", "empty.drat", False),
        ("wrong-model", "sat.cnf", "unsat.drat", False),
    ]:
        result = run(
            [str(paths["drat-trim"]), str(RAW / cnf), str(RAW / proof), "-i", "-t", "5"], RAW / name
        )
        require((result["exit"] == 0 and result["verified"]) == expected, "binary checker control")
        checks.append({"name": name, "expected": expected, **result})
    output = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "tools_sha256": sha(TOOL_DIR / "tools.json"),
        "solver": solver,
        "proof_sha256": sha(RAW / "unsat.drat"),
        "proof_bytes": (RAW / "unsat.drat").stat().st_size,
        "checks": checks,
        "scope": "Tiny binary proof controls only; no research solve.",
    }
    (HERE / "binary-controls.json").write_text(json.dumps(output, indent=2) + "\n")
    (RAW / "prepare_binary_controls.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({"passed": True, "proof_bytes": output["proof_bytes"], "checks": len(checks)}))


if __name__ == "__main__":
    main()
