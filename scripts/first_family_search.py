# Document:    Fixed First-Family Regular Cover Search
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      25b6ea0f7fc07b04580a34924b846353c2cdad17d85439463046492ed3fdad03
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Extend a verified local first family in the normalized sevenfold-triple branch.

Point-essentiality is not required by this broader construction model. Every
full cover is checked independently. The fixed local family is on labels4..16.
"""

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover, write_blocks

G = {(4, 5), (4, 6)} | {(p, p + 1) for p in range(7, 16, 2)}
COMMON = [(1, 2, 3, *pair) for pair in sorted(G)]


def check_family(blocks):
    if len(blocks) != 13 or len(set(blocks)) != 13:
        raise ValueError("expected13 distinct local quadruples")
    if any(len(b) != 4 or len(set(b)) != 4 or any(p < 4 or p > 16 for p in b) for b in blocks):
        raise ValueError("local family must use four distinct labels in4..16")
    if Counter(p for b in blocks for p in b) != Counter({p: 4 for p in range(4, 17)}):
        raise ValueError("local degrees must be four")
    pairs = Counter(t for b in blocks for t in combinations(b, 2))
    missing = {t for t in combinations(range(4, 17), 2) if pairs[t] == 0}
    if not missing <= G or (4, 5) not in missing or (4, 6) in missing:
        raise ValueError("expected first-spoke omission and holes inside G")
    if len(missing) not in (4, 6):
        raise ValueError("unexpected local family type")
    return sorted(missing)


def build_model(
    family,
    max_missing=0,
    *,
    require_outside_pair_bound=True,
    require_opposite_spoke=True,
):
    check_family(family)
    universe = Universe.build()
    model = cp_model.CpModel()
    xs = [model.new_bool_var(f"block_{i}") for i in range(len(universe.blocks))]
    holes = [model.new_bool_var(f"hole_{i}") for i in range(len(universe.triples))]
    for t, ids in enumerate(universe.containing):
        count = sum(xs[i] for i in ids)
        model.add(count == 0).only_enforce_if(holes[t])
        model.add(count >= 1).only_enforce_if(holes[t].Not())
    model.add(sum(xs) == 64)
    model.add(sum(holes) <= max_missing)
    rank = {b: i for i, b in enumerate(universe.blocks)}
    fixed = set(COMMON) | {(1, *b) for b in family}
    for b in fixed:
        model.add(xs[rank[b]] == 1)
    for i, b in enumerate(universe.blocks):
        if b not in fixed and (1 in b or len(set(b) & {1, 2, 3}) >= 2):
            model.add(xs[i] == 0)
    for p in range(1, 17):
        model.add(sum(xs[i] for i, b in enumerate(universe.blocks) if p in b) == 20)
    for pair in combinations(range(1, 17), 2):
        incidence = sum(xs[i] for i, b in enumerate(universe.blocks) if set(pair) <= set(b))
        if pair[0] <= 3:
            target = 7 if pair[1] <= 3 else 6 if pair[1] == 4 else 5
            model.add(incidence == target)
        elif require_outside_pair_bound:
            model.add(incidence >= 5)
    # A constructive partial state also covers every triple touching the
    # heavy triple. These constraints are redundant in full-cover mode.
    local_spoke_missing = []
    for a in (2, 3):
        local_holes = []
        local_spokes = []
        for pair in combinations(range(4, 17), 2):
            ids = [
                i
                for i, b in enumerate(universe.blocks)
                if a in b and 1 not in b and (3 if a == 2 else 2) not in b and set(pair) <= set(b)
            ]
            count = sum(xs[i] for i in ids)
            if pair not in G:
                model.add(count >= 1)
            else:
                flag = model.new_bool_var(f"local_hole_{a}_{pair}")
                model.add(count == 0).only_enforce_if(flag)
                model.add(count >= 1).only_enforce_if(flag.Not())
                local_holes.append(flag)
                if pair in ((4, 5), (4, 6)):
                    local_spokes.append(flag)
                if pair == (4, 6):
                    local_spoke_missing.append(flag)
        total = model.new_int_var(0, 7, f"local_deficit_{a}")
        model.add(total == sum(local_holes))
        model.add(sum(local_spokes) <= 1)
        model.add_allowed_assignments([total], [(0,), (4,), (6,)])
    # Point-essential covers need the other spoke omitted by another family.
    # Keeping this property defines the construction branch under study.
    if require_opposite_spoke:
        model.add(sum(local_spoke_missing) >= 1)
    if max_missing:
        model.minimize(sum(holes))
    return universe, model, xs, holes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", type=Path)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--seed", type=int, default=2026101901)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--max-missing", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (
        not math.isfinite(args.seconds)
        or args.seconds <= 0
        or args.workers < 1
        or not 0 <= args.max_missing <= 560
    ):
        parser.error("invalid search budget")
    args.output.mkdir(parents=True, exist_ok=True)
    family = read_blocks(args.family, v=16, k=4)
    universe, model, xs, _ = build_model(family, args.max_missing)
    raw_source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(raw_source)
    write_blocks(args.output / "family.txt", family)
    model_path = args.output / "model.pbtxt"
    model.export_to_file(str(model_path))
    metadata = {
        "source_sha256": hashlib.sha256(raw_source).hexdigest(),
        "input_sha256": hashlib.sha256(args.family.read_bytes()).hexdigest(),
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "solver_version": ortools.__version__,
        "seconds": args.seconds,
        "seed": args.seed,
        "workers": args.workers,
        "max_missing": args.max_missing,
        "local_holes": check_family(family),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "scope": "Fixed first family of normalized regular sevenfold-triple branch; "
        "partial optimization is restricted and timeout is inconclusive.",
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = args.workers
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    with (args.output / "solver.log").open("w") as log:
        solver.log_callback = lambda line: log.write(line + "\n")
        status = solver.solve(model)
    result = {
        "status": solver.status_name(status),
        "seconds": solver.wall_time,
        "response_stats": solver.response_stats(),
        "cover_found": False,
    }
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        blocks = [b for i, b in enumerate(universe.blocks) if solver.value(xs[i])]
        candidate = args.output / "candidate.txt"
        write_blocks(candidate, blocks)
        package = verify_cover(blocks)
        proc = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(candidate), "--expected-blocks", "64"],
            capture_output=True,
            text=True,
        )
        if proc.returncode not in (0, 1):
            raise RuntimeError(proc.stderr)
        standalone = json.loads(proc.stdout)
        if len(package["uncovered"]) != standalone["uncovered_count"]:
            raise RuntimeError("cover verifiers disagree")
        if Counter(p for b in blocks for p in b) != Counter({p: 20 for p in range(1, 17)}):
            raise RuntimeError("regularity check failed")
        result.update(
            package=package,
            standalone=standalone,
            uncovered=standalone["uncovered_count"],
            cover_found=standalone["valid"],
        )
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("package", "standalone", "response_stats")
            }
        )
    )


if __name__ == "__main__":
    main()
