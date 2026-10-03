#!/usr/bin/env python3
# Document:    Independent Audit of Degree-Nineteen Link Hub Shapes
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5cca6b28553e42af3cd97a42e7ada8b4deddd97a3762634ca07c4a2ab90faaf1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Independently enumerate colored hub graphs and check supplied link witnesses.

Conditional on the normalized excess graph K(1,4) plus five matching edges,
the hub has replication six, since its pair degree is 14+4=3*6. All fourteen
other points have replication five. The four leaves occur in two hub blocks;
each other point occurs in one. There are therefore 8+10=18 available slots.
Each leaf is a nonloop edge A on the six hub blocks. Two parallel A edges
would repeat a leaf-leaf pair, forbidden by its target of one, so A is simple.
Each matching pair is a B edge, with loops permitted and counted twice in
the vertex degree. Every vertex satisfies degree(A)+degree(B)=3.

Conversely every such A/B graph gives six valid hub blocks with no pair above
its target. Block reorderings act by S6; leaf permutations, matching-pair
permutations and endpoint swaps remove the edge labels. Canonicalizing A by
S6 and then B by Aut(A) is therefore complete. This implementation enumerates
B via upper-triangular integer matrices, not the builder's stub matchings.

The other thirteen blocks avoid the hub. Their pair incidence must equal
target minus the six hub blocks, exactly a K4 decomposition of that residual
multigraph. No CP status is independently certified by this audit.
"""

import argparse
import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

EDGES = list(itertools.combinations(range(6), 2))
MULTIEDGES = [(a, b) for a in range(6) for b in range(a, 6)]
EDGE_RANK = {e: i for i, e in enumerate(EDGES)}
MULTIEDGE_RANK = {e: i for i, e in enumerate(MULTIEDGES)}
PERMS = list(itertools.permutations(range(6)))
EDGE_ACTIONS = [
    [EDGE_RANK[tuple(sorted((p[a], p[b])))] for a, b in EDGES] for p in PERMS
]
MULTIEDGE_ACTIONS = [
    [MULTIEDGE_RANK[tuple(sorted((p[a], p[b])))] for a, b in MULTIEDGES] for p in PERMS
]
PAIRS = list(itertools.combinations(range(2, 17), 2))
EXCESS = {(2, x) for x in range(3, 7)} | {(x, x + 1) for x in range(7, 17, 2)}
TARGET = {pair: 1 + int(pair in EXCESS) for pair in PAIRS}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def transformed_mask(mask, action):
    return sum(1 << action[i] for i in range(15) if mask & (1 << i))


def transformed_matrix(matrix, action):
    output = [0] * 21
    for index, count in enumerate(matrix):
        output[action[index]] = count
    return tuple(output)


def signature(mask, matrix):
    images = [transformed_mask(mask, action) for action in EDGE_ACTIONS]
    minimum = min(images)
    return minimum, min(transformed_matrix(matrix, MULTIEDGE_ACTIONS[i])
                        for i, image in enumerate(images) if image == minimum)


def multigraph_matrices(degree):
    """Unique symmetric nonnegative matrices with loops contributing degree two."""
    values = [0] * 21

    def row(vertex, remaining):
        if vertex == 6:
            if all(d == 0 for d in remaining):
                yield tuple(values)
            return
        for loops in range(remaining[vertex] // 2 + 1):
            values[MULTIEDGE_RANK[(vertex, vertex)]] = loops
            need = remaining[vertex] - 2 * loops
            next_degrees = list(remaining)
            next_degrees[vertex] = 0

            def distribute(neighbor, left):
                if neighbor == 6:
                    if left == 0:
                        yield from row(vertex + 1, next_degrees)
                    return
                index = MULTIEDGE_RANK[(vertex, neighbor)]
                for count in range(min(left, next_degrees[neighbor]) + 1):
                    values[index] = count
                    next_degrees[neighbor] -= count
                    yield from distribute(neighbor + 1, left - count)
                    next_degrees[neighbor] += count

            yield from distribute(vertex + 1, need)

    yield from row(0, list(degree))


def enumerate_classes():
    representatives = set()
    labeled_count = 0
    for edge_ids in itertools.combinations(range(15), 4):
        degree = [0] * 6
        for eid in edge_ids:
            a, b = EDGES[eid]
            degree[a] += 1
            degree[b] += 1
        if max(degree) > 3:
            continue
        labeled_count += 1
        mask = sum(1 << eid for eid in edge_ids)
        representatives.add(min(transformed_mask(mask, action) for action in EDGE_ACTIONS))
    classes = set()
    counts = []
    for mask in sorted(representatives):
        degree = [0] * 6
        for i, (a, b) in enumerate(EDGES):
            if mask & (1 << i):
                degree[a] += 1
                degree[b] += 1
        autos = [i for i, action in enumerate(EDGE_ACTIONS)
                 if transformed_mask(mask, action) == mask]
        matrices = list(multigraph_matrices([3 - d for d in degree]))
        require(len(matrices) == len(set(matrices)), "duplicate matrix enumeration")
        canonical_matrices = {
            min(transformed_matrix(matrix, MULTIEDGE_ACTIONS[i]) for i in autos)
            for matrix in matrices
        }
        classes.update((mask, matrix) for matrix in canonical_matrices)
        counts.append({"canonical_a_mask": mask, "labeled_b_matrices": len(matrices),
                       "a_automorphisms": len(autos), "b_classes": len(canonical_matrices)})
    return classes, counts, labeled_count


def check_blocks(blocks, count, allowed, name):
    require(isinstance(blocks, list) and len(blocks) == count, f"{name}: block count")
    normalized = []
    for block in blocks:
        require(isinstance(block, list) and len(block) == 4, f"{name}: malformed block")
        require(all(type(x) is int and x in allowed for x in block), f"{name}: bad label")
        require(block == sorted(set(block)), f"{name}: duplicate or unordered label")
        normalized.append(tuple(block))
    require(len(set(normalized)) == count, f"{name}: duplicate block")
    return normalized


def check_link(blocks):
    blocks = check_blocks(blocks, 19, range(2, 17), "link")
    counts = Counter(pair for block in blocks for pair in itertools.combinations(block, 2))
    require(dict(counts) == TARGET, "link: pair target mismatch")
    replication = Counter(x for block in blocks for x in block)
    require(replication == {x: 6 if x == 2 else 5 for x in range(2, 17)},
            "link: replication mismatch")
    require(sum(2 in b for b in blocks) == 6, "link: hub count")
    return blocks


def check_shape(shape):
    a_edges = shape["a_edges"]
    b_edges = shape["b_edges"]
    require(isinstance(a_edges, list) and len(a_edges) == 4, "A edge count")
    require(isinstance(b_edges, list) and len(b_edges) == 5, "B edge count")
    for edges, loops, name in [(a_edges, False, "A"), (b_edges, True, "B")]:
        for edge in edges:
            require(isinstance(edge, list) and len(edge) == 2, f"{name}: malformed edge")
            require(all(type(x) is int and 0 <= x < 6 for x in edge), f"{name}: endpoint")
            require(edge[0] <= edge[1] if loops else edge[0] < edge[1],
                    f"{name}: edge order or forbidden loop")
    require(len({tuple(edge) for edge in a_edges}) == 4, "parallel A edge")
    degree = Counter(v for edge in a_edges + b_edges for v in edge)
    require(degree == {v: 3 for v in range(6)}, "A+B degree must be three")
    mask = sum(1 << EDGE_RANK[tuple(edge)] for edge in a_edges)
    matrix = [0] * 21
    for edge in b_edges:
        matrix[MULTIEDGE_RANK[tuple(edge)]] += 1
    stated_signature = signature(mask, tuple(matrix))
    orbit = {transformed_mask(mask, action) for action in EDGE_ACTIONS}
    autos = sum(transformed_mask(mask, action) == mask for action in EDGE_ACTIONS)
    require(shape["a_orbit_size"] == len(orbit), "A orbit size")
    require(shape["a_automorphism_count"] == autos and len(orbit) * autos == 720,
            "A automorphism count")
    hub = check_blocks(shape["hub_blocks"], 6, range(2, 17), "hub")
    require(all(2 in block for block in hub), "hub missing distinguished point")
    locations = {x: [i for i, b in enumerate(hub) if x in b] for x in range(3, 17)}
    require(all(len(locations[x]) == (2 if x < 7 else 1) for x in range(3, 17)),
            "hub point replication")
    recovered_a = [tuple(locations[x]) for x in range(3, 7)]
    require(len(set(recovered_a)) == 4, "hub induces parallel A")
    recovered_mask = sum(1 << EDGE_RANK[edge] for edge in recovered_a)
    recovered_matrix = [0] * 21
    for point in range(7, 17, 2):
        edge = tuple(sorted((locations[point][0], locations[point + 1][0])))
        recovered_matrix[MULTIEDGE_RANK[edge]] += 1
    require(signature(recovered_mask, tuple(recovered_matrix)) == stated_signature,
            "hub blocks disagree with colored graph")
    fixed = Counter(pair for b in hub for pair in itertools.combinations(b, 2))
    require(all(fixed[p] <= TARGET[p] for p in PAIRS), "hub exceeds pair targets")
    residual = {p: TARGET[p] - fixed[p] for p in PAIRS}
    require(sum(residual.values()) == 13 * 6, "residual pair sum")
    require(all(residual[p] == 0 for p in PAIRS if 2 in p), "hub pairs not exhausted")
    require(all(sum(c for p, c in residual.items() if x in p) % 3 == 0
                for x in range(3, 17)), "residual degrees not divisible by three")
    quads = [b for b in itertools.combinations(range(3, 17), 4)
             if all(residual[p] > 0 for p in itertools.combinations(b, 2))]
    return stated_signature, hub, residual, quads


def audit(metadata, results, expected_classes=None):
    if expected_classes is None:
        expected_classes, _, _ = enumerate_classes()
    require(metadata["shape_count"] == len(metadata["shapes"]), "metadata shape count")
    found = set()
    checked = []
    for shape in metadata["shapes"]:
        sig, hub, residual, quads = check_shape(shape)
        require(sig not in found, "duplicate colored shape class")
        found.add(sig)
        checked.append((hub, residual, quads))
    require(found == expected_classes, "missing or extra colored shape classes")
    indices = [r["index"] for r in results]
    require(len(indices) == len(set(indices)), "duplicate result index")
    require(set(indices) == set(range(len(checked))), "missing or extra result case")
    witnesses = []
    for result in results:
        index = result["index"]
        hub, _, quads = checked[index]
        require(result["residual_candidate_count"] == len(quads), "residual candidate count")
        if result["link"] is None:
            require(result["status"] not in ["OPTIMAL", "FEASIBLE"], "missing link witness")
            continue
        require(result["status"] in ["OPTIMAL", "FEASIBLE"], "unexpected witnessed status")
        blocks = check_link(result["link"])
        require(set(b for b in blocks if 2 in b) == set(hub), "link has wrong hub shape")
        require(all(b in quads for b in blocks if 2 not in b), "link residual quad invalid")
        witnesses.append({"shape_index": index, "link": [list(b) for b in blocks],
                          "canonical_link_sha256": sha(sorted(blocks))})
    return {"shape_count": len(found), "witness_count": len(witnesses),
            "witnesses": witnesses,
            "solver_status_counts_not_independently_proved": dict(Counter(
                result["status"] for result in results)),
            "classification_sha256": sha(sorted(found))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to overwrite output")
    raw_metadata = (args.directory / "metadata.json").read_bytes()
    raw_results = (args.directory / "results.jsonl").read_bytes()
    raw_source = (args.directory / "source.py").read_bytes()
    metadata = json.loads(raw_metadata)
    results = [json.loads(line) for line in raw_results.splitlines()]
    require(metadata["source_sha256"] == hashlib.sha256(raw_source).hexdigest(),
            "archived builder source hash mismatch")
    classes, counts, labeled = enumerate_classes()
    body = audit(metadata, results, classes)
    body.update({"scope": "Complete hub classification conditional on normalized excess graph; "
                 "validates supplied witnesses; CP negative statuses are not certified",
                 "labeled_simple_a_graphs": labeled, "a_classes": counts,
                 "checker_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 "metadata_sha256": hashlib.sha256(raw_metadata).hexdigest(),
                 "results_sha256": hashlib.sha256(raw_results).hexdigest(),
                 "builder_source_sha256": hashlib.sha256(raw_source).hexdigest(),
                 "canonical_classes": sorted(classes)})
    header = {"Document": "Independent Link Hub Classification Audit", "Version": "v1.0.0",
              "Author": "Celaya Solutions", "Contact": "hello@celayasolutions.com",
              "Date": "2026-10-03", "SHA256": sha(body), "Chain": "n/a",
              "Tx": "[not anchored]", "License": "All Rights Reserved / Celaya Solutions"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(canonical_bytes(
        {"document_header": header, "body": body}) + b"\n", mtime=0))
    print(json.dumps({"shape_count": len(classes), "a_class_count": len(counts),
                      "labeled_a_graphs": labeled, "witness_count": body["witness_count"],
                      "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
