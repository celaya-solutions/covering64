# Document:    Independent Heavy Template Master Relaxation Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      4d53cef9b2492624dec97a229413ff00fe1b0cba1a7eb490a7d1db4dc964ef10
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check only an integrality relaxation occurred; do not call any solver."""

import gzip
import hashlib
import itertools as it
import json
from pathlib import Path

from ortools.linear_solver import linear_solver_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-master-v1.0.0"
BASE = ROOT / "experiments/scratch/four-seven-template-mip-v1.0.0/model.pb.gz"
SOURCE_HASH = "ca38951e994b1b2f0f0d6b42a3bfa60124366b010f10dd1d0ec2528fce82214b"
MASTER_HASH = "bfc530db33484e36be4f24e2e7a4991dec98eb0d65a4fbfcdda07333e8c0cff2"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def heavy_indices():
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    blocks = list(it.combinations(range(1, 17), 5))
    groups = []
    for group, anchor in enumerate(anchors):
        indices = {
            index
            for index, block in enumerate(blocks)
            if anchor <= set(block)
            and all(len(set(block) & other) <= 1 for g, other in enumerate(anchors) if g != group)
        }
        require(len(indices) == 69, "heavy group size")
        groups.append(indices)
    heavy = set().union(*groups)
    require(len(heavy) == 276, "heavy groups overlap")
    return heavy


def check(base, master, heavy):
    require(len(base.variable) == len(master.variable) == 55528, "variable count")
    require(len(base.constraint) == len(master.constraint) == 4550, "row count")
    require(
        all(v.is_integer == (i < 4768) for i, v in enumerate(base.variable)),
        "source integrality changed",
    )
    require(
        {i for i, v in enumerate(master.variable) if v.is_integer} == heavy,
        "master integer set changed",
    )
    changed = {
        i
        for i, (a, b) in enumerate(zip(base.variable, master.variable, strict=True))
        if a.is_integer != b.is_integer
    }
    require(
        changed == set(range(4768)) - heavy and len(changed) == 4492, "wrong relaxed-variable set"
    )
    restored = linear_solver_pb2.MPModelProto()
    restored.CopyFrom(master)
    for i, variable in enumerate(base.variable):
        restored.variable[i].is_integer = variable.is_integer
    require(restored == base, "non-integrality model field changed")
    return sorted(changed)


def main():
    require(sha(BASE) == SOURCE_HASH and sha(RAW / "model.pb.gz") == MASTER_HASH, "model hash")
    metadata = json.loads((RAW / "manifest.json").read_text())
    require(sha(RAW / "prepare.py") == metadata["source_sha256"], "source snapshot hash")
    source_audit = ROOT / "experiments/2026-10-03/four-seven-template-mip-independent/audit.json"
    previous = json.loads(source_audit.read_text())
    require(
        sha(source_audit) == metadata["source_audit_sha256"]
        and previous["passed"]
        and previous["model_sha256"] == SOURCE_HASH,
        "prior audit binding",
    )
    base, master = linear_solver_pb2.MPModelProto(), linear_solver_pb2.MPModelProto()
    base.ParseFromString(gzip.decompress(BASE.read_bytes()))
    master.ParseFromString(gzip.decompress((RAW / "model.pb.gz").read_bytes()))
    heavy = heavy_indices()
    changed = check(base, master, heavy)
    require(
        metadata["integer_variables"] == sorted(heavy) and metadata["relaxed_variables"] == changed,
        "manifest integrality inventory mismatch",
    )
    controls = []
    edits = [
        ("heavy_relaxed", lambda m: setattr(m.variable[min(heavy)], "is_integer", False)),
        ("ordinary_integer", lambda m: setattr(m.variable[100], "is_integer", True)),
        ("double_integer", lambda m: setattr(m.variable[4368], "is_integer", True)),
        ("selector_integer", lambda m: setattr(m.variable[4768], "is_integer", True)),
        ("bound_changed", lambda m: setattr(m.variable[100], "upper_bound", 2)),
        ("row_changed", lambda m: m.constraint[0].coefficient.__setitem__(0, 2)),
        ("objective_changed", lambda m: setattr(m, "objective_offset", 1)),
        ("column_name_changed", lambda m: setattr(m.variable[0], "name", "wrong")),
    ]
    require(100 not in heavy, "control index is not relaxed")
    for name, edit in edits:
        bad = linear_solver_pb2.MPModelProto()
        bad.CopyFrom(master)
        edit(bad)
        try:
            check(base, bad, heavy)
        except ValueError as error:
            controls.append({"name": name, "rejected": str(error)})
        else:
            raise ValueError(f"damaged model accepted: {name}")
    report = {
        "passed": True,
        "source_model_sha256": SOURCE_HASH,
        "model_sha256": MASTER_HASH,
        "checker_sha256": sha(Path(__file__)),
        "variables": 55528,
        "rows": 4550,
        "heavy_integer_columns": sorted(heavy),
        "integer_columns": 276,
        "relaxed_integer_flags": 4492,
        "other_proto_fields_identical": True,
        "damaged_controls": controls,
        "solve_called": False,
        "scope": "Heuristic master relaxation of the106-catalog MIP; not a cover or exclusion.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["passed", "model_sha256", "relaxed_integer_flags"]}))


if __name__ == "__main__":
    main()
