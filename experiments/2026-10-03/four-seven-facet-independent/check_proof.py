# Document:    Independent Exact Four Feature Hull Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild raw features, enumerate exact supporting hyperplanes, and check signed transport."""

import copy
import gzip
import hashlib
import json
import math
from fractions import Fraction
from itertools import combinations, permutations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORBIT = HERE.parent / "four-seven-link-orbits"
PROOF_SHA = "7f79089fd414539551863b367b161ee1b8a5dffbaf1e5bd9013ee6ac33cc3e51"
ANCHORS = ({1, 2, 3}, {5, 6, 7}, {9, 10, 11}, {13, 14, 15})
HUBS = {4, 8, 12, 16}
GROUP = {p: g for g in range(4) for p in range(4 * g + 1, 4 * g + 5)}
GRAPH = {"cycle": {frozenset(e) for e in ((0, 1), (1, 2), (2, 3), (3, 0))},
         "matching": {frozenset((0, 1)), frozenset((2, 3))}}
OLD = {"cycle": {(0, 0, 1, 0, 3), (1, 0, 0, -1, 0)},
       "matching": {(-1, -1, 0, 0, -1), (0, 0, 1, 0, 2), (0, 0, 0, 1, 2)}}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def edge_vector(edge, case):
    a, b = edge
    hubs = len(set(edge) & HUBS)
    own = GROUP[a] == GROUP[b]
    adjacent = frozenset((GROUP[a], GROUP[b])) in GRAPH[case]
    return (int(hubs == 2), int(hubs == 1 and own),
            int(hubs == 1 and adjacent), int(hubs == 0 and adjacent))


def vector(edges, case):
    values = [edge_vector(edge, case) for edge in edges]
    result = tuple(sum(v[i] for v in values) for i in range(4))
    if case == "cycle":
        opposite_aa = sum(not (set(edge) & HUBS) and GROUP[edge[0]] != GROUP[edge[1]]
                          and frozenset(GROUP[p] for p in edge) not in GRAPH[case]
                          for edge in edges)
        require(opposite_aa == result[0] + 2 - result[3], "old cycle cut identity failed")
    return result


def rank(rows):
    matrix = [[Fraction(v) for v in row] for row in rows]
    pivot = 0
    for column in range(4):
        choice = next((i for i in range(pivot, len(matrix)) if matrix[i][column]), None)
        if choice is None:
            continue
        matrix[pivot], matrix[choice] = matrix[choice], matrix[pivot]
        scale = matrix[pivot][column]
        matrix[pivot] = [v / scale for v in matrix[pivot]]
        for i in range(len(matrix)):
            if i != pivot:
                scale = matrix[i][column]
                matrix[i] = [a - scale * b for a, b in zip(matrix[i], matrix[pivot])]
        pivot += 1
    return pivot


def affine_rank(points):
    return rank([[p[i] - points[0][i] for i in range(4)] for p in points[1:]])


PERM3 = [(p, (-1) ** sum(p[i] > p[j] for i in range(3) for j in range(i + 1, 3)))
         for p in permutations(range(3))]


def determinant3(matrix):
    return sum(sign * math.prod(matrix[i][p[i]] for i in range(3)) for p, sign in PERM3)


