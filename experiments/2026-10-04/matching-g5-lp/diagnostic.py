# Document:    Prepared Matching Graph Five Elastic Diagnostics
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      fdf75e4bb782e60ab532a5fa89366fadde131d65ce98acaad37381a4fde73abc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare without solving; each explicitly launched case gets one elastic LP."""

import argparse
import importlib.util
import json
import subprocess
import time
from hashlib import sha256
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/matching-g5-lp-20261004"
ANCHORS = [tuple(range(a, a + 3)) for a in (1, 5, 9, 13)]
HUBS = [4, 8, 12, 16]
EXCESS = [2, 0, 0, 0, 0, 2]
INF = 2**63 - 1
PROOF = DAY / "four-seven-pinned-regularity/check.py"
HELPER = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/lp_core.py"
REGISTRY = DAY / "matching-seed-registry/audit.json"


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def elastic(rows):
    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetNumThreads(1)
    solver.SetTimeLimit(1000)
    assert solver.SetSolverSpecificParametersAsString("random_seed: 2026104")
    xs = [solver.NumVar(0, 1, f"x_{i}") for i in range(1200)]
    constraints = []
    for index, (ids, coefficients, lo, hi) in enumerate(rows):
        row = solver.Constraint(lo, hi if hi != INF else solver.infinity(), f"row_{index}")
        for i, coefficient in zip(ids, coefficients, strict=True):
            row.SetCoefficient(xs[i], coefficient)
        for side, bound, coefficient in [("lo", lo, 1), ("hi", hi, -1)]:
            if bound != INF:
                slack = solver.NumVar(0, solver.infinity(), f"{side}_{index}")
                row.SetCoefficient(slack, coefficient)
                solver.Objective().SetCoefficient(slack, 1)
        constraints.append(row)
    solver.Objective().SetMinimization()
    return solver, xs, constraints


def prepare():
    assert not RAW.exists() and not (HERE / "manifest.json").exists()
    registry = json.loads(REGISTRY.read_text())
    assert registry["passed"] and registry["optimization_calls"] == 0
    blocks = list(combinations(range(1, 17), 5))
    ordinary = [b for b in blocks if all(len(set(b) & set(a)) <= 1 for a in ANCHORS)]
    pairs = list(combinations(range(1, 17), 2))
    proof = load(PROOF, "separate_pinned_model_checker")
    RAW.mkdir()
    (RAW / "diagnostic-frozen.py").write_bytes(Path(__file__).read_bytes())
    cases = []
    for source in registry["cases"]:
        if source["label"] not in ("soft-raw-17", "soft-score-19"):
            continue
        assert source["registry_open_in_graph_5"]
        label = source["label"]
        folder, raw = HERE / label, RAW / label
        folder.mkdir()
        raw.mkdir()
        seed_path = ROOT / source["seed_path"]
        assert digest(seed_path) == source["seed_sha256"]
        seed = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
        fixed = sorted(b for b in seed if any(set(a) <= set(b) for a in ANCHORS))
        assert len(fixed) == 28 and len([b for b in seed if b in ordinary]) == 36
        (folder / "seed.txt").write_bytes(seed_path.read_bytes())
        targets = {}
        for anchor, hub in zip(ANCHORS, HUBS, strict=True):
            for point in anchor:
                for other in range(1, 17):
                    if point != other:
                        targets[tuple(sorted((point, other)))] = (
                            7 if other in anchor else 6 if other == hub else 5
                        )
        targets |= {pair: 5 + e for pair, e in zip(combinations(HUBS, 2), EXCESS, strict=True)}
        conditions = [(t, 1, INF if t in ANCHORS else 2) for t in combinations(range(1, 17), 3)]
        conditions += [((p,), 20, 20) for p in range(1, 17)]
        conditions += [(pair, targets[pair], targets[pair]) for pair in pairs]
        rows = [(list(range(1200)), [1] * 1200, 36, 36)]
        for support, lo, hi in conditions:
            ids = [i for i, b in enumerate(ordinary) if all(p in b for p in support)]
            shift = sum(all(p in b for p in support) for b in fixed)
            rows.append((ids, [1] * len(ids), lo - shift, hi if hi == INF else hi - shift))
        proto = cp_model_pb2.CpModelProto()
        for b in ordinary:
            proto.variables.add(name=f"block_{blocks.index(b)}", domain=[0, 1])
        for ids, coefficients, lo, hi in rows:
            row = proto.constraints.add().linear
            row.vars.extend(ids)
            row.coeffs.extend(coefficients)
            row.domain.extend([lo, hi])
        independently_ordinary, independent_rows, _ = proof.derive(ANCHORS, HUBS, fixed)
        assert independently_ordinary == ordinary
        for pair, e in zip(combinations(HUBS, 2), EXCESS, strict=True):
            index = 577 + pairs.index(pair)
            support, _, _ = independent_rows[index]
            bound = 5 + e - sum(set(pair) <= set(b) for b in fixed)
            independent_rows[index] = (support, bound, bound)
        proof.check_model(proto, ordinary, independent_rows)
        (raw / "model.pbtxt").write_text(text_format.MessageToString(proto))
        save(raw / "rows.json", rows)
        solver, _, _ = elastic(rows)
        (raw / "elastic-model.lp").write_text(solver.ExportModelAsLpFormat(False))
        heavy_text = "".join(" ".join(map(str, b)) + "\n" for b in fixed)
        manifest = {
            "case": label,
            "graph_index": 5,
            "hub_excesses": EXCESS,
            "hub_pair_targets": [7, 5, 5, 5, 5, 7],
            "heavy_blocks": fixed,
            "heavy_global_ids": [blocks.index(b) for b in fixed],
            "ordinary_global_ids": [blocks.index(b) for b in ordinary],
            "heavy_sha256": sha256(heavy_text.encode()).hexdigest(),
            "source_seed_path": source["seed_path"],
            "seed_sha256": digest(seed_path),
            "rows": 697,
            "columns": 1200,
            "model_sha256": digest(raw / "model.pbtxt"),
            "rows_sha256": digest(raw / "rows.json"),
            "elastic_model_sha256": digest(raw / "elastic-model.lp"),
            "source_sha256": digest(__file__),
            "checker_sha256": digest(PROOF),
            "workers": 1,
            "seconds": 1,
            "seed": 2026104,
            "optimization_calls": 0,
            "registry_link_classes": [entry["representative"] for entry in source["links"]],
            "scope": "One prepared fixed-heavy, graph-5 elastic diagnostic. Not yet launched.",
        }
        save(folder / "manifest.json", manifest)
        cases.append({"case": label, "manifest_sha256": digest(folder / "manifest.json")})
    assert len(cases) == 2
    save(
        HERE / "manifest.json",
        {
            "source_sha256": digest(__file__),
            "cases": cases,
            "optimization_calls": 0,
            "proposed_runs": 2,
            "seconds_each": 1,
            "workers_each": 1,
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "ortools_version": ortools_version,
            "input_sha256": {
                str(p.relative_to(ROOT)): digest(p) for p in [PROOF, HELPER, REGISTRY]
            },
        },
    )
    print(
        json.dumps(
            {
                "prepared": 2,
                "optimization_calls": 0,
                "manifest_sha256": digest(HERE / "manifest.json"),
            }
        )
    )


def run(case, gate_path):
    top = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == digest(HERE / "manifest.json")
    assert gate["runner_sha256"] == top["source_sha256"] == digest(__file__)
    for path, expected in top["input_sha256"].items():
        assert digest(ROOT / path) == expected
    folder, raw = HERE / case, RAW / case
    entry = next(r for r in top["cases"] if r["case"] == case)
    assert digest(folder / "manifest.json") == entry["manifest_sha256"]
    manifest = json.loads((folder / "manifest.json").read_text())
    for name, field in [
        ("rows.json", "rows_sha256"),
        ("model.pbtxt", "model_sha256"),
        ("elastic-model.lp", "elastic_model_sha256"),
    ]:
        assert digest(raw / name) == manifest[field]
    with (folder / "launch.json").open("x") as handle:
        json.dump(
            {
                "case": case,
                "gate_sha256": digest(gate_path),
                "workers": 1,
                "seconds": 1,
                "seed": 2026104,
                "optimization_calls": 1,
            },
            handle,
            indent=2,
        )
        handle.write("\n")
    rows = json.loads((raw / "rows.json").read_text())
    solver, xs, constraints = elastic(rows)
    assert (
        sha256(solver.ExportModelAsLpFormat(False).encode()).hexdigest()
        == (manifest["elastic_model_sha256"])
    )
    solver.EnableOutput()
    before = time.monotonic()
    status = solver.Solve()
    result = {
        "case": case,
        "status": {0: "OPTIMAL", 1: "FEASIBLE"}.get(status, str(status)),
        "seconds": time.monotonic() - before,
        "solver": solver.SolverVersion(),
        "graph_index": 5,
        "optimization_calls": 1,
        "manifest_sha256": digest(folder / "manifest.json"),
    }
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        values = [x.solution_value() for x in xs]
        dual = [row.dual_value() for row in constraints]
        save(raw / "primal.json", values)
        save(raw / "dual-numerical.json", dual)
        save(
            raw / "all-variables.json", [[x.name(), x.solution_value()] for x in solver.variables()]
        )
        result["branch_elastic_objective"] = solver.Objective().Value()
        helper = load(HELPER, "frozen_matching_exact_arithmetic")
        if result["branch_elastic_objective"] == 0:
            exact = helper.exact_primal(rows, values, 10**9)
            assert exact is not None
            save(folder / "exact-primal.json", exact)
            result["exact_fractional_feasibility"] = True
        else:
            certificate = helper.exact_dual(rows, dual, 10**6)
            assert certificate["proves_infeasible"]
            certificate |= {
                "model_sha256": manifest["model_sha256"],
                "heavy_sha256": manifest["heavy_sha256"],
                "manifest_sha256": digest(folder / "manifest.json"),
            }
            save(folder / "dual.json", certificate)
            proof = load(PROOF, "separate_matching_dual_replay")
            proof.INPUT = folder / "manifest.json"
            blocks = list(combinations(range(1, 17), 5))
            ordinary = [blocks[i] for i in manifest["ordinary_global_ids"]]
            concrete = [([ordinary[i] for i in ids], lo, hi) for ids, _, lo, hi in rows]
            checked = proof.check_dual(certificate, ordinary, concrete, manifest)
            save(
                folder / "dual-audit.json",
                {
                    "passed": True,
                    "exact": checked,
                    "dual_sha256": digest(folder / "dual.json"),
                    "checker_sha256": digest(PROOF),
                    "scope": "Fixed heavy tuple and graph 5 only; not an all-graph cut.",
                },
            )
            result["exact_gap"] = checked["gap"]
            result["exact_fractional_feasibility"] = False
    save(folder / "result.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "run"])
    parser.add_argument("--case", choices=["soft-raw-17", "soft-score-19"])
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        assert args.case and args.gate
        run(args.case, args.gate)
