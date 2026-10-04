# Document:    Fixed-Link and Hub-Case Boolean Template CP Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Append exactly nine equalities to the unchanged audited 106-template CP base."""

import hashlib
import itertools
import json
import math
import subprocess
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent / "four-seven-template-cp-proposal"
OUTPUT = ROOT / "experiments/scratch/four-seven-template-cp-restricted-v1.0.0"
PLAN = HERE.parent / "four-seven-template-hub-priority/priority-plan.json"
REGISTRY = (
    HERE.parent / "four-seven-template-hull-refresh-independent/combined-first-link-exclusions.json"
)
HUBS = {4, 8, 12, 16}
CASES = [("matching-029", (0, 2)), ("matching-063", (0, 1))]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    require(not OUTPUT.exists(), "new output directory required")
    plan = load(PLAN)
    registry = load(REGISTRY)
    require(registry["passed"] is True and registry["excluded_count"] == 108, "wrong registry")
    require(
        sha(REGISTRY) == "2809b2f39fac1971ca6bf3997e789a4a41463b62394e7525e5d282d084527f88",
        "registry changed",
    )
    for key in ["source_hub_audit", "hub_partition_audit"]:
        require(sha(ROOT / plan[key]) == plan[key + "_sha256"], "hub audit changed")
    hub_audit = load(ROOT / plan["source_hub_audit"])
    require(hub_audit["passed"] is True, "hub audit not passed")
    base_manifest = load(BASE / "manifest.json")
    base_audit = load(BASE / "independent-audit.json")
    require(
        base_audit["passed"] is True
        and sha(BASE / "manifest.json") == base_audit["manifest_sha256"],
        "base audit does not bind manifest",
    )
    base_record = next(c for c in base_manifest["cases"] if c["case"] == "matching")
    source_path = ROOT / base_record["model"]
    require(sha(source_path) == base_record["model_sha256"], "original Boolean base changed")
    require(
        base_manifest["refresh_manifest_sha256"]
        == "84183ee44ed2916ffd18d64b5f113774e4eda47bad5e82c6c79b1b3a64db5bdf",
        "not106 base",
    )
    original = cp_model_pb2.CpModelProto()
    text_format.Parse(source_path.read_text(), original)
    require(
        len(original.variables) == 55528 and len(original.constraints) == 4550, "base dimensions"
    )
    blocks = list(itertools.combinations(range(1, 17), 5))
    block_ids = {b: i for i, b in enumerate(blocks)}
    catalog_path = HERE.parent / "four-seven-link-orbits/result.json"
    catalog = load(catalog_path)
    representatives = {
        r["id"]: r
        for case in catalog["cases"]
        if case["case"] == "matching"
        for r in case["representatives"]
    }
    OUTPUT.mkdir(parents=True)
    records = []
    for identifier, hub_case in CASES:
        require(identifier in registry["remaining_ids"], "selected representative excluded")
        priority = next(p for p in plan["priority"] if p["id"] == identifier)
        require(priority["hub_case"] == list(hub_case), "wrong remaining hub case")
        excluded = hub_audit["case_exclusions_by_id"][identifier]
        require(
            excluded == priority["previously_excluded_hub_cases"] and len(excluded) == 5,
            "wrong prior exclusions",
        )
        all_cases = {(m, z) for m in range(2) for z in range(3)}
        require(all_cases - set(map(tuple, excluded)) == {hub_case}, "not sole remaining case")
        proof_refs = []
        for m4, z in excluded:
            key = f"m4-{m4}-z-{z}"
            path = HERE.parent / "four-seven-hub-count-screen" / (key + "-audit.json")
            require(sha(path) == plan["prior_child_audit_sha256"][key], "child proof changed")
            proof_refs.append(
                {"hub_case": [m4, z], "audit": str(path.relative_to(ROOT)), "sha256": sha(path)}
            )
        fixed_ids = [
            block_ids[tuple(sorted((1, 2, 3, *edge)))]
            for edge in representatives[identifier]["edges"]
        ]
        require(len(fixed_ids) == len(set(fixed_ids)) == 7, "bad fixed link")
        m4, z = hub_case
        four = [i for i, block in enumerate(blocks) if HUBS <= set(block)]
        triple = [
            (i, math.comb(len(set(block) & HUBS), 3))
            for i, block in enumerate(blocks)
            if len(set(block) & HUBS) >= 3
        ]
        rows = [[[i], [1], 1, 1] for i in fixed_ids] + [
            [four, [1] * len(four), m4, m4],
            [[i for i, _ in triple], [a for _, a in triple], 4 + z, 4 + z],
        ]
        proto = cp_model_pb2.CpModelProto()
        proto.CopyFrom(original)
        for ids, coefficients, lower, upper in rows:
            row = proto.constraints.add().linear
            row.vars.extend(ids)
            row.coeffs.extend(coefficients)
            row.domain.extend([lower, upper])
        stripped = cp_model_pb2.CpModelProto()
        stripped.CopyFrom(proto)
        del stripped.constraints[4550:]
        require(stripped == original, "base changed")
        model = cp_model.CpModel()
        model.proto.parse_text_format(text_format.MessageToString(proto))
        require(not model.validate(), "invalid restricted CP model")
        model_path = OUTPUT / (identifier + ".pbtxt")
        model_path.write_text(text_format.MessageToString(proto))
        rows_path = OUTPUT / (identifier + "-added-rows.json")
        rows_path.write_text(json.dumps(rows, indent=2) + "\n")
        records.append(
            {
                "case": identifier,
                "base_case": "matching",
                "hub_case": list(hub_case),
                "fixed_ids": fixed_ids,
                "fixed_blocks": [blocks[i] for i in fixed_ids],
                "model": str(model_path.relative_to(ROOT)),
                "model_sha256": sha(model_path),
                "added_rows": str(rows_path.relative_to(ROOT)),
                "added_rows_sha256": sha(rows_path),
                "source_base": str(source_path.relative_to(ROOT)),
                "source_base_sha256": sha(source_path),
                "total_variables": len(proto.variables),
                "total_constraints": len(proto.constraints),
                "original_proto_preserved": True,
                "added_equalities": 9,
                "prior_hub_case_proofs": proof_refs,
                "cp_model_valid": True,
            }
        )
    manifest = {
        "version": "v1.0.0",
        "builder_sha256": sha(Path(__file__)),
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "ortools_version": ortools_version,
        "base_manifest_sha256": sha(BASE / "manifest.json"),
        "base_independent_audit_sha256": sha(BASE / "independent-audit.json"),
        "priority_plan_sha256": sha(PLAN),
        "registry_sha256": sha(REGISTRY),
        "representative_catalog_sha256": sha(catalog_path),
        "cases": records,
        "scope": "Two restricted construction pilots only. Base remains the audited106 "
        "catalog version;108 registry used solely for open-case selection. No solve.",
    }
    for name in ["build.py"]:
        (OUTPUT / name).write_bytes((HERE / name).read_bytes())
    for path in [OUTPUT / "manifest.json", HERE / "manifest.json"]:
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
