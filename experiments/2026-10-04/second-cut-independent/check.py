# Document:    Independent Replay of the Second Heavy Pattern Cut
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "experiments/2026-10-03"
ORACLE = OLD / "lookahead-cut-independent/check.py"
MODEL = ROOT / "experiments/scratch/cut-pilot-heavy-completion-v1.0.0/model.pbtxt"
WITNESS = OLD / "lookahead-cut-orbit/cut-pilot-best.txt"
CUT = OLD / "cut-pilot-parametric-cut/cut.json"
DUAL = OLD / "cut-pilot-heavy-completion/dual.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replay(cut, dual, basis):
    blocks, ordinary, heavy, fixed, rows = basis
    assert cut["denominator"] == dual["denominator"] == 1000
    assert cut["direction"] == ">="
    indices = [i for i, _ in dual["weights"]]
    assert indices == sorted(set(indices)) and len(indices) == 542
    ordinary_sum, heavy_sum, constant = [0] * 1200, [0] * 276, 0
    for i, weight in dual["weights"]:
        assert type(i) is int and 0 <= i < 697
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
    assert cut["heavy_blocks"] == [list(b) for b in heavy]
    assert cut["heavy_global_ids"] == [blocks.index(b) for b in heavy]
    assert cut["ordinary_global_ids"] == [blocks.index(b) for b in ordinary]
    assert cut["seed_heavy_global_ids"] == sorted(blocks.index(b) for b in fixed)
    assert cut["coefficients"] == heavy_sum
    assert cut["ordinary_combined_coefficients"] == ordinary_sum
    assert cut["constant_numerator"] == constant
    assert cut["ordinary_box_max_numerator"] == box
    assert (cut["rhs"], cut["seed_lhs"], cut["seed_violation_numerator"]) == (
        rhs, lhs, rhs - lhs
    )
    assert (rhs, lhs, rhs - lhs, box) == (104444, 91904, 12540, 108)
    assert constant - lhs == dual["rhs_numerator"] == 12648
    assert box == dual["box_max_numerator"]
    return {"rhs": rhs, "fixed_heavy_lhs": lhs, "violation_numerator": rhs - lhs}


def main():
    paths = {"oracle": ORACLE, "model": MODEL, "witness": WITNESS,
             "cut": CUT, "dual": DUAL, "checker": Path(__file__)}
    captured = {key: path.read_bytes() for key, path in paths.items()}
    hashes = {key: sha(data) for key, data in captured.items()}
    assert hashes["oracle"] == "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    assert hashes["model"] == "057df1c0d1f9f9404f8edeef30373a63b161ee1af558da926a63893da8fd4d47"
    assert hashes["witness"] == "b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93"
    assert hashes["cut"] == "24c9a407e4abf90fe712ba297e549d32e748e000370d841984b107d0723a88a8"
    assert hashes["dual"] == "e058d7dd35d83ce2d2b9e3141dc7e6939c688fe33e905a5c64a6ed63f8464c61"
    spec = importlib.util.spec_from_file_location("independent_incidence", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)

    # The frozen oracle reads text paths. Supply captured bytes so receipt hashes
    # and reconstructed rows use exactly the same model and witness snapshots.
    class CapturedText:
        def __init__(self, data):
            self.data = data

        def read_text(self):
            return self.data.decode()

    oracle.MODEL = CapturedText(captured["model"])
    oracle.WITNESS = CapturedText(captured["witness"])
    basis = oracle.rebuild()
    cut, dual = json.loads(captured["cut"]), json.loads(captured["dual"])
    assert cut["dual_sha256"] == hashes["dual"]
    assert cut["source_model_sha256"] == hashes["model"]
    assert cut["seed_sha256"] == hashes["witness"]
    result = replay(cut, dual, basis)
    controls = []
    for key in ("rhs", "constant_numerator", "ordinary_box_max_numerator", "seed_lhs"):
        bad = copy.deepcopy(cut)
        bad[key] += 1
        controls.append((key, bad, dual))
    for key in ("coefficients", "ordinary_combined_coefficients", "heavy_global_ids"):
        bad = copy.deepcopy(cut)
        bad[key][0] += 1
        controls.append((key, bad, dual))
    bad_dual = copy.deepcopy(dual)
    bad_dual["weights"].append(bad_dual["weights"][0])
    controls.append(("duplicate dual row", cut, bad_dual))
    for label, damaged_cut, damaged_dual in controls:
        try:
            replay(damaged_cut, damaged_dual, basis)
        except AssertionError:
            continue
        raise AssertionError(f"damaged control accepted: {label}")
    result.update({"passed": True, "denominator": 1000, "reconstructed_rows": 697,
                   "ordinary_columns": 1200, "heavy_columns": 276, "signed_rows": 542,
                   "hub_graphs_retained": 6, "damaged_controls_rejected": len(controls),
                   "sha256": hashes,
                   "scope": "Regular four-sevenfold family only; no global lower bound."})
    output = HERE / "audit.json"
    assert not output.exists(), "Preserve completed evidence"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
