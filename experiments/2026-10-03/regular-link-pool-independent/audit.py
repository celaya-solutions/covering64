# Document:    Independent Pooled Regular Link Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      941f2fc049dc30be5df12332e2c4c6cdc463040aea7a31c061c08a99287e9950
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check frozen finite-pool maps, all model rows, and assembled controls."""

import gzip
import hashlib
import importlib.util
import itertools as it
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "experiments/scratch/regular-link-pool-20261003"
OUT = Path(__file__).resolve().parent
EDGES = {(0, 1), (0, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12)}
PAIRS = list(it.combinations(range(13), 2))
TRIPLES = list(it.combinations(range(13), 3))
LIMIT = 9223372036854775807


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(family):
    return tuple(sorted(tuple(sorted(b)) for b in family))


def inspect(family):
    require(len(family) == len(set(family)) == 13, "family cardinality or duplicates")
    require(all(len(b) == len(set(b)) == 4 and tuple(sorted(b)) == b
                and all(type(x) is int and 0 <= x < 13 for x in b)
                for b in family), "malformed quadruple")
    require(Counter(x for b in family for x in b) == {x: 4 for x in range(13)},
            "family degree mismatch")
    pair_counts = Counter(p for b in family for p in it.combinations(b, 2))
    missing = set(PAIRS) - set(pair_counts)
    require(missing <= EDGES, "uncovered pair outside allowed graph")
    return pair_counts, missing


def normalized_maps(source):
    # Graph automorphisms fix its center, exchange leaves, and permute/orient
    # five isolated edges. A second source orientation exchanges endpoints01.
    target_edges = sorted(EDGES - {(0, 1), (0, 2)})
    result = set()
    map_count = 0
    for swap_leaf, swap_source, order, orientations in it.product(
            range(2), range(2), it.permutations(target_edges), it.product(range(2), repeat=5)):
        mapping = [0, 1, 2] + [0] * 10
        if swap_source:
            mapping[0], mapping[1] = mapping[1], mapping[0]
        for index, edge in enumerate(order):
            mapping[3 + 2 * index:5 + 2 * index] = edge[::(-1 if orientations[index] else 1)]
        if swap_leaf:
            mapping = [2 if x == 1 else 1 if x == 2 else x for x in mapping]
        require(sorted(mapping) == list(range(13)), "independent map is not bijective")
        result.add(canonical(tuple(mapping[x] for x in b) for b in source))
        map_count += 1
    return result, map_count


def row_matches(row, coefficients, bounds):
    actual = dict(zip(row.linear.vars, row.linear.coeffs))
    return (not row.enforcement_literal and actual == coefficients
            and len(actual) == len(row.linear.vars)
            and list(row.linear.domain) == list(bounds))


def audit_rows(families, source, pair_counts, missing):
    model = cp_model.CpModel()
    require(model.proto.parse_text_format((ARCHIVE / "model.pbtxt").read_text()),
            "cannot parse stored model")
    count = len(families)
    all_blocks = list(it.combinations(range(1, 17), 5))
    outside_ids = [i for i, b in enumerate(all_blocks) if b[0] >= 4]
    outside = [tuple(x - 4 for x in all_blocks[i]) for i in outside_ids]
    require(len(outside) == 1287, "outside universe mismatch")
    expected_vars = [(f"family_{i}", [0, 3]) for i in range(count)]
    expected_vars += [(f"block_{i}", [0, 1]) for i in outside_ids]
    require([(v.name, list(v.domain)) for v in model.proto.variables] == expected_vars,
            "variable order, label or domain mismatch")
    rows = [({i: 1 for i in range(count)}, (3, 3)),
            ({count + i: 1 for i in range(1287)}, (18, 18))]
    family_triples = [{t for b in family for t in it.combinations(b, 3)} for family in families]
    for triple in TRIPLES:
        coefficients = {i: 1 for i, ts in enumerate(family_triples) if triple in ts}
        coefficients.update({count + i: 1 for i, b in enumerate(outside) if set(triple) <= set(b)})
        rows.append((coefficients, (1, LIMIT)))
    for point in range(13):
        degree = 6 if point == 0 else 7
        rows.append(({count + i: 1 for i, b in enumerate(outside) if point in b},
                     (degree, degree)))
    for pair in PAIRS:
        coefficients = {i: values[pair] for i, values in enumerate(pair_counts) if values[pair]}
        coefficients.update({count + i: 1 for i, b in enumerate(outside) if set(pair) <= set(b)})
        rows.append((coefficients, (5 - int(pair in EDGES), LIMIT)))
    rows.append(({families.index(source): 1}, (1, LIMIT)))
    for spoke in [(0, 1), (0, 2)]:
        rows.append(({i: 1 for i, holes in enumerate(missing) if spoke in holes}, (1, LIMIT)))
    require(len(rows) == len(model.proto.constraints) == 382, "extra or missing model row")
    for index, (row, (coefficients, bounds)) in enumerate(zip(model.proto.constraints, rows)):
        require(row_matches(row, coefficients, bounds), f"model row mismatch: {index}")
    controls = {}
    for label, index in [("outside_cardinality", 1), ("hub_degree", 288),
                         ("outside_pair_target", 301), ("joint_spoke_omission", 381)]:
        row = model.proto.constraints[index]
        coefficients, bounds = rows[index]
        row.linear.domain[0] = bounds[0] - 1
        controls[label] = not row_matches(row, coefficients, bounds)
        row.linear.domain[0] = bounds[0]
    require(all(controls.values()), "model-row damage was not detected")
    return {"variable_count": len(expected_vars), "family_variables": count,
            "outside_variables": 1287, "checked_rows": len(rows),
            "family_sum": 3, "outside_sum": 18, "fixed_blocks": 46,
            "outside_degrees": [6] + [7] * 12, "damage_controls": controls}


def candidate_controls(families, source):
    with tempfile.TemporaryDirectory(prefix="frozen-pool-audit-") as directory:
        directory = Path(directory)
        frozen_source = directory / "regular_link_pool_search.py"
        frozen_source.write_bytes((ARCHIVE / "source.py").read_bytes())
        (directory / "three_link_search.py").write_bytes((ARCHIVE / "helper.py").read_bytes())
        spec = importlib.util.spec_from_file_location("frozen_pool", frozen_source)
        subject = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(subject)
        swapped = canonical(tuple(2 if x == 1 else 1 if x == 2 else x for x in b) for b in source)
        counts = [0] * len(families)
        counts[families.index(source)] = 2
        counts[families.index(swapped)] += 1
        outside = [tuple(sorted((i + j) % 13 for j in range(5))) for i in range(13)]
        outside += [(0, 1, 4, 7, 10), (1, 2, 3, 5, 6), (4, 8, 9, 11, 12),
                    (2, 5, 7, 8, 11), (3, 6, 9, 10, 12)]
        lifted = [tuple(x + 4 for x in b) for b in outside]
        blocks = subject.assemble(families, counts, lifted)
        require(len(blocks) == len(set(blocks)) == 64, "assembled blocks not64 distinct")
        require(Counter(x for b in blocks for x in b) == {x: 20 for x in range(1, 17)},
                "assembled point degrees wrong")
        covered = {t for b in blocks for t in it.combinations(b, 3)}
        absent = sorted(set(it.combinations(range(1, 17), 3)) - covered)
        require(absent and all(min(t) >= 4 for t in absent), "anchor links not closed")
        path = OUT / "assembled-incomplete-control.txt"
        path.write_text("".join(" ".join(map(str, b)) + "\n" for b in blocks))
        checks = []
        for command in [["uv", "run", "covering64", "verify"],
                        [sys.executable, "scripts/check_cover.py"]]:
            process = subprocess.run(command + [str(path), "--expected-blocks", "64"],
                                     cwd=ROOT, capture_output=True, text=True, check=False)
            data = json.loads(process.stdout)
            require(process.returncode == 1 and not data["valid"], "incomplete control accepted")
            require(sorted(map(tuple, data["uncovered"])) == absent, "missing triples disagree")
            checks.append(data)
        require(checks[0]["canonical_sha256"] == checks[1]["canonical_sha256"],
                "candidate hashes disagree")
        controls = {}
        for label, operation in [
            ("bad_family_count", lambda: subject.assemble([source], [2], lifted)),
            ("bad_map", lambda: subject.links.mapped(source, list(range(12)))),
            ("duplicate_quad", lambda: inspect((source[0],) + source[:-1])),
            ("damaged_quad", lambda: inspect((source[0][:-1],) + source[1:])),
        ]:
            try:
                operation()
            except (ValueError, AssertionError):
                controls[label] = True
            else:
                raise AssertionError(f"damage control accepted: {label}")
        return {"distinct_blocks": 64, "all_degrees": 20, "repeated_family_multiplicity": 2,
                "missing_triples": absent, "all_missing_outside_anchors": True,
                "canonical_sha256": checks[0]["canonical_sha256"],
                "both_verifiers_reject_as_incomplete": True, "damage_controls": controls,
                "live_full_run_has_witness": json.loads((ARCHIVE / "result.json").read_text())
                    ["witness"] is not None}


def main():
    metadata = json.loads((ARCHIVE / "metadata.json").read_text())
    for filename, key in [("source.py", "source_sha256"), ("helper.py", "helper_sha256"),
                          ("pool.json.gz", "pool_sha256"), ("model.pbtxt", "model_sha256")]:
        require(sha(ARCHIVE / filename) == metadata[key], "archive hash mismatch")
    pool = json.loads(gzip.decompress((ARCHIVE / "pool.json.gz").read_bytes()))
    families = [canonical(family) for family in pool["families"]]
    source = canonical(pool["source_template"])
    require(families == sorted(set(families)), "noncanonical or duplicate pool family")
    inspected = [inspect(family) for family in families]
    pair_counts, missing = zip(*inspected)
    expected, map_count = normalized_maps(source)
    require(expected == {f for f, holes in zip(families, missing) if holes},
            "normalized source-hole-to-spoke pool mismatch")
    require(map_count == len(expected) == metadata["spoke_family_count"] == 15360,
            "normalized map or family count mismatch")
    require(sum(not holes for holes in missing) == metadata["pg_samples"] == 256,
            "sampled projective-plane family count mismatch")
    body = {"scope": "Only archived finite source-hole-to-spoke pool plus sampled planes; "
                    "not all regular link families and not all source-hole choices",
            "status": "PASS",
            "archive_hashes": {k: v for k, v in metadata.items() if "sha256" in k},
            "audit_source_sha256": sha(Path(__file__)), "map_count": map_count,
            "spoke_family_count": len(expected), "plane_family_count": 256,
            "rows": audit_rows(families, source, pair_counts, missing),
            "candidate_controls": candidate_controls(families, source)}
    header = {"Document": "Independent Pooled Regular Link Model Audit", "Version": "v1.0.0",
              "Author": "Celaya Solutions", "Contact": "hello@celayasolutions.com",
              "Date": "2026-10-03", "SHA256": hashlib.sha256(json.dumps(body, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest(), "Chain": "n/a",
              "Tx": "[not anchored]", "License": "All Rights Reserved / Celaya Solutions"}
    (OUT / "result.json").write_text(json.dumps({"document_header": header, "body": body},
                                               indent=2) + "\n")
    print(json.dumps({"status": "PASS", "families": len(families), "model_rows": 382,
                      "control_missing_triples": len(
                          body["candidate_controls"]["missing_triples"])}))


if __name__ == "__main__":
    main()