def enumerate_facets(points):
    planes = {}
    for quadruple in combinations(points, 4):
        differences = [[p[i] - quadruple[0][i] for i in range(4)] for p in quadruple[1:]]
        normal = [(-1) ** column * determinant3(
            [[row[i] for i in range(4) if i != column] for row in differences])
            for column in range(4)]
        if not any(normal):
            continue
        divisor = math.gcd(*normal)
        sign = 1 if next(n for n in normal if n) > 0 else -1
        normal = tuple(sign * n // divisor for n in normal)
        bound = dot(normal, quadruple[0])
        planes.setdefault((*normal, bound), quadruple)
    facets = {}
    for plane, witness in planes.items():
        normal, bound = plane[:4], plane[4]
        values = [dot(normal, point) for point in points]
        if max(values) == bound:
            facets[plane] = witness
        elif min(values) == bound:
            facets[tuple(-v for v in plane)] = witness
    return facets, len(planes)


def check_transport(facet, case):
    normal = facet["normal"]
    blocks = list(combinations(range(1, 17), 5))
    targets = facet["target_groups"]
    require(len(targets) == 4 and {t["group_index"] for t in targets} == set(range(4)),
            "incomplete target groups")
    rows = {}
    for target in targets:
        group = target["group_index"]
        require(set(target["anchor_triple"]) == ANCHORS[group], "wrong target anchors")
        coefficients = {}
        for index, block in enumerate(blocks):
            block_set = set(block)
            if not ANCHORS[group] <= block_set:
                continue
            if any(len(block_set & anchor) == 2 for anchor in ANCHORS):
                continue
            edge = tuple(sorted(block_set - ANCHORS[group]))
            coefficient = dot(normal, edge_vector(edge, case))
            if coefficient:
                coefficients[index] = {"edge": list(edge), "block": list(block),
                                       "variable_index": index, "coefficient": coefficient}
        records = target["coefficients"]
        require(len(records) == len(coefficients)
                and {r["variable_index"]: r for r in records} == coefficients,
                "signed global coefficients differ from raw blocks")
        rows[group] = {tuple(r["block"]): r["coefficient"] for r in records}
        permutation = target["group_permutation"]
        point_map = target["point_permutation"]
        inverse = target["inverse_point_permutation"]
        require(sorted(permutation) == list(range(4)) and permutation[0] == group,
                "wrong group permutation")
        require(all((frozenset(pair) in GRAPH[case]) ==
                    (frozenset(permutation[i] for i in pair) in GRAPH[case])
                    for pair in combinations(range(4), 2)), "hub graph not preserved")
        require(point_map == [4 * permutation[GROUP[p]] + (p - 1) % 4 + 1
                              for p in range(1, 17)], "wrong point map")
        require(sorted(inverse) == list(range(1, 17))
                and all(point_map[inverse[p - 1] - 1] == p for p in range(1, 17)),
                "wrong inverse map")
    for target in targets:
        point_map = target["point_permutation"]
        image = {tuple(sorted(point_map[p - 1] for p in block)): coefficient
                 for block, coefficient in rows[0].items()}
        require(image == rows[target["group_index"]], "transported signed row differs")


def check_case(case_data, vectors, checked, points, exact):
    case = case_data["case"]
    require(case_data["survivor_feature_points"] == [list(p) for p in points], "wrong survivors")
    witness = [tuple(p) for p in case_data["full_dimension_witness"]]
    require(len(witness) == 5 and set(witness).issubset(points)
            and affine_rank(witness) == 4, "not a full-dimensional witness")
    require(case_data["quadruples_enumerated"] == math.comb(len(points), 4), "wrong tuple count")
    facets, plane_count = exact
    require(case_data["distinct_hyperplanes"] == plane_count, "wrong hyperplane count")
    records = case_data["all_facets"]
    require(len(records) == len(facets)
            and {(*f["normal"], f["upper_bound"]) for f in records} == set(facets),
            "incomplete or changed exact hull facets")
    selected, new, excluded = 0, 0, set()
    for facet in records:
        normal, bound = facet["normal"], facet["upper_bound"]
        require(all(type(v) is int for v in [*normal, bound]), "noninteger facet")
        key = (*normal, bound)
        equals = [p for p in points if dot(normal, p) == bound]
        require(facet["equality_points"] == [list(p) for p in equals], "wrong equality points")
        witness = [tuple(p) for p in facet["equality_witness"]]
        require(len(witness) == 4 and set(witness).issubset(equals)
                and affine_rank(witness) == 3, "not a facet equality witness")
        bad = {rid: v for rid, v in vectors.items() if dot(normal, v) > bound}
        claimed = facet["violations"]
        require(len(claimed) == len(bad) and {r["id"] for r in claimed} == set(bad),
                "incorrect violation set")
        for row in claimed:
            rid = row["id"]
            require(row["feature_vector"] == list(bad[rid])
                    and row["value"] == dot(normal, bad[rid]), "incorrect violating value")
            certificate = checked[rid]
            require(certificate["proves_infeasible"] is True
                    and Fraction(*certificate["gap"]) > 0
                    and row["certificate_gap"] == certificate["gap"],
                    "violation lacks replayed positive certificate")
        require(facet["excludes_certified_orbits"] == len(bad), "wrong exclusion count")
        require(facet["already_in_five_rules"] is (key in OLD[case]), "old rule classification")
        if bad:
            selected += 1
            new += key not in OLD[case]
            excluded.update(bad)
            check_transport(facet, case)
    require(case_data["selected_facets"] == selected and case_data["new_facets"] == new,
            "wrong selected facet count")
    require(case_data["excluded_union_ids"] == sorted(excluded), "wrong excluded union")
    return {"case": case, "survivor_vectors": len(points), "all_hull_facets": len(facets),
            "hyperplanes": plane_count, "selected_facets": selected, "new_facets": new,
            "distinct_violating_ids": len(excluded), "transported_selected_rows": 4 * selected}


def main():
    path = ORBIT / "safe-feature-facets.json"
    require(sha(path) == PROOF_SHA, "proof hash mismatch")
    proof = json.loads(path.read_text())
    require(proof["valid"] is True and proof["feature_coordinates"] == ["H", "S", "A", "C"],
            "wrong feature coordinates")
    files = {"features_sha256": ORBIT / "lp-feature-analysis.json",
             "orbit_archive_sha256": ORBIT / "relabelings.json.gz",
             "audit_sha256": (HERE.parent /
                              "four-seven-link-lp-independent/full-v1.1.0-final-audit.json"),
             "screen_sha256": ROOT / "experiments/scratch/four-seven-link-lp-full/results.json.gz",
             "source_sha256": ORBIT / "derive_feature_facets.py"}
    require(all(sha(file) == proof[key] for key, file in files.items()),
            "proof source hash mismatch")
    orbit_audit = json.loads((ORBIT / "independent-result.json").read_text())
    require(orbit_audit["complete"] is True
            and orbit_audit["metadata_sha256"] == sha(ORBIT / "result.json")
            and orbit_audit["archive_sha256"] == sha(files["orbit_archive_sha256"]),
            "classification provenance mismatch")
    replay_path = HERE / "replayed-input-certificates.json"
    replay = json.loads(replay_path.read_text())
    require(replay["records"] == 258 and replay["excluded"] == 100
            and replay["complete_selected_coverage"] is True
            and replay["results_sha256"] == proof["screen_sha256"], "certificate replay incomplete")
    checked = {r["id"]: r for r in replay["checks"]}
    reps = json.loads((ORBIT / "result.json").read_text())
    orbit_maps = json.loads(gzip.decompress(files["orbit_archive_sha256"].read_bytes()))
    feature_rows = json.loads(files["features_sha256"].read_text())["rows"]
    all_vectors = {c["case"]: {r["id"]: vector(r["edges"], c["case"])
                              for r in c["representatives"]} for c in reps["cases"]}
    require(len(checked) == 258 and sum(map(len, all_vectors.values())) == 258, "wrong ID coverage")
    for row in feature_rows:
        raw = all_vectors[row["case"]][row["id"]]
        require(raw == tuple(row["features"][key] for key in proof["feature_fields"])
                and row["excluded"] == checked[row["id"]]["proves_infeasible"],
                "feature table differs from raw links or checked status")
    map_count = 0
    for group in orbit_maps:
        for orbit in group["orbits"]:
            for record in orbit["maps"]:
                require(vector(record["edges"], group["case"]) ==
                        all_vectors[group["case"]][orbit["id"]], "feature map not invariant")
                map_count += 1
    require(map_count == 59940, "incomplete labeled maps")
    summaries, controls = [], {}
    for case_data in proof["cases"]:
        case = case_data["case"]
        vectors = all_vectors[case]
        points = sorted({v for rid, v in vectors.items() if not checked[rid]["proves_infeasible"]})
        exact = enumerate_facets(points)
        summary = check_case(case_data, vectors, checked, points, exact)
        summaries.append(summary)
        print(json.dumps(summary), flush=True)
        for control in ("bound", "normal", "witness", "coefficient", "transport", "gap"):
            bad = copy.deepcopy(case_data)
            facet = next(f for f in bad["all_facets"] if f["excludes_certified_orbits"])
            if control == "bound":
                facet["upper_bound"] += 1
            elif control == "normal":
                facet["normal"][0] += 1
            elif control == "witness":
                facet["equality_witness"] = [facet["equality_witness"][0]] * 4
            elif control == "coefficient":
                facet["target_groups"][0]["coefficients"][0]["coefficient"] += 1
            elif control == "transport":
                facet["target_groups"][1]["point_permutation"][0] = 1
            else:
                facet["violations"][0]["certificate_gap"][0] += 1
            try:
                check_case(bad, vectors, checked, points, exact)
            except ValueError:
                controls[f"{case}:{control}"] = "rejected"
            else:
                raise ValueError(f"damaged proof accepted: {case}/{control}")
    result = {"passed": True, "proof_sha256": PROOF_SHA, "cases": summaries,
              "labeled_feature_maps_checked": map_count, "damaged_controls": controls,
              "replayed_certificate_audit_sha256": sha(replay_path),
              "checker_sha256": sha(Path(__file__)),
              "scope": "Necessary inequalities for integer regular four-sevenfold covers only. "
              "All four-group transports are label equivalences, not cover-invariance assumptions."}
    (HERE / "proof-audit.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
