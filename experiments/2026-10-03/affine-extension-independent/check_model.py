# Document:    Independent Inversive Pool Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit the PGL pool and exact64 CP model using the independent norm construction."""

import copy
import hashlib
import itertools
import json
from pathlib import Path

from construct import construct
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "inversive-plane-pool"


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(proto, pool, supports):
    universe = list(itertools.combinations(range(1, 17), 5))
    global_ids = [universe.index(block) for block in pool]
    require(len(proto.variables) == 288, "variable count")
    require([v.name for v in proto.variables] == [f"block_{i}" for i in global_ids],
            "lexicographic block names")
    require(all(list(v.domain) == [0, 1] for v in proto.variables), "Boolean domains")
    require({d.name for d, _ in proto.ListFields()} <= {"variables", "constraints"},
            "extra model fields")
    require(len(proto.constraints) == 561, "constraint count")
    expected = [(list(range(288)), 64, 64)] + [(ids, 1, 2**63 - 1) for ids in supports]
    for row, (ids, lower, upper) in zip(proto.constraints, expected, strict=True):
        require(not row.enforcement_literal and row.WhichOneof("constraint") == "linear",
                "unexpected constraint kind or enforcement")
        require(list(row.linear.vars) == ids and list(row.linear.coeffs) == [1] * len(ids),
                "row variables or coefficients")
        require(list(row.linear.domain) == [lower, upper], "row bounds")


def main():
    manifest = json.loads((INPUT / "manifest.json").read_text())
    require(sha(INPUT / "build.py") == manifest["builder_sha256"], "builder changed")
    source_pool, model_path = ROOT / manifest["pool"], ROOT / manifest["model"]
    require(sha(source_pool) == manifest["pool_sha256"] and
            sha(model_path) == manifest["model_sha256"], "input changed")
    pgl = json.loads(source_pool.read_text())
    independent = construct()
    pool = independent["pool"]
    require([tuple(e["block"]) for e in pgl["pool"]] == pool, "independent pool disagreement")
    require(sorted(map(tuple, pgl["plane_blocks"])) == independent["steiner17"],
            "independent Steiner plane disagreement")
    require(sorted(map(tuple, pgl["affine_lines"])) == independent["lines"],
            "independent affine lines disagreement")
    require(sorted(map(tuple, pgl["retained_circles"])) == independent["circles"],
            "independent circles disagreement")
    require(pgl["supports"] == independent["containing"], "independent supports disagreement")
    proto = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
    inspect(proto, pool, independent["containing"])
    mutations = []
    damaged = copy.deepcopy(proto)
    del damaged.variables[-1]
    mutations.append(("missing variable", damaged))
    damaged = copy.deepcopy(proto)
    damaged.variables[1].name = damaged.variables[0].name
    mutations.append(("duplicate block identity", damaged))
    damaged = copy.deepcopy(proto)
    damaged.variables[0].domain[1] = 2
    mutations.append(("nonBoolean domain", damaged))
    damaged = copy.deepcopy(proto)
    del damaged.constraints[-1]
    mutations.append(("missing coverage row", damaged))
    damaged = copy.deepcopy(proto)
    damaged.constraints[0].linear.domain[0] = 63
    mutations.append(("wrong block target", damaged))
    damaged = copy.deepcopy(proto)
    damaged.constraints[1].linear.coeffs[0] = -1
    mutations.append(("wrong coefficient", damaged))
    damaged = copy.deepcopy(proto)
    damaged.constraints[1].linear.domain[0] = 0
    mutations.append(("vacuous coverage", damaged))
    damaged = copy.deepcopy(proto)
    damaged.solution_hint.vars.append(0)
    damaged.solution_hint.values.append(1)
    mutations.append(("unapproved extra field", damaged))
    controls = []
    for name, damaged in mutations:
        try:
            inspect(damaged, pool, independent["containing"])
        except ValueError as error:
            controls.append({"control": name, "rejected": str(error)})
        else:
            raise ValueError("damaged model accepted: " + name)
    report = {"passed": True, "checker_sha256": sha(Path(__file__)),
              "independent_constructor_sha256": sha(HERE / "construct.py"),
              "manifest_sha256": sha(INPUT / "manifest.json"),
              "pool_sha256": sha(source_pool), "model_sha256": sha(model_path),
              "variables": 288, "rows": 561, "damaged_controls": controls,
              "scope": "Exact64 feasibility inside independently reconstructed 288-block pool. "
              "No imposed circle/extension split, degree profile or symmetry. No solver call."}
    (HERE / "model-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
