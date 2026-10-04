# Document:    Symmetry Selection for the Two SQS Extension Pool
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a7e7b971e9682d8671a5c1859fc1225a06de2c6b668d529cc4cbc0799a78ac9c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Clone the audited base and append exactly one certified representative row."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE_RAW = ROOT / "experiments/scratch/new-construction-web-20261003"
RAW = ROOT / "experiments/scratch/sqs-union-symmetry-pilot-20261003"
CERT = ROOT / "experiments/2026-10-03/sqs-union-symmetry"
REPS = [132, 543, 1688, 1691, 1692, 1694]
BASE_HASH = "d0a70c16b53c2399ed10eae2deb77b3c817e352a4fc950d7584291b3c249703f"
POOL_HASH = "b1e0e13ac3787643b25e920d2ce8f83d7119dedcb3c78daaf8316e04510c68c6"
CERT_HASH = "9e4dea39bbebaba8647ae02f492c579d05f83e628e8af9a330ce8d62fca02aa6"
AUDIT_HASH = "cc19d63e135568479bd83161e3ce2bbed3907bfc174929abb659ef5508323bf4"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not (HERE / "model-manifest.json").exists(), "preserve completed export"
    assert not RAW.exists(), "preserve completed raw artifacts"
    base_path = BASE_RAW / "exact64-sqs-union.pbtxt"
    pool_path = BASE_RAW / "union-pool.json"
    certificate_path = CERT / "certificate.json"
    audit_path = CERT / "audit.json"
    assert digest(base_path) == BASE_HASH and digest(pool_path) == POOL_HASH
    assert digest(certificate_path) == CERT_HASH and digest(audit_path) == AUDIT_HASH
    certificate = json.loads(certificate_path.read_text())
    audit = json.loads(audit_path.read_text())
    assert audit["passed"] and audit["certificate_sha256"] == CERT_HASH
    assert audit["source_sha256"] == digest(CERT / "check_certificate.py")
    verified_inputs = dict(audit["verified_inputs"])
    for relative, expected in verified_inputs.items():
        path = (ROOT / relative).resolve()
        assert path.is_relative_to(ROOT) and digest(path) == expected
    assert certificate["pool_sha256"] == audit["pool_sha256"] == POOL_HASH
    assert certificate["base_model_sha256"] == audit["model_sha256"] == BASE_HASH
    assert certificate["representative_local_ids"] == audit["representative_local_ids"] == REPS
    assert certificate["group_order"] == audit["group_order"] == 1536
    assert certificate["stabilizer_order"] == audit["stabilizer_order"] == 48
    assert certificate["target_triple"] == [9, 10, 11]
    assert (
        audit["all_group_maps_explicitly_checked"] and len(audit["damaged_controls_rejected"]) == 14
    )
    base = cp_model_pb2.CpModelProto()
    text_format.Parse(base_path.read_text(), base)
    assert len(base.variables) == 1744 and len(base.constraints) == 561
    model = cp_model_pb2.CpModelProto()
    model.CopyFrom(base)
    row = model.constraints.add().linear
    row.vars.extend(REPS)
    row.coeffs.extend([1] * 6)
    row.domain.extend([1, 6])
    stripped = cp_model_pb2.CpModelProto()
    stripped.CopyFrom(model)
    del stripped.constraints[-1]
    assert stripped.SerializeToString(deterministic=True) == base.SerializeToString(
        deterministic=True
    )
    model_text = text_format.MessageToString(model)
    validation = cp_model.CpModel()
    assert validation.proto.parse_text_format(model_text) and not validation.validate()
    RAW.mkdir()
    model_path = RAW / "exact64-sqs-union-symmetry.pbtxt"
    model_path.write_text(model_text)
    (RAW / "build_model.py").write_bytes(Path(__file__).read_bytes())
    for path in (certificate_path, audit_path, CERT / "check_certificate.py"):
        verified_inputs[str(path.relative_to(ROOT))] = digest(path)
    manifest = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "builder_sha256": digest(Path(__file__)),
        "base_model_path": str(base_path.relative_to(ROOT)),
        "base_model_sha256": BASE_HASH,
        "pool_path": str(pool_path.relative_to(ROOT)),
        "pool_sha256": POOL_HASH,
        "certificate_path": str(certificate_path.relative_to(ROOT)),
        "certificate_sha256": CERT_HASH,
        "certificate_audit_path": str(audit_path.relative_to(ROOT)),
        "certificate_audit_sha256": AUDIT_HASH,
        "verified_inputs": verified_inputs,
        "model_path": str(model_path.relative_to(ROOT)),
        "model_sha256": digest(model_path),
        "ortools_version": ortools.__version__,
        "variables": 1744,
        "rows": 562,
        "coverage_rows": 560,
        "cardinality": 64,
        "base_proto_preserved_exactly": True,
        "added_constraint": {"vars": REPS, "coeffs": [1] * 6, "domain": [1, 6]},
        "representative_global_ids": certificate["representative_global_ids"],
        "representative_blocks": audit["representatives"],
        "proposed_pilot": {"seed": 2026104011, "seconds": 180, "workers": 1, "status": "not_run"},
        "solver_calls": 0,
        "scope": "Exact64 feasibility in the fixed 1744-block two-SQS extension union. "
        "One certified representative row preserves existence under pool automorphisms; "
        "it is not necessary for every labeled cover. No implication for unrestricted "
        "C(16,5,3) from failure.",
        "global_lower_bound_claim": False,
    }
    (HERE / "model-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
