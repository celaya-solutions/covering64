# Document:    Independent Five Overlap Pilot Encoding Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Construct all expected raw protobuf rows without calling the model generator."""

import copy
import gzip
import hashlib
import json
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "degree19-overlap-five"
HIGH = (1 << 63) - 1
BLOCKS = list(combinations(range(1, 17), 5))
IDS = {block: i for i, block in enumerate(BLOCKS)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_proto(pilot):
    fixed = sorted(IDS[tuple(block)] for block in pilot["fixed_blocks"])
    anchors = set(pilot["anchors"])
    free = [i for i, block in enumerate(BLOCKS) if not anchors.intersection(block)]
    forbidden = sorted(set(range(4368)) - set(fixed) - set(free))
    require(len(fixed) == 33 and len(free) == 2002, "wrong independent block partition")
    proto = cp_model_pb2.CpModelProto()
    for i in range(4368):
        proto.variables.add(name=f"block_{i}", domain=[0, 1])

    def row(ids, lower, upper):
        terms = list(ids)
        constraint = proto.constraints.add()
        constraint.linear.vars.extend(terms)
        constraint.linear.coeffs.extend([1] * len(terms))
        constraint.linear.domain.extend([lower, upper])

    for i in fixed:
        row([i], 1, 1)
    for i in forbidden:
        row([i], 0, 0)
    row(range(4368), 64, 64)
    for triple in combinations(range(1, 17), 3):
        row((i for i, block in enumerate(BLOCKS) if set(triple).issubset(block)), 1, HIGH)
    for point in range(1, 17):
        row((i for i, block in enumerate(BLOCKS) if point in block),
            19, 19 if point in anchors else HIGH)
    for pair in combinations(range(1, 17), 2):
        row((i for i, block in enumerate(BLOCKS) if set(pair).issubset(block)), 5, HIGH)
    return proto, fixed, free, forbidden


def check_proto(actual, expected):
    require(actual == expected, "raw model differs from independently reconstructed model")


def main():
    durable = json.loads((INPUT / "pilot-manifest.json").read_text())
    folder = ROOT / durable["raw_archive"]
    require(sha(folder / "manifest.json") == durable["raw_manifest_sha256"], "manifest hash")
    manifest = json.loads((folder / "manifest.json").read_text())
    require(manifest["search_launched"] is False and manifest["seeds"] is None
            and manifest["solver_budget"] is None, "preparation claims a solve")
    for name, digest in manifest["sources"].items():
        require(sha(folder / name) == digest, "frozen pilot source changed")
    factor_audit = json.loads((HERE / "audit.json").read_text())
    require(factor_audit["passed"] and sha(folder / "factorization.json.gz") ==
            factor_audit["factorization_sha256"], "independent factorization audit missing")
    payload = json.loads(gzip.decompress((folder / "factorization.json.gz").read_bytes()))
    require(len(manifest["cases"]) == len(durable["cases"]) == len(payload["pilots"]) == 4,
            "wrong pilot count")
    reports = []
    for number, (pilot, metadata) in enumerate(zip(payload["pilots"], manifest["cases"])):
        name = f"pilot-{number:03d}"
        require(metadata["id"] == name, "wrong pilot ID")
        subdir = folder / name
        require(json.loads((subdir / "metadata.json").read_text()) == metadata,
                "pilot metadata differs from manifest")
        path = subdir / "model.pbtxt"
        require(sha(path) == metadata["model_sha256"], "pilot model hash")
        actual = text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())
        expected, fixed, free, forbidden = expected_proto(pilot)
        check_proto(actual, expected)
        require(metadata["fixed_ids"] == fixed and metadata["free_ids"] == free
                and metadata["forbidden_ids"] == forbidden, "incorrect block metadata")
        require(metadata["fixed_count"] == 33 and metadata["free_count"] == 2002
                and metadata["variables"] == 4368 and metadata["rows"] == 3063
                and metadata["additions_required"] == 31, "incorrect dimension metadata")
        rows_path = subdir / "lp-rows.json.gz"
        require(sha(rows_path) == metadata["lp_rows_sha256"], "LP row hash")
        rows = [[list(c.linear.vars), list(c.linear.coeffs), c.linear.domain[0],
                 None if c.linear.domain[1] == HIGH else c.linear.domain[1]]
                for c in expected.constraints]
        require(json.loads(gzip.decompress(rows_path.read_bytes())) ==
                {"width": 4368, "rows": rows}, "LP rows differ from independent reconstruction")
        rejected = []
        for control in ("variable_order", "variable_domain", "free_block_fixed_zero",
                        "drop_coverage", "weaken_coverage", "anchor_degree", "objective",
                        "conditional_row"):
            damaged = copy.deepcopy(actual)
            if control == "variable_order":
                damaged.variables[0].name = "block_1"
            elif control == "variable_domain":
                damaged.variables[0].domain[1] = 2
            elif control == "free_block_fixed_zero":
                c = damaged.constraints.add()
                c.linear.vars.append(free[0])
                c.linear.coeffs.append(1)
                c.linear.domain.extend([0, 0])
            elif control == "drop_coverage":
                del damaged.constraints[2367]
            elif control == "weaken_coverage":
                damaged.constraints[2367].linear.domain[0] = 0
            elif control == "anchor_degree":
                damaged.constraints[2927].linear.domain[1] = 20
            elif control == "objective":
                damaged.objective.offset = 1
            else:
                damaged.constraints[2367].enforcement_literal.append(0)
            try:
                check_proto(damaged, expected)
            except ValueError:
                rejected.append(control)
            else:
                raise ValueError(f"damaged pilot accepted: {control}")
        reports.append({"id": name, "passed": True, "model_sha256": sha(path),
                        "lp_rows_sha256": sha(rows_path), "rows_checked": len(rows),
                        "variables_checked": len(actual.variables), "all_free_blocks": len(free),
                        "fixed_blocks": len(fixed), "damaged_controls_rejected": rejected})
    result = {"passed": True, "models": reports, "checker_sha256": sha(Path(__file__)),
              "manifest_sha256": sha(folder / "manifest.json"),
              "factorization_audit_sha256": sha(HERE / "audit.json"),
              "scope": "Exactly four conditional 33-block pilot unions. Full Boolean and LP "
                       "encodings checked; no solver run, cover, or branch exclusion claimed."}
    (HERE / "pilot-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "pilots": len(reports), "damaged_models_rejected": 32}))


if __name__ == "__main__":
    main()
