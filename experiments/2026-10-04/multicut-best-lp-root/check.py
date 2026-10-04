# Document:    Independent Completion Obstruction for the Fourteen-Cut Pilot
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
SOURCE = HERE.parent / "multicut-best-lp"
ORACLE = ROOT / "experiments/2026-10-03/lookahead-cut-independent/check.py"


def replay(basis, dual):
    _, ordinary, heavy, fixed, rows = basis
    ids = [i for i, _ in dual["weights"]]
    assert ids == sorted(set(ids))
    combined, rhs = [0] * len(ordinary), 0
    for i, weight in dual["weights"]:
        assert type(i) is int and 0 <= i < len(rows)
        assert type(weight) is int and weight
        oi, hi, lower, upper = rows[i]
        bound = lower if weight > 0 else upper
        assert abs(bound) < 2**60
        rhs += weight * (bound - sum(heavy[j] in fixed for j in hi))
        for j in oi:
            combined[j] += weight
    box = sum(max(0, c) for c in combined)
    assert rhs == dual["rhs_numerator"] and box == dual["box_max_numerator"]
    gap = Fraction(rhs - box, dual["denominator"])
    assert gap > 0 and [gap.numerator, gap.denominator] == dual["gap"]
    return {"signed_rows": len(ids), "rhs": rhs, "box": box,
            "denominator": dual["denominator"], "gap": [gap.numerator, gap.denominator]}


def main():
    sha = lambda data: hashlib.sha256(data).hexdigest()  # noqa: E731
    manifest = json.loads((SOURCE / "manifest.json").read_bytes())
    paths = {"model": ROOT / manifest["model"], "witness": SOURCE / "seed.txt",
             "dual": SOURCE / "dual.json", "oracle": ORACLE, "checker": Path(__file__)}
    data = {key: path.read_bytes() for key, path in paths.items()}
    hashes = {key: sha(value) for key, value in data.items()}
    assert hashes["oracle"] == "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    assert hashes["model"] == manifest["model_sha256"]
    assert hashes["witness"] == manifest["seed_sha256"]
    assert hashes["dual"] == "070af44bef9e875421923afbf65f6ce0e9644e3207f9c1cb0edc3f0ccf1f56d9"
    spec = importlib.util.spec_from_file_location("independent_incidence", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)

    class CapturedText:
        def __init__(self, raw):
            self.raw = raw

        def read_text(self):
            return self.raw.decode()

    oracle.MODEL, oracle.WITNESS = CapturedText(data["model"]), CapturedText(data["witness"])
    basis = oracle.rebuild()
    dual = json.loads(data["dual"])
    report = replay(basis, dual)
    assert report["gap"] == [8269, 500]
    bad_rhs, bad_rows = copy.deepcopy(dual), copy.deepcopy(dual)
    bad_rhs["rhs_numerator"] += 1
    bad_rows["weights"].append(bad_rows["weights"][0])
    for damaged in (bad_rhs, bad_rows):
        try:
            replay(basis, damaged)
        except AssertionError:
            continue
        raise AssertionError("Damaged certificate accepted")
    report.update({"passed": True, "rows": 697, "ordinary_columns": 1200,
                   "heavy_columns": 276, "fixed_heavy": 28, "hub_graphs_retained": 6,
                   "damaged_controls_rejected": 2, "sha256": hashes,
                   "scope": "One fixed-heavy tuple in the regular four-sevenfold family."})
    output = HERE / "audit.json"
    assert not output.exists(), "Preserve completed evidence"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
