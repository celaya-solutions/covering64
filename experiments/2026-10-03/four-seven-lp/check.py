# Document:    Four Sevenfold Triple Branch Linear Relaxations
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Solve both LP relaxations and check rational witnesses against every original row."""

import hashlib
import importlib.util
import json
import subprocess
import time
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import permutations
from pathlib import Path

import ortools
from google.protobuf import text_format
from ortools.linear_solver import pywraplp
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRATCH = ROOT / "experiments/scratch/four-seven-lp-20261003"


def check_exact(proto, values):
    if len(values) != len(proto.variables):
        return False
    for variable, value in zip(proto.variables, values):
        domain = variable.domain
        if not any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)):
            return False
    for row in proto.constraints:
        if row.enforcement_literal or row.WhichOneof("constraint") != "linear":
            raise ValueError("unsupported constraint")
        value = sum((coefficient * values[index] for index, coefficient in
                     zip(row.linear.vars, row.linear.coeffs)), Fraction(0))
        domain = row.linear.domain
        if not any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)):
            return False
    return True


def solve(proto, mapping, label, directory):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetTimeLimit(60000)
    parameters = "primal_feasibility_tolerance: 1e-9\ndual_feasibility_tolerance: 1e-9\n"
    solver.SetSolverSpecificParametersAsString(parameters)
    variables = [solver.NumVar(0, 1, f"weight_{i}") for i in range(max(mapping) + 1)]
    infinity = solver.infinity()
    for row in proto.constraints:
        if row.enforcement_literal or row.WhichOneof("constraint") != "linear":
            raise ValueError("expected unconditional linear constraints")
        if len(row.linear.domain) != 2:
            raise ValueError("nonconvex linear domain")
        lower, upper = row.linear.domain
        constraint = solver.RowConstraint(
            -infinity if lower == -(2**63) else lower,
            infinity if upper == 2**63 - 1 else upper, "",
        )
        terms = Counter()
        for index, coefficient in zip(row.linear.vars, row.linear.coeffs):
            terms[mapping[index]] += coefficient
        for index, coefficient in terms.items():
            constraint.SetCoefficient(variables[index], coefficient)
    began = time.monotonic()
    status = solver.Solve()
    elapsed = time.monotonic() - began
    (directory / f"{label}.mps").write_text(solver.ExportModelAsMpsFormat(False, False))
    result = {"status": status, "seconds": elapsed, "variables": len(variables),
              "rows": solver.NumConstraints(), "iterations": solver.iterations(),
              "solver_version": solver.SolverVersion(), "parameters": parameters}
    values = None
    if status in (solver.OPTIMAL, solver.FEASIBLE):
        floating = [x.solution_value() for x in variables]
        (directory / f"{label}-floating.json").write_text(json.dumps(floating) + "\n")
        for denominator in (1000, 1000000, 1000000000):
            rational = [Fraction(value).limit_denominator(denominator) for value in floating]
            candidate = [rational[i] for i in mapping]
            if check_exact(proto, candidate):
                values = candidate
                result["exact_rational_witness"] = True
                result["denominator_limit"] = denominator
                result["denominators"] = sorted({x.denominator for x in candidate})
                break
        result.setdefault("exact_rational_witness", False)
    return result, values


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    source = ROOT / "scripts/four_seven_search.py"
    frozen = SCRATCH / "four_seven_search.py"
    frozen.write_bytes(source.read_bytes())
    spec = importlib.util.spec_from_file_location("frozen_four_seven_lp", frozen)
    branch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(branch)
    records = {}
    for case in ("cycle", "matching"):
        directory = SCRATCH / case
        directory.mkdir(exist_ok=True)
        universe, model, _, _ = branch.build_model(case)
        model_path = directory / "model.pbtxt"
        model.export_to_file(str(model_path))
        proto = cp_model_pb2.CpModelProto()
        text_format.Parse(model_path.read_text(), proto)
        if any(tuple(v.domain) != (0, 1) for v in proto.variables):
            raise ValueError("expected only Boolean block variables")
        direct, direct_values = solve(proto, list(range(len(proto.variables))), "full", directory)
        signatures = [tuple(sum(p in b for p in group) for group in branch.ANCHORS)
                      + tuple(int(p in b) for p in branch.HUBS) for b in universe.blocks]
        distinct = {s: i for i, s in enumerate(sorted(set(signatures)))}
        mapping = [distinct[s] for s in signatures]
        symmetric, values = solve(proto, mapping, "anchor-symmetric", directory)
        edge_set = {frozenset((0, 1)), frozenset((2, 3))}
        if case == "cycle":
            edge_set |= {frozenset((1, 2)), frozenset((0, 3))}
        group = [p for p in permutations(range(4))
                 if {frozenset(p[i] for i in edge) for edge in edge_set} == edge_set]
        canonical = [min(tuple(s[p[i]] for i in range(4))
                         + tuple(s[4 + p[i]] for i in range(4)) for p in group)
                     for s in signatures]
        orbit_ids = {s: i for i, s in enumerate(sorted(set(canonical)))}
        orbit_mapping = [orbit_ids[s] for s in canonical]
        all_symmetric, all_values = solve(proto, orbit_mapping, "all-symmetric", directory)
        if all_values is not None:
            values = all_values
        if values is None:
            values = direct_values
        record = {"full_lp": direct, "anchor_symmetric_lp": symmetric,
                  "all_symmetric_lp": all_symmetric, "group_permutations": group,
                  "source_model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                  "variables": len(proto.variables), "rows": len(proto.constraints),
                  "rational_witness_checked": values is not None}
        if values is not None:
            positive = [[i, x.numerator, x.denominator] for i, x in enumerate(values) if x]
            groups = defaultdict(list)
            for i, value in enumerate(values):
                if value:
                    groups[str(value)].append(i)
            witness = {"case": case, "nonzero_weights": positive,
                       "source_model_sha256": record["source_model_sha256"],
                       "all_variable_domains_checked": len(proto.variables),
                       "all_linear_rows_checked": len(proto.constraints),
                       "total_block_weight": str(sum(values, Fraction(0))),
                       "weight_histogram": {key: len(ids) for key, ids in groups.items()},
                       "scope": "Fractional LP witness, not a set of cover blocks."}
            path = HERE / f"{case}-witness.json"
            path.write_text(json.dumps(witness, indent=2) + "\n")
            record["witness_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            damaged = values[:]
            damaged[next(i for i, x in enumerate(damaged) if x)] += Fraction(1, 1000)
            if check_exact(proto, damaged):
                raise ValueError("damaged fractional witness accepted")
            record["damaged_weight_rejected"] = True
        records[case] = record
        print(json.dumps({"case": case, **record}), flush=True)
    manifest = {str(p.relative_to(SCRATCH)): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size} for p in SCRATCH.rglob("*") if p.is_file()}
    result = {"cases": records, "source_sha256": hashlib.sha256(frozen.read_bytes()).hexdigest(),
              "source_revision": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "ortools_version": ortools.__version__, "scratch_manifest": manifest,
              "scope": "LP feasibility is arithmetic consistency, not an integral cover."}
    (HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
