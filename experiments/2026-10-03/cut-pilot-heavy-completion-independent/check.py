# Document:    Independent Gate for the Cut-Pilot Heavy Completion
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL = ROOT / "experiments/scratch/cut-pilot-heavy-completion-v1.0.0/model.pbtxt"
WITNESS = HERE.parent / "lookahead-cut-orbit/cut-pilot-best.txt"
ORACLE = HERE.parent / "lookahead-cut-independent/check.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert sha(ORACLE) == "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    assert sha(MODEL) == "057df1c0d1f9f9404f8edeef30373a63b161ee1af558da926a63893da8fd4d47"
    assert sha(WITNESS) == "b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93"
    spec = importlib.util.spec_from_file_location("root_incidence_replay", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    oracle.MODEL, oracle.WITNESS = MODEL, WITNESS
    _, ordinary, heavy, fixed, rows = oracle.rebuild()
    assert (len(ordinary), len(heavy), len(fixed), len(rows)) == (1200, 276, 28, 697)
    proto = text_format.Parse(MODEL.read_text(), cp_model_pb2.CpModelProto())
    damage_count = 0
    with tempfile.TemporaryDirectory(dir=ROOT / "experiments/scratch") as directory:
        for index in range(6):
            bad = copy.deepcopy(proto)
            if index == 0:
                bad.constraints[0].linear.domain[0] += 1
            elif index == 1:
                bad.constraints[2].linear.domain[1] += 1
            elif index == 2:
                bad.constraints[577].linear.domain[0] += 1
            elif index == 3:
                row = next(row for row in bad.constraints[1:561] if row.linear.vars)
                row.linear.vars[0] += 1
            elif index == 4:
                bad.variables[0].domain[1] = 2
            else:
                bad.constraints[0].enforcement_literal.append(0)
            damaged = Path(directory) / f"bad-{index}.pbtxt"
            damaged.write_text(text_format.MessageToString(bad))
            oracle.MODEL = damaged
            try:
                oracle.rebuild()
            except AssertionError:
                damage_count += 1
                continue
            raise AssertionError("damaged completion model accepted")
    oracle.MODEL = MODEL
    result = {"passed": True, "model_sha256": sha(MODEL), "witness_sha256": sha(WITNESS),
              "checker_sha256": sha(Path(__file__)), "oracle_sha256": sha(ORACLE),
              "ordinary_variables": 1200, "fixed_heavy_blocks": 28,
              "reconstructed_rows": 697, "hub_graphs_retained": 6,
              "damaged_models_rejected": damage_count,
              "scope": "Necessary completion encoding for this fixed heavy tuple in the "
                       "regular four-sevenfold family; no first-link or global exclusion."}
    (HERE / "gate.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
