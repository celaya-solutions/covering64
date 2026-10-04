# Document:    Linear Screens for First Heavy-Link Representatives
# Version:     v1.4.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      de73a2222f83de803108527dc974a82e3ea95e2093599b545468e4c46e29a5a4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Bounded LP screens; only positive, exactly checked certificates exclude a case."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import subprocess
from fractions import Fraction
from pathlib import Path

import ortools
from four_seven_double_cuts import add_double_triple_cuts
from four_seven_search import build_model
from ortools.linear_solver import pywraplp


def validate_rows(rows, width):
    if type(width) is not int or width <= 0:
        raise ValueError("positive integer column count required")
    for row in rows:
        if len(row) != 4:
            raise ValueError("four fields required per row")
        indices, coefficients, lower, upper = row
        if len(indices) != len(coefficients) or len(set(indices)) != len(indices):
            raise ValueError("unique indices with matching coefficient count required")
        if any(type(i) is not int or not 0 <= i < width for i in indices):
            raise ValueError("integer column indices must be in range")
        if any(type(c) is not int for c in coefficients):
            raise ValueError("integer coefficients required")
        if any(bound is not None and type(bound) is not int for bound in (lower, upper)):
            raise ValueError("integer or infinite row bounds required")
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("row lower bound exceeds upper bound")


def linear_rows(model):
    rows = []
    for constraint in model.proto.constraints:
        if not constraint.has_linear():
            raise ValueError("linear constraints required")
        lin = constraint.linear
        if constraint.enforcement_literal or len(lin.domain) != 2:
            raise ValueError("unconditional single-interval linear rows required")
        lo, hi = map(int, lin.domain)
        rows.append((tuple(lin.vars), tuple(lin.coeffs),
                     lo if lo > -(1 << 60) else None, hi if hi < (1 << 60) else None))
    if any(tuple(v.domain) != (0, 1) for v in model.proto.variables):
        raise ValueError("Boolean variable domains required")
    return rows, len(model.proto.variables)


def solve_lp(rows, width, seconds, phase_one=False, soft_rows=None):
    validate_rows(rows, width)
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("positive finite time budget required")
    if soft_rows is not None:
        soft_rows = list(soft_rows)
        if len(set(soft_rows)) != len(soft_rows):
            raise ValueError("soft row indices must be distinct")
        if not phase_one or any(type(i) is not int or not 0 <= i < len(rows) for i in soft_rows):
            raise ValueError("soft rows must name existing rows in a phase-one model")
        soft_rows = set(soft_rows)
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.set_time_limit(max(1, round(seconds * 1000)))
    xs = [solver.NumVar(0, 1, f"x{i}") for i in range(width)]
    constraints = []
    for i, (indices, coefficients, lower, upper) in enumerate(rows):
        row = solver.Constraint(lower if lower is not None else -solver.infinity(),
                                upper if upper is not None else solver.infinity())
        for index, coefficient in zip(indices, coefficients):
            row.SetCoefficient(xs[index], coefficient)
        if phase_one and (soft_rows is None or i in soft_rows):
            for name, bound, sign in (("lo", lower, 1), ("hi", upper, -1)):
                if bound is not None:
                    slack = solver.NumVar(0, solver.infinity(), f"{name}{i}")
                    row.SetCoefficient(slack, sign)
                    solver.Objective().SetCoefficient(slack, 1)
        constraints.append(row)
    solver.Objective().SetMinimization()
    status = solver.Solve()
    result = {"status": status, "milliseconds": solver.wall_time(), "phase_one": phase_one}
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        result["objective"] = solver.Objective().Value()
        result["weights"] = [row.dual_value() for row in constraints]
    return result


