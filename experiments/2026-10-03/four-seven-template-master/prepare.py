# Document:    Heavy Pattern Master Relaxation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Relax only ordinary block and double variables in the audited matching MIP."""

import gzip
import hashlib
import json
import subprocess
from pathlib import Path

from ortools.linear_solver import linear_solver_pb2, pywraplp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/scratch/four-seven-template-mip-v1.0.0"
OUTPUT = ROOT / "experiments/scratch/four-seven-template-master-v1.0.0"
AUDIT = HERE.parent / "four-seven-template-mip-independent/audit.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        raise ValueError("new output required")
    audit = json.loads(AUDIT.read_text())
    assert audit["passed"] and sha(SOURCE / "model.pb.gz") == audit["model_sha256"]
    assert sha(SOURCE / "matrix.json.gz") == audit["matrix_sha256"]
    matrix = json.loads(gzip.decompress((SOURCE / "matrix.json.gz").read_bytes()))
    heavy = sorted({e["block_index"] for e in matrix["extension_rows"]
                    if e["kind"] == "heavy_block_marginal"})
    assert len(heavy) == 276 and all(0 <= i < 4368 for i in heavy)
    original = linear_solver_pb2.MPModelProto()
    original.ParseFromString(gzip.decompress((SOURCE / "model.pb.gz").read_bytes()))
    model = linear_solver_pb2.MPModelProto()
    model.CopyFrom(original)
    changed = []
    for i, variable in enumerate(model.variable):
        if variable.is_integer and i not in heavy:
            variable.is_integer = False
            changed.append(i)
    assert len(changed) == 4492 and sum(v.is_integer for v in model.variable) == 276
    reverted = linear_solver_pb2.MPModelProto()
    reverted.CopyFrom(model)
    for i in changed:
        reverted.variable[i].is_integer = True
    assert reverted == original
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assert solver is not None and solver.LoadModelFromProtoKeepNames(model) == ""
    roundtrip = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(roundtrip)
    assert roundtrip == model
    OUTPUT.mkdir(parents=True)
    target = OUTPUT / "model.pb.gz"
    target.write_bytes(gzip.compress(model.SerializeToString(deterministic=True), mtime=0))
    (OUTPUT / "prepare.py").write_bytes(Path(__file__).read_bytes())
    metadata = {
        "source_sha256": sha(Path(__file__)), "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_model": str((SOURCE / "model.pb.gz").relative_to(ROOT)),
        "source_model_sha256": sha(SOURCE / "model.pb.gz"),
        "source_audit_sha256": sha(AUDIT), "matrix_sha256": audit["matrix_sha256"],
        "model_sha256": sha(target), "variables": len(model.variable),
        "rows": len(model.constraint), "integer_variables": heavy,
        "relaxed_variables": changed, "unsolved_scip_roundtrip_passed": True,
        "scope": "Heuristic seed master only; ordinary block and double variables are "
        "continuous. A feasible master is not a cover. Only integrality was relaxed. "
        "No model row, column order, bound, objective or coefficient was changed.",
    }
    for folder in (HERE, OUTPUT):
        (folder / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({k: v for k, v in metadata.items()
                      if k not in ["integer_variables", "relaxed_variables"]}))


if __name__ == "__main__":
    main()
