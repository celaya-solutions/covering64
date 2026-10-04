#!/usr/bin/env python3
# Document:    Folded Five-Cube Pair-Profile Construction Probe
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5188118a67bc349cdc6f2db693ca90a17a51757a54eb1281739bcd32e14c0328
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Restricted construction probe; no nonexistence theorem follows from a solver status."""

from __future__ import annotations

import argparse
import hashlib
import itertools
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


def geometry():
    """Use 1-based labels, sorted even-parity binary words of length five."""
    words = [x for x in range(32) if x.bit_count() % 2 == 0]
    edges = {
        (i + 1, j + 1)
        for i, j in itertools.combinations(range(16), 2)
        if (words[i] ^ words[j]).bit_count() == 4
    }
    triples = list(itertools.combinations(range(1, 17), 3))
    wedges = {
        t for t in triples if sum(p in edges for p in itertools.combinations(t, 2)) == 2
    }
    return words, edges, wedges


def build_model(profile=None):
    """All block variables in lexicographic order; pair geometry is a restriction."""
    universe = Universe.build()
    words, edges, wedges = geometry()
    model = cp_model.CpModel()
    selected = [model.new_bool_var(f"block_{i}") for i in range(len(universe.blocks))]
    model.add(sum(selected) == 64)
    for point in range(1, 17):
        model.add(sum(selected[i] for i, b in enumerate(universe.blocks) if point in b) == 20)
    for pair in itertools.combinations(range(1, 17), 2):
        model.add(
            sum(selected[i] for i, b in enumerate(universe.blocks) if set(pair) <= set(b))
            == 5 + int(pair in edges)
        )
    if profile is not None:
        raw = list(profile)
        if len(raw) != 80 or any(
            not isinstance(t, (list, tuple)) or len(t) != 3
            or any(type(x) is not int or not 1 <= x <= 16 for x in t)
            or tuple(t) != tuple(sorted(set(t))) for t in raw
        ):
            raise ValueError("profile must have 80 well-formed 1-based increasing triples")
        profile = {tuple(t) for t in raw}
        if len(profile) != 80 or not profile <= wedges:
            raise ValueError("profile must be 80 distinct induced paths")
        for pair in itertools.combinations(range(1, 17), 2):
            if sum(set(pair) <= set(t) for t in profile) != 1 + 3 * int(pair in edges):
                raise ValueError("wrong excess pair degrees")
    for t, containing in zip(universe.triples, universe.containing, strict=True):
        expression = sum(selected[i] for i in containing)
        if profile is not None:
            model.add(expression == 1 + int(t in profile))
        elif t in wedges:
            model.add_linear_constraint(expression, 1, 2)
        else:
            model.add(expression == 1)
    return universe, model, selected, {"words": words, "edges": sorted(edges)}


def run(out, seconds, seed, profile_seed=None):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("seconds must be finite and positive")
    out.mkdir(parents=True, exist_ok=False)
    profile = None
    if profile_seed is not None:
        from independent_clebsch_profiles import make_profile

        profile = make_profile(profile_seed)
        (out / "excess.json").write_text(json.dumps(sorted(profile), indent=2) + "\n")
    universe, model, selected, graph = build_model(profile)
    model.export_to_file(str(out / "model.pbtxt"))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    started = time.time()
    with (out / "solver.log").open("w") as log:
        solver.log_callback = lambda s: (log.write(s + "\n"), log.flush())
        status = solver.solve(model)
    record = {
        "scope": "restricted folded-five-cube pair profile, not an unrestricted reduction",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "seed": seed,
        "profile_seed": profile_seed,
        "budget_seconds": seconds,
        "workers": 1,
        "python": platform.python_version(),
        "ortools": ortools.__version__,
        "started_unix": started,
        "elapsed_seconds": time.time() - started,
        "status": solver.status_name(status),
        "stats": solver.response_stats(),
        "graph": graph,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_sha256": hashlib.sha256((out / "model.pbtxt").read_bytes()).hexdigest(),
    }
    if profile_seed is not None:
        record["profile_source_sha256"] = hashlib.sha256(
            Path(__file__).with_name("independent_clebsch_profiles.py").read_bytes()
        ).hexdigest()
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        blocks = [b for b, x in zip(universe.blocks, selected, strict=True) if solver.value(x)]
        witness = out / "witness.txt"
        write_blocks(witness, blocks)
        record["package_verifier"] = verify_cover(blocks)
        check = subprocess.run(
            [sys.executable, "-I", "scripts/check_cover.py", str(witness),
             "--expected-blocks", "64"], capture_output=True, text=True, check=False,
        )
        record["standalone_verifier"] = {"exit_code": check.returncode,
                                          "report": json.loads(check.stdout)}
        if not record["package_verifier"]["valid"] or check.returncode != 0:
            raise RuntimeError("solver witness failed an independent covering check")
    (out / "result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: record[k] for k in ("status", "elapsed_seconds", "seed", "profile_seed")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--seed", type=int, default=640301)
    parser.add_argument("--profile-seed", type=int)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("seconds must be finite and positive")
    run(args.out, args.seconds, args.seed, args.profile_seed)
