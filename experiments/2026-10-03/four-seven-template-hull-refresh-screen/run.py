# Document:    Refreshed Matching Template-Hull LP Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      3f494ad686d5f1b481bd0e00d3ea8702d1babe285fd4021ccb916dcf353d0560
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Solve the audited refreshed matching hull, then its 50 surviving first links."""

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from itertools import combinations
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ARTIFACTS = REPO / "experiments/2026-10-03"
RAW = REPO / "experiments/scratch/four-seven-template-hull-refresh-106-20261003"
PREVIOUS_SHA256 = "c8841227df38eec07b28f9776e812e1df4c8c4175e80c0feead9fb15f8289b9e"
MANIFEST_SHA256 = "84183ee44ed2916ffd18d64b5f113774e4eda47bad5e82c6c79b1b3a64db5bdf"
MATRIX_SHA256 = "ee2072837ae28bcce599c60975995a5c88b3fc3eb635352abc089b3eb6d78bab"
AUDIT_SHA256 = "af1c3224050faa086859930489e3bbce8fa5d9acaa922c6769f1c1bce528911b"
UNION_SHA256 = "dc1f0790d593238d00c8eff3ac58753d70a7fc9c6820d73d0bb835569ac9fd0e"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def previous_module():
    path = HERE / "previous-runner.py"
    if not path.exists():
        path = ARTIFACTS / "four-seven-template-link-screen/run.py"
    require(digest(path) == PREVIOUS_SHA256, "frozen fixed/reset implementation")
    spec = importlib.util.spec_from_file_location("frozen_matching_link_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


PREVIOUS, PREVIOUS_PATH = previous_module()


class WholeHull(PREVIOUS.ReusableHull):
    """Immutable whole-branch layout, with optional soft template extension rows."""

    def __init__(self, payload, phase_one=False):
        self.width, self.phase_one = payload["width"], phase_one
        self.solver = pywraplp.Solver.CreateSolver("GLOP")
        require(self.solver is not None, "GLOP unavailable")
        self.variables = [self.solver.NumVar(0, 1, f"x{i}") for i in range(self.width)]
        self.constraints, self.fixed_rows, self.slacks = [], [], []
        for index, (ids, coefficients, lower, upper) in enumerate(payload["rows"]):
            row = self.solver.RowConstraint(
                lower if lower is not None else -self.solver.infinity(),
                upper if upper is not None else self.solver.infinity(),
                f"row_{index}",
            )
            for column, coefficient in zip(ids, coefficients, strict=True):
                row.SetCoefficient(self.variables[column], coefficient)
            if phase_one and index >= 4270:
                for label, bound, sign in (("lower", lower, 1), ("upper", upper, -1)):
                    if bound is not None:
                        slack = self.solver.NumVar(
                            0, self.solver.infinity(), f"slack_{label}_{index}"
                        )
                        row.SetCoefficient(slack, sign)
                        self.solver.Objective().SetCoefficient(slack, 1)
                        self.slacks.append(slack)
            self.constraints.append(row)
        self.solver.Objective().SetMinimization()
        self.active = []
        self.prefix_bytes = self.export().SerializeToString(deterministic=True)
        self.prefix_sha256 = hashlib.sha256(self.prefix_bytes).hexdigest()
        self.audit([])

    def audit(self, fixed_ids):
        require(fixed_ids == [], "whole branch has no fixed first link")
        proto = self.export()
        require(len(proto.constraint) == 4550, "whole-branch row count")
        require(len(proto.variable) == self.width + (560 if self.phase_one else 0), "whole width")
        require(
            hashlib.sha256(proto.SerializeToString(deterministic=True)).hexdigest()
            == self.prefix_sha256,
            "whole-branch model changed",
        )
        return dict(
            prefix_sha256=self.prefix_sha256,
            active_fixed_ids=[],
            phase_one=self.phase_one,
            soft_rows=280 if self.phase_one else 0,
        )


def prepare():
    manifest_path = RAW / "manifest.json"
    matrix_path = RAW / "matching/extended-rows.json.gz"
    audit_path = ARTIFACTS / "four-seven-template-hull-refresh/independent-audit.json"
    union_path = (
        ARTIFACTS / "four-seven-template-hub-independent/combined-first-link-exclusions.json"
    )
    representatives_path = ARTIFACTS / "four-seven-link-orbits/result.json"
    for path, checksum in (
        (manifest_path, MANIFEST_SHA256),
        (matrix_path, MATRIX_SHA256),
        (audit_path, AUDIT_SHA256),
        (union_path, UNION_SHA256),
    ):
        require(digest(path) == checksum, f"frozen input {path.name}")
    manifest, matrix, audit, union = map(load, (manifest_path, matrix_path, audit_path, union_path))
    require(audit["passed"] and audit["manifest_sha256"] == MANIFEST_SHA256, "catalog audit")
    record = next(c for c in manifest["cases"] if c["case"] == "matching")
    require(
        record["matrix_sha256"] == MATRIX_SHA256 and matrix["width"] == 55528,
        "refreshed matching dimensions",
    )
    require(
        len(matrix["rows"]) == 4550 and record["surviving_orbits"] == 50, "refreshed rows/orbits"
    )
    require(
        matrix["variable_bounds"]
        == "Every variable has bounds [0,1]; all are continuous in this LP.",
        "unit-box domain declaration",
    )
    representatives = next(
        c for c in load(representatives_path)["cases"] if c["case"] == "matching"
    )
    by_id = {r["id"]: r for r in representatives["representatives"]}
    ids = [i for i in union["remaining_ids"] if i.startswith("matching-")]
    catalog = load(RAW / "matching/base-catalog.json.gz")
    require(
        set(ids) == {t["representative_id"] for t in catalog["templates"]} and len(ids) == 50,
        "complete matching survivor selection",
    )
    blocks = {b: i for i, b in enumerate(combinations(range(1, 17), 5))}
    selection = []
    for identifier in ids:
        rep = by_id[identifier]
        fixed = sorted(blocks[tuple(sorted((1, 2, 3, *edge)))] for edge in rep["edges"])
        require(len(fixed) == len(set(fixed)) == 7, "seven fixed blocks")
        selection.append(dict(id=identifier, case="matching", edges=rep["edges"], fixed_ids=fixed))
    return (
        matrix,
        selection,
        dict(
            manifest=MANIFEST_SHA256,
            matrix=MATRIX_SHA256,
            catalog_audit=AUDIT_SHA256,
            exclusion_union=UNION_SHA256,
            representatives=digest(representatives_path),
        ),
        audit_path,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=15)
    args = parser.parse_args()
    require(math.isfinite(args.seconds) and 0 < args.seconds <= 15, "solver budget")
    require(not args.output.exists(), "new output directory required")
    matrix, selection, input_hashes, audit_path = prepare()
    preflight = load(args.preflight)
    require(
        preflight["valid"] and preflight["runner_sha256"] == digest(Path(__file__)),
        "passing no-solve preflight of this exact runner required",
    )
    helpers, utility_path = PREVIOUS.utilities()
    helpers.validate_rows(matrix["rows"], matrix["width"])
    output = args.output
    output.mkdir(parents=True)
    for name, path in (
        ("run.py", Path(__file__)),
        ("previous-runner.py", PREVIOUS_PATH),
        ("whole-hull-utilities.py", utility_path),
        ("preflight.json", args.preflight),
        ("catalog-audit.json", audit_path),
        ("check_cover.py", REPO / "scripts/check_cover.py"),
        ("core.py", Path(helpers.verify_cover.__code__.co_filename)),
        ("extended-rows.json.gz", RAW / "matching/extended-rows.json.gz"),
    ):
        (output / name).write_bytes(path.read_bytes())
    (output / "selection.json").write_text(json.dumps(selection, indent=2) + "\n")
    metadata = dict(
        source_sha256=digest(Path(__file__)),
        previous_source_sha256=PREVIOUS_SHA256,
        utilities_sha256=PREVIOUS.UTILITIES_SHA256,
        preflight_sha256=digest(args.preflight),
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        ortools_version=ortools_version,
        command=sys.argv,
        input_hashes=input_hashes,
        seconds_per_case=args.seconds,
        model_prefixes={},
    )
    models, results = {}, []
    for selected in [dict(id="matching-whole", case="matching", fixed_ids=[]), *selection]:
        whole = selected["id"] == "matching-whole"
        kind = "whole" if whole else "fixed"
        if kind not in models:
            model = WholeHull(matrix) if whole else PREVIOUS.ReusableHull(matrix)
            models[kind] = [model, None]
            (output / f"{kind}-feasibility-base.pb.gz").write_bytes(
                gzip.compress(model.prefix_bytes, mtime=0)
            )
            metadata["model_prefixes"][kind] = dict(feasibility=model.prefix_sha256)
        model, phase_model = models[kind]
        target = output / selected["id"]
        target.mkdir()
        fixed = selected["fixed_ids"]
        fixed_rows = [[[i], [1], 1, 1] for i in fixed]
        rows = [*matrix["rows"], *fixed_rows]
        (target / "fixed-rows.json").write_text(
            json.dumps(
                dict(
                    id=selected["id"],
                    width=matrix["width"],
                    base_matrix_sha256=MATRIX_SHA256,
                    rows=fixed_rows,
                ),
                indent=2,
            )
            + "\n"
        )
        before = model.audit([]) if whole else model.fix(fixed)
        try:
            feasibility, primal, _ = model.solve(args.seconds, target / "feasibility-solver.log")
        finally:
            reset = model.audit([]) if whole else model.reset()
        result = dict(
            **selected,
            whole_branch=whole,
            checked_rows=len(rows),
            checked_columns=matrix["width"],
            feasibility_lp=feasibility,
            fixed_state_audit=before,
            reset_audit=reset,
            certificate_pending_replay=False,
            independently_excluded=False,
        )
        if primal is not None:
            result["primal_metrics"] = helpers.primal_metrics(primal, rows)
            PREVIOUS.save_compressed(
                target / "sparse-primal.json.gz",
                dict(
                    width=model.width,
                    values=[[i, v] for i, v in enumerate(primal) if v != 0],
                    zero_default=True,
                    fixed_ids=fixed,
                    base_matrix_sha256=MATRIX_SHA256,
                ),
            )
            result["sparse_primal_sha256"] = digest(target / "sparse-primal.json.gz")
            result["integral_blocks"] = helpers.check_integral_blocks(
                primal, target, output / "check_cover.py"
            )
        elif feasibility["status"] == pywraplp.Solver.INFEASIBLE:
            remaining = max(0, args.seconds - feasibility["solve_seconds"])
            if remaining >= 0.001:
                if phase_model is None:
                    phase_model = (
                        WholeHull(matrix, True) if whole else PREVIOUS.ReusableHull(matrix, True)
                    )
                    models[kind][1] = phase_model
                    (output / f"{kind}-phase-one-base.pb.gz").write_bytes(
                        gzip.compress(phase_model.prefix_bytes, mtime=0)
                    )
                    metadata["model_prefixes"][kind]["phase_one"] = phase_model.prefix_sha256
                if not whole:
                    phase_model.fix(fixed)
                try:
                    phase, _, dual = phase_model.solve(remaining, target / "phase-one-solver.log")
                finally:
                    phase_reset = phase_model.audit([]) if whole else phase_model.reset()
                result["phase_one_lp"] = phase
                result["phase_one_reset_audit"] = phase_reset
                if dual is not None:
                    PREVIOUS.save_compressed(target / "phase-one-dual.json.gz", dict(weights=dual))
                    result["certificate_attempts"] = []
                    for denominator in (1_000_000, 1_000_000_000):
                        certificate = helpers.integer_certificate(
                            rows, model.width, dual, denominator
                        )
                        path = target / f"certificate-{denominator}.json"
                        path.write_text(json.dumps(certificate, indent=2) + "\n")
                        result["certificate_attempts"].append(
                            dict(
                                file=path.name,
                                sha256=digest(path),
                                gap=certificate["gap"],
                                exact_gap_positive=certificate["proves_infeasible"],
                            )
                        )
                        if certificate["proves_infeasible"]:
                            result["certificate_pending_replay"] = True
                            break
        result["solve_seconds_total"] = feasibility["solve_seconds"] + result.get(
            "phase_one_lp", {}
        ).get("solve_seconds", 0)
        (target / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        results.append(result)
        PREVIOUS.save_compressed(output / "results.json.gz", results)
        (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        print(
            json.dumps(
                dict(
                    id=result["id"],
                    status=feasibility["status_name"],
                    pending_certificate=result["certificate_pending_replay"],
                    solve_seconds=result["solve_seconds_total"],
                )
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
