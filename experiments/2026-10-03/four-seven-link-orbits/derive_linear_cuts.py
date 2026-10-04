# Document:    Finite Certificate Derivation of Four-Sevenfold Link Cuts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      8ea02f81575ce8191b58734b9dbb353374945edb8288074ed1202cbbe49d5b51
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ANCHORS = [(1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15)]
HUBS = (4, 8, 12, 16)
RULES = (
    ("cycle", "adjacent_anchor_hub", "<=", 3, 14, 18),
    ("cycle", "nonadjacent_anchor_anchor", "<=", 2, 4, 9),
    ("matching", "hub_hub_or_own_anchor_hub", ">=", 1, 15, 15),
    ("matching", "adjacent_anchor_hub", "<=", 2, 9, 9),
    ("matching", "adjacent_anchor_anchor", "<=", 2, 4, 9),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group(point):
    return (point - 1) // 4


def is_hub(point):
    return point % 4 == 0


def excess(case, first, second):
    edge = frozenset((first, second))
    if case == "cycle":
        return int(edge in {frozenset(e) for e in ((0, 1), (1, 2), (2, 3), (0, 3))})
    return 2 * int(edge in {frozenset((0, 1)), frozenset((2, 3))})


def qualifies(case, kind, edge):
    a, b = edge
    hubs = int(is_hub(a)) + int(is_hub(b))
    own_group = group(a) == group(b)
    adjacent = excess(case, group(a), group(b)) > 0
    if kind == "adjacent_anchor_hub":
        return hubs == 1 and adjacent
    if kind == "nonadjacent_anchor_anchor":
        return hubs == 0 and not own_group and not adjacent
    if kind == "hub_hub_or_own_anchor_hub":
        return hubs == 2 or (hubs == 1 and own_group)
    if kind == "adjacent_anchor_anchor":
        return hubs == 0 and adjacent
    raise ValueError("unknown predicate")


def allowed_edges(anchor_group):
    points = [p for p in range(1, 17) if p not in ANCHORS[anchor_group]]
    return [
        e
        for e in itertools.combinations(points, 2)
        if not (group(e[0]) == group(e[1]) and not is_hub(e[0]) and not is_hub(e[1]))
    ]


def image(edge, perm):
    return tuple(sorted(perm[p - 1] for p in edge))


def automorphisms(case):
    perms = [
        p
        for p in itertools.permutations(range(4))
        if all(
            excess(case, i, j) == excess(case, p[i], p[j])
            for i, j in itertools.combinations(range(4), 2)
        )
    ]
    require(len(perms) == 8, "hub graph automorphism order")
    require({p[0] for p in perms} == set(range(4)), "hub graph not transitive")
    return perms


def main():
    reps_path = HERE / "result.json"
    orbits_path = HERE / "relabelings.json.gz"
    orbit_audit_path = HERE / "independent-result.json"
    lp_path = REPO / "experiments/scratch/four-seven-link-lp-full/results.json.gz"
    lp_audit_path = HERE.parent / "four-seven-link-lp-independent/full-v1.1.0-final-audit.json"
    reps = json.loads(reps_path.read_text())
    orbit_audit = json.loads(orbit_audit_path.read_text())
    lp_audit = json.loads(lp_audit_path.read_text())
    require(
        orbit_audit["complete"] is True
        and orbit_audit["metadata_sha256"] == sha(reps_path)
        and orbit_audit["archive_sha256"] == sha(orbits_path),
        "orbit audit mismatch",
    )
    require(
        lp_audit["complete_selected_coverage"] is True
        and lp_audit["records"] == 258
        and lp_audit["expected_records"] == 258
        and lp_audit["results_sha256"] == sha(lp_path),
        "LP audit incomplete or stale",
    )
    checks = {r["id"]: r for r in lp_audit["checks"]}
    require(len(checks) == 258, "duplicate audit record")
    cases = {c["case"]: c for c in reps["cases"]}
    mappings = {c["case"]: c for c in json.loads(gzip.decompress(orbits_path.read_bytes()))}
    blocks = list(itertools.combinations(range(1, 17), 5))
    indices = {b: i for i, b in enumerate(blocks)}
    rules = []
    for case, kind, sense, bound, expected_bad, expected_terms in RULES:

        def value(edges):
            return sum(qualifies(case, kind, edge) for edge in edges)

        values = {r["id"]: value(r["edges"]) for r in cases[case]["representatives"]}
        bad = [
            r
            for r in cases[case]["representatives"]
            if (values[r["id"]] > bound if sense == "<=" else values[r["id"]] < bound)
        ]
        require(len(bad) == expected_bad, "violating orbit count")
        for representative in bad:
            checked = checks[representative["id"]]
            require(
                checked["case"] == case
                and checked["proves_infeasible"] is True
                and Fraction(*checked["gap"]) > 0,
                "violation lacks checked certificate",
            )
        invariant_maps = 0
        for orbit in mappings[case]["orbits"]:
            for record in orbit["maps"]:
                require(value(record["edges"]) == values[orbit["id"]], "predicate not invariant")
                invariant_maps += 1
        transports = []
        full_group = automorphisms(case)
        base_edges = set(allowed_edges(0))
        base_selected = {e for e in base_edges if qualifies(case, kind, e)}
        for target in range(4):
            g = min(p for p in full_group if p[0] == target)
            point_perm = tuple(4 * g[i] + offset + 1 for i in range(4) for offset in range(4))
            inverse = tuple(point_perm.index(p) + 1 for p in range(1, 17))
            target_edges = set(allowed_edges(target))
            selected = {e for e in target_edges if qualifies(case, kind, e)}
            require(len(target_edges) == 69 and len(selected) == expected_terms, "edge counts")
            require(
                {image(e, point_perm) for e in base_edges} == target_edges, "allowed-edge transport"
            )
            require(
                {image(e, point_perm) for e in base_selected} == selected, "predicate transport"
            )
            require({image(e, inverse) for e in selected} == base_selected, "inverse transport")
            coefficients = []
            for edge in sorted(selected):
                block = tuple(sorted((*ANCHORS[target], *edge)))
                require(len(block) == 5 and len(set(block)) == 5, "invalid block")
                coefficients.append(
                    dict(edge=edge, block=block, variable_index=indices[block], coefficient=1)
                )
            transports.append(
                dict(
                    group_index=target,
                    anchor_triple=ANCHORS[target],
                    hub=HUBS[target],
                    base_to_target_group_permutation=g,
                    base_to_target_point_permutation=point_perm,
                    target_to_base_point_permutation=inverse,
                    coefficients=sorted(coefficients, key=lambda c: c["variable_index"]),
                )
            )
        rules.append(
            dict(
                case=case,
                predicate=kind,
                sense=sense,
                bound=bound,
                violations=[
                    dict(
                        id=r["id"],
                        value=values[r["id"]],
                        orbit_size=r["orbit_size"],
                        checked_gap=checks[r["id"]]["gap"],
                    )
                    for r in bad
                ],
                violating_orbits=len(bad),
                violating_labeled_links=sum(r["orbit_size"] for r in bad),
                all_base_representative_values=values,
                invariant_maps_checked=invariant_maps,
                full_hub_graph_automorphisms=full_group,
                target_groups=transports,
            )
        )
    result = dict(
        valid=True,
        variables="first 4368 block variables in global lexicographic order",
        labels="1-based points; 0-based group indices and variable indices",
        anchors=ANCHORS,
        hubs=HUBS,
        rules=rules,
        total_linear_cuts=sum(len(r["target_groups"]) for r in rules),
        source_sha256=sha(Path(__file__)),
        representatives_sha256=sha(reps_path),
        orbit_archive_sha256=sha(orbits_path),
        orbit_audit_sha256=sha(orbit_audit_path),
        lp_results_sha256=sha(lp_path),
        lp_audit_sha256=sha(lp_audit_path),
        scope="Necessary inequalities for integer regular 64-block covers in the normalized "
        "four-sevenfold branch. Proof uses complete finite link classification and separately "
        "checked positive LP exclusion certificates. Group transport is relabeling, "
        "not cover invariance.",
    )
    (HERE / "safe-linear-cuts.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "valid": True,
                "rules": len(rules),
                "total_linear_cuts": result["total_linear_cuts"],
                "violating_orbits": [
                    (r["case"], r["predicate"], r["violating_orbits"]) for r in rules
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
