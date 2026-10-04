# Document:    Hard Top-Two Runner Rejection Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      273b6114a6a94a6fa9e692dbff542940eb5de9a674a7f3a44e7360a0d3e8d00e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exercise rejection paths without calling Solve or writing a candidate hint."""

import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = HERE / "runner-controls.json"
    if output.exists():
        raise SystemExit("receipt exists")
    spec = importlib.util.spec_from_file_location("hard_runner", HERE / "execute.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    require = runner.require
    require(not runner.RUN.exists(), "unexpected existing runtime directory")
    manifest = json.loads((HERE / "manifest.json").read_text())
    model = cp_model.CpModel()
    require(model.proto.parse_text_format((ROOT / manifest["model_path"]).read_text()), "parse")
    guide = json.loads((ROOT / manifest["guidance_path"]).read_text())
    blocks = [
        tuple(map(int, line.split()))
        for line in (ROOT / guide["candidate_path"]).read_text().splitlines()
    ]
    pairs = tuple(itertools.combinations(range(1, 17), 2))
    triples = tuple(itertools.combinations(range(1, 17), 3))
    counts = {
        size: Counter(q for block in blocks for q in itertools.combinations(block, size))
        for size in (2, 3)
    }
    z_values, y_values = [], []
    for pair in pairs:
        values = [counts[3][tuple(sorted((*pair, a)))] for a in range(1, 17) if a not in pair]
        z = sorted(values, reverse=True)[1]
        z_values.append(z)
        y_values.extend(max(0, value - z) for value in values)
    vector = guide["values"] + [counts[2][q] for q in pairs] + [counts[3][q] for q in triples]
    vector += [int(counts[3][q] == 0) for q in triples] + z_values + y_values
    require(len(vector) == 7408, "negative vector size")
    try:
        runner.check_vector(model, vector)
    except ValueError as error:
        vector_error = str(error)
        require(vector_error.startswith("linear row violation"), "unexpected H49 rejection")
    else:
        raise ValueError("infeasible H49 extension accepted")
    broken = vector.copy()
    broken[0] = 2
    try:
        runner.check_vector(model, broken)
    except ValueError as error:
        domain_error = str(error)
        require(domain_error == "variable domain violation 0", "unexpected domain rejection")
    else:
        raise ValueError("damaged domain accepted")
    refusals = []
    with tempfile.TemporaryDirectory(prefix="hard-runner-controls-") as temporary:
        tmp = Path(temporary)
        for name, gate in (
            ("no_go", {"passed": False, "decision": "NO_GO"}),
            ("wrong_bindings", {"passed": True, "decision": "GO"}),
        ):
            path = tmp / f"{name}.json"
            path.write_text(json.dumps(gate))
            run = subprocess.run(
                [
                    sys.executable,
                    str(HERE / "execute.py"),
                    "--execute",
                    "--gate",
                    str(path),
                    "--gate-sha256",
                    sha(path),
                ],
                capture_output=True,
                text=True,
            )
            require(run.returncode != 0 and not runner.RUN.exists(), "unsafe gate acceptance")
            marker = "independent GO required" if name == "no_go" else "gate binding mismatch"
            require(marker in run.stderr, "unexpected gate refusal")
            refusals.append({"name": name, "returncode": run.returncode, "marker": marker})
        old_run, old_argv = runner.RUN, sys.argv
        runner.RUN = tmp
        sys.argv = ["execute.py", "--execute", "--gate", str(path), "--gate-sha256", sha(path)]
        try:
            runner.main()
        except ValueError as error:
            require(str(error) == "run already exists", "unexpected relaunch rejection")
        else:
            raise ValueError("existing directory accepted")
        finally:
            runner.RUN, sys.argv = old_run, old_argv
    receipt = {
        "passed": True,
        "optimizer_calls": 0,
        "hints_written": 0,
        "source_sha256": sha(Path(__file__)),
        "runner_sha256": sha(HERE / "execute.py"),
        "runner_manifest_sha256": sha(HERE / "runner-manifest.json"),
        "model_sha256": manifest["model_sha256"],
        "H49_extension_rejected": vector_error,
        "damaged_domain_rejected": domain_error,
        "gate_refusals": refusals,
        "relaunch_rejected": True,
        "runtime_directory_absent": not runner.RUN.exists(),
        "scope": "Negative controls only; no feasible hard assignment available.",
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "optimizer_calls": 0, "receipt_sha256": sha(output)}))


if __name__ == "__main__":
    main()
