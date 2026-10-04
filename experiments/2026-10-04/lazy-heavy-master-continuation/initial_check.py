#!/usr/bin/env python3
# Document:    Lazy Master Continuation Initial Model Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Compare 24-cut start with the checked original master and ten replayed cuts."""

import ast
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "initial-gate.json"
    assert not output.exists()
    previous = HERE.parent / "lazy-heavy-master"
    audit_dir = HERE.parent / "lazy-heavy-master-independent"
    gate = json.loads((audit_dir / "audit.json").read_bytes())
    post_bytes = (audit_dir / "postcheck.json").read_bytes()
    post = json.loads(post_bytes)
    assert gate["passed"] and post["passed"] and post["total_checked_cuts"] == 24
    old_source, new_source = (previous / "run.py").read_bytes(), (HERE / "run.py").read_bytes()
    assert sha(old_source) == gate["source_sha256"]
    manifest_bytes = (HERE / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest["source_sha256"] == sha(new_source)
    assert manifest["previous_gate_sha256"] == sha(post_bytes)
    old_fn = next(n for n in ast.parse(old_source).body
                  if isinstance(n, ast.FunctionDef) and n.name == "build_master")
    new_fn = next(n for n in ast.parse(new_source).body
                  if isinstance(n, ast.FunctionDef) and n.name == "build_master")
    assert ast.dump(old_fn) == ast.dump(new_fn)
    old_model = (ROOT / "experiments/scratch/lazy-heavy-master-20261004/master.pbtxt").read_bytes()
    assert sha(old_model) == gate["master_sha256"]
    expected = text_format.Parse(old_model.decode(), cp_model_pb2.CpModelProto())
    for step in range(10):
        path = previous / f"learned-cut-{step:02}.json"
        captured = path.read_bytes()
        assert sha(captured) == post["receipts"][str(path.relative_to(ROOT))]
        cut = json.loads(captured)
        row = expected.constraints.add().linear
        for i, c in enumerate(cut["coefficients"]):
            if c:
                row.vars.append(i)
                row.coeffs.append(c)
        row.domain.extend([cut["rhs"], 2**63 - 1])
    raw = ROOT / "experiments/scratch/lazy-heavy-master-continuation-20261004"
    actual_bytes = (raw / "master.pbtxt").read_bytes()
    assert sha(actual_bytes) == manifest["master_sha256"]
    assert (raw / "run-frozen.py").read_bytes() == new_source
    actual = text_format.Parse(actual_bytes.decode(), cp_model_pb2.CpModelProto())
    assert actual.SerializeToString(deterministic=True) == expected.SerializeToString(
        deterministic=True)
    assert (len(actual.variables), len(actual.constraints)) == (276, 629)
    for key in ("oracle_sha256", "lp_sha256", "bundle_sha256"):
        assert manifest[key] == gate[key]
    result = {"passed": True, "variables": 276, "rows": 629, "checked_cuts": 24,
              "complete_initial_proto_match": True, "master_builder_ast_unchanged": True,
              "source_sha256": sha(new_source), "manifest_sha256": sha(manifest_bytes),
              "master_sha256": sha(actual_bytes), "prior_postcheck_sha256": sha(post_bytes),
              "checker_sha256": sha(Path(__file__).read_bytes()), "optimization_runs": 0}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
