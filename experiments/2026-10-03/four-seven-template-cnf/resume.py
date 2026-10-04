# Document:    Recover Routed SAT Status and Continue Frozen Proof Campaign
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check the saved first proof after the stdout guard failed, then launch only the second case."""

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("bounded_drat_runner", HERE / "run.py")
RUN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUN)


def main():
    manifest = json.loads((RUN.OUTPUT / "manifest.json").read_text())
    audit = json.loads((RUN.OUTPUT / "independent-audit.json").read_text())
    RUN.require(
        audit["passed"] is True
        and RUN.sha(RUN.OUTPUT / "manifest.json") == audit["manifest_sha256"],
        "saved CNF audit chain changed",
    )
    tools = json.loads((RUN.OUTPUT / "tools.json").read_text())
    paths = {tool["name"]: RUN.ROOT / tool["binary"] for tool in tools["tools"]}
    for tool in tools["tools"]:
        RUN.require(RUN.sha(paths[tool["name"]]) == tool["binary_sha256"], "tool binary changed")
    meta = manifest["cases"][0]
    folder = RUN.OUTPUT / meta["case"]
    RUN.require(
        not (folder / "result.json").exists() and not (folder / "checker.stdout.log").exists(),
        "refusing repeated recovery",
    )
    cnf, proof = RUN.ROOT / meta["cnf"], folder / "proof.drat"
    RUN.require(RUN.sha(cnf) == meta["cnf_sha256"] and proof.exists(), "raw proof input changed")
    log = (folder / "solver.stdout.log").read_text()
    RUN.require(
        "s UNSATISFIABLE" in (folder / "solution.sol").read_text().splitlines()
        and "c exit 20" in log.splitlines(),
        "saved solver did not report UNSAT",
    )
    native_real = re.search(r"total real time since initialization:\s+([0-9.]+)", log)
    RUN.require(native_real is not None, "missing native wall time")
    launch = json.loads((folder / "launch.json").read_text())
    solved = {
        "command": launch["command"],
        "exit": 20,
        "elapsed_seconds": None,
        "started_unix": None,
        "native_reported_real_seconds": float(native_real.group(1)),
        "forced_termination": False,
        "native_time_limit_seconds": RUN.SECONDS,
        "hard_wait_seconds": RUN.SECONDS + 30,
        "maximum_file_bytes": RUN.MAX_FILE,
        "stdout_sha256": RUN.sha(folder / "solver.stdout.log"),
        "stderr_sha256": RUN.sha(folder / "solver.stderr.log"),
        "recovery": "Original wrapper expected status on stdout; -w placed it in solution.sol. "
        "No solver rerun. Python timing receipt was not saved before that guard, "
        "so those two timing fields are unknown; native rounded time is retained.",
    }
    RUN.save(folder / "solver-result.json", solved)
    (RUN.OUTPUT / "run-resumed.py").write_bytes((HERE / "run.py").read_bytes())
    (RUN.OUTPUT / "resume.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {"event": "recover_check", "case": meta["case"], "proof_bytes": proof.stat().st_size}
        ),
        flush=True,
    )
    checked = RUN.bounded(
        [str(paths["drat-trim"]), str(cnf), str(proof), "-t", str(RUN.SECONDS)], folder / "checker"
    )
    checked["verified"] = (
        checked["exit"] == 0
        and not checked["forced_termination"]
        and "s VERIFIED" in (folder / "checker.stdout.log").read_text().splitlines()
    )
    first = {
        "case": meta["case"],
        "hub_case": meta["hub_case"],
        "fixed_ids": meta["fixed_ids"],
        "status": "UNSAT_DRAT_VERIFIED" if checked["verified"] else "UNSAT_UNCHECKED",
        "seed": launch["seed"],
        "cnf_sha256": RUN.sha(cnf),
        "solver": solved,
        "proof": str(proof.relative_to(RUN.ROOT)),
        "proof_sha256": RUN.sha(proof),
        "proof_bytes": proof.stat().st_size,
        "checker": checked,
        "witness": None,
        "scope": "Only this audited restricted CP projection; combining a complete first-link "
        "exclusion still requires its five other checked hub cases.",
    }
    RUN.save(folder / "result.json", first)
    results = [first]
    RUN.save(RUN.OUTPUT / "results.json", results)
    RUN.save(HERE / "proof-results.json", results)
    print(
        json.dumps(
            {
                "event": "recovered",
                "case": meta["case"],
                "status": first["status"],
                "checker_seconds": checked["elapsed_seconds"],
            }
        ),
        flush=True,
    )
    if not checked["verified"]:
        return
    results.append(RUN.run(manifest["cases"][1], paths["cadical"], paths["drat-trim"], 2026103902))
    RUN.save(RUN.OUTPUT / "results.json", results)
    RUN.save(HERE / "proof-results.json", results)


if __name__ == "__main__":
    main()
