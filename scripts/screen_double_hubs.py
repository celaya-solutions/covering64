#!/usr/bin/env python3
# Document:    Exact Rational Screening of Double Hub Seeds
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Solve dual LPs on all2002 nonanchor blocks and check rounded weights exactly."""

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import time
from fractions import Fraction
from pathlib import Path

import ortools
from ortools.linear_solver import pywraplp

from covering64.core import Universe


def restricted_dual(universe, retained, allowed):
    if any(len(ids) != len(set(ids)) or any(type(i) is not int or not 0 <= i
            < len(universe.blocks) for i in ids) for ids in (retained, allowed)):
        raise ValueError("invalid or duplicate block IDs")
    if set(retained) & set(allowed):
        raise ValueError("retained and additional block families overlap")
    covered = {t for i in retained for t in universe.coverage[i]}
    missing = sorted(set(range(len(universe.triples))) - covered)
    solver = pywraplp.Solver.CreateSolver("GLOP")
    variables = {t: solver.NumVar(0, solver.infinity(), str(t)) for t in missing}
    for i in allowed:
        terms = [variables[t] for t in universe.coverage[i] if t in variables]
        if terms:
            solver.Add(sum(terms) <= 1)
    solver.Maximize(sum(variables.values()))
    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        raise RuntimeError(f"LP did not finish optimally: {status}")
    denominator = 1_000_000
    weights = {t: max(0, math.floor(x.solution_value() * denominator))
               for t, x in variables.items()}
    weights = {t: n for t, n in weights.items() if n}
    all_loads = [sum(weights.get(t, 0) for t in coverage) for coverage in universe.coverage]
    denominator = max(denominator, max(all_loads[i] for i in allowed))
    bound = Fraction(sum(weights.values()), denominator)
    return {"weights": [[t, n, denominator] for t, n in weights.items()],
            "lower_bound": [bound.numerator, bound.denominator],
            "lp_status": "OPTIMAL", "missing_triples": missing,
            "all_block_capacity_valid": max(all_loads) <= denominator,
            "allowed_block_capacity_valid": max(all_loads[i] for i in allowed) <= denominator,
            "maximum_integer_load": max(all_loads), "denominator": denominator,
            "constraint_block_count": len(allowed)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    raw = args.candidates.read_bytes()
    data = json.loads(gzip.decompress(raw))
    source = Path(__file__).read_bytes()
    (args.output / "source.py").write_bytes(source)
    universe = Universe.build()
    allowed = [i for i, block in enumerate(universe.blocks) if 1 not in block and 2 not in block]
    if len(allowed) != 2002:
        raise RuntimeError("wrong nonanchor block family")
    metadata = {"source_sha256": hashlib.sha256(source).hexdigest(),
                "input_sha256": hashlib.sha256(raw).hexdigest(), "solver": "OR-Tools GLOP",
                "solver_version": ortools.__version__, "workers": 1,
                "source_revision": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True).strip(),
                "allowed_block_ids": allowed, "additional_budget": 32,
                "scope": "only these prescribed32-block unions; no global bound claim"}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rows = []
    started = time.monotonic()
    with (args.output / "certificates.jsonl").open("w") as stream:
        for number, case in enumerate(data["candidates"]):
            retained = case["retained_block_ids"]
            if ([list(universe.blocks[i]) for i in retained] != case["retained_blocks"]
                    or len(retained) != 32):
                raise ValueError("retained block IDs do not match the32-block witness")
            certificate = restricted_dual(universe, retained, allowed)
            if any(1 in universe.triples[t] or 2 in universe.triples[t]
                   for t in certificate["missing_triples"]):
                raise ValueError("the supplied union does not close both anchor links")
            # Here nonanchor blocks dominate any anchor block on missing triples.
            # Check all4368 capacities anyway, so the saved dual is also valid
            # for arbitrary additions to this fixed union.
            if not certificate["all_block_capacity_valid"]:
                raise RuntimeError("rounded dual fails a full-universe capacity")
            row = {"case": number, "identifier": case["identifier"],
                   "first_class": case["first_class"], "certificate": certificate,
                   "retained_block_ids": retained,
                   "excluded": Fraction(*certificate["lower_bound"]) > 32}
            rows.append(row)
            stream.write(json.dumps(row) + "\n")
            stream.flush()
            print(json.dumps({"case": number, "identifier": case["identifier"],
                              "bound": certificate["lower_bound"],
                              "excluded": row["excluded"]}), flush=True)
    summary = {"cases": len(rows), "excluded": sum(row["excluded"] for row in rows),
               "minimum_bound": min(Fraction(*row["certificate"]["lower_bound"]) for row in rows),
               "maximum_bound": max(Fraction(*row["certificate"]["lower_bound"]) for row in rows),
               "elapsed_seconds": time.monotonic() - started}
    summary["minimum_bound"] = str(summary["minimum_bound"])
    summary["maximum_bound"] = str(summary["maximum_bound"])
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output / "certificates.json.gz").write_bytes(gzip.compress(
        json.dumps({"metadata": metadata, "summary": summary, "cases": rows}, indent=2).encode()
        + b"\n", mtime=0))
    print(json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
