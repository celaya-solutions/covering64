# Document:    Fifteen Clebsch Neighborhoods Force the Sixteenth
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      799d873d447acf23a660e912a05416c0be8faf75203ee1653b7bf1741f4d55e8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exhaustive finite classification and exact identities; no optimizer imports."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SIXTEEN_CERTIFICATE = HERE.parent / "clebsch-neighborhood-cycle-certificate/certificate.json"
SIXTEEN_AUDIT = HERE.parent / "clebsch-neighborhood-cycle-certificate-independent/audit.json"
SIXTEEN_CERTIFICATE_SHA = "6802e49098940c70253dbf17e0a44bc05acb800185d85356dc5031faa6c545fc"
SIXTEEN_AUDIT_SHA = "de03e575af4237a99f5ad10083ac7f0651021c8349d3250162cef2972f752e84"
VERTICES = tuple(range(1, 17))
BITS = tuple(value for value in range(32) if value.bit_count() % 2 == 0)
EDGES = {
    pair
    for pair in combinations(VERTICES, 2)
    if (BITS[pair[0] - 1] ^ BITS[pair[1] - 1]).bit_count() == 4
}
BLOCKS = tuple(combinations(VERTICES, 5))
TRIPLES = tuple(combinations(VERTICES, 3))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def dump(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def edge_count(vertices):
    return sum(pair in EDGES for pair in combinations(vertices, 2))


def classify(block):
    edges = [pair for pair in combinations(block, 2) if pair in EDGES]
    degrees = Counter(point for edge in edges for point in edge)
    degree_sequence = sorted(degrees[point] for point in block)
    independent = sum(edge_count(triple) == 0 for triple in combinations(block, 3))
    key = (len(edges), tuple(degree_sequence), independent)
    classes = {
        (5, (2, 2, 2, 2, 2), 0): "C5",
        (5, (1, 2, 2, 2, 3), 1): "C4-leaf",
        (4, (1, 1, 2, 2, 2), 1): "P5",
        (4, (1, 1, 1, 1, 4), 4): "K1,4",
        (0, (0, 0, 0, 0, 0), 10): "missing-neighborhood",
    }
    require(key in classes, "complete five-class candidate classification")
    return {
        "class": classes[key],
        "edge_count": len(edges),
        "degree_sequence": degree_sequence,
        "independent_triples": independent,
        "contains_point_one": 1 in block,
        "point_one_graph_degree": degrees[1] if 1 in block else 0,
    }


def main():
    require(digest(SIXTEEN_CERTIFICATE) == SIXTEEN_CERTIFICATE_SHA, "sixteen proof pin")
    require(digest(SIXTEEN_AUDIT) == SIXTEEN_AUDIT_SHA, "sixteen independent audit pin")
    audit = json.loads(SIXTEEN_AUDIT.read_text())
    require(
        audit["passed"] and audit["certificate_sha256"] == SIXTEEN_CERTIFICATE_SHA,
        "checked sixteen proof",
    )
    neighborhoods = {
        point: tuple(other for other in VERTICES if tuple(sorted((point, other))) in EDGES)
        for point in VERTICES
    }
    require(
        len(EDGES) == 40 and all(len(block) == 5 for block in neighborhoods.values()),
        "Clebsch regularity",
    )
    require(
        all(edge_count(block) == 0 for block in neighborhoods.values()), "independent neighborhoods"
    )
    require(
        Counter(edge_count(triple) for triple in TRIPLES) == {0: 160, 1: 240, 2: 160},
        "triple classes",
    )
    fixed = [neighborhoods[point] for point in VERTICES if point != 1]
    fixed_counts = Counter(triple for block in fixed for triple in combinations(block, 3))
    require(
        len(fixed_counts) == 150 and set(fixed_counts.values()) == {1},
        "150 fixed independent triples",
    )
    missing_triples = {
        triple for triple in TRIPLES if edge_count(triple) == 0 and triple not in fixed_counts
    }
    require(
        missing_triples == set(combinations(neighborhoods[1], 3)),
        "exact ten missing independent triples",
    )
    records = []
    for index, block in enumerate(BLOCKS):
        if any(triple in fixed_counts for triple in combinations(block, 3)):
            continue
        record = {"id": index, "block": block, **classify(block)}
        name = record["class"]
        if name == "C5":
            require(
                record["point_one_graph_degree"] == (2 if 1 in block else 0), "cycle point degree"
            )
        elif name in ("C4-leaf", "K1,4"):
            require(
                1 in block and record["point_one_graph_degree"] == (3 if name == "C4-leaf" else 4),
                "exceptional rooted degree",
            )
        else:
            require(1 not in block, "P5 and missing neighborhood omit point one")
        records.append(record)
    counts = Counter(record["class"] for record in records)
    require(
        counts == {"C5": 192, "C4-leaf": 30, "P5": 30, "K1,4": 5, "missing-neighborhood": 1},
        "258 candidate census",
    )
    dump("candidates.json", records)
    fixed_pair = Counter(pair for block in fixed for pair in combinations(block, 2))
    pair_demand = {
        pair: (6 if pair in EDGES else 5) - fixed_pair[pair] for pair in combinations(VERTICES, 2)
    }
    support_pair = Counter(pair for record in records for pair in combinations(record["block"], 2))
    support_triple = Counter(
        triple for record in records for triple in combinations(record["block"], 3)
    )
    exact_triple = {
        triple: 1 - fixed_counts[triple] for triple in TRIPLES if edge_count(triple) < 2
    }
    require(
        all(support_pair[pair] >= demand for pair, demand in pair_demand.items()), "pair supports"
    )
    require(
        all(support_triple[t] >= demand for t, demand in exact_triple.items()),
        "exact triple supports",
    )
    require(
        all(support_triple[t] >= 1 for t in TRIPLES if edge_count(t) == 2),
        "P3 lower-bound supports",
    )
    require(sum(1 in block for block in fixed) == 5, "five fixed point-one occurrences")
    require(
        sum((6 if pair in EDGES else 5) for pair in combinations(VERTICES, 2) if 1 in pair) == 80,
        "point-one pair sum",
    )
    require(sum(pair_demand[pair] for pair in EDGES) == 240, "remaining graph edge incidences")
    require(
        sum(pair_demand[pair] for pair in EDGES if 1 in pair) == 30,
        "remaining graph edges at point one",
    )

    # Variables a,b,c,d,e are counts of C5,C4-leaf,P5,K1,4,missing-N.
    # x counts just those selected C5 candidates containing point one.
    identities = {
        "columns": ["a", "b", "c", "d", "e", "x"],
        "rows": {
            "cardinality": {"coefficients": [1, 1, 1, 1, 1, 0], "rhs": 49},
            "graph_edges": {"coefficients": [5, 5, 4, 4, 0, 0], "rhs": 240},
            "independent_triples": {"coefficients": [0, 1, 1, 4, 10, 0], "rhs": 10},
            "point_one_occurrences": {"coefficients": [0, 1, 0, 1, 0, 1], "rhs": 15},
            "graph_edges_at_point_one": {"coefficients": [0, 3, 0, 4, 0, 2], "rhs": 30},
        },
    }
    rows = identities["rows"]
    degree_difference = [
        rows["graph_edges_at_point_one"]["coefficients"][i]
        - 2 * rows["point_one_occurrences"]["coefficients"][i]
        for i in range(6)
    ]
    require(degree_difference == [0, 1, 0, 2, 0, 0], "b plus twice d identity")
    first = [
        5 * rows["cardinality"]["coefficients"][i] - rows["graph_edges"]["coefficients"][i]
        for i in range(6)
    ]
    require(first == [0, 0, 1, 1, 5, 0] and 5 * 49 - 240 == 5, "c+d+5e=5")
    second = [rows["independent_triples"]["coefficients"][i] - first[i] for i in range(6)]
    require(second == [0, 1, 0, 3, 5, 0] and 10 - 5 == 5, "b+3d+5e=5")
    solutions = []
    for e in range(2):
        for d in range(6):
            for b in range(31):
                c = 5 - d - 5 * e
                a = 49 - b - c - d - e
                x = 15 - b - d
                values = [a, b, c, d, e, x]
                if min(values) < 0 or c > 30 or a > 192 or x > a:
                    continue
                if all(
                    sum(v * coefficient for v, coefficient in zip(values, row["coefficients"]))
                    == row["rhs"]
                    for row in rows.values()
                ):
                    solutions.append(values)
    require(
        solutions == [[48, 0, 0, 0, 1, 15]],
        "only aggregate solution forces the missing neighborhood",
    )
    identities["aggregate_solutions"] = solutions
    identities["nonnegativity_deduction"] = "b+2d=0 implies b=d=0; then b+3d+5e=5 implies e=1."
    dump("identities.json", identities)

    translations = []
    labels = {value: index + 1 for index, value in enumerate(BITS)}
    for point in VERTICES:
        mapping = {other: labels[BITS[other - 1] ^ BITS[point - 1]] for other in VERTICES}
        require(
            mapping[point] == 1 and set(mapping.values()) == set(VERTICES), "translation bijection"
        )
        require(
            {tuple(sorted(mapping[x] for x in edge)) for edge in EDGES} == EDGES,
            "edge-preserving translation",
        )
        require(
            all(
                tuple(sorted(mapping[x] for x in neighborhoods[q])) == neighborhoods[mapping[q]]
                for q in VERTICES
            ),
            "neighborhood-preserving translation",
        )
        translations.append(
            {"missing_neighborhood_point": point, "to_point_one": [mapping[x] for x in VERTICES]}
        )
    dump("translations.json", translations)
    summary = {
        "passed": True,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": digest(__file__),
        "python_version": sys.version,
        "all_pentads_examined": len(BLOCKS),
        "fixed_neighborhoods": fixed,
        "missing_neighborhood": neighborhoods[1],
        "fixed_independent_triples": 150,
        "remaining_independent_triples": 10,
        "candidate_count": len(records),
        "candidate_classes": dict(counts),
        "candidate_class_point_degrees": {
            name: dict(
                Counter(
                    str(record["point_one_graph_degree"])
                    for record in records
                    if record["class"] == name
                )
            )
            for name in counts
        },
        "minimum_pair_support_slack": min(
            support_pair[pair] - demand for pair, demand in pair_demand.items()
        ),
        "minimum_positive_exact_triple_support_slack": min(
            support_triple[t] - demand for t, demand in exact_triple.items() if demand
        ),
        "all_single_row_support_checks_passed": True,
        "aggregate_solution_columns": identities["columns"],
        "aggregate_solution": solutions[0],
        "forcing_conclusion": (
            "Any such exact64 cover containing these fifteen neighborhoods "
            "must contain the sixteenth."
        ),
        "conditional_exclusion": (
            "The separately checked sixteen-neighborhood contradiction therefore excludes "
            "every cover in this stated pair and triple profile with at least fifteen "
            "Clebsch neighborhood blocks."
        ),
        "transitivity_cases_checked": 16,
        "conditional_scope": (
            "Clebsch pair profile: edge pairs6, nonedge pairs5; "
            "non-P3 triple counts1 and P3 triple counts between1and2; exact64 distinct blocks; "
            "at least15 Clebsch neighborhoods selected."
        ),
        "unrestricted_claim": False,
        "solver_calls": 0,
        "sixteen_neighborhood_exclusion_dependency": {
            "certificate": str(SIXTEEN_CERTIFICATE.relative_to(ROOT)),
            "certificate_sha256": SIXTEEN_CERTIFICATE_SHA,
            "independent_audit": str(SIXTEEN_AUDIT.relative_to(ROOT)),
            "independent_audit_sha256": SIXTEEN_AUDIT_SHA,
            "independent_audit_passed": True,
        },
    }
    dump("summary.json", summary)
    print(
        json.dumps(
            {
                key: summary[key]
                for key in (
                    "passed",
                    "candidate_count",
                    "candidate_classes",
                    "aggregate_solution",
                    "solver_calls",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
