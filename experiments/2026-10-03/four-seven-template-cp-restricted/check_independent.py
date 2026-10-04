# Document:    Independent Fixed Link and Hub Count CP Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5d78b473245420b696bda172f5d8d282bf61816e9428412c1764c935669f1472
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check the exact nine-row extension independently of its builder."""

import copy
import hashlib
import json
from itertools import combinations, product
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED = {"matching-029": [0, 2], "matching-063": [0, 1]}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def inspect(proto, base, expected_rows):
    require(len(proto.variables) == 55528 and len(proto.constraints) == 4559, "dimensions")
    stripped = copy.deepcopy(proto)
    del stripped.constraints[4550:]
    require(stripped == base, "original proto or variables changed")
    actual = []
    for constraint in proto.constraints[4550:]:
        require(not constraint.enforcement_literal and
                constraint.WhichOneof("constraint") == "linear", "not a plain equality")
        row = constraint.linear
        require(len(row.domain) == 2 and row.domain[0] == row.domain[1], "not an equality")
        actual.append([list(row.vars), list(row.coeffs), *row.domain])
    require(actual == expected_rows, "nine equalities differ from independent reconstruction")


def main():
    manifest = read(HERE / "manifest.json")
    require(sha(HERE / "build.py") == manifest["builder_sha256"], "source changed")
    inputs = {"base_manifest": HERE.parent / "four-seven-template-cp-proposal/manifest.json",
              "base_independent_audit": HERE.parent /
              "four-seven-template-cp-proposal/independent-audit.json",
              "priority_plan": HERE.parent / "four-seven-template-hub-priority/priority-plan.json",
              "registry": HERE.parent / "four-seven-template-hull-refresh-independent" /
              "combined-first-link-exclusions.json",
              "representative_catalog": HERE.parent / "four-seven-link-orbits/result.json"}
    for key, path in inputs.items():
        require(sha(path) == manifest[key + "_sha256"], "input hash: " + key)
    audit = read(inputs["base_independent_audit"])
    require(audit["passed"], "base audit missing")
    base_entry = next(r for r in audit["cases"] if r["case"] == "matching")
    registry = read(inputs["registry"])
    require(registry["passed"] and registry["excluded_count"] == 108, "checked open registry")
    reps = {rep["id"]: rep for group in read(inputs["representative_catalog"])["cases"]
            for rep in group["representatives"]}
    priority = {row["id"]: row for row in read(inputs["priority_plan"])["priority"]}
    blocks = list(combinations(range(1, 17), 5))
    ids = {b: i for i, b in enumerate(blocks)}
    hub_count = [len(set(block) & {4, 8, 12, 16}) for block in blocks]
    four = [i for i, n in enumerate(hub_count) if n == 4]
    triples = [(i, 1 if n == 3 else 4) for i, n in enumerate(hub_count) if n >= 3]
    require(len(manifest["cases"]) == 2 and
            {r["case"] for r in manifest["cases"]} == set(EXPECTED), "case inventory")
    reports, controls = [], []
    for record in manifest["cases"]:
        name = record["case"]
        require(record["base_case"] == "matching" and record["hub_case"] == EXPECTED[name]
                == priority[name]["hub_case"], "wrong branch scope")
        require(name in registry["remaining_ids"] and name not in registry["proof_sources"],
                "case no longer open")
        m4, z = record["hub_case"]
        fixed_blocks = [tuple(sorted((1, 2, 3, *edge))) for edge in reps[name]["edges"]]
        fixed_ids = [ids[block] for block in fixed_blocks]
        require(record["fixed_ids"] == fixed_ids and record["fixed_blocks"] ==
                [list(block) for block in fixed_blocks], "fixed IDs or labels changed")
        expected_rows = [[[i], [1], 1, 1] for i in fixed_ids]
        expected_rows.extend([[four, [1] * len(four), m4, m4],
                              [[i for i, _ in triples], [n for _, n in triples], 4 + z, 4 + z]])
        row_path = ROOT / record["added_rows"]
        require(sha(row_path) == record["added_rows_sha256"] and read(row_path) == expected_rows,
                "added-row archive changed")
        proofs = record["prior_hub_case_proofs"]
        require(len(proofs) == 5 and {tuple(p["hub_case"]) for p in proofs} ==
                set(product((0, 1), range(3))) - {(m4, z)}, "five other hub cases required")
        for proof in proofs:
            path = ROOT / proof["audit"]
            require(sha(path) == proof["sha256"], "prior hub proof changed")
            data = read(path)
            require(data["passed"] and data["hub_case"] == proof["hub_case"], "prior proof scope")
            entry = next(c for c in data["checks"] if c["id"] == name)
            require(entry["proves_infeasible"] and entry["gap"][0] > 0, "uncertified hub case")
        path, base_path = ROOT / record["model"], ROOT / record["source_base"]
        require(sha(path) == record["model_sha256"] and sha(base_path) ==
                record["source_base_sha256"] == base_entry["model_sha256"], "model provenance")
        base = text_format.Parse(base_path.read_text(), cp_model_pb2.CpModelProto())
        proto = text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())
        inspect(proto, base, expected_rows)
        mutations = [
            ("extra variable", lambda p: p.variables.add(name="extra", domain=[0, 1])),
            ("missing equality", lambda p: p.constraints.__delitem__(-1)),
            ("changed fixed block", lambda p: p.constraints[4550].linear.vars.__setitem__(0, 2)),
            ("changed fixed sign", lambda p: p.constraints[4550].linear.coeffs.__setitem__(0, -1)),
            ("changed hub bound", lambda p: p.constraints[4557].linear.domain.__setitem__(1, 1)),
            ("changed triple count", lambda p: p.constraints[4558].linear.coeffs.__setitem__(0, 9)),
            ("changed variable domain", lambda p: p.variables[0].domain.__setitem__(1, 2)),
            ("conditional row", lambda p: p.constraints[4550].enforcement_literal.append(0)),
        ]
        for label, mutate in mutations:
            damaged = copy.deepcopy(proto)
            mutate(damaged)
            try:
                inspect(damaged, base, expected_rows)
            except ValueError:
                controls.append({"case": name, "mutation": label, "rejected": True})
            else:
                raise ValueError("damaged control accepted: " + label)
        reports.append({"case": name, "passed": True, "hub_case": record["hub_case"],
                        "model_sha256": sha(path), "base_model_sha256": sha(base_path),
                        "fixed_ids": fixed_ids, "preserved_rows": 4550, "added_equalities": 9,
                        "variables": 55528, "rows": 4559, "prior_checked_hub_cases": 5})
    report = {"passed": True, "manifest_sha256": sha(HERE / "manifest.json"),
              "checker_sha256": sha(Path(__file__)), "cases": reports,
              "damaged_controls": controls, "solver_calls": 0,
              "scope": "Two fixed-first-link and fixed-hub-count construction models only."}
    (HERE / "independent-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": reports, "damaged_controls": len(controls)}))


if __name__ == "__main__":
    main()
