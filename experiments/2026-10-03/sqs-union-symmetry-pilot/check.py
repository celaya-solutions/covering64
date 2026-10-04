# Document:    Independent Gate for the SQS Representative Constraint
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
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE_RAW = ROOT / "experiments/scratch/new-construction-web-20261003"
MODEL = (ROOT / "experiments/scratch/sqs-union-symmetry-pilot-20261003"
         / "exact64-sqs-union-symmetry.pbtxt")
CERTIFICATE = HERE.parent / "sqs-union-symmetry/certificate.json"
REPS = [132, 543, 1688, 1691, 1692, 1694]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_certificate(certificate, pool):
    target = {9, 10, 11}
    carriers = {block for block in pool if target <= set(block)}
    assert len(carriers) == 30 and certificate["target_triple"] == sorted(target)
    assert certificate["representative_local_ids"] == REPS
    representatives = []
    seen = set()
    for orbit in certificate["orbits"]:
        representative = tuple(orbit["representative"])
        assert representative in carriers
        representatives.append(representative)
        assert len(orbit["members"]) == orbit["size"]
        for member in orbit["members"]:
            block = tuple(member["block"])
            assert block in carriers and block not in seen
            seen.add(block)
            mapping = member["to_representative"]
            assert sorted(mapping) == list(range(1, 17))
            assert {mapping[p - 1] for p in target} == target
            assert tuple(sorted(mapping[p - 1] for p in block)) == representative
            assert {tuple(sorted(mapping[p - 1] for p in b)) for b in pool} == set(pool)
    assert seen == carriers
    assert representatives == [pool[i] for i in REPS]
    # Every cover contains a carrier. Its stored permutation preserves the
    # complete allowed pool and sends that carrier to a selected representative.
    # Thus some relabeling satisfies the new row; cover invariance is not assumed.


def check_model(base, restricted):
    assert len(restricted.variables) == 1744 and len(restricted.constraints) == 562
    clone = copy.deepcopy(restricted)
    row = clone.constraints[561]
    assert {f.name for f, _ in row.ListFields()} == {"linear"}
    assert list(row.linear.vars) == REPS
    assert list(row.linear.coeffs) == [1] * 6
    assert list(row.linear.domain) == [1, 6]
    del clone.constraints[561]
    assert clone.SerializeToString(deterministic=True) == base.SerializeToString(deterministic=True)


def main():
    files = [MODEL, BASE_RAW / "exact64-sqs-union.pbtxt", BASE_RAW / "union-pool.json",
             CERTIFICATE, HERE.parent / "sqs-union-symmetry/audit.json",
             HERE.parent / "sqs-extension-independent/gate.json", HERE / "manifest.json"]
    # The runner's manifest has its own checked dependency bindings.
    if not files[-1].exists():
        files[-1] = HERE / "model-manifest.json"
    before = {str(p.relative_to(ROOT)): sha(p) for p in files}
    baseline_gate = json.loads(files[5].read_text())
    assert baseline_gate["passed"]
    assert baseline_gate["model_sha256"] == sha(files[1])
    assert baseline_gate["pool_sha256"] == sha(files[2])
    assert sha(MODEL) == "ceb6f7abd092cc79aaf12b4f7d8fc8b8421d0408724025c4f07c1c70f99e2783"
    certificate = json.loads(CERTIFICATE.read_text())
    pool = [tuple(r["block"]) for r in json.loads(files[2].read_text())["pool"]]
    assert len(pool) == len(set(pool)) == 1744 and pool == sorted(pool)
    check_certificate(certificate, pool)
    base = text_format.Parse(files[1].read_text(), cp_model_pb2.CpModelProto())
    restricted = text_format.Parse(MODEL.read_text(), cp_model_pb2.CpModelProto())
    check_model(base, restricted)
    damage_count = 0
    for index in range(4):
        bad = copy.deepcopy(restricted)
        if index == 0:
            bad.constraints[561].linear.vars[0] += 1
        elif index == 1:
            bad.constraints[561].linear.domain[0] = 0
        elif index == 2:
            bad.constraints[0].linear.domain[0] = 63
        else:
            bad.objective.vars.append(0)
        try:
            check_model(base, bad)
        except AssertionError:
            damage_count += 1
            continue
        raise AssertionError("damaged model accepted")
    for index in range(3):
        bad = copy.deepcopy(certificate)
        if index == 0:
            bad["orbits"][0]["members"].pop()
        elif index == 1:
            bad["orbits"][0]["members"][0]["to_representative"][0] = 2
        else:
            bad["representative_local_ids"][0] += 1
        try:
            check_certificate(bad, pool)
        except AssertionError:
            damage_count += 1
            continue
        raise AssertionError("damaged carrier certificate accepted")
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in files}
    result = {"passed": True, "source_sha256": sha(Path(__file__)),
              "model_sha256": sha(MODEL), "pool_sha256": sha(files[2]),
              "verified_inputs": before, "variables": 1744, "rows": 562,
              "base_proto_unchanged": True, "carrier_maps_replayed": 30,
              "representative_local_ids": REPS, "damaged_controls_rejected": damage_count,
              "scope": "Equisatisfiable representative selection within the1744-block pool; "
                       "no invariant-cover assumption or unrestricted reduction."}
    (HERE / "gate.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "verified_inputs"}))


if __name__ == "__main__":
    main()
