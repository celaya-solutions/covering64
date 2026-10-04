# Document:    Exact Elastic Lower Bounds from the Complete Link Sweep
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e84072a10f8f370974e1004b6f32453dc14f77249c33900ff3d8e8b8aab48059
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Lift saved numerical row weights into exact, bounded elastic support planes."""

import hashlib
import importlib.util
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SWEEP = ROOT / "experiments/2026-10-04/lp-guided-full-sweep"
RAW = ROOT / "experiments/scratch/lp-guided-sweep-cuts-20261004"
DENOMINATOR = 1_000_000
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def lift(rows, numerical):
    """For |w_i| <= D, (rhs - box - heavy dot)/D <= total L1 row slack.

    Positive weights multiply lower bounds and negative weights upper bounds.
    Each row contributes at most |w_i| times its violated side to the weighted
    deficit. Maximizing the ordinary linear form over [0,1]^1200 gives the box
    term. Thus the bound needs no numerical optimality or dual-feasibility claim.
    """
    assert len(rows) == len(numerical) == 697
    assert all(math.isfinite(value) for value in numerical)
    weights = [max(-DENOMINATOR, min(DENOMINATOR, round(value * DENOMINATOR)))
               for value in numerical]
    ordinary, heavy, constant = [0] * 1200, [0] * 276, 0
    for index, (ordinary_ids, heavy_ids, lower, upper) in enumerate(rows):
        weight = weights[index]
        if weight < 0 and upper == INF:
            weights[index] = weight = 0
        if not weight:
            continue
        bound = lower if weight > 0 else upper
        assert abs(bound) < 2**60
        constant += weight * bound
        for column in ordinary_ids:
            ordinary[column] += weight
        for column in heavy_ids:
            heavy[column] += weight
    box = sum(max(0, value) for value in ordinary)
    return weights, ordinary, heavy, constant, box


def main():
    assert not RAW.exists() and not (HERE / "bundle.json").exists()
    result = json.loads((SWEEP / "result.json").read_text())
    assert result["complete_neighborhood"] and result["evaluated_count"] == 136
    assert result["source_sha256"] == sha(SWEEP / "sweep.py")
    assert result["proposal_sha256"] == sha(SWEEP / "proposal.json")
    spec = importlib.util.spec_from_file_location("frozen_sweep_basis", SWEEP / "sweep.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    blocks, ordinary, heavy, _, rows = module.basis()
    heavy_global_ids = [blocks.index(block) for block in heavy]
    positions = {global_id: local_id for local_id, global_id in enumerate(heavy_global_ids)}
    records = [record for record in result["records"] if not record["cached"]]
    assert len(records) == result["fresh_evaluations"] == 113
    RAW.mkdir()
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    cuts = []
    for record in records:
        assert record["status"] == "OPTIMAL"
        dual_path = ROOT / record["dual_path"]
        assert sha(dual_path) == record["dual_sha256"]
        weights, ordinary_coefficients, coefficients, constant, box = lift(
            rows, json.loads(dual_path.read_text()))
        chosen = [positions[index] for index in record["heavy_global_ids"]]
        lhs = sum(coefficients[index] for index in chosen)
        gap = Fraction(constant - box - lhs, DENOMINATOR)
        assert gap > 0
        assert float(gap) <= record["objective"] + 1e-6
        certificate = {
            "weights": [[index, weight] for index, weight in enumerate(weights) if weight],
            "denominator": DENOMINATOR,
            "constant_numerator": constant,
            "ordinary_coefficients": ordinary_coefficients,
            "ordinary_box_max_numerator": box,
            "heavy_coefficients": coefficients,
            "source_heavy_global_ids": record["heavy_global_ids"],
            "source_gap": [gap.numerator, gap.denominator],
            "source_dual_path": record["dual_path"],
            "source_dual_sha256": record["dual_sha256"],
            "source_shifted_rows_sha256": record["shifted_rows_sha256"],
        }
        certificate_path = RAW / f"rank-{record['rank']:03d}.json"
        dump(certificate_path, certificate)
        cuts.append({
            "id": f"complete-sweep-{record['rank']:03d}",
            "direction": ">=",
            "denominator": DENOMINATOR,
            "rhs": constant - box,
            "coefficients": coefficients,
            "constant_numerator": constant,
            "ordinary_box_max_numerator": box,
            "ordinary_coefficients_sha256": digest(ordinary_coefficients),
            "maximum_signed_row_weight": max(map(abs, weights)),
            "source_gap": [gap.numerator, gap.denominator],
            "source_heavy_sha256": record["heavy_sha256"],
            "certificate_path": str(certificate_path.relative_to(ROOT)),
            "certificate_sha256": sha(certificate_path),
        })
    bundle = {
        "version": "v1.0.0",
        "scope": "Regular four-sevenfold family, fixed anchors; elastic L1 lower bounds.",
        "global_lower_bound_claim": False,
        "covering_witness": False,
        "solver_calls": 0,
        "builder_sha256": sha(__file__),
        "sweep_source_sha256": sha(SWEEP / "sweep.py"),
        "sweep_result_sha256": sha(SWEEP / "result.json"),
        "basis_rows_sha256": digest(rows),
        "heavy_global_ids": heavy_global_ids,
        "ordinary_global_ids": [blocks.index(block) for block in ordinary],
        "cuts": cuts,
    }
    dump(HERE / "bundle.json", bundle)
    print(json.dumps({"cuts": len(cuts), "bundle_sha256": sha(HERE / "bundle.json"),
                      "minimum_source_gap": min(float(Fraction(*c["source_gap"]))
                                                for c in cuts), "solver_calls": 0}))


if __name__ == "__main__":
    main()
