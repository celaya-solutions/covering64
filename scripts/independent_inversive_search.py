#!/usr/bin/env python3
# Document:    Inversive Circle and Extended-Line Construction Probe
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      53f0957777df34785671573777b8043f22db4ae90028527897fe7a6adad4533a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Search only the 288-block inversive pool; solver status is not a theorem."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import subprocess
import sys
import time
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, verify_cover, write_blocks

DOMAIN_SOURCE = (Path(__file__).resolve().parents[1] / "experiments" / "2026-10-03"
                 / "independent-geometry" / "check_inversive.py")


def inversive_domain():
    spec = importlib.util.spec_from_file_location("independent_inversive_geometry", DOMAIN_SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load independent domain constructor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    circles, lines = module.construct()
    module.audit(circles, lines)
    pool = sorted(set(circles).union(
        tuple(sorted(line + (point,))) for line in lines
        for point in range(1, 17) if point not in line
    ))
    if len(pool) != 288:
        raise RuntimeError("inversive pool has wrong size")
    return pool


def build_model():
    """All 4368 lexicographic variables; only the 288-block domain is allowed."""
    universe = Universe.build()
    allowed = set(inversive_domain())
    if not allowed.issubset(universe.blocks):
        raise RuntimeError("domain contains a block outside the full universe")
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"block_{i}") for i in range(len(universe.blocks))]
    model.add(sum(selected) == 64)
    for block, var in zip(universe.blocks, selected, strict=True):
        if block not in allowed:
            model.add(var == 0)
    for containing in universe.containing:
        model.add(sum(selected[i] for i in containing) >= 1)
    return universe, model, selected


def run(out, seconds, seed):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be finite and positive")
    out.mkdir(parents=True, exist_ok=False)
    source_bytes = Path(__file__).read_bytes()
    domain_bytes = DOMAIN_SOURCE.read_bytes()
    (out / "source.py").write_bytes(source_bytes)
    (out / "domain_source.py").write_bytes(domain_bytes)
    pool = inversive_domain()
    pool_text = json.dumps(pool, sort_keys=True, separators=(",", ":")) + "\n"
    (out / "domain.json").write_text(pool_text)
    universe, model, selected = build_model()
    model.export_to_file(str(out / "model.pbtxt"))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    started = time.time()
    with (out / "solver.log").open("w") as log:
        solver.log_callback = lambda text: (log.write(text + "\n"), log.flush())
        status = solver.solve(model)
    record = {
        "scope": "restricted 288-block circle/extended-line pool, not an unrestricted reduction",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "seed": seed,
        "budget_seconds": seconds,
        "workers": 1,
        "python": platform.python_version(),
        "ortools": ortools.__version__,
        "started_unix": started,
        "elapsed_seconds": time.time() - started,
        "status": solver.status_name(status),
        "stats": solver.response_stats(),
        "block_variables": len(selected),
        "allowed_blocks": len(pool),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "domain_source_sha256": hashlib.sha256(domain_bytes).hexdigest(),
        "domain_sha256": hashlib.sha256(pool_text.encode()).hexdigest(),
        "model_sha256": hashlib.sha256((out / "model.pbtxt").read_bytes()).hexdigest(),
    }
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        blocks = [block for block, var in zip(universe.blocks, selected, strict=True)
                  if solver.value(var)]
        witness = out / "witness.txt"
        write_blocks(witness, blocks)
        record["witness_sha256"] = hashlib.sha256(witness.read_bytes()).hexdigest()
        record["domain_check"] = len(blocks) == 64 and set(blocks).issubset(pool)
        record["package_verifier"] = verify_cover(blocks)
        check = subprocess.run(
            [sys.executable, "-I", "scripts/check_cover.py", str(witness),
             "--expected-blocks", "64"], capture_output=True, text=True, check=False,
        )
        record["standalone_verifier"] = {
            "exit_code": check.returncode, "report": json.loads(check.stdout),
        }
        if (not record["package_verifier"]["valid"] or check.returncode != 0
                or not record["domain_check"]):
            raise RuntimeError("solver witness failed a covering or domain check")
    (out / "result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: record[key] for key in ("status", "elapsed_seconds", "seed")}))
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--seed", type=int, default=640304)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    run(args.out, args.seconds, args.seed)
