# Document:    Fourteen Exact Parametric Cuts for the Regular Four-Sevenfold Family
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      ab87e88827b6a4b306eb719bec2ebc776f57ba6b12d27d930e2c63f9bc0f69e9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORACLE = HERE.parent / "lookahead-cut-independent/check.py"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector_hash(values):
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def derive(dual, rows):
    ordinary = [0] * 1200
    heavy = [0] * 276
    constant = 0
    seen = set()
    for row_id, weight in dual["weights"]:
        assert type(row_id) is int and type(weight) is int and weight != 0
        assert 0 <= row_id < 697 and row_id not in seen
        seen.add(row_id)
        os, hs, lower, upper = rows[row_id]
        assert weight > 0 or upper != INF
        constant += weight * (lower if weight > 0 else upper)
        for index in os:
            ordinary[index] += weight
        for index in hs:
            heavy[index] += weight
    box = sum(max(0, value) for value in ordinary)
    return {
        "direction": ">=",
        "denominator": dual["denominator"],
        "coefficients": heavy,
        "rhs": constant - box,
        "constant_numerator": constant,
        "ordinary_box_max_numerator": box,
        "ordinary_combined_coefficients_sha256": vector_hash(ordinary),
    }


def main():
    assert not (HERE / "cut-bundle.json").exists(), "Preserve a frozen bundle."
    manifest = json.loads((HERE / "manifest.json").read_text())
    results = json.loads((HERE / "results.json").read_text())
    audit = json.loads((HERE / "audit.json").read_text())
    assert audit["passed"] and audit["certificates_replayed"] == 12
    assert sha(HERE / "manifest.json") == audit["manifest_sha256"]
    assert sha(HERE / "results.json") == audit["results_sha256"]
    assert sha(HERE / "check.py") == audit["checker_sha256"]
    assert sha(ORACLE) == manifest["generic_oracle_sha256"]
    spec = importlib.util.spec_from_file_location("incidence_oracle", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    oracle.MODEL = ROOT / manifest["cases"][0]["model"]
    oracle.WITNESS = ROOT / manifest["cases"][0]["seed"]
    blocks, ordinary, heavy, _, rows = oracle.rebuild()
    global_ids = {b: i for i, b in enumerate(blocks)}
    heavy_ids = [global_ids[b] for b in heavy]
    ordinary_ids = [global_ids[b] for b in ordinary]
    cuts = []
    originals = [
        ("original-01", "lookahead-parametric-cut", "lookahead-heavy-strengthened"),
        ("original-02", "cut-pilot-parametric-cut", "cut-pilot-heavy-completion"),
    ]
    for cut_id, folder, source in originals:
        cut_path = HERE.parent / folder / "cut.json"
        old = json.loads(cut_path.read_text())
        dual_path = HERE.parent / source / "dual.json"
        dual = json.loads(dual_path.read_text())
        assert sha(dual_path) == old["dual_sha256"]
        assert old["heavy_global_ids"] == heavy_ids
        assert old["ordinary_global_ids"] == ordinary_ids
        new = derive(dual, rows)
        for key in [
            "direction",
            "denominator",
            "coefficients",
            "rhs",
            "constant_numerator",
            "ordinary_box_max_numerator",
        ]:
            assert new[key] == old[key]
        assert new["ordinary_combined_coefficients_sha256"] == vector_hash(
            old["ordinary_combined_coefficients"]
        )
        source_global_ids = set(old["seed_heavy_global_ids"])
        source_heavy = [b for b in heavy if global_ids[b] in source_global_ids]
        canonical = "".join(" ".join(map(str, b)) + "\n" for b in source_heavy)
        new.update(
            {
                "id": cut_id,
                "source_case": None,
                "source_heavy_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                "source_model_sha256": old["source_model_sha256"],
                "source_cut_path": str(cut_path.relative_to(ROOT)),
                "source_cut_sha256": sha(cut_path),
                "dual_path": str(dual_path.relative_to(ROOT)),
                "dual_sha256": sha(dual_path),
                "source_lhs": old["seed_lhs"],
                "source_violation_numerator": old["seed_violation_numerator"],
            }
        )
        assert new["source_lhs"] == sum(
            new["coefficients"][i] for i, b in enumerate(heavy) if b in source_heavy
        )
        assert new["rhs"] - new["source_lhs"] == new["source_violation_numerator"]
        cuts.append(new)
    for case, result in zip(manifest["cases"], results["cases"], strict=True):
        assert case["heavy_sha256"] == result["heavy_sha256"]
        assert result["exact_status"] == "RATIONAL_INFEASIBLE"
        dual_path = ROOT / result["dual"]
        assert sha(dual_path) == result["dual_sha256"]
        dual = json.loads(dual_path.read_text())
        new = derive(dual, rows)
        fixed = set(map(tuple, case["heavy_blocks"]))
        lhs = sum(new["coefficients"][i] for i, b in enumerate(heavy) if b in fixed)
        violation = new["rhs"] - lhs
        assert violation == dual["rhs_numerator"] - dual["box_max_numerator"] > 0
        assert new["ordinary_box_max_numerator"] == dual["box_max_numerator"]
        assert Fraction(violation, new["denominator"]) == Fraction(*dual["gap"])
        new.update(
            {
                "id": f"survivor-{case['index']:02d}",
                "source_case": case["index"],
                "source_heavy_sha256": case["heavy_sha256"],
                "source_model_sha256": case["model_sha256"],
                "dual_path": str(dual_path.relative_to(ROOT)),
                "dual_sha256": sha(dual_path),
                "source_lhs": lhs,
                "source_violation_numerator": violation,
            }
        )
        cuts.append(new)
    bundle = {
        "version": "v1.0.0",
        "cut_count": len(cuts),
        "deriver_sha256": sha(Path(__file__)),
        "generic_oracle_sha256": sha(ORACLE),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "results_sha256": sha(HERE / "results.json"),
        "audit_sha256": sha(HERE / "audit.json"),
        "vector_hash_serialization": (
            "UTF-8 json.dumps(integer_vector, separators=(',', ':')); no newline"
        ),
        "heavy_global_ids": heavy_ids,
        "heavy_blocks": heavy,
        "ordinary_global_ids": ordinary_ids,
        "cuts": cuts,
        "scope": (
            "Necessary inequalities for the degree-20 regular four-sevenfold family "
            "with anchor triples {1,2,3},{5,6,7},{9,10,11},{13,14,15} and own hubs "
            "4,8,12,16. All six hub graphs retained. No unrestricted bound or "
            "first-link exclusion is asserted."
        ),
    }
    save(HERE / "cut-bundle.json", bundle)
    inventory_path = HERE.parent / "cut-pilot-parametric-cut/tuple-inventory.json"
    inventory = json.loads(inventory_path.read_text())
    assert sha(inventory_path) == manifest["inventory_sha256"]
    tuples = inventory["tuples"]
    screen = []
    for entry in tuples:
        fixed = set(map(tuple, entry["heavy_blocks"]))
        lhs_values = [
            sum(c["coefficients"][i] for i, b in enumerate(heavy) if b in fixed) for c in cuts
        ]
        violations = [max(0, c["rhs"] - lhs) for c, lhs in zip(cuts, lhs_values, strict=True)]
        screen.append(
            {
                "heavy_sha256": entry["heavy_sha256"],
                "lhs_by_cut": lhs_values,
                "violation_numerator_by_cut": violations,
                "excluded_by": [c["id"] for c, v in zip(cuts, violations, strict=True) if v > 0],
            }
        )
    screening = {
        "bundle_sha256": sha(HERE / "cut-bundle.json"),
        "inventory_sha256": sha(inventory_path),
        "distinct_labeled_tuples": len(screen),
        "excluded_tuples": sum(bool(s["excluded_by"]) for s in screen),
        "cut_ids": [c["id"] for c in cuts],
        "tuples": screen,
        "scope": "Labeled cut evaluation only; no additional symmetry orbit screen.",
    }
    save(HERE / "cut-bundle-saved-tuple-screen.json", screening)
    print(
        json.dumps(
            {
                "cut_count": len(cuts),
                "bundle_sha256": sha(HERE / "cut-bundle.json"),
                "saved_tuples_excluded": screening["excluded_tuples"],
            }
        )
    )


if __name__ == "__main__":
    main()
