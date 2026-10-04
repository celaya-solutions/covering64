# Document:    Refreshed 108 Template Hull Targeted Hub LP Checks
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      0afd4b068465955acc0d48a506ec9d169ce3522b10fa575a5a6866fec14a4304
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Two bounded checks of independently selected first-link/hub cases."""

import copy
import gzip
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ART = HERE.parent
RAW = ROOT / "experiments/scratch/four-seven-template-hub-refresh-108-20261003"
MATRIX = (ROOT / "experiments/scratch/four-seven-template-hull-refresh-108-20261003"
          / "matching/extended-rows.json.gz")
MATRIX_SHA = "e9b2289291479c5f1119f432f0131d8fda8130ace2e64c773cf93dd8928ceade"
EXPECTED = {"matching-029": ([0, 2], [0, 4, 26, 38, 47, 63, 77]),
            "matching-063": ([0, 1], [3, 4, 18, 29, 39, 61, 67])}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def save(path, value):
    raw = (json.dumps(value, indent=2) + "\n").encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == ".gz" else raw)


def inspect(model, payload, fixed, hub_rows):
    """Compare the full exported coefficients and domains against frozen JSON."""
    proto = model.export()
    require(len(proto.variable) == payload["width"] + (14 if model.phase_one else 0),
            "variable count")
    expected = [*payload["rows"], *hub_rows, *[[[i], [1], 1, 1] for i in fixed]]
    require(len(proto.constraint) == len(expected) == 4559, "row count")
    for index, (row, wanted) in enumerate(zip(proto.constraint, expected, strict=True)):
        ids, coeff, lower, upper = wanted
        terms = list(zip(ids, coeff, strict=True))
        if model.phase_one and index >= 4552:
            offset = 2 * (index - 4552) + payload["width"]
            terms.extend(((offset, 1), (offset + 1, -1)))
        require(sorted(zip(row.var_index, row.coefficient, strict=True)) == sorted(terms),
                "coefficient mismatch")
        require(row.lower_bound == (float("-inf") if lower is None else lower) and
                row.upper_bound == (float("inf") if upper is None else upper), "bound mismatch")
    for index, var in enumerate(proto.variable):
        slack = index >= payload["width"]
        require(var.lower_bound == 0 and var.upper_bound == (float("inf") if slack else 1)
                and var.objective_coefficient == int(slack) and not var.is_integer,
                "variable domain/objective mismatch")
    return proto


def main():
    require(not RAW.exists(), "raw directory must be new")
    cp_path = ART / "four-seven-template-cp-restricted/manifest.json"
    cp_audit_path = ART / "four-seven-template-cp-restricted/independent-audit.json"
    hull_path = ART / "four-seven-template-hull-refresh-108/manifest.json"
    hull_audit_path = ART / "four-seven-template-hull-refresh-108/independent-audit.json"
    cp, cp_audit, _, hull_audit = map(load, (cp_path, cp_audit_path, hull_path, hull_audit_path))
    require(cp_audit["passed"] and cp_audit["manifest_sha256"] == sha(cp_path), "case audit")
    require(sha(cp_path) == "38e8854797e5775bec5da9834218b2a4a8ded191274d4a472e047505f06378dc"
            and sha(cp_audit_path) ==
            "594641767d810c30f233ef6854433f84a6dde1793691e7e8046a8b6df7b8f04f", "frozen selection")
    require(hull_audit["passed"] and hull_audit["manifest_sha256"] == sha(hull_path)
            and hull_audit["checked_exclusions"] == 108, "hull audit")
    require(sha(MATRIX) == MATRIX_SHA, "immutable108 matrix")
    payload = load(MATRIX)
    require(payload["width"] == 52936 and len(payload["rows"]) == 4550, "108 dimensions")
    source = ART / "four-seven-template-hub-priority/run.py"
    require(sha(source) == "9d4689c59d12c7326cf5a7e03cafe9d09eb7c5698db1f085446cd57d02fca661",
            "frozen combined model source")
    spec = importlib.util.spec_from_file_location("frozen_hub_runner", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    helpers, utility_path = module.PREVIOUS.utilities()
    records = cp["cases"]
    require(len(records) == 2 and {x["case"] for x in records} == set(EXPECTED), "two cases")
    RAW.mkdir(parents=True)
    for path in (Path(__file__), source, module.PREVIOUS_PATH, utility_path):
        (RAW / (path.parent.name + "-" + path.name)).write_bytes(path.read_bytes())
    (RAW / "check_cover.py").write_bytes((ROOT / "scripts/check_cover.py").read_bytes())
    metadata = dict(started_utc=datetime.now(UTC).isoformat(), seconds_per_case=15,
                    random_seed=None, deterministic_lp=True, ortools_version=ortools_version,
                    source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                            cwd=ROOT, text=True).strip(),
                    command=sys.argv, input_hashes={str(p.relative_to(ROOT)): sha(p) for p in
                    (cp_path, cp_audit_path, hull_path, hull_audit_path, MATRIX, source,
                     module.PREVIOUS_PATH, utility_path, Path(__file__))})
    blocks = list(combinations(range(1, 17), 5))
    results, controls = [], []
    for record in records:
        name = record["case"]
        hub, fixed = EXPECTED[name]
        require(record["hub_case"] == hub and record["fixed_ids"] == fixed, "case selection")
        require(record["fixed_blocks"] == [list(blocks[i]) for i in fixed], "block labels")
        prior_rows = ROOT / record["added_rows"]
        require(sha(prior_rows) == record["added_rows_sha256"], "audited extension")
        hub_rows = module.hub_rows(*hub)
        require(load(prior_rows) == [*[[[i], [1], 1, 1] for i in fixed], *hub_rows],
                "same nine equalities")
        target = RAW / name
        target.mkdir()
        full_rows = [*payload["rows"], *hub_rows, *[[[i], [1], 1, 1] for i in fixed]]
        save(target / "full-rows.json.gz", dict(width=payload["width"], rows=full_rows))
        models = []
        for phase in (False, True):
            model = module.CombinedHull(payload, *hub, phase_one=phase)
            model.fix(fixed)
            proto = inspect(model, payload, fixed, hub_rows)
            for index in (0, 4550, 4551, 4552):
                damaged = copy.deepcopy(payload) if index == 0 else None
                if damaged is not None:
                    damaged["rows"][0][2] += 1
                    args = (damaged, fixed, hub_rows)
                elif index == 4552:
                    args = (payload, [fixed[0] + 1, *fixed[1:]], hub_rows)
                else:
                    wrong_hub = copy.deepcopy(hub_rows)
                    wrong_hub[index - 4550][2] += 1
                    args = (payload, fixed, wrong_hub)
                try:
                    inspect(model, *args)
                except ValueError:
                    controls.append(dict(case=name, phase_one=phase, row=index, rejected=True))
                else:
                    raise ValueError("damaged model accepted")
            (target / ("phase-one.pb.gz" if phase else "feasibility.pb.gz")).write_bytes(
                gzip.compress(proto.SerializeToString(deterministic=True), mtime=0))
            models.append(model)
        feasibility, primal, _ = models[0].solve(15, target / "feasibility-solver.log")
        result = dict(id=name, hub_case=hub, fixed_ids=fixed, width=payload["width"],
                      rows=4559, matrix_sha256=MATRIX_SHA,
                      full_rows_sha256=sha(target / "full-rows.json.gz"),
                      feasibility_lp=feasibility, certificate_pending_replay=False,
                      independently_excluded=False)
        if primal is not None:
            result["primal_metrics"] = helpers.primal_metrics(primal, full_rows)
            save(target / "sparse-primal.json.gz", dict(width=payload["width"],
                 values=[[i, v] for i, v in enumerate(primal) if v], zero_default=True))
            result["integral_blocks"] = helpers.check_integral_blocks(primal, target,
                                                                      RAW / "check_cover.py")
        elif feasibility["status"] == pywraplp.Solver.INFEASIBLE:
            remaining = 15 - feasibility["solve_seconds"]
            if remaining >= .001:
                phase, _, dual = models[1].solve(remaining, target / "phase-one-solver.log")
                result["phase_one_lp"] = phase
                if dual is not None:
                    save(target / "phase-one-dual.json.gz", dict(weights=dual))
                    result["certificate_attempts"] = []
                    for denominator in (1_000_000, 1_000_000_000):
                        certificate = helpers.integer_certificate(full_rows, payload["width"],
                                                                  dual, denominator)
                        path = target / f"certificate-{denominator}.json"
                        save(path, certificate)
                        result["certificate_attempts"].append(dict(path=str(path.relative_to(ROOT)),
                             sha256=sha(path), gap=certificate["gap"],
                             exact_gap_positive=certificate["proves_infeasible"]))
                        if certificate["proves_infeasible"]:
                            result["certificate_pending_replay"] = True
                            break
        result["solve_seconds_total"] = feasibility["solve_seconds"] + result.get(
            "phase_one_lp", {}).get("solve_seconds", 0)
        result["reset_audits"] = [model.reset() for model in models]
        save(target / "result.json", result)
        results.append(result)
        save(RAW / "results.json", results)
        print(json.dumps({k: result[k] for k in ("id", "hub_case", "certificate_pending_replay",
                                                "solve_seconds_total")}), flush=True)
    save(RAW / "preflight.json", dict(passed=True, layouts=4, damaged_controls=controls,
                                     solver_calls_during_preflight=0))
    metadata["finished_utc"] = datetime.now(UTC).isoformat()
    save(RAW / "metadata.json", metadata)


if __name__ == "__main__":
    main()
