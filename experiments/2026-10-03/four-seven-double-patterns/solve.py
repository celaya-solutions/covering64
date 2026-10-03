# Document:    Bounded Integer Double Triple Pattern Construction
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b99267693924ad3cf8ceba3f780a409a938f9e9292fd81caa08e4b808328a1b7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import hashlib
import itertools
import json
import pathlib
import subprocess
import sys

import ortools
from ortools.sat.python import cp_model

ROOT = pathlib.Path(__file__).resolve().parent
GROUPS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
HUBS = (4, 8, 12, 16)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=("cycle", "matching"))
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    scratch = pathlib.Path("experiments/scratch/four-seven-double-patterns-20261003") / args.case
    scratch.mkdir(parents=True, exist_ok=False)
    triples = [
        t
        for t in itertools.combinations(range(1, 17), 3)
        if all(len(set(t) & set(group)) <= 1 for group in GROUPS)
    ]
    assert len(triples) == 400
    model = cp_model.CpModel()
    xs = [model.new_bool_var("triple_" + "_".join(map(str, t))) for t in triples]
    heavy = {group: 7 for group in GROUPS}
    fixed = {}
    for group, hub in zip(GROUPS, HUBS, strict=True):
        for pair in itertools.combinations(group, 2):
            for point in range(1, 17):
                if point not in group:
                    fixed[tuple(sorted((*pair, point)))] = 2 if point == hub else 1
    target = dict.fromkeys(itertools.combinations(range(1, 17), 2), 5)
    for group, hub in zip(GROUPS, HUBS, strict=True):
        for pair in itertools.combinations(group, 2):
            target[pair] = 7
        for point in group:
            target[tuple(sorted((point, hub)))] = 6
    edges = [(4, 8), (8, 12), (12, 16), (4, 16)] if args.case == "cycle" else [(4, 8), (12, 16)]
    for pair in edges:
        target[pair] += 1 if args.case == "cycle" else 2
    rows = 0
    for pair, count in target.items():
        ids = [i for i, t in enumerate(triples) if set(pair) <= set(t)]
        known = sum(v for t, v in {**fixed, **heavy}.items() if set(pair) <= set(t))
        demand = 3 * count - known - len(ids)
        if not ids:
            assert demand == 0
            continue
        model.add(sum(xs[i] for i in ids) == demand)
        rows += 1
    assert rows == 108 and len(model.proto.variables) == 400
    model_path = scratch / "model.pbtxt"
    model.export_to_file(str(model_path))
    source = pathlib.Path(__file__).read_bytes()
    (scratch / "solve.py").write_bytes(source)
    (scratch / "check.py").write_bytes((ROOT / "check.py").read_bytes())
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = args.seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = args.seed
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    metadata = dict(
        case=args.case,
        seconds=args.seconds,
        seed=args.seed,
        workers=1,
        variables=400,
        nonzero_pair_rows=108,
        solver_version=ortools.__version__,
        source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        source_sha256=hashlib.sha256(source).hexdigest(),
        checker_sha256=hashlib.sha256((ROOT / "check.py").read_bytes()).hexdigest(),
        model_sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),
        scope="Necessary integer double-triple system only; no64-block cover claim.",
    )
    (ROOT / f"{args.case}-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    with (scratch / "solver.log").open("w") as log:
        solver.log_callback = lambda line: (log.write(line + "\n"), log.flush())
        status = solver.solve(model)
    result = dict(
        status=solver.status_name(status),
        seconds=solver.wall_time,
        response_stats=solver.response_stats(),
        integer_pattern_found=False,
    )
    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        chosen = [t for i, t in enumerate(triples) if solver.value(xs[i])]
        assert len(chosen) == 44
        witness = ROOT / f"{args.case}-pattern.txt"
        witness.write_text("".join(" ".join(map(str, t)) + "\n" for t in chosen))
        subprocess.run(
            [
                sys.executable,
                str(ROOT / "check.py"),
                args.case,
                str(witness),
                str(ROOT / f"{args.case}-check.json"),
            ],
            check=True,
        )
        result.update(
            integer_pattern_found=True,
            witness_sha256=hashlib.sha256(witness.read_bytes()).hexdigest(),
        )
    (ROOT / f"{args.case}-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "response_stats"}))


if __name__ == "__main__":
    main()
