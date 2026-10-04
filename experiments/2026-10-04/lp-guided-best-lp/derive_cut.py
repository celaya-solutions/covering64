# Document:    Necessary Heavy Cut from the LP-Guided Best Tuple
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e9dc54af2dd3d05ae8403e5b9f311c7aee1c531594b9844939a878f838297055
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import importlib.util
import itertools as it
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORACLE = ROOT / "experiments/2026-10-03/lookahead-cut-independent/check.py"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main():
    assert not (HERE / "cut.json").exists()
    manifest = json.loads((HERE / "manifest.json").read_text())
    dual = json.loads((HERE / "dual.json").read_text())
    replay = json.loads((HERE / "dual-audit.json").read_text())
    assert replay["passed"] and replay["dual_sha256"] == sha(HERE / "dual.json")
    assert manifest["generic_oracle_sha256"] == sha(ORACLE)
    assert dual["model_sha256"] == manifest["model_sha256"]
    assert dual["manifest_sha256"] == sha(HERE / "manifest.json")
    assert sha(ROOT / manifest["model"]) == manifest["model_sha256"]
    spec = importlib.util.spec_from_file_location("cut_basis", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    oracle.MODEL, oracle.WITNESS = ROOT / manifest["model"], HERE / "seed.txt"
    blocks, ordinary, heavy, fixed, rows = oracle.rebuild()
    weights = dict(dual["weights"])
    assert len(weights) == len(dual["weights"])
    ordinary_coefficients, heavy_coefficients = [0] * 1200, [0] * 276
    constant = 0
    for index, weight in weights.items():
        os, hs, lower, upper = rows[index]
        assert weight > 0 or upper != INF
        constant += weight * (lower if weight > 0 else upper)
        for i in os:
            ordinary_coefficients[i] += weight
        for i in hs:
            heavy_coefficients[i] += weight
    box = sum(max(0, a) for a in ordinary_coefficients)
    rhs = constant - box
    lhs = sum(c for b, c in zip(heavy, heavy_coefficients, strict=True) if b in fixed)
    assert constant - lhs == dual["rhs_numerator"]
    assert box == dual["box_max_numerator"]
    assert rhs - lhs == 5425 > 0
    max_weight = max(abs(w) for w in weights.values())
    assert max_weight <= dual["denominator"] == 1000
    # Reverse the incidence calculation independently, from block subsets,
    # and recover the constants from the fixed-model bounds plus incidence.
    supports = [()] + list(it.combinations(range(1, 17), 3))
    supports += [(p,) for p in range(1, 17)] + list(it.combinations(range(1, 17), 2))
    reverse_heavy = [
        sum(w for i, w in weights.items() if set(supports[i]) <= set(b)) for b in heavy
    ]
    reverse_ordinary = [
        sum(w for i, w in weights.items() if set(supports[i]) <= set(b)) for b in ordinary
    ]
    assert heavy_coefficients == reverse_heavy and ordinary_coefficients == reverse_ordinary
    proto = text_format.Parse(oracle.MODEL.read_text(), cp_model_pb2.CpModelProto())
    recovered_constant = 0
    for i, weight in weights.items():
        lower, upper = proto.constraints[i].linear.domain
        bound = lower if weight > 0 else upper
        assert bound != INF
        incidence = sum(set(supports[i]) <= set(b) for b in fixed)
        recovered_constant += weight * (bound + incidence)
    assert recovered_constant == constant
    cut = {
        "version": "v1.0.0",
        "id": "lp-guided-best-01",
        "direction": ">=",
        "rhs": rhs,
        "denominator": dual["denominator"],
        "coefficients": heavy_coefficients,
        "heavy_global_ids": [blocks.index(b) for b in heavy],
        "heavy_blocks": heavy,
        "ordinary_global_ids": [blocks.index(b) for b in ordinary],
        "ordinary_combined_coefficients_sha256": digest(ordinary_coefficients),
        "constant_numerator": constant,
        "ordinary_box_max_numerator": box,
        "dual_path": str((HERE / "dual.json").relative_to(ROOT)),
        "dual_sha256": sha(HERE / "dual.json"),
        "source_model_sha256": manifest["model_sha256"],
        "source_heavy_sha256": manifest["heavy_sha256"],
        "source_seed_sha256": manifest["seed_sha256"],
        "source_manifest_sha256": sha(HERE / "manifest.json"),
        "source_dual_audit_sha256": sha(HERE / "dual-audit.json"),
        "deriver_sha256": sha(Path(__file__)),
        "generic_oracle_sha256": sha(ORACLE),
        "source_lhs": lhs,
        "source_violation_numerator": rhs - lhs,
        "maximum_signed_row_weight": max_weight,
        "elastic_lower_bound_denominator": 1000,
        "scope": (
            "Necessary inequality for the fixed-anchor regular degree20 four-sevenfold "
            "family with all six hub graphs retained. No first-link or unrestricted claim."
        ),
    }
    (HERE / "cut.json").write_text(json.dumps(cut, indent=2) + "\n")
    audit = {
        "passed": True,
        "cut_sha256": sha(HERE / "cut.json"),
        "deriver_sha256": sha(Path(__file__)),
        "reverse_heavy_coefficients": len(reverse_heavy),
        "reverse_ordinary_coefficients": len(reverse_ordinary),
        "rows": len(rows),
        "signed_rows": len(weights),
        "constant": constant,
        "ordinary_box": box,
        "rhs": rhs,
        "source_lhs": lhs,
        "violation_numerator": rhs - lhs,
        "normalized_gap": [217, 40],
        "solver_calls": 0,
        "scope": "Reverse block-incidence and lifted-bound cross-check; root replay is separate.",
    }
    (HERE / "cut-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit), flush=True)


if __name__ == "__main__":
    main()
