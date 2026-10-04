# Document:    Independent Circulant Pair Graph Arithmetic Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b6d7a01a1379352d4f5529be5cbae703fdbae22d443bc75d66064dc0e67ff34f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exhaustive finite graph/profile arithmetic, without producer imports or solvers."""

import copy
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "circulant-pair-graph-screen"
PINS = {
    "build.py": "4a7901e6413c56ccefab9caf870c3b651a902aeb6f560a6097e5fe380b211ad0",
    "summary.json": "27dd7ebf038525fa55b9c6ac631127b20ffbf6f424c4c20b4d784a93c1737d03",
    "profiles.json": "dec757aef695e80546c0408a5ebe116cb4666e9472e1e3b429d07bef2990a908",
    "geometry.json": "3476c522dcb2dfc01478d41da25a1a2c8766acaeb189f0341fe991949e3b6d23",
    "screen.json": "c12a292954a417a09525dca7e0651d7e50db75920406c8de468a67f88daa54b9",
    "rejected-orbit-choices.json": (
        "168861717eb0779006895cf488b6ebaedc37be9ed1369d9039ea911a273c5f95"
    ),
}
POINTS = tuple(range(1, 17))
PAIRS = tuple(combinations(POINTS, 2))
TRIPLES = tuple(combinations(POINTS, 3))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(actual, expected, label):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), label)


def canonical(rows):
    return "".join(" ".join(map(str, t)) + "\n" for t in sorted(rows)).encode()


def graph(a, b):
    steps = {a, b, 8, 16 - a, 16 - b}
    adjacency = {p: {1 + ((p - 1 + step) % 16) for step in steps} for p in POINTS}
    edges = {tuple(sorted((p, q))) for p in POINTS for q in adjacency[p]}
    require(len(edges) == 40 and all(len(v) == 5 for v in adjacency.values()), "5regular graph")
    return edges, adjacency


def cuts(adjacency, size):
    masks = {p: sum(1 << (q - 1) for q in neighbors) for p, neighbors in adjacency.items()}
    histogram, maximum, first, tight = Counter(), -1, None, []
    for subset in combinations(POINTS, size):
        if size == 8 and 1 not in subset:
            continue
        outside = 65535 ^ sum(1 << (p - 1) for p in subset)
        value = sum((masks[p] & outside).bit_count() for p in subset)
        histogram[value] += 1
        if value > maximum:
            maximum, first = value, list(subset)
        if size == 8 and value == 32:
            tight.append(list(subset))
    require(sum(histogram.values()) == (11440 if size == 7 else 6435), "all cut sides")
    return {
        "histogram": {str(k): v for k, v in sorted(histogram.items())},
        "maximum": maximum,
        "first_maximizer": first,
        "tight32_sides": tight,
    }


def screen_graphs():
    output = []
    for a, b in combinations(range(1, 8), 2):
        edges, adjacency = graph(a, b)
        triangles = [t for t in TRIPLES if all(pair in edges for pair in combinations(t, 2))]
        nonedges = [pair for pair in PAIRS if pair not in edges]
        missing = [pair for pair in nonedges if not adjacency[pair[0]] & adjacency[pair[1]]]
        histogram = Counter(len(adjacency[p] & adjacency[q]) for p, q in nonedges)
        row = {
            "positive_steps": [a, b, 8],
            "triangles": len(triangles),
            "first_triangle": [list(t) for t in triangles[:1]],
            "nonedge_common_center_histogram": {str(k): v for k, v in sorted(histogram.items())},
            "nonedges_without_center": [list(p) for p in missing],
        }
        if triangles:
            row["disposition"] = "outside requested triangle-free branch"
        elif missing:
            row["disposition"] = "impossible triangle-free pair profile: nonedge has no P3 center"
        else:
            row["seven_cut"], row["eight_cut"] = cuts(adjacency, 7), cuts(adjacency, 8)
            row["disposition"] = (
                "survives necessary arithmetic"
                if row["seven_cut"]["maximum"] <= 31 and row["eight_cut"]["maximum"] <= 32
                else "violates regular-cover cut bound"
            )
        output.append(row)
    return output


