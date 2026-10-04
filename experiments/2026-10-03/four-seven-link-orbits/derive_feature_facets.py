# Document:    Exact Four-Dimensional Feature Hull Facets and Transport
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      11c471b85983d5dbef6ccbf604d97cc077ff4283676367780ad6f841ddf7bfc9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KEYS = ("hub_hub", "ah_own", "ah_neighbor", "aa_neighbor")
ANCHORS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
PREVIOUS = {
    "cycle": {((0, 0, 1, 0), 3), ((1, 0, 0, -1), 0)},
    "matching": {((-1, -1, 0, 0), -1), ((0, 0, 1, 0), 2), ((0, 0, 0, 1), 2)},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def det3(matrix):
    a, b, c = matrix
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def det4(matrix):
    return sum(
        (-1) ** j
        * matrix[0][j]
        * det3([[row[k] for k in range(4) if k != j] for row in matrix[1:]])
        for j in range(4)
    )


def normal_from_points(quadruple):
    differences = [[p[j] - quadruple[0][j] for j in range(4)] for p in quadruple[1:]]
    normal = [
        (-1) ** j * det3([[row[k] for k in range(4) if k != j] for row in differences])
        for j in range(4)
    ]
    common = math.gcd(*normal)
    if not common:
        return None
    normal = tuple(v // common for v in normal)
    sign = 1 if next(v for v in normal if v) > 0 else -1
    return tuple(v * sign for v in normal)


def exact_facets(points):
    # Five affinely independent points prove that this is genuinely a 4D hull.
    full_dimension = next(
        (
            q
            for q in itertools.combinations(points, 5)
            if det4([[p[j] - q[0][j] for j in range(4)] for p in q[1:]])
        ),
        None,
    )
    require(full_dimension is not None, "feature hull is not four dimensional")
    planes = set()
    facets = {}
    for quadruple in itertools.combinations(points, 4):
        normal = normal_from_points(quadruple)
        if normal is None:
            continue
        bound = dot(normal, quadruple[0])
        plane = (normal, bound)
        if plane in planes:
            continue
        planes.add(plane)
        differences = [dot(normal, p) - bound for p in points]
        if max(differences) <= 0:
            facets[plane] = quadruple
        elif min(differences) >= 0:
            facets[(tuple(-v for v in normal), -bound)] = quadruple
    require(facets, "no facets")
    return facets, full_dimension, len(planes)


def group(point):
    return (point - 1) // 4


def adjacent(case, a, b):
    edges = ((0, 1), (1, 2), (2, 3), (0, 3)) if case == "cycle" else ((0, 1), (2, 3))
    return frozenset((a, b)) in {frozenset(e) for e in edges}


def edge_features(case, edge):
    a, b = edge
    hubs = int(a % 4 == 0) + int(b % 4 == 0)
    own = group(a) == group(b)
    near = adjacent(case, group(a), group(b))
    return (
        int(hubs == 2),
        int(hubs == 1 and own),
        int(hubs == 1 and near),
        int(hubs == 0 and near),
    )


def link_features(case, edges):
    return tuple(sum(edge_features(case, edge)[i] for edge in edges) for i in range(4))


def available_edges(target):
    return [
        e
        for e in itertools.combinations([p for p in range(1, 17) if p not in ANCHORS[target]], 2)
        if not (group(e[0]) == group(e[1]) and e[0] % 4 and e[1] % 4)
    ]


def main():
    feature_path = HERE / "lp-feature-analysis.json"
    features = json.loads(feature_path.read_text())
    audit_path = HERE.parent / "four-seven-link-lp-independent/full-v1.1.0-final-audit.json"
    audit = json.loads(audit_path.read_text())
    screen_path = REPO / "experiments/scratch/four-seven-link-lp-full/results.json.gz"
    require(
        audit["complete_selected_coverage"] is True
        and audit["records"] == 258
        and audit["results_sha256"] == sha(screen_path) == features["screen_sha256"],
        "audit scope",
    )
    checked = {r["id"]: r for r in audit["checks"]}
    require(len(checked) == 258, "complete checked records")
    blocks = list(itertools.combinations(range(1, 17), 5))
    block_ids = {b: i for i, b in enumerate(blocks)}
    orbit_path = HERE / "relabelings.json.gz"
    require(sha(orbit_path) == features["orbit_archive_sha256"], "orbit archive changed")
    orbit_maps = {c["case"]: c for c in json.loads(gzip.decompress(orbit_path.read_bytes()))}
    output = []
    for case in ("cycle", "matching"):
        records = [r for r in features["rows"] if r["case"] == case]
        vectors = {r["id"]: tuple(r["features"][k] for k in KEYS) for r in records}
        for record in records:
            require(
                vectors[record["id"]] == link_features(case, record["edges"]),
                "feature reconstruction",
            )
            require(
                record["excluded"] == checked[record["id"]]["proves_infeasible"], "status mismatch"
            )
        points = sorted({vectors[r["id"]] for r in records if not r["excluded"]})
        facets, dimensional_witness, distinct_planes = exact_facets(points)
        all_group_perms = [
            p
            for p in itertools.permutations(range(4))
            if all(
                adjacent(case, i, j) == adjacent(case, p[i], p[j])
                for i, j in itertools.combinations(range(4), 2)
            )
        ]
        require(
            len(all_group_perms) == 8 and {p[0] for p in all_group_perms} == set(range(4)),
            "group transitivity",
        )
        for orbit in orbit_maps[case]["orbits"]:
            require(
                all(
                    link_features(case, item["edges"]) == vectors[orbit["id"]]
                    for item in orbit["maps"]
                ),
                "feature orbit invariance",
            )
        case_output = []
        rejected_union = set()
        for normal, bound in sorted(facets):
            bad = [r for r in records if dot(normal, vectors[r["id"]]) > bound]
            for record in bad:
                certificate = checked[record["id"]]
                require(
                    certificate["proves_infeasible"] is True and Fraction(*certificate["gap"]) > 0,
                    "facet violation lacks a checked certificate",
                )
            item = dict(
                normal=normal,
                upper_bound=bound,
                equality_witness=facets[(normal, bound)],
                equality_points=[p for p in points if dot(normal, p) == bound],
                violations=[
                    dict(
                        id=r["id"],
                        feature_vector=vectors[r["id"]],
                        value=dot(normal, vectors[r["id"]]),
                        certificate_gap=checked[r["id"]]["gap"],
                    )
                    for r in bad
                ],
                excludes_certified_orbits=len(bad),
                already_in_five_rules=(normal, bound) in PREVIOUS[case],
            )
            if bad:
                rejected_union.update(r["id"] for r in bad)
                target_rows = []
                for target in range(4):
                    group_perm = min(p for p in all_group_perms if p[0] == target)
                    perm = tuple(
                        4 * group_perm[i] + offset + 1 for i in range(4) for offset in range(4)
                    )
                    inverse = tuple(perm.index(p) + 1 for p in range(1, 17))
                    base = {e: dot(normal, edge_features(case, e)) for e in available_edges(0)}
                    expected = {
                        e: dot(normal, edge_features(case, e)) for e in available_edges(target)
                    }
                    transformed = {
                        tuple(sorted(perm[p - 1] for p in e)): coefficient
                        for e, coefficient in base.items()
                    }
                    require(transformed == expected, "signed coefficient transport mismatch")
                    require(
                        {
                            tuple(sorted(inverse[p - 1] for p in e)): coefficient
                            for e, coefficient in expected.items()
                        }
                        == base,
                        "inverse coefficient mismatch",
                    )
                    coefficients = []
                    for edge, coefficient in expected.items():
                        if coefficient:
                            block = tuple(sorted((*ANCHORS[target], *edge)))
                            coefficients.append(
                                dict(
                                    edge=edge,
                                    block=block,
                                    variable_index=block_ids[block],
                                    coefficient=coefficient,
                                )
                            )
                    target_rows.append(
                        dict(
                            group_index=target,
                            anchor_triple=ANCHORS[target],
                            group_permutation=group_perm,
                            point_permutation=perm,
                            inverse_point_permutation=inverse,
                            coefficients=sorted(coefficients, key=lambda c: c["variable_index"]),
                        )
                    )
                item["target_groups"] = target_rows
            case_output.append(item)
        selected = [f for f in case_output if f["excludes_certified_orbits"]]
        output.append(
            dict(
                case=case,
                survivor_feature_points=points,
                full_dimension_witness=dimensional_witness,
                quadruples_enumerated=math.comb(len(points), 4),
                distinct_hyperplanes=distinct_planes,
                all_facets=case_output,
                selected_facets=len(selected),
                new_facets=sum(not f["already_in_five_rules"] for f in selected),
                excluded_union_ids=sorted(rejected_union),
            )
        )
    result = dict(
        valid=True,
        feature_coordinates=["H", "S", "A", "C"],
        feature_fields=KEYS,
        method="Exact integer determinants over every four-point subset; no floating hull solver.",
        cases=output,
        source_sha256=sha(Path(__file__)),
        features_sha256=sha(feature_path),
        orbit_archive_sha256=sha(orbit_path),
        audit_sha256=sha(audit_path),
        screen_sha256=sha(screen_path),
        scope="Valid for integer covers in the regular four-sevenfold branch. A facet is retained "
        "only after every violating first-link orbit has a checked positive certificate. "
        "Transport is label equivalence. No cuts applied and no new covering search run.",
    )
    (HERE / "safe-feature-facets.json").write_text(json.dumps(result, indent=2) + "\n")
    for case in output:
        print(
            json.dumps(
                {
                    k: v
                    for k, v in case.items()
                    if k in ("case", "selected_facets", "new_facets", "excluded_union_ids")
                }
            )
        )


if __name__ == "__main__":
    main()
