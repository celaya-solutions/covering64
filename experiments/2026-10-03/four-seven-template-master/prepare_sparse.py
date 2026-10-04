# Document:    Sparse Heavy Pattern Master Relaxation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Drop the template extension from the audited seed master; do not solve."""

import gzip
import hashlib
import json
from pathlib import Path

from ortools.linear_solver import linear_solver_pb2, pywraplp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/scratch/four-seven-template-master-v1.0.0"
OUTPUT = ROOT / "experiments/scratch/four-seven-template-master-sparse-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not OUTPUT.exists()
    meta = json.loads((SOURCE / "manifest.json").read_text())
    audit_path = HERE.parent / "four-seven-template-master-independent/audit.json"
    audit = json.loads(audit_path.read_text())
    assert audit["passed"] and audit["model_sha256"] == sha(SOURCE / "model.pb.gz")
    original = linear_solver_pb2.MPModelProto()
    original.ParseFromString(gzip.decompress((SOURCE / "model.pb.gz").read_bytes()))
    assert len(original.variable) == 55528 and len(original.constraint) == 4550
    assert all(all(i < 4768 for i in row.var_index) for row in original.constraint[:4270])
    model = linear_solver_pb2.MPModelProto()
    model.CopyFrom(original)
    del model.variable[4768:]
    del model.constraint[4270:]
    assert [i for i, v in enumerate(model.variable) if v.is_integer] == meta["integer_variables"]
    assert len(model.variable) == 4768 and len(model.constraint) == 4270
    reverted = linear_solver_pb2.MPModelProto()
    reverted.CopyFrom(model)
    reverted.variable.extend(original.variable[4768:])
    reverted.constraint.extend(original.constraint[4270:])
    assert reverted == original
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assert solver is not None and solver.LoadModelFromProtoKeepNames(model) == ""
    roundtrip = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(roundtrip)
    assert roundtrip == model
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "model.pb.gz").write_bytes(
        gzip.compress(model.SerializeToString(deterministic=True), mtime=0))
    (OUTPUT / "prepare_sparse.py").write_bytes(Path(__file__).read_bytes())
    manifest = {"model_sha256": sha(OUTPUT / "model.pb.gz"),
                "source_model_sha256": sha(SOURCE / "model.pb.gz"),
                "source_audit_sha256": sha(audit_path),
                "source_sha256": sha(Path(__file__)),
                "integer_variables": meta["integer_variables"],
                "variables": 4768, "rows": 4270,
                "scope": "Sparse heuristic master without surviving-template hull. "
                "Ordinary blocks and double variables are continuous. "
                "Its integer heavy patterns require checked-catalog membership and "
                "a separate integer completion; they are never covering witnesses."}
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (HERE / "sparse-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k != "integer_variables"}))


if __name__ == "__main__":
    main()
