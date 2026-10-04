# Document:    Separate Exact Replay of Twelve Fixed-Heavy LP Certificates
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7632e21248d78ba5bbc764ea0a68c4fcf95dee910407a72dc02cdd33eadd933c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import ast
import copy
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/cut-survivor-lp-screen-v1.0.0"
ORACLE = HERE.parent / "lookahead-cut-independent/check.py"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(certificate, row_data, case, manifest_hash):
    assert set(certificate) == {
        "denominator",
        "weights",
        "rhs_numerator",
        "box_max_numerator",
        "gap",
        "proves_infeasible",
        "heavy_sha256",
        "model_sha256",
        "manifest_sha256",
    }
    assert certificate["model_sha256"] == case["model_sha256"]
    assert certificate["heavy_sha256"] == case["heavy_sha256"]
    assert certificate["manifest_sha256"] == manifest_hash
    denominator = certificate["denominator"]
    assert type(denominator) is int and denominator > 0
    weights = certificate["weights"]
    assert type(weights) is list and weights
    last = -1
    rhs = 0
    columns = [0 for _ in range(1200)]
    for pair in weights:
        assert type(pair) is list and len(pair) == 2
        index, weight = pair
        assert type(index) is int and type(weight) is int
        assert last < index < len(row_data) and weight != 0
        last = index
        support, lower, upper = row_data[index]
        assert weight > 0 or upper != INF
        rhs += weight * (lower if weight > 0 else upper)
        for column in support:
            columns[column] += weight
    box = sum(value for value in columns if value > 0)
    gap = Fraction(rhs - box, denominator)
    assert type(certificate["rhs_numerator"]) is int
    assert type(certificate["box_max_numerator"]) is int
    assert certificate["rhs_numerator"] == rhs
    assert certificate["box_max_numerator"] == box
    assert certificate["gap"] == [gap.numerator, gap.denominator]
    assert rhs > box and certificate["proves_infeasible"] is True
    return {
        "rhs_numerator": rhs,
        "box_max_numerator": box,
        "gap": [gap.numerator, gap.denominator],
        "signed_rows": len(weights),
        "combined_columns_sha256": hashlib.sha256(
            json.dumps(columns, separators=(",", ":")).encode()
        ).hexdigest(),
    }


def main():
    manifest_path = HERE / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    results_path = HERE / "results.json"
    results = json.loads(results_path.read_text())
    assert manifest["gate_passed"]
    assert manifest["case_count"] == results["case_count"] == 12
    assert results["counts"] == {
        "RATIONAL_INFEASIBLE": 12,
        "RATIONAL_FEASIBLE": 0,
        "UNRESOLVED": 0,
    }
    assert sha(manifest_path) == results["manifest_sha256"]
    assert sha(ORACLE) == manifest["generic_oracle_sha256"]
    assert sha(RAW / "lp-frozen-run.py") == results["runner_sha256"]
    assert sha(RAW / "lp-frozen-lp_core.py") == results["lp_core_sha256"]
    # The current runner only wraps one long string for lint; executed source is retained.
    assert ast.dump(ast.parse((HERE / "run.py").read_text())) == ast.dump(
        ast.parse((RAW / "lp-frozen-run.py").read_text())
    )
    spec = importlib.util.spec_from_file_location("model_oracle", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    checked = []
    controls = []
    for case, result in zip(manifest["cases"], results["cases"], strict=True):
        assert result["exact_status"] == "RATIONAL_INFEASIBLE"
        assert result["heavy_sha256"] == case["heavy_sha256"]
        assert result["model_sha256"] == case["model_sha256"]
        assert sha(ROOT / case["model"]) == case["model_sha256"]
        assert sha(ROOT / case["seed"]) == case["seed_sha256"]
        oracle.MODEL, oracle.WITNESS = ROOT / case["model"], ROOT / case["seed"]
        _, ordinary, heavy, fixed, symbolic = oracle.rebuild()
        assert len(ordinary) == 1200 and len(symbolic) == 697
        canonical = "".join(" ".join(map(str, b)) + "\n" for b in sorted(fixed))
        assert hashlib.sha256(canonical.encode()).hexdigest() == case["heavy_sha256"]
        assert sorted(map(tuple, case["heavy_blocks"])) == sorted(fixed)
        rows = []
        for support, heavy_ids, lower, upper in symbolic:
            shift = sum(heavy[i] in fixed for i in heavy_ids)
            rows.append((support, lower - shift, upper if upper == INF else upper - shift))
        path = ROOT / result["dual"]
        assert sha(path) == result["dual_sha256"]
        cert = json.loads(path.read_text())
        details = replay(cert, rows, case, sha(manifest_path))
        checked.append(
            {
                "index": case["index"],
                "heavy_sha256": case["heavy_sha256"],
                "model_sha256": case["model_sha256"],
                "dual_sha256": sha(path),
                "passed": True,
                **details,
            }
        )
        mutations = {
            "wrong_model": lambda c: c.update(model_sha256="0" * 64),
            "wrong_heavy": lambda c: c.update(heavy_sha256="0" * 64),
            "wrong_manifest": lambda c: c.update(manifest_sha256="0" * 64),
            "zero_denominator": lambda c: c.update(denominator=0),
            "wrong_rhs": lambda c: c.update(rhs_numerator=c["rhs_numerator"] + 1),
            "wrong_box": lambda c: c.update(box_max_numerator=c["box_max_numerator"] + 1),
            "wrong_gap": lambda c: c.update(gap=[0, 1]),
            "duplicate_weight": lambda c: c["weights"].insert(0, c["weights"][0]),
            "dropped_weight": lambda c: c["weights"].pop(0),
            "bad_row_index": lambda c: c["weights"].append([697, 1]),
            "wrong_claim": lambda c: c.update(proves_infeasible=False),
        }
        for name, mutate in mutations.items():
            damaged = copy.deepcopy(cert)
            mutate(damaged)
            try:
                replay(damaged, rows, case, sha(manifest_path))
            except AssertionError:
                controls.append({"index": case["index"], "damage": name, "rejected": True})
            else:
                raise AssertionError(f"Damaged control accepted: {case['index']} {name}")
    audit = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(manifest_path),
        "results_sha256": sha(results_path),
        "generic_oracle_sha256": sha(ORACLE),
        "independently_reconstructed_models": len(checked),
        "certificates_replayed": len(checked),
        "cases": checked,
        "damaged_controls_rejected": len(controls),
        "damaged_controls": controls,
        "solver_calls": 0,
        "scope": "Twelve fixed-heavy regular-family contradictions; no unrestricted theorem.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(
        json.dumps(
            {k: audit[k] for k in ["passed", "certificates_replayed", "damaged_controls_rejected"]}
        )
    )


if __name__ == "__main__":
    main()