def exact_certificate(rows, width, weights, denominator=1_000_000):
    validate_rows(rows, width)
    if type(denominator) is not int or denominator <= 0:
        raise ValueError("positive integer denominator required")
    if len(weights) != len(rows) or any(not math.isfinite(w) for w in weights):
        raise ValueError("finite weight for every row required")
    integer_weights = [round(w * denominator) for w in weights]
    column_sums = [0] * width
    rhs = 0
    for (indices, coefficients, lower, upper), weight in zip(rows, integer_weights):
        if not weight:
            continue
        bound = lower if weight > 0 else upper
        if bound is None:
            raise ValueError("weight points toward an infinite row bound")
        rhs += weight * bound
        for index, coefficient in zip(indices, coefficients):
            column_sums[index] += weight * coefficient
    box_max = sum(max(0, value) for value in column_sums)
    gap = Fraction(rhs - box_max, denominator)
    return {
        "denominator": denominator,
        "weights": [[i, w] for i, w in enumerate(integer_weights) if w],
        "rhs_numerator": rhs,
        "box_max_numerator": box_max,
        "gap": [gap.numerator, gap.denominator],
        "checked_columns": width,
        "proves_infeasible": gap > 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--representatives", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=10)
    parser.add_argument("--case", choices=("cycle", "matching", "both"), default="both")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--feature-cuts", action="store_true")
    parser.add_argument("--feature-proof", type=Path)
    parser.add_argument("--facet-cuts", action="store_true")
    parser.add_argument("--facet-proof", type=Path)
    parser.add_argument("--blossom-cuts", action="store_true")
    parser.add_argument("--four-hub-blocks", type=int)
    parser.add_argument("--double-hub-triples", type=int)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0 or (
        args.limit is not None and args.limit < 1
    ):
        parser.error("positive time and optional positive limit required")
    if args.feature_cuts != (args.feature_proof is not None):
        parser.error("feature cuts and their proof artifact must be supplied together")
    if args.facet_cuts != (args.facet_proof is not None):
        parser.error("facet cuts and their proof artifact must be supplied together")
    if (args.four_hub_blocks is None) != (args.double_hub_triples is None):
        parser.error("both hub counts must be supplied together")
    hub_split = args.four_hub_blocks is not None
    if hub_split:
        from four_seven_hub_split import CASES

        if (args.four_hub_blocks, args.double_hub_triples) not in CASES:
            parser.error("one of the six exhaustive integer hub cases is required")
    feature_proof = args.feature_proof.read_bytes() if args.feature_cuts else None
    if args.feature_cuts:
        from four_seven_feature_cuts import PROOF_MANIFEST_SHA256

        if hashlib.sha256(feature_proof).hexdigest() != PROOF_MANIFEST_SHA256:
            parser.error("feature proof hash does not match the audited helper")
    facet_proof = args.facet_proof.read_bytes() if args.facet_cuts else None
    if args.facet_cuts:
        from four_seven_facet_cuts import PROOF_MANIFEST_SHA256 as FACET_PROOF_SHA256

        if hashlib.sha256(facet_proof).hexdigest() != FACET_PROOF_SHA256:
            parser.error("facet proof hash does not match the audited helper")
    if args.output.exists():
        parser.error("output directory must be new")
    args.output.mkdir(parents=True)
    payload = json.loads(args.representatives.read_text())
    (args.output / "representatives.json").write_bytes(args.representatives.read_bytes())
    if feature_proof:
        (args.output / "feature-proof.json").write_bytes(feature_proof)
    if facet_proof:
        (args.output / "facet-proof.json").write_bytes(facet_proof)
    source_paths = [Path(__file__), Path(__file__).with_name("four_seven_search.py"),
                    Path(__file__).with_name("four_seven_double_cuts.py")]
    if args.feature_cuts:
        source_paths.append(Path(__file__).with_name("four_seven_feature_cuts.py"))
    if args.facet_cuts:
        source_paths.append(Path(__file__).with_name("four_seven_facet_cuts.py"))
    if args.blossom_cuts:
        source_paths.append(Path(__file__).with_name("four_seven_blossom_cuts.py"))
    if hub_split:
        source_paths.append(Path(__file__).with_name("four_seven_hub_split.py"))
    sources = {}
    for path in source_paths:
        raw = path.read_bytes()
        (args.output / path.name).write_bytes(raw)
        sources[path.name] = hashlib.sha256(raw).hexdigest()
    metadata = {
        "scope": "Each result concerns one fixed first-heavy-link representative in one "
                 "regular four-sevenfold branch. Numerical feasibility is not an exact witness.",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "sources": sources,
        "representatives_sha256": hashlib.sha256(args.representatives.read_bytes()).hexdigest(),
        "solver_version": ortools.__version__, "seconds_per_stage": args.seconds,
        "case": args.case, "limit": args.limit,
        "feature_cuts": args.feature_cuts,
        "feature_proof_sha256": (
            hashlib.sha256(feature_proof).hexdigest() if feature_proof else None
        ),
        "facet_cuts": args.facet_cuts,
        "facet_proof_sha256": (
            hashlib.sha256(facet_proof).hexdigest() if facet_proof else None
        ),
        "blossom_cuts": args.blossom_cuts,
        "hub_count_split": [args.four_hub_blocks, args.double_hub_triples] if hub_split else None,
    }
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    results = []
    for case_data in payload["cases"]:
        case = case_data["case"]
        if args.case not in (case, "both"):
            continue
        universe, model, xs, _ = build_model(case)
        add_double_triple_cuts(universe, model, xs, case)
        feature_application = None
        if args.feature_cuts:
            from four_seven_feature_cuts import add_feature_cuts

            feature_application = add_feature_cuts(universe, model, xs, case)
        facet_application = None
        if args.facet_cuts:
            from four_seven_facet_cuts import add_facet_cuts

            facet_application = add_facet_cuts(universe, model, xs, case)
        blossom_application = None
        if args.blossom_cuts:
            from four_seven_blossom_cuts import add_blossom_cuts

            blossom_application = add_blossom_cuts(universe, model, xs, case)
        hub_application = None
        if hub_split:
            from four_seven_hub_split import add_hub_count_split

            hub_application = add_hub_count_split(
                universe, model, xs, case, args.four_hub_blocks, args.double_hub_triples)
        base_rows, width = linear_rows(model)
        model_path = args.output / f"{case}-base.pbtxt"
        model.export_to_file(str(model_path))
        rows_path = args.output / f"{case}-rows.json.gz"
        rows_path.write_bytes(gzip.compress(
            (json.dumps({"width": width, "rows": base_rows}) + "\n").encode(), mtime=0
        ))
        metadata.setdefault("models", {})[case] = {
            "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
            "rows_sha256": hashlib.sha256(rows_path.read_bytes()).hexdigest(),
            "feature_cuts": feature_application,
            "facet_cuts": facet_application,
            "blossom_cuts": blossom_application,
            "hub_count_split": hub_application,
        }
        (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        ids = {b: i for i, b in enumerate(universe.blocks)}
        for rep in case_data["representatives"][:args.limit]:
            fixed_ids = [ids[(1, 2, 3, *edge)] for edge in rep["edges"]]
            rows = base_rows + [((i,), (1,), 1, 1) for i in fixed_ids]
            result = {"id": rep["id"], "case": case, "fixed_ids": fixed_ids,
                      "checked_rows": len(rows), "checked_columns": width,
                      "proves_infeasible": False}
            lp = solve_lp(rows, width, args.seconds)
            result["feasibility_lp"] = {k: v for k, v in lp.items() if k != "weights"}
            if lp["status"] == pywraplp.Solver.INFEASIBLE:
                soft_start = len(base_rows) - (2 if hub_split else 0)
                phase = solve_lp(rows, width, args.seconds, phase_one=True,
                                 soft_rows=range(soft_start, len(rows)))
                result["phase_one_mode"] = (
                    "fixed_link_and_hub_counts" if hub_split else "fixed_link"
                )
                if phase["status"] == pywraplp.Solver.INFEASIBLE:
                    result["restricted_phase_one_lp"] = phase
                    phase = solve_lp(rows, width, args.seconds, phase_one=True)
                    result["phase_one_mode"] = "all_rows_fallback"
                result["phase_one_lp"] = {k: v for k, v in phase.items() if k != "weights"}
                if phase["status"] in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
                    certificate = exact_certificate(rows, width, phase["weights"])
                    result["certificate"] = certificate
                    result["proves_infeasible"] = certificate["proves_infeasible"]
            results.append(result)
            archive = gzip.compress((json.dumps(results, indent=2) + "\n").encode(), mtime=0)
            (args.output / "results.json.gz").write_bytes(archive)
            print(json.dumps({"id": result["id"], "lp_status": lp["status"],
                              "excluded": result["proves_infeasible"]}), flush=True)


if __name__ == "__main__":
    main()
