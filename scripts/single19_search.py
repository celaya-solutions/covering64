# Document:    Sole Degree-Nineteen Branch Models
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2d68c55a00ee637782c3c2188e6f7f1d160fafe50ff5fe816c0dcc6fac1b9699
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare the 38 audited lone-degree19 cases; perform no extension search."""

import argparse
import gzip
import hashlib
import json
import subprocess
from itertools import combinations
from pathlib import Path

import ortools
from four_seven_link_lp import linear_rows
from ortools.sat.python import cp_model

from covering64.core import Universe, read_blocks, verify_cover

ROOT = Path(__file__).resolve().parents[1]


def build_model(link, degree21_point):
    """Keep every global block variable, fixing exactly the supplied point1 link.

    In a cover of at most64 blocks with exactly one degree19 point, the degree
    sum is at least319 and at most320 and is divisible by5. Thus it is320:
    exactly64 blocks, one degree21 point, and fourteen degree20 points.
    This function encodes that conditional profile; other branches remain open.
    """
    if type(degree21_point) is not int or not 2 <= degree21_point <= 16:
        raise ValueError("degree21 point must be an integer label from2 through16")
    link = tuple(tuple(block) for block in link)
    if len(link) != 19 or len(set(link)) != 19:
        raise ValueError("nineteen distinct link blocks required")
    for block in link:
        if (len(block) != 5 or any(type(p) is not int or not 1 <= p <= 16 for p in block)
                or tuple(sorted(set(block))) != block or block[0] != 1):
            raise ValueError("canonical five-subsets containing point1 required")
    local = [tuple(point - 1 for point in block[1:]) for block in link]
    if not verify_cover(local, 15, 4, 2)["valid"]:
        raise ValueError("the supplied point1 link does not cover all105 pairs")
    universe = Universe.build()
    model = cp_model.CpModel()
    xs = [model.new_bool_var(f"block_{i}") for i in range(len(universe.blocks))]
    for containing in universe.containing:
        model.add(sum(xs[i] for i in containing) >= 1)
    model.add(sum(xs) == 64)
    points = {point: [] for point in range(1, 17)}
    pairs = {pair: [] for pair in combinations(range(1, 17), 2)}
    for index, block in enumerate(universe.blocks):
        for point in block:
            points[point].append(index)
        for pair in combinations(block, 2):
            pairs[pair].append(index)
    for point, ids in points.items():
        target = 19 if point == 1 else 21 if point == degree21_point else 20
        model.add(sum(xs[index] for index in ids) == target)
    for ids in pairs.values():
        model.add(sum(xs[index] for index in ids) >= 5)
    fixed = set(link)
    for index in points[1]:
        model.add(xs[index] == int(universe.blocks[index] in fixed))
    return universe, model, xs


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output directory must be new")
    roadmap = ROOT / "experiments/2026-10-03/degree19-roadmap/orbits.json"
    records = json.loads(roadmap.read_text())
    if records["single19_cases"] != 38:
        parser.error("expected the independently checked38-case roadmap")
    args.output.mkdir(parents=True)
    (args.output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (args.output / "roadmap.json").write_bytes(roadmap.read_bytes())
    manifest = {
        "scope": "Exactly one degree19 point, normalized to1. Four-class link completeness "
                 "and the38 high-point orbits are separately audited prerequisites.",
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": digest(Path(__file__)), "roadmap_sha256": digest(roadmap),
        "ortools_version": ortools.__version__, "solves_performed": 0, "cases": [],
    }
    for record in records["classes"]:
        shape = record["shape"]
        witness = ROOT / f"experiments/2026-10-03/link-classification/shape-{shape}-class-0.txt"
        if digest(witness) != record["witness_sha256"]:
            raise ValueError("link witness hash mismatch")
        link = read_blocks(witness)
        (args.output / witness.name).write_bytes(witness.read_bytes())
        for case in record["single19_cases"]:
            universe, model, xs = build_model(link, case["degree21_point"])
            path = args.output / f"{case['id']}.pbtxt"
            model.export_to_file(str(path))
            rows, width = linear_rows(model)
            row_path = args.output / f"{case['id']}-rows.json.gz"
            row_path.write_bytes(gzip.compress(
                (json.dumps({"width": width, "rows": rows}) + "\n").encode(), mtime=0))
            manifest["cases"].append({**case, "shape": shape, "variables": len(xs),
                                      "rows": len(rows), "model_sha256": digest(path),
                                      "rows_sha256": digest(row_path),
                                      "witness_sha256": digest(witness)})
    if len(manifest["cases"]) != 38 or len({x["id"] for x in manifest["cases"]}) != 38:
        raise ValueError("wrong or duplicate case set")
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"cases": 38, "solves_performed": 0,
                      "manifest_sha256": digest(args.output / "manifest.json")}))


if __name__ == "__main__":
    main()
