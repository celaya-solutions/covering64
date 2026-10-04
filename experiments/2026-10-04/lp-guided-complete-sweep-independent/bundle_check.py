#!/usr/bin/env python3
# Document:    Independent Complete Sweep Dual Envelope Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild each support plane with exact integers, without any optimizer."""

import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

from basis import INF, digest, neighbors, rebuild, shifted

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUNDLE = HERE.parent / "lp-guided-sweep-cuts/bundle.json"
SWEEP = HERE.parent / "lp-guided-full-sweep"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rational(value):
    return [value.numerator, value.denominator]


def incumbent_upper(rows, heavy, chosen):
    pilot_path = HERE.parent / "lp-guided-link-switch/result.json"
    pilot = json.loads(pilot_path.read_text())
    entries = [record for turn in pilot["rounds"] for record in turn["results"]
               if record.get("objective") == pilot["final_objective"]]
    assert len(entries) == 1
    entry = entries[0]
    path = ROOT / entry["vector_path"]
    assert sha(path) == entry["vector_sha256"]
    raw = json.loads(path.read_text())
    assert len(raw) == 1200 and all(math.isfinite(v) for v in raw)
    values = [max(Fraction(0), min(Fraction(1), Fraction.from_float(v))) for v in raw]
    residual = Fraction(0)
    for ids, coefficients, lower, upper in shifted(rows, heavy, chosen):
        value = sum((coefficient * values[i] for i, coefficient
                     in zip(ids, coefficients, strict=True)), Fraction(0))
        residual += max(Fraction(0), lower - value)
        if upper != INF:
            residual += max(Fraction(0), value - upper)
    return residual, {"path": str(path.relative_to(ROOT)), "sha256": sha(path),
                      "clamped_values": sum(v != raw[i] for i, v in enumerate(values)),
                      "exact_residual": rational(residual)}


