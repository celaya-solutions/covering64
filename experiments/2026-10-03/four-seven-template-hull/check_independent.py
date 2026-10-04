# Document:    Independent Surviving-Link Hull Matrix Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2fabf1e6493fdb066b4846ecbc8f035c45ec2c7cfc708636faca849f91bc4368
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check frozen local hull matrices using only standard-library raw evidence."""

import gzip
import hashlib
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-hull-20261003"
ORIGINAL = ROOT / "experiments/scratch/four-seven-link-lp-full"


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(edges):
    return tuple(sorted(tuple(sorted(edge)) for edge in edges))


def check_row(actual, expected):
    require(len(actual) == 4, "row shape")
    indices, coefficients, lower, upper = actual
    require(len(indices) == len(coefficients), "coefficient length")
    require(len(indices) == len(set(indices)), "repeated variable")
    require(all(type(i) is int and i >= 0 for i in indices), "variable type")
    require(all(type(c) is int and c != 0 for c in coefficients), "coefficient type")
    require(dict(zip(indices, coefficients)) == expected[0], "row coefficients")
    require((lower, upper) == expected[1:], "row bounds")


def main():
    manifest = load(HERE / "prototype-manifest.json")
    require(sha(HERE / "build.py") == manifest["source_sha256"], "builder hash")
    for name, digest in manifest["inputs"].items():
        require(sha(ROOT / name) == digest, "input hash " + name)
    maps = load(ROOT / "experiments/2026-10-03/four-seven-link-orbits/relabelings.json.gz")
    results = load(ORIGINAL / "results.json.gz")
    excluded = {entry["id"] for entry in results if entry["proves_infeasible"]}
    require(len(excluded) == 100, "original exclusion count")
    for entry in results:
        if entry["id"] in excluded:
            numerator, denominator = entry["certificate"]["gap"]
            require(numerator > 0 and denominator > 0, "nonpositive certificate gap")
    blocks = list(combinations(range(1, 17), 5))
    block_ids = {block: i for i, block in enumerate(blocks)}
    anchors = [set(range(4 * group + 1, 4 * group + 4)) for group in range(4)]
    reports = []
    for data in manifest["cases"]:
        case = data["case"]
        catalog_path = RAW / case / "base-catalog.json.gz"
        matrix_path = RAW / case / "extended-rows.json.gz"
        require(sha(catalog_path) == data["catalog_sha256"], "catalog hash")
        require(sha(matrix_path) == data["extended_rows_sha256"], "matrix hash")
        expected_catalog = {}
        case_maps = next(item for item in maps if item["case"] == case)
        for orbit in case_maps["orbits"]:
            if orbit["id"] in excluded:
                continue
            for mapping in orbit["maps"]:
                key = normalized(mapping["edges"])
                require(key not in expected_catalog, "duplicate input link")
                expected_catalog[key] = orbit["id"]
        catalog = load(catalog_path)
        templates = catalog["templates"]
        n = len(expected_catalog)
        require(n == data["templates_per_group"] == catalog["template_count"], "catalog count")
        actual_catalog = {}
        for index, entry in enumerate(templates):
            require(entry["index"] == index, "template order")
            key = normalized(entry["edges"])
            require(len(key) == 7 and len(set(key)) == 7, "malformed link")
            require(key not in actual_catalog, "duplicate surviving template")
            actual_catalog[key] = entry["representative_id"]
        require(actual_catalog == expected_catalog, "surviving catalog differs")
        require(list(actual_catalog) == sorted(expected_catalog), "catalog not lexicographic")
        matrix = load(matrix_path)
        base = load(ORIGINAL / f"{case}-rows.json.gz")
        require(matrix["rows"][:4270] == base["rows"], "changed base row")
        require(matrix["base_width"] == base["width"] == 4768, "changed base width")
        require(matrix["base_rows"] == 4270, "changed base row count")
        require(matrix["width"] == 4768 + 4 * n == data["total_variables"], "total width")
        require(matrix["variable_bounds"] ==
                "Every variable has bounds [0,1]; all are continuous in this LP.", "bounds")
        hub_edges = ({(0, 1), (1, 2), (2, 3), (0, 3)} if case == "cycle"
                     else {(0, 1), (2, 3)})
        expected_rows = []
        for group, transport in enumerate(matrix["transports"]):
            require(transport["group_index"] == group, "transport order")
            perm = transport["point_permutation"]
            inverse = transport["inverse_point_permutation"]
            require(sorted(perm) == sorted(inverse) == list(range(1, 17)), "not bijections")
            require(all(inverse[perm[i] - 1] == i + 1 for i in range(16)), "inverse map")
            gp = [(perm[4 * g + 3] - 1) // 4 for g in range(4)]
            require(gp[0] == group and sorted(gp) == list(range(4)), "group transport")
            for g in range(4):
                require(perm[4 * g + 3] == 4 * gp[g] + 4, "hub transport")
                require({perm[p - 1] for p in anchors[g]} == anchors[gp[g]], "anchor map")
            require({tuple(sorted((gp[a], gp[b]))) for a, b in hub_edges} == hub_edges,
                    "hub graph changed")
            start = 4768 + group * n
            require((transport["lambda_start"], transport["lambda_stop_exclusive"])
                    == (start, start + n), "lambda interval")
            expected_rows.append(({index: 1 for index in range(start, start + n)}, 1, 1))
            incidences = defaultdict(dict)
            outside = set(range(1, 17)) - anchors[group]
            edges = [edge for edge in combinations(sorted(outside), 2)
                     if not any(set(edge) <= anchor for anchor in anchors)]
            require(len(edges) == 69, "allowed edge count")
            for index, template in enumerate(templates):
                transformed = normalized((perm[a - 1], perm[b - 1])
                                         for a, b in template["edges"])
                require(len(set(transformed)) == 7, "damaged transported link")
                for edge in transformed:
                    require(edge in edges, "illegal transported edge")
                    incidences[edge][start + index] = -1
            for edge in edges:
                block_id = block_ids[tuple(sorted(anchors[group] | set(edge)))]
                expected_rows.append(({block_id: 1, **incidences[edge]}, 0, 0))
        require(len(matrix["transports"]) == 4 and len(expected_rows) == 280, "extension count")
        require(len(matrix["rows"]) == 4550, "total row count")
        for row, expected in zip(matrix["rows"][4270:], expected_rows):
            check_row(row, expected)
        damaged_controls = 0
        sample = matrix["rows"][4271]
        mutations = [
            [sample[0], [-value for value in sample[1]], sample[2], sample[3]],
            [sample[0][1:], sample[1][1:], sample[2], sample[3]],
            [sample[0], sample[1], 1, 1],
            [sample[0] + [sample[0][0]], sample[1] + [sample[1][0]], 0, 0],
        ]
        for damaged in mutations:
            try:
                check_row(damaged, expected_rows[1])
            except ValueError:
                damaged_controls += 1
            else:
                raise ValueError("damaged row was accepted")
        reports.append({"case": case, "passed": True, "templates_per_group": n,
                        "all_catalog_members_checked": True, "base_rows_preserved": 4270,
                        "transported_rows_checked": 280, "damaged_controls": damaged_controls,
                        "catalog_sha256": sha(catalog_path), "matrix_sha256": sha(matrix_path)})
    report = {"passed": True, "valid": True,
              "manifest_sha256": sha(HERE / "prototype-manifest.json"),
              "cases": reports, "checker_sha256": sha(Path(__file__)),
              "scope": "Independent raw matrix and complete catalog check; no solve. "
                       "Original exclusions use their separately replayed exact certificates."}
    (HERE / "independent-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
