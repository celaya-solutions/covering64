# Document:    Nearest Step 038 Fixed Graph One Elastic Diagnostic
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      8bcf8efb5d83d25ef81c9e57c782aa2bef12442faf3d5650846c92ed95ad1b3c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""One authorized elastic LP, with independently rebuilt fixed-graph rows."""

import importlib.util
import json
import platform
import subprocess
import sys
import time
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.linear_solver import pywraplp
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/nearest-step038-g1-lp-20261004"
DAY = HERE.parent
INF = 2**63 - 1
ANCHORS = [tuple(range(a, a + 3)) for a in (1, 5, 9, 13)]
HUBS = [4, 8, 12, 16]
EXCESS = [0, 1, 1, 1, 1, 0]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert not RAW.exists(), "Do not repeat this authorized run"
    RAW.mkdir()
    (RAW / "run-frozen.py").write_bytes(Path(__file__).read_bytes())
    records_path = DAY / "nearest-heavy-master/result.json"
    record = json.loads(records_path.read_text())["records"][38]
    assert record["step"] == 38
    blocks = list(combinations(range(1, 17), 5))
    triples = list(combinations(range(1, 17), 3))
    pairs = list(combinations(range(1, 17), 2))
    fixed = [blocks[i] for i in record["heavy_global_ids"]]
    ordinary = [b for b in blocks if all(len(set(b) & set(a)) <= 1 for a in ANCHORS)]
    assert len(fixed) == 28 and len(ordinary) == 1200
    input_seed = DAY / "lp-guided-best-lp/seed.txt"
    previous = [tuple(map(int, line.split())) for line in input_seed.read_text().splitlines()]
    retained = [b for b in previous if b in ordinary]
    assert len(retained) == 36
    seed = sorted(fixed + retained)
    seed_path = HERE / "seed.txt"
    seed_path.write_text("".join(" ".join(map(str, b)) + "\n" for b in seed))
    for label, command in [
        ("package", [str(ROOT / ".venv/bin/covering64"), "verify"]),
        ("standalone", [sys.executable, str(ROOT / "scripts/check_cover.py")]),
    ]:
        proc = subprocess.run(
            command + [str(seed_path), "--expected-blocks", "64"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        result = json.loads(proc.stdout)
        assert proc.returncode in (0, 1) and result["blocks"] == 64
        save(HERE / f"seed-{label}.json", result)
    p = json.loads((HERE / "seed-package.json").read_text())
    q = json.loads((HERE / "seed-standalone.json").read_text())
    assert p["uncovered"] == q["uncovered"] and p["valid"] == q["valid"]

    targets = {}
    for anchor, hub in zip(ANCHORS, HUBS, strict=True):
        for point in anchor:
            for other in range(1, 17):
                if point != other:
                    targets[tuple(sorted((point, other)))] = (
                        7 if other in anchor else 6 if other == hub else 5
                    )
    targets |= {
        pair: 5 + excess for pair, excess in zip(combinations(HUBS, 2), EXCESS, strict=True)
    }
    conditions = [(t, 1, INF if t in ANCHORS else 2) for t in triples]
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
    model_path = RAW / "model.pbtxt"
    model_path.write_text(text_format.MessageToString(proto))
    save(RAW / "rows.json", rows)

    # Separate general pin theorem reconstructs all unrestricted-completion
    # consequences; only its six hub-pair bounds are narrowed to this graph.
    proof_path = DAY / "four-seven-pinned-regularity/check.py"
    proof = load(proof_path, "independent_pinned_profile")
    independently_ordinary, independent_rows, _ = proof.derive(ANCHORS, HUBS, fixed)
    assert independently_ordinary == ordinary
    for pair, excess in zip(combinations(HUBS, 2), EXCESS, strict=True):
        index = 577 + pairs.index(pair)
        support, _, _ = independent_rows[index]
        bound = 5 + excess - sum(set(pair) <= set(b) for b in fixed)
        independent_rows[index] = (support, bound, bound)
    proof.check_model(proto, ordinary, independent_rows)
    assert len(rows) == 697
    save(
        HERE / "model-audit.json",
        {
            "passed": True,
            "rows": 697,
            "columns": 1200,
            "fixed_hub_graph": 1,
            "hub_pair_targets": [5 + x for x in EXCESS],
            "model_sha256": digest(model_path),
            "separate_checker_sha256": digest(proof_path),
            "scope": "Only nearest step 038 heavy pins and hub graph 1.",
        },
    )

    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.SetNumThreads(1)
    solver.SetTimeLimit(10000)
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
    (RAW / "elastic-model.lp").write_text(solver.ExportModelAsLpFormat(False))
    heavy_text = "".join(" ".join(map(str, b)) + "\n" for b in sorted(fixed))
    manifest = {
        "model_sha256": digest(model_path),
        "heavy_sha256": sha256(heavy_text.encode()).hexdigest(),
        "heavy_blocks": fixed,
        "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "seed_sha256": digest(seed_path),
        "retained_ordinary_blocks": retained,
        "source_sha256": digest(Path(__file__)),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python_version": platform.python_version(),
        "ortools_version": ortools_version,
        "workers": 1,
        "seconds": 10,
        "seed": 2026104,
        "optimization_calls": 1,
        "graph_index": 1,
        "hub_excesses": EXCESS,
        "broad_elastic_objective": record["lp"]["objective"],
        "inputs": {
            str(path.relative_to(ROOT)): digest(path)
            for path in [records_path, input_seed, proof_path]
        },
    }
    save(HERE / "manifest.json", manifest)
    solver.EnableOutput()
    started = time.monotonic()
    status = solver.Solve()
    seconds = time.monotonic() - started
    result = {
        "status": {0: "OPTIMAL", 1: "FEASIBLE", 6: "NOT_SOLVED"}.get(status, str(status)),
        "seconds": seconds,
        "solver": solver.SolverVersion(),
        "graph_index": 1,
        "broad_elastic_objective": record["lp"]["objective"],
        "manifest_sha256": digest(HERE / "manifest.json"),
        "covering_witness": False,
    }
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        values = [x.solution_value() for x in xs]
        numerical_dual = [row.dual_value() for row in constraints]
        save(RAW / "primal.json", values)
        save(RAW / "dual-numerical.json", numerical_dual)
        save(
            RAW / "all-variables.json", [[x.name(), x.solution_value()] for x in solver.variables()]
        )
        result["branch_elastic_objective"] = solver.Objective().Value()
        helper_path = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/lp_core.py"
        helper = load(helper_path, "frozen_exact_lp_arithmetic")
        assert (
            digest(helper_path)
            == "35d379455244f2511b00d6fb8dff01de69c1c6a0ca2869c3c73c7e03ce5220d1"
        )
        if result["branch_elastic_objective"] == 0:
            exact = helper.exact_primal(rows, values, 10**9)
            assert exact is not None, "Numerical zero is not an exact feasible witness"
            save(HERE / "exact-primal.json", exact)
            result["exact_fractional_feasibility"] = True
        else:
            certificate = helper.exact_dual(rows, numerical_dual, 10**6)
            assert certificate["proves_infeasible"]
            certificate |= {
                "model_sha256": manifest["model_sha256"],
                "heavy_sha256": manifest["heavy_sha256"],
                "manifest_sha256": digest(HERE / "manifest.json"),
            }
            save(HERE / "dual.json", certificate)
            proof.INPUT = HERE / "manifest.json"
            exact = proof.check_dual(certificate, ordinary, independent_rows, manifest)
            save(
                HERE / "dual-audit.json",
                {
                    "passed": True,
                    "exact": exact,
                    "dual_sha256": digest(HERE / "dual.json"),
                    "checker_sha256": digest(proof_path),
                    "scope": "The fixed graph 1 completion only; not an all-graph cut.",
                },
            )
            result["exact_gap"] = exact["gap"]
            result["exact_fractional_feasibility"] = False
        residual = sum(
            max(Fraction(lo) - sum(Fraction(values[i]) for i in ids), 0)
            + (max(sum(Fraction(values[i]) for i in ids) - hi, 0) if hi != INF else 0)
            for ids, _, lo, hi in rows
        )
        result["rational_replayed_elastic_residual_upper_bound"] = float(residual) + 1e-10
    save(HERE / "result.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