def main():
    output = HERE / "bundle-audit.json"
    assert not output.exists()
    bundle = json.loads(BUNDLE.read_text())
    assert sha(BUNDLE) == "27de6b8dee365b7bcf4adc205dedd6799f437476cfdbc35ec94cace953e877e8"
    proposal = json.loads((SWEEP / "proposal.json").read_text())
    result = json.loads((SWEEP / "result.json").read_text())
    assert sha(SWEEP / "result.json") == bundle["sweep_result_sha256"]
    assert sha(SWEEP / "sweep.py") == bundle["sweep_source_sha256"]
    assert sha(BUNDLE.parent / "build.py") == bundle["builder_sha256"]
    blocks, anchors, ordinary, heavy, rows = rebuild()
    assert digest(rows) == bundle["basis_rows_sha256"]
    assert [blocks.index(block) for block in ordinary] == bundle["ordinary_global_ids"]
    assert [blocks.index(block) for block in heavy] == bundle["heavy_global_ids"]
    heavy_positions = {blocks.index(block): i for i, block in enumerate(heavy)}
    ordinary_support = [[r for r, row in enumerate(rows) if i in row[0]]
                        for i in range(1200)]
    heavy_support = [[r for r, row in enumerate(rows) if i in row[1]] for i in range(276)]
    fresh = {record["rank"]: record for record in result["records"] if not record["cached"]}
    assert len(fresh) == len(bundle["cuts"]) == 113
    checked, planes = [], []
    for cut in bundle["cuts"]:
        rank = int(cut["id"].removeprefix("complete-sweep-"))
        record = fresh.pop(rank)
        certificate_path = ROOT / cut["certificate_path"]
        assert sha(certificate_path) == cut["certificate_sha256"]
        certificate = json.loads(certificate_path.read_text())
        denominator = certificate["denominator"]
        assert denominator == cut["denominator"] == 1000000
        assert cut["direction"] == ">="
        weights = [0] * len(rows)
        seen = set()
        for index, value in certificate["weights"]:
            assert type(index) is int and type(value) is int
            assert index not in seen and 0 <= index < len(rows)
            assert 0 < abs(value) <= denominator
            assert value >= 0 or rows[index][3] != INF
            seen.add(index)
            weights[index] = value
        numerical_path = ROOT / certificate["source_dual_path"]
        assert sha(numerical_path) == certificate["source_dual_sha256"] == record["dual_sha256"]
        numerical = json.loads(numerical_path.read_text())
        assert len(numerical) == len(rows) and all(math.isfinite(v) for v in numerical)
        expected = [round(max(-1.0, min(1.0, v)) * denominator) for v in numerical]
        expected = [0 if w < 0 and rows[i][3] == INF else w for i, w in enumerate(expected)]
        assert weights == expected
        constant = sum(w * (rows[r][2] if w > 0 else rows[r][3])
                       for r, w in enumerate(weights) if w)
        ordinary_coefficients = [sum(weights[r] for r in support)
                                 for support in ordinary_support]
        heavy_coefficients = [sum(weights[r] for r in support) for support in heavy_support]
        box = sum(value for value in ordinary_coefficients if value > 0)
        assert ordinary_coefficients == certificate["ordinary_coefficients"]
        assert heavy_coefficients == certificate["heavy_coefficients"] == cut["coefficients"]
        assert digest(ordinary_coefficients) == cut["ordinary_coefficients_sha256"]
        assert constant == certificate["constant_numerator"] == cut["constant_numerator"]
        assert box == certificate["ordinary_box_max_numerator"] == cut["ordinary_box_max_numerator"]
        assert constant - box == cut["rhs"]
        assert max(map(abs, weights)) == cut["maximum_signed_row_weight"]
        chosen_ids = certificate["source_heavy_global_ids"]
        chosen = tuple(blocks[i] for i in chosen_ids)
        assert chosen_ids == record["heavy_global_ids"]
        assert digest(chosen) == cut["source_heavy_sha256"] == record["heavy_sha256"]
        assert digest(shifted(rows, heavy, chosen)) == certificate["source_shifted_rows_sha256"]
        numerator = constant - box - sum(heavy_coefficients[heavy_positions[i]] for i in chosen_ids)
        gap = Fraction(numerator, denominator)
        assert gap > 0 and rational(gap) == cut["source_gap"] == certificate["source_gap"]
        checked.append({"rank": rank, "certificate_sha256": sha(certificate_path),
                        "source_gap": rational(gap)})
        planes.append((constant - box, heavy_coefficients, denominator))
    assert not fresh
    baseline = tuple(blocks[i] for i in proposal["baseline_heavy_global_ids"])
    upper, upper_evidence = incumbent_upper(rows, heavy, baseline)
    local = neighbors(baseline, anchors, heavy)
    assert len(local) == 136

    def envelope(chosen):
        positions = [heavy.index(block) for block in chosen]
        return max(Fraction(0), *(Fraction(rhs - sum(coefficients[i] for i in positions), den)
                                  for rhs, coefficients, den in planes))

    bounds = [envelope(chosen) for chosen in local]
    assert all(value > 0 for value in bounds)
    assert min(bounds) == Fraction(362507, 500000)
    assert envelope(baseline) == Fraction(3429927, 1000000)
    assert sum(value >= upper for value in bounds) == 116
    report = {
        "passed": True, "solver_calls": 0, "cuts": len(checked),
        "bundle_sha256": sha(BUNDLE), "checker_sha256": sha(__file__),
        "basis_source_sha256": sha(HERE / "basis.py"), "rows_sha256": digest(rows),
        "incumbent_upper": upper_evidence, "baseline_lower": rational(envelope(baseline)),
        "neighbors": len(bounds), "neighbors_exact_positive_lower_bound": len(bounds),
        "neighbor_minimum_lower": rational(min(bounds)),
        "neighbor_maximum_lower": rational(max(bounds)),
        "neighbors_exact_pruned_against_incumbent_upper": sum(value >= upper for value in bounds),
        "certificates": checked,
        "scope": "Fixed-anchor regular four-sevenfold family; no global lower-bound claim.",
        "interpretation": "All 136 heavy tuples are exactly LP-infeasible in this family. "
                          "Only 116 lower bounds reach the exact incumbent upper bound; "
                          "numerical local minimality is not an exact optimum certificate.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "certificates"}, indent=2))


if __name__ == "__main__":
    main()
