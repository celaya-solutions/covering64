# Document:    Readback Audit of the Surviving Heavy-Link Hull Prototype
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      48ca5a89c28bb1c11d4499d9916009277eea32f9efd235ee27362d0000fcd55d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import gzip
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCRATCH = REPO / "experiments/scratch/four-seven-template-hull-20261003"
SCREEN = REPO / "experiments/scratch/four-seven-link-lp-full"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compressed(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def check_rows(payload, expected_template_edges, blocks):
    count = len(expected_template_edges)
    require(
        payload["width"] == 4768 + 4 * count and len(payload["rows"]) == 4550, "model dimensions"
    )
    require(payload["base_width"] == 4768 and payload["base_rows"] == 4270, "base offsets")
    require(
        len(payload["transports"]) == 4 and len(payload["extension_rows"]) == 280,
        "extension metadata",
    )
    lambdas = collections.defaultdict(list)
    for group in range(4):
        record = payload["transports"][group]
        require(
            record["group_index"] == group and record["template_count"] == count, "transport index"
        )
        start = 4768 + group * count
        require(
            record["lambda_start"] == start and record["lambda_stop_exclusive"] == start + count,
            "lambda index range",
        )
        anchors = tuple(range(4 * group + 1, 4 * group + 4))
        require(record["anchor_triple"] == list(anchors), "anchor labels")
        points = record["point_permutation"]
        inverse = record["inverse_point_permutation"]
        require(sorted(points) == sorted(inverse) == list(range(1, 17)), "point bijection")
        require(all(inverse[points[p - 1] - 1] == p for p in range(1, 17)), "inverse map")
        normalization = payload["rows"][4270 + 70 * group]
        require(
            normalization == [list(range(start, start + count)), [1] * count, 1, 1], "simplex row"
        )
        block_ids = set()
        for row_index in range(4270 + 70 * group + 1, 4270 + 70 * (group + 1)):
            indices, coefficients, lower, upper = payload["rows"][row_index]
            require(lower == upper == 0 and len(indices) == len(coefficients), "marginal format")
            require(indices == sorted(set(indices)) and 0 <= indices[0] < 4368, "marginal indices")
            require(coefficients == [1, *([-1] * (len(indices) - 1))], "marginal signs")
            block = blocks[indices[0]]
            require(set(anchors) <= set(block) and indices[0] not in block_ids, "marginal block")
            block_ids.add(indices[0])
            edge = tuple(p for p in block if p not in anchors)
            require(len(edge) == 2, "outside edge")
            for variable in indices[1:]:
                require(start <= variable < start + count, "wrong group lambda")
                lambdas[variable].append(edge)
        expected_blocks = {
            i
            for i, block in enumerate(blocks)
            if set(anchors) <= set(block)
            and not any(len(set(block) & set(range(4 * g + 1, 4 * g + 4))) == 2 for g in range(4))
        }
        require(block_ids == expected_blocks and len(block_ids) == 69, "marginal completeness")
        for template, edges in enumerate(expected_template_edges):
            transported = tuple(sorted(tuple(sorted(points[p - 1] for p in e)) for e in edges))
            actual = tuple(sorted(lambdas[start + template]))
            require(
                actual == transported and len(actual) == 7,
                "template column does not equal its link",
            )
    require(len(lambdas) == 4 * count, "missing lambda column")
    return dict(
        one_hot_columns_checked=4 * count,
        marginal_rows_checked=276,
        simplex_rows_checked=4,
        extension_nonzeros=sum(len(r[0]) for r in payload["rows"][4270:]),
    )


def main():
    manifest = json.loads((SCRATCH / "manifest.json").read_text())
    require(
        (SCRATCH / "manifest.json").read_bytes() == (HERE / "prototype-manifest.json").read_bytes(),
        "manifest copy mismatch",
    )
    for path, expected in manifest["inputs"].items():
        require(digest(REPO / path) == expected, "input hash mismatch")
    audit = json.loads(
        (HERE.parent / "four-seven-link-lp-independent/full-v1.1.0-final-audit.json").read_text()
    )
    excluded = {r["id"] for r in audit["checks"] if r["proves_infeasible"]}
    raw_orbits = compressed(HERE.parent / "four-seven-link-orbits/relabelings.json.gz")
    expected = {
        c["case"]: {
            tuple(tuple(e) for e in m["edges"]): orbit["id"]
            for orbit in c["orbits"]
            if orbit["id"] not in excluded
            for m in orbit["maps"]
        }
        for c in raw_orbits
    }
    blocks = list(itertools.combinations(range(1, 17), 5))
    results = []
    for saved in manifest["cases"]:
        case = saved["case"]
        directory = SCRATCH / case
        catalog_path = directory / "base-catalog.json.gz"
        rows_path = directory / "extended-rows.json.gz"
        require(
            digest(catalog_path) == saved["catalog_sha256"]
            and digest(rows_path) == saved["extended_rows_sha256"],
            "generated artifact hash",
        )
        catalog = compressed(catalog_path)
        templates = catalog["templates"]
        require([t["index"] for t in templates] == list(range(len(templates))), "catalog numbering")
        links = [tuple(tuple(e) for e in t["edges"]) for t in templates]
        require(
            links == sorted(expected[case]) and catalog["template_count"] == len(links),
            "complete labeled catalog",
        )
        require(
            all(
                t["representative_id"] == expected[case][link]
                for t, link in zip(templates, links, strict=True)
            ),
            "representative provenance",
        )
        payload = compressed(rows_path)
        base = compressed(SCREEN / f"{case}-rows.json.gz")
        require(
            payload["rows"][:4270] == base["rows"] and base["width"] == 4768, "base rows preserved"
        )
        report = check_rows(payload, links, blocks)
        controls = []
        for name, row_index, part, position, broken in (
            ("wrong marginal sign", 4271, 1, 1, 1),
            ("wrong lambda group", 4271, 0, 1, payload["width"]),
            ("wrong simplex coefficient", 4270, 1, 0, 2),
        ):
            original = payload["rows"][row_index][part][position]
            payload["rows"][row_index][part][position] = broken
            try:
                check_rows(payload, links, blocks)
            except ValueError:
                controls.append(dict(control=name, rejected=True))
            else:
                raise ValueError("damaged extension accepted")
            finally:
                payload["rows"][row_index][part][position] = original
        report.update(
            case=case,
            valid=True,
            templates=len(links),
            damaged_controls=controls,
            catalog_sha256=digest(catalog_path),
            extended_rows_sha256=digest(rows_path),
        )
        results.append(report)
        print(json.dumps(report), flush=True)
    output = dict(
        valid=True,
        source_sha256=digest(Path(__file__)),
        manifest_sha256=digest(SCRATCH / "manifest.json"),
        results=results,
        scope="Catalog and sparse-extension readback only. No LP or integer solve.",
    )
    (HERE / "readback-audit.json").write_text(json.dumps(output, indent=2) + "\n")


if __name__ == "__main__":
    main()
