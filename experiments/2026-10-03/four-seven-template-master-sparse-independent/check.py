# Document:    Independent Sparse Heavy Master Truncation Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      cf97bb14c4f323d98c8db97d5133508473427a6812ae0481157e9501aa55d7dd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Audit exact prefix truncation of the earlier independently checked master."""

import gzip
import hashlib
import itertools as it
import json
from pathlib import Path

from ortools.linear_solver import linear_solver_pb2, pywraplp

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-master-sparse-v1.0.0"
BASE = ROOT / "experiments/scratch/four-seven-template-master-v1.0.0/model.pb.gz"
SOURCE_HASH = "bfc530db33484e36be4f24e2e7a4991dec98eb0d65a4fbfcdda07333e8c0cff2"
MODEL_HASH = "d108411db23b738e99971e469b441344e31ece3cb56ea525275224dcee44a526"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def heavy_indices():
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    blocks = list(it.combinations(range(1, 17), 5))
    groups = [
        {
            i
            for i, b in enumerate(blocks)
            if anchor <= set(b)
            and all(len(set(b) & other) <= 1 for other in anchors if other != anchor)
        }
        for anchor in anchors
    ]
    require(all(len(group) == 69 for group in groups), "wrong heavy groups")
    return set().union(*groups)


def check(base, sparse, heavy):
    require(len(base.variable) == 55528 and len(base.constraint) == 4550, "base dimensions")
    require(len(sparse.variable) == 4768 and len(sparse.constraint) == 4270, "sparse dimensions")
    require(
        all(all(0 <= i < 4768 for i in row.var_index) for row in sparse.constraint),
        "row references removed variable",
    )
    require(
        {i for i, v in enumerate(sparse.variable) if v.is_integer} == heavy and len(heavy) == 276,
        "heavy integrality changed",
    )
    restored = linear_solver_pb2.MPModelProto()
    restored.CopyFrom(sparse)
    restored.variable.extend(base.variable[4768:])
    restored.constraint.extend(base.constraint[4270:])
    require(restored == base, "restored model differs from audited source")


def main():
    require(sha(BASE) == SOURCE_HASH and sha(RAW / "model.pb.gz") == MODEL_HASH, "model hashes")
    manifest = json.loads((RAW / "manifest.json").read_text())
    audit_path = ROOT / "experiments/2026-10-03/four-seven-template-master-independent/audit.json"
    audit = json.loads(audit_path.read_text())
    require(
        sha(audit_path) == manifest["source_audit_sha256"]
        and audit["passed"]
        and audit["model_sha256"] == SOURCE_HASH,
        "prior independent audit binding",
    )
    require(sha(RAW / "prepare_sparse.py") == manifest["source_sha256"], "source snapshot binding")
    base, sparse = linear_solver_pb2.MPModelProto(), linear_solver_pb2.MPModelProto()
    base.ParseFromString(gzip.decompress(BASE.read_bytes()))
    sparse.ParseFromString(gzip.decompress((RAW / "model.pb.gz").read_bytes()))
    heavy = heavy_indices()
    check(base, sparse, heavy)
    require(manifest["integer_variables"] == sorted(heavy), "manifest integer inventory")
    controls = []
    edits = [
        ("heavy_relaxed", lambda m: setattr(m.variable[min(heavy)], "is_integer", False)),
        ("ordinary_integer", lambda m: setattr(m.variable[100], "is_integer", True)),
        ("double_integer", lambda m: setattr(m.variable[4368], "is_integer", True)),
        ("row_changed", lambda m: m.constraint[0].coefficient.__setitem__(0, 2)),
        ("removed_column_reference", lambda m: m.constraint[0].var_index.__setitem__(0, 4768)),
        ("bound_changed", lambda m: setattr(m.variable[100], "upper_bound", 2)),
        ("objective_changed", lambda m: setattr(m, "objective_offset", 1)),
        ("column_name_changed", lambda m: setattr(m.variable[0], "name", "wrong")),
    ]
    for name, edit in edits:
        bad = linear_solver_pb2.MPModelProto()
        bad.CopyFrom(sparse)
        edit(bad)
        try:
            check(base, bad, heavy)
        except ValueError as error:
            controls.append({"name": name, "rejected": str(error)})
        else:
            raise ValueError(f"damaged sparse model accepted: {name}")
    solver = pywraplp.Solver.CreateSolver("SCIP")
    require(solver is not None and solver.LoadModelFromProtoKeepNames(sparse) == "", "SCIP load")
    roundtrip = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(roundtrip)
    require(roundtrip == sparse and solver.SetNumThreads(1), "SCIP roundtrip/thread setting")
    report = {
        "passed": True,
        "model_sha256": MODEL_HASH,
        "source_model_sha256": SOURCE_HASH,
        "checker_sha256": sha(Path(__file__)),
        "variables": 4768,
        "rows": 4270,
        "integer_variables": sorted(heavy),
        "removed_variables": 50760,
        "removed_rows": 280,
        "restoring_tails_equals_source": True,
        "damaged_controls": controls,
        "unsolved_scip_roundtrip_equal": True,
        "single_thread_accepted": True,
        "solve_called": False,
        "scope": "Strict heuristic seed relaxation; no cover or proof.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["passed", "model_sha256", "source_model_sha256"]}))


if __name__ == "__main__":
    main()
