# Document:    Two-Cut Orbit Screen of Saved Heavy Tuples
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "experiments/2026-10-03"
RAW = ROOT / "experiments/scratch/four-seven-template-cut-pilot-v1.0.0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "audit.json"
    assert not output.exists(), "Preserve completed evidence"
    oracle_path = OLD / "lookahead-cut-orbit/check.py"
    assert sha(oracle_path.read_bytes()) == (
        "7e71d05ed94b99977564ed6742ab0bb7575335788a4e0a2cc9823f7c230658c8"
    )
    spec = importlib.util.spec_from_file_location("orbit_oracle", oracle_path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    inventory_path = OLD / "cut-pilot-parametric-cut/tuple-inventory.json"
    inventory_bytes = inventory_path.read_bytes()
    inventory = json.loads(inventory_bytes)
    assert inventory["distinct_heavy_tuples"] == len(inventory["tuples"]) == 17
    cut_paths = [OLD / "lookahead-parametric-cut/cut.json",
                 OLD / "cut-pilot-parametric-cut/cut.json"]
    cut_bytes = [p.read_bytes() for p in cut_paths]
    cuts = [json.loads(b) for b in cut_bytes]
    expected_hashes = ["9b946f1dbb41f49495a2303b1cac8b2de8a68e0e2eca2aa455dab02f5c5872c1",
                       "24c9a407e4abf90fe712ba297e549d32e748e000370d841984b107d0723a88a8"]
    assert list(map(sha, cut_bytes)) == expected_hashes
    gates = [OLD / "lookahead-cut-independent/audit.json",
             HERE.parent / "second-cut-independent/audit.json"]
    for gate, expected in zip(gates, expected_hashes, strict=True):
        receipt = json.loads(gate.read_bytes())
        assert receipt["passed"] and receipt["sha256"]["cut"] == expected
    heavy = list(map(tuple, cuts[0]["heavy_blocks"]))
    assert heavy == list(map(tuple, cuts[1]["heavy_blocks"]))
    index = {b: i for i, b in enumerate(heavy)}
    maps = sorted(set(oracle.maps()))
    assert len(maps) == 31104
    columns = []
    bound_witnesses = {}
    for record in inventory["tuples"]:
        member = record["members"][0]
        witness = (RAW / member["file"]).read_bytes()
        assert sha(witness) == member["sha256"]
        parsed = sorted(oracle.inspect_witness(witness, index))
        assert parsed == list(map(tuple, record["heavy_blocks"]))
        columns.append([index[b] for b in parsed])
        bound_witnesses[member["file"]] = sha(witness)
    images = np.empty((len(maps), len(heavy)), dtype=np.int16)
    for row, mapping in enumerate(maps):
        oracle.validate_map(mapping)
        images[row] = [index[tuple(sorted(mapping[p - 1] for p in b))] for b in heavy]
        assert len(set(map(int, images[row]))) == 276
    # Reuse the independently reviewed complete group; verify its generators
    # preserve ordinary blocks here as a direct validity check as well.
    anchors = oracle.ANCHORS
    ordinary = {b for b in itertools.combinations(range(1, 17), 5)
                if all(len(set(b) & a) <= 1 for a in anchors)}
    assert len(ordinary) == 1200
    generators = []
    for g in range(4):
        for a, b in ((0, 1), (1, 2)):
            p = list(range(1, 17))
            p[4*g+a], p[4*g+b] = p[4*g+b], p[4*g+a]
            generators.append(p)
    for g in range(3):
        p = list(range(1, 17))
        p[4*g:4*g+4], p[4*g+4:4*g+8] = p[4*g+4:4*g+8], p[4*g:4*g+4]
        generators.append(p)
    for mapping in generators:
        assert {tuple(sorted(mapping[p - 1] for p in b)) for b in ordinary} == ordinary
    results = []
    for record, selected in zip(inventory["tuples"], columns, strict=True):
        per_cut = []
        for cut in cuts:
            coefficients = np.array(cut["coefficients"], dtype=np.int64)
            values = coefficients[images[:, selected]].sum(axis=1)
            minimum = int(values.min())
            argmin = int(values.argmin())
            permutation = maps[argmin]
            direct = sum(cut["coefficients"][index[tuple(sorted(permutation[p-1] for p in b))]]
                         for b in map(tuple, record["heavy_blocks"]))
            assert direct == minimum
            per_cut.append({"rhs": cut["rhs"], "minimum": minimum,
                            "maximum": int(values.max()),
                            "rejecting_images": int((values < cut["rhs"]).sum()),
                            "minimum_map": permutation})
        results.append({"heavy_sha256": record["heavy_sha256"],
                        "min_holes": record["min_holes"], "cuts": per_cut,
                        "excluded": any(r["rejecting_images"] for r in per_cut)})
    report = {"passed": True, "maps": len(maps), "tuples": len(results),
              "excluded": sum(r["excluded"] for r in results), "results": results,
              "input_sha256": {"checker": sha(Path(__file__).read_bytes()),
                               "oracle": sha(oracle_path.read_bytes()),
                               "inventory": sha(inventory_bytes),
                               "cut1": expected_hashes[0], "cut2": expected_hashes[1]},
              "witness_sha256": bound_witnesses,
              "scope": "Saved tuples in the regular four-sevenfold family only."}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("passed", "maps", "tuples", "excluded")}))


if __name__ == "__main__":
    main()
