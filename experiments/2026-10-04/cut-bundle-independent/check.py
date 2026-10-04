# Document:    Independent Replay of the Fourteen Heavy Pattern Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import importlib.util
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "experiments/2026-10-03"
SOURCE = OLD / "cut-survivor-lp-screen"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replay(cut, dual, basis):
    _, ordinary, heavy, fixed, rows = basis
    assert cut["denominator"] == dual["denominator"] == 1000
    indices = [i for i, _ in dual["weights"]]
    assert indices == sorted(set(indices))
    ordinary_sum, heavy_sum, constant = [0] * len(ordinary), [0] * len(heavy), 0
    for i, weight in dual["weights"]:
        assert type(i) is int and 0 <= i < len(rows)
        assert type(weight) is int and weight != 0
        ordinary_ids, heavy_ids, lower, upper = rows[i]
        bound = lower if weight > 0 else upper
        assert abs(bound) < 2**60
        constant += weight * bound
        for j in ordinary_ids:
            ordinary_sum[j] += weight
        for j in heavy_ids:
            heavy_sum[j] += weight
    box = sum(max(0, value) for value in ordinary_sum)
    lhs = sum(value for b, value in zip(heavy, heavy_sum, strict=True) if b in fixed)
    rhs = constant - box
    assert constant - lhs == dual["rhs_numerator"]
    assert box == dual["box_max_numerator"]
    gap = Fraction(rhs - lhs, dual["denominator"])
    assert gap > 0 and list((gap.numerator, gap.denominator)) == dual["gap"]
    assert cut["coefficients"] == heavy_sum
    assert cut["constant_numerator"] == constant
    assert cut["ordinary_box_max_numerator"] == box
    assert (cut["rhs"], cut["source_lhs"], cut["source_violation_numerator"]) == (
        rhs, lhs, rhs - lhs
    )
    vector_hash = sha(json.dumps(ordinary_sum, separators=(",", ":")).encode())
    assert cut["ordinary_combined_coefficients_sha256"] == vector_hash
    return {"rhs": rhs, "source_lhs": lhs, "gap": [gap.numerator, gap.denominator],
            "signed_rows": len(indices)}


def main():
    output = HERE / "audit.json"
    assert not output.exists(), "Preserve completed evidence"
    oracle_path = OLD / "lookahead-cut-independent/check.py"
    oracle_hash = sha(oracle_path.read_bytes())
    assert oracle_hash == "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    spec = importlib.util.spec_from_file_location("independent_incidence", oracle_path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)

    class CapturedText:
        def __init__(self, data):
            self.data = data

        def read_text(self):
            return self.data.decode()

    manifest_bytes = (SOURCE / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert sha(manifest_bytes) == "9aaa0938f9cabef66e3fda488290436b8d4111cf90e457344af85d2f3d584228"
    models = {case["model_sha256"]: (ROOT / case["model"], ROOT / case["seed"],
                                     case["seed_sha256"]) for case in manifest["cases"]}
    models.update({
        "069652fee5d3f4c56c1bdd30f71f98498c996c97d7ec0d05e10e962b86cd2edb": (
            ROOT / "experiments/scratch/lookahead-heavy-strengthened-v1.0.0/model.pbtxt",
            OLD / "four-seven-template-native-lookahead/performance-cycle-best.txt",
            "8bfb962deaeeede2032d9efac1783f7eaabde38aada16c8f5fecdd2f19f84ef3"),
        "057df1c0d1f9f9404f8edeef30373a63b161ee1af558da926a63893da8fd4d47": (
            ROOT / "experiments/scratch/cut-pilot-heavy-completion-v1.0.0/model.pbtxt",
            OLD / "lookahead-cut-orbit/cut-pilot-best.txt",
            "b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93")
    })
    bundle_bytes = (SOURCE / "cut-bundle.json").read_bytes()
    bundle = json.loads(bundle_bytes)
    assert len(bundle["cuts"]) == len(models) == 14
    results, rejected = [], 0
    for cut in bundle["cuts"]:
        model_path, witness_path, witness_hash = models[cut["source_model_sha256"]]
        model_bytes, witness_bytes = model_path.read_bytes(), witness_path.read_bytes()
        assert sha(model_bytes) == cut["source_model_sha256"]
        assert sha(witness_bytes) == witness_hash
        oracle.MODEL, oracle.WITNESS = CapturedText(model_bytes), CapturedText(witness_bytes)
        basis = oracle.rebuild()
        blocks, ordinary, heavy, _, _ = basis
        assert bundle["heavy_blocks"] == [list(b) for b in heavy]
        assert bundle["heavy_global_ids"] == [blocks.index(b) for b in heavy]
        assert bundle["ordinary_global_ids"] == [blocks.index(b) for b in ordinary]
        dual_bytes = (ROOT / cut["dual_path"]).read_bytes()
        assert sha(dual_bytes) == cut["dual_sha256"]
        dual = json.loads(dual_bytes)
        result = replay(cut, dual, basis)
        bad_cut = copy.deepcopy(cut)
        bad_cut["coefficients"][0] += 1
        bad_dual = copy.deepcopy(dual)
        bad_dual["weights"].append(bad_dual["weights"][0])
        for damaged_cut, damaged_dual in ((bad_cut, dual), (cut, bad_dual)):
            try:
                replay(damaged_cut, damaged_dual, basis)
            except AssertionError:
                rejected += 1
            else:
                raise AssertionError("Damaged control accepted")
        result.update({"id": cut["id"], "model_sha256": sha(model_bytes),
                       "dual_sha256": sha(dual_bytes), "witness_sha256": witness_hash})
        results.append(result)
    assert len({r["model_sha256"] for r in results}) == 14
    report = {"passed": True, "cuts": 14, "rows_per_model": 697,
              "ordinary_columns": 1200, "heavy_columns": 276, "hub_graphs_retained": 6,
              "damaged_controls_rejected": rejected, "results": results,
              "bundle_sha256": sha(bundle_bytes), "manifest_sha256": sha(manifest_bytes),
              "checker_sha256": sha(Path(__file__).read_bytes()), "oracle_sha256": oracle_hash,
              "scope": "Regular four-sevenfold family only; no unrestricted lower bound."}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("passed", "cuts", "damaged_controls_rejected")}))


if __name__ == "__main__":
    main()
