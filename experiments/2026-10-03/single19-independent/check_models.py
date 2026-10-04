# Document:    Independent Raw Model Audit for the Sole Degree-Nineteen Branch
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5c0742239afa850faa8d9c37c7624437f7349f54a6fc92ef22153fc429791056
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reconstruct every linear row from combinations and frozen blocks, without builders."""

import argparse
import copy
import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[3]
BUILDER_SHA256 = "df69255f9855eb28d226d449dbb08e446eb4b47c8becece99ae0c49a7bd7ba72"
ROADMAP_SHA256 = "5354e30061fff68bc34fd18699ba7ced11145f0230d1b04bb7d092eac42f7f67"
MAX = 2**63 - 1
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
PAIRS = tuple(itertools.combinations(range(1, 17), 2))
INCIDENT = {subset: [] for size in (1, 2, 3)
            for subset in itertools.combinations(range(1, 17), size)}
for index, block in enumerate(BLOCKS):
    for size in (1, 2, 3):
        for subset in itertools.combinations(block, size):
            INCIDENT[subset].append(index)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row_signature(indices, lower, upper):
    return tuple((index, 1) for index in indices), (lower, upper)


def expected_rows(fixed, high):
    require(type(high) is int and 2 <= high <= 16, "invalid degree21 point")
    require(len(fixed) == len(set(fixed)) == 19, "nineteen distinct fixed blocks required")
    require(all(block in BLOCKS and block[0] == 1 for block in fixed), "invalid fixed link block")
    selected = set(fixed)
    result = Counter(row_signature(INCIDENT[triple], 1, MAX) for triple in TRIPLES)
    result[row_signature(range(4368), 64, 64)] += 1
    for point in range(1, 17):
        degree = 19 if point == 1 else 21 if point == high else 20
        result[row_signature(INCIDENT[(point,)], degree, degree)] += 1
    result.update(row_signature(INCIDENT[pair], 5, MAX) for pair in PAIRS)
    for index, block in enumerate(BLOCKS):
        if block[0] == 1:
            value = int(block in selected)
            result[row_signature([index], value, value)] += 1
    require(sum(result.values()) == 2062, "bad expected row count")
    return result


def check_proto(model, fixed, high):
    require({field.name for field, _ in model.ListFields()} <= {"variables", "constraints"},
            "unexpected model field such as objective or hint")
    require(len(model.variables) == 4368, "wrong variable count")
    for index, variable in enumerate(model.variables):
        require(variable.name == f"block_{index}" and tuple(variable.domain) == (0, 1),
                "wrong variable order, name, or Boolean domain")
    actual = Counter()
    rows = []
    for constraint in model.constraints:
        require(constraint.WhichOneof("constraint") == "linear"
                and not constraint.enforcement_literal, "unconditional linear rows required")
        linear = constraint.linear
        require(len(linear.domain) == 2 and len(linear.vars) == len(linear.coeffs)
                and len(set(linear.vars)) == len(linear.vars), "malformed linear row")
        require(all(0 <= index < 4368 for index in linear.vars), "bad coefficient index")
        actual[(tuple(sorted(zip(linear.vars, linear.coeffs))), tuple(linear.domain))] += 1
        lower, upper = linear.domain
        rows.append([list(linear.vars), list(linear.coeffs),
                     int(lower) if lower > -(1 << 60) else None,
                     int(upper) if upper < (1 << 60) else None])
    require(actual == expected_rows(fixed, high), "raw constraints differ from independent model")
    return rows


def check_case_records(records, roadmap):
    expected = {case["id"]: {**case, "shape": item["shape"],
                            "witness_sha256": item["witness_sha256"]}
                for item in roadmap["classes"] for case in item["single19_cases"]}
    require(len(records) == len(expected) == 38, "incomplete case inventory")
    require({item["id"] for item in records} == set(expected), "wrong or duplicated case IDs")
    for record in records:
        for key, value in expected[record["id"]].items():
            require(record[key] == value, f"case metadata changed: {key}")
        require(record["variables"] == 4368 and record["rows"] == 2062, "wrong declared dimensions")


def controls(model, fixed, high, records, roadmap):
    damaged = []

    def reject(name, mutation):
        duplicate = cp_model_pb2.CpModelProto()
        duplicate.CopyFrom(model)
        mutation(duplicate)
        try:
            check_proto(duplicate, fixed, high)
        except ValueError:
            damaged.append(name)
        else:
            raise ValueError(f"damaged control accepted: {name}")

    reject("missing row", lambda m: m.constraints.pop())
    reject("duplicate row", lambda m: m.constraints.add().CopyFrom(m.constraints[0]))
    reject("weakened coverage", lambda m: m.constraints[0].linear.domain.__setitem__(0, 0))
    reject("altered coefficient", lambda m: m.constraints[0].linear.coeffs.__setitem__(0, 2))
    reject("duplicated coefficient index", lambda m: m.constraints[0].linear.vars.__setitem__(
        0, m.constraints[0].linear.vars[1]))
    reject("conditional coverage", lambda m: m.constraints[0].enforcement_literal.append(0))
    reject("split domain", lambda m: m.constraints[0].linear.domain.extend([MAX, MAX]))
    reject("changed variable name", lambda m: setattr(m.variables[0], "name", "block_1"))
    reject("changed variable domain", lambda m: m.variables[0].domain.__setitem__(1, 2))
    reject("extra variable", lambda m: m.variables.add(name="unexpected", domain=[0, 1]))
    reject("added objective", lambda m: m.objective.vars.append(0))
    reject("added hint", lambda m: m.solution_hint.vars.append(0))
    fixed_row = next(index for index, row in enumerate(model.constraints)
                     if len(row.linear.vars) == 1 and list(row.linear.domain) == [1, 1])
    reject("changed selected block",
           lambda m: m.constraints[fixed_row].linear.domain.__setitem__(0, 0))
    cardinality = next(index for index, row in enumerate(model.constraints)
                       if len(row.linear.vars) == 4368)
    reject("changed cardinality",
           lambda m: m.constraints[cardinality].linear.domain.__setitem__(0, 63))
    for name, mutate in (
            ("missing case", lambda cases: cases.pop()),
            ("duplicated case", lambda cases: cases.__setitem__(0, copy.deepcopy(cases[1]))),
            ("wrong high point", lambda cases: cases[0].__setitem__("degree21_point", 1)),
            ("wrong case shape", lambda cases: cases[0].__setitem__("shape", 999))):
        cases = copy.deepcopy(records)
        mutate(cases)
        try:
            check_case_records(cases, roadmap)
        except ValueError:
            damaged.append(name)
        else:
            raise ValueError(f"damaged case control accepted: {name}")
    return damaged


def audit(directory):
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    roadmap_path = directory / "roadmap.json"
    roadmap = json.loads(roadmap_path.read_text())
    require(sha(roadmap_path) == manifest["roadmap_sha256"] == ROADMAP_SHA256,
            "audited roadmap hash mismatch")
    require(sha(directory / "single19_search.py") == manifest["source_sha256"] == BUILDER_SHA256,
            "builder source hash mismatch")
    require(manifest["solves_performed"] == 0, "unexpected preparation claim")
    check_case_records(manifest["cases"], roadmap)
    results = []
    first = None
    for record in manifest["cases"]:
        witness = directory / f"shape-{record['shape']}-class-0.txt"
        require(sha(witness) == record["witness_sha256"], "witness hash mismatch")
        fixed = tuple(tuple(map(int, line.split())) for line in witness.read_text().splitlines()
                      if line.strip())
        path = directory / f"{record['id']}.pbtxt"
        require(sha(path) == record["model_sha256"], "model hash mismatch")
        model = text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())
        rows = check_proto(model, fixed, record["degree21_point"])
        row_path = directory / f"{record['id']}-rows.json.gz"
        require(sha(row_path) == record["rows_sha256"], "row archive hash mismatch")
        require(json.loads(gzip.decompress(row_path.read_bytes())) == {"width": 4368, "rows": rows},
                "LP row archive differs from raw protobuf")
        results.append({"id": record["id"], "passed": True, "variables": 4368, "rows": 2062,
                        "model_sha256": record["model_sha256"],
                        "rows_sha256": record["rows_sha256"]})
        if first is None:
            first = model, fixed, record["degree21_point"]
    damaged = controls(*first, manifest["cases"], roadmap)
    return {"checker_sha256": sha(Path(__file__)), "input_manifest_sha256": sha(manifest_path),
            "builder_sha256": BUILDER_SHA256, "roadmap_sha256": ROADMAP_SHA256,
            "cases": results, "damaged_controls_rejected": damaged,
            "scope": "Exact reconstruction of all38 sole-degree19 models. Four-link classification "
                     "and distinguished-point orbit completeness were independently "
                     "audited separately."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.directory)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"cases_passed": len(result["cases"]),
                      "damaged_controls_rejected": len(result["damaged_controls_rejected"])}))


if __name__ == "__main__":
    main()