def validate_profile(raw, edges, forbidden):
    require(type(raw) is list and len(raw) == 80, "eighty triples")
    for triple in raw:
        require(type(triple) is list and len(triple) == 3, "triple width")
        require(all(type(p) is int and p in POINTS for p in triple), "1based integer labels")
        require(triple == sorted(set(triple)), "distinct ordered labels")
    profile = tuple(tuple(t) for t in raw)
    require(list(profile) == sorted(set(profile)), "sorted distinct triples")
    require(all(sum(pair in edges for pair in combinations(t, 2)) == 2 for t in profile), "P3s")
    require(not set(profile) & forbidden, "no tight-cut internal excess")
    loads = Counter(pair for t in profile for pair in combinations(t, 2))
    require(all(loads[pair] == (4 if pair in edges else 1) for pair in PAIRS), "exact pair loads")
    require(all(sum(p in t for t in profile) == 15 for p in POINTS), "point degrees15")
    return profile


def point_link(profile, point, adjacency):
    edges = {tuple(p for p in t if p != point) for t in profile if point in t}
    heavy = adjacency[point]
    degree = Counter(p for pair in edges for p in pair)
    require(
        len(edges) == 15
        and all(degree[p] == (4 if p in heavy else 1) for p in POINTS if p != point),
        "link degrees",
    )
    core = {pair for pair in edges if set(pair) <= heavy}
    require(
        len(core) == 5 and all(len(set(pair) & heavy) == 1 for pair in edges - core),
        "core with pendant leaves",
    )
    require(
        {p for pair in edges - core for p in pair if p not in heavy}
        == set(POINTS) - heavy - {point},
        "all ten leaves",
    )
    ds = sorted(sum(p in pair for pair in core) for p in heavy)
    triangle_count = sum(
        all(pair in core for pair in combinations(t, 2)) for t in combinations(sorted(heavy), 3)
    )
    names = {
        ((2, 2, 2, 2, 2), 0): "C5",
        ((1, 2, 2, 2, 3), 0): "C4-leaf",
        ((1, 2, 2, 2, 3), 1): "triangle-path2",
        ((1, 1, 2, 3, 3), 1): "triangle-distinct-leaves",
    }
    require((tuple(ds), triangle_count) in names, "allowed core shape")
    return {
        "point": point,
        "type": names[(tuple(ds), triangle_count)],
        "heavy_points": sorted(heavy),
        "core_edges": list(map(list, sorted(core))),
        "link_edges": list(map(list, sorted(edges))),
        "core_degree_sequence": ds,
        "core_triangles": triangle_count,
    }


def main():
    require(not (HERE / "review.json").exists(), "preserve audit")
    for name, digest in PINS.items():
        require(sha(PRODUCER / name) == digest, "frozen " + name)
    summary, geometry = read(PRODUCER / "summary.json"), read(PRODUCER / "geometry.json")
    screens = screen_graphs()
    exact(read(PRODUCER / "screen.json"), screens, "all21 graph screens")
    survivors = [r for r in screens if r["disposition"] == "survives necessary arithmetic"]
    require(
        [r["positive_steps"] for r in survivors] == [[1, 3, 8], [1, 5, 8], [3, 7, 8], [5, 7, 8]],
        "four surviving labeled graphs",
    )
    edges, adjacency = graph(1, 3)
    exact(geometry["positive_steps"], [1, 3, 8], "graph steps")
    exact(geometry["edges"], list(map(list, sorted(edges))), "graph edges")
    for iso, target in zip(geometry["survivor_isomorphisms"], survivors, strict=True):
        permutation = iso["point_permutation"]
        require(
            all(type(p) is int for p in permutation) and sorted(permutation) == list(POINTS),
            "graph isomorphism bijection",
        )
        require(
            permutation == [1 + (iso["multiplier"] * (p - 1)) % 16 for p in POINTS],
            "multiplication map",
        )
        require(iso["target_positive_steps"] == target["positive_steps"], "isomorphism target")
        require(
            {tuple(sorted((permutation[a - 1], permutation[b - 1]))) for a, b in edges}
            == graph(*target["positive_steps"][:2])[0],
            "isomorphism edges",
        )
    tight = [set(side) for side in survivors[0]["eight_cut"]["tight32_sides"]]
    exact(geometry["tight_balanced_cut_sides"], [sorted(side) for side in tight], "nine tight cuts")
    paths = {tuple(sorted((p, a, b))) for p in POINTS for a, b in combinations(adjacency[p], 2)}
    require(len(paths) == 160, "160 induced paths")
    forbidden = {t for t in paths if any(set(t) <= side or not set(t) & side for side in tight)}
    exact(geometry["forbidden_excess_paths"], list(map(list, sorted(forbidden))), "32 forbidden")
    nonedges = [pair for pair in PAIRS if pair not in edges]
    allowed = {
        pair: [
            p
            for p in sorted(adjacency[pair[0]] & adjacency[pair[1]])
            if tuple(sorted((*pair, p))) not in forbidden
        ]
        for pair in nonedges
    }
    require(Counter(map(len, allowed.values())) == {1: 32, 2: 48}, "32forced48binary choices")
    forced = {
        tuple(sorted((*pair, values[0]))) for pair, values in allowed.items() if len(values) == 1
    }
    exact(geometry["forced_excess_paths"], list(map(list, sorted(forced))), "forced triples")
    exact(
        geometry["nonedge_center_choices_after_tight_cuts"],
        [{"pair": list(pair), "centers": vals} for pair, vals in allowed.items()],
        "all80center rows",
    )
    forced_load = Counter(sum(set(pair) <= set(t) for t in forced) for pair in edges)
    exact(
        geometry["forced_edge_load_histogram"],
        {str(k): v for k, v in sorted(forced_load.items())},
        "forced edge loads",
    )
    # Enumerate all ten translation orbits and all252 five-orbit subsets independently.
    remaining, orbits = set(paths), []
    while remaining:
        triple = min(remaining)
        orbit = {tuple(sorted(1 + (p - 1 + shift) % 16 for p in triple)) for shift in range(16)}
        require(len(orbit) == 16 and orbit <= remaining, "full disjoint translation orbit")
        orbits.append(orbit)
        remaining -= orbit
    require(len(orbits) == 10, "ten P3 translation orbits")
    invariant = set()
    for choice in combinations(range(10), 5):
        proposed = sorted(set().union(*(orbits[i] for i in choice)))
        try:
            validated = validate_profile(list(map(list, proposed)), edges, forbidden)
        except ValueError:
            continue
        invariant.add(validated)
    profiles = read(PRODUCER / "profiles.json")
    require(len(profiles) == len(invariant) == 8, "eight invariant profiles")
    hashes, actual_profiles, core_census = [], set(), Counter()
    for record in profiles:
        profile = validate_profile(record["excess_triples"], edges, forbidden)
        actual_profiles.add(profile)
        require(record["differences"] == [2, 4, 5, 6, 7], "nonedge orbit representatives")
        offsets = record["center_offsets"]
        require(
            len(offsets) == 5 and all(type(x) is int and 0 <= x < 16 for x in offsets), "offsets"
        )
        require(
            profile
            == tuple(
                sorted(
                    {
                        tuple(sorted((1 + x, 1 + (x + d) % 16, 1 + (x + c) % 16)))
                        for x in range(16)
                        for d, c in zip(record["differences"], offsets, strict=True)
                    }
                )
            ),
            "offset reconstruction",
        )
        link_rows = [point_link(profile, p, adjacency) for p in POINTS]
        exact(record["point_links"], link_rows, "all16 point links")
        require(len({r["type"] for r in link_rows}) == 1, "translated constant core shape")
        core_census[link_rows[0]["type"]] += 1
        exact(record["pair_excess_histogram"], {"1": 80, "4": 40}, "pair histogram")
        exact(record["point_excess_histogram"], {"15": 16}, "point histogram")
        hashes.append(hashlib.sha256(canonical(profile)).hexdigest())
    require(actual_profiles == invariant, "complete translation-invariant arithmetic family")
    require(
        dict(core_census) == {"C4-leaf": 4, "C5": 2, "triangle-distinct-leaves": 2}, "core census"
    )
    controls = []
    for name in ("missing", "duplicate", "zero_label", "bool_label", "nonsorted", "nonpath"):
        bad = copy.deepcopy(profiles[0]["excess_triples"])
        if name == "missing":
            bad.pop()
        elif name == "duplicate":
            bad[-1] = bad[0]
        elif name == "zero_label":
            bad[0][0] = 0
        elif name == "bool_label":
            bad[0][0] = True
        elif name == "nonsorted":
            bad[0].reverse()
        else:
            t = next(t for t in TRIPLES if t not in paths and list(t) not in bad)
            bad[0] = list(t)
            bad.sort()
        try:
            validate_profile(bad, edges, forbidden)
        except ValueError:
            controls.append(name)
        else:
            raise AssertionError("damage accepted " + name)
    for key, val in {
        "graphs_enumerated": 21,
        "outside_triangle_free_branch": 13,
        "nonedge_center_obstructions": 4,
        "labeled_survivors": 4,
        "survivor_isomorphism_types": 1,
        "max_seven_cut": 31,
        "max_eight_cut": 32,
        "tight_balanced_cuts": 9,
        "forbidden_excess_paths": 32,
        "forced_excess_paths_after_tight_cuts": 32,
        "binary_nonedge_choices_before_edge_balance": 48,
        "translation_orbit_choices_tested": 24,
        "constructed_excess_profiles": 8,
        "point_link_cases_checked": 128,
        "cover_invariance_assumed": False,
        "all_excess_profiles_classified": False,
        "distinct_from_clebsch": True,
        "solver_calls": 0,
        "cover_searches": 0,
        "covers_constructed": 0,
    }.items():
        exact(summary[key], val, "summary " + key)
    exact(summary["point_link_profile_core_census"], dict(core_census), "summary core census")
    for filename, digest in summary["output_hashes"].items():
        require(sha(PRODUCER / filename) == digest, "output hash " + filename)
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "producer_pins": PINS,
        "graphs_checked": 21,
        "all_recorded_cut_rows_checked": sum(11440 + 6435 for row in screens if "seven_cut" in row),
        "graph_edges": 40,
        "graph_triangles": 0,
        "graph_induced_paths": 160,
        "nonedge_common_neighbor_histogram": {"1": 16, "2": 48, "3": 16},
        "distinct_from_clebsch": True,
        "translation_orbits": 10,
        "five_orbit_subsets_checked": 252,
        "invariant_profiles": 8,
        "profile_hashes_in_producer_order": hashes,
        "point_links_checked": 128,
        "core_profile_census": dict(core_census),
        "tight32_cuts": 9,
        "forbidden_excess_paths": 32,
        "forced_excess_paths": 32,
        "remaining_binary_nonedge_choices": 48,
        "damaged_controls_rejected": controls,
        "optimizer_calls": 0,
        "producer_imported": False,
        "scope": (
            "Necessary regular pair-profile arithmetic for this triangle-free graph; "
            "eight translation-invariant excess profiles, not all possible excess "
            "profiles. No block-family invariance imposed and no cover constructed."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(HERE / "review.json"),
                "profiles": 8,
                "point_links": 128,
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
