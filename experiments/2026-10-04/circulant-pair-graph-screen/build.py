# Document:    Finite Circulant Pair Graph Arithmetic Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c86afe80de475d3a86baecd175f16b84d377937ccae194f683071fc0d8b6d78b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Enumerate graph arithmetic and explicit excess profiles; no cover solver."""

import copy
import hashlib
import itertools
import json
import platform
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
POINTS = tuple(range(16))
PAIRS = tuple(itertools.combinations(POINTS, 2))
TRIPLES = tuple(itertools.combinations(POINTS, 3))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def labeled(items):
    return [[p + 1 for p in item] for item in sorted(tuple(sorted(item)) for item in items)]


def graph(a, b):
    steps = {a, b, 8, 16 - a, 16 - b}
    edges = {pair for pair in PAIRS if (pair[1] - pair[0]) % 16 in steps}
    adjacent = [{q for q in POINTS if q != p and tuple(sorted((p, q))) in edges} for p in POINTS]
    assert len(edges) == 40 and all(len(n) == 5 for n in adjacent)
    return edges, adjacent


def cuts(edges, size):
    histogram = Counter()
    maximum = -1
    first = None
    tight = []
    for items in itertools.combinations(POINTS, size):
        if size == 8 and 0 not in items:
            continue
        inside = set(items)
        value = sum((p in inside) != (q in inside) for p, q in edges)
        histogram[value] += 1
        if value > maximum:
            maximum, first = value, items
        if size == 8 and value == 32:
            tight.append(items)
    assert sum(histogram.values()) == (11440 if size == 7 else 6435)
    return {
        "histogram": dict(sorted(histogram.items())),
        "maximum": maximum,
        "first_maximizer": [p + 1 for p in first],
        "tight32_sides": labeled(tight),
    }


def screen():
    records = []
    for a, b in itertools.combinations(range(1, 8), 2):
        edges, adjacent = graph(a, b)
        triangles = [
            t for t in TRIPLES if all(pair in edges for pair in itertools.combinations(t, 2))
        ]
        nonedges = [pair for pair in PAIRS if pair not in edges]
        no_center = [pair for pair in nonedges if not adjacent[pair[0]] & adjacent[pair[1]]]
        record = {
            "positive_steps": [a, b, 8],
            "triangles": len(triangles),
            "first_triangle": labeled(triangles[:1]),
            "nonedge_common_center_histogram": dict(
                sorted(Counter(len(adjacent[p] & adjacent[q]) for p, q in nonedges).items())
            ),
            "nonedges_without_center": labeled(no_center),
        }
        if triangles:
            record["disposition"] = "outside requested triangle-free branch"
        elif no_center:
            record["disposition"] = (
                "impossible triangle-free pair profile: nonedge has no P3 center"
            )
        else:
            record["seven_cut"] = cuts(edges, 7)
            record["eight_cut"] = cuts(edges, 8)
            record["disposition"] = (
                "survives necessary arithmetic"
                if (record["seven_cut"]["maximum"] <= 31 and record["eight_cut"]["maximum"] <= 32)
                else "violates regular-cover cut bound"
            )
        records.append(record)
    return records


def check_profile(profile, edges, forbidden):
    if not isinstance(profile, list) or len(profile) != 80:
        raise ValueError("eighty triples required")
    if any(
        not isinstance(t, list)
        or len(t) != 3
        or any(type(p) is not int or not 1 <= p <= 16 for p in t)
        or t != sorted(set(t))
        for t in profile
    ):
        raise ValueError("malformed triple")
    triples = [tuple(p - 1 for p in t) for t in profile]
    if triples != sorted(set(triples)):
        raise ValueError("unordered or duplicate triples")
    if any(sum(pair in edges for pair in itertools.combinations(t, 2)) != 2 for t in triples):
        raise ValueError("non-P3 triple")
    if set(triples) & forbidden:
        raise ValueError("tight-cut internal excess")
    pairs = Counter(pair for t in triples for pair in itertools.combinations(t, 2))
    if any(pairs[pair] != (4 if pair in edges else 1) for pair in PAIRS):
        raise ValueError("wrong pair demand")
    if any(sum(p in t for t in triples) != 15 for p in POINTS):
        raise ValueError("wrong point excess degree")


def point_links(profile, adjacent):
    triples = [tuple(p - 1 for p in t) for t in profile]
    records = []
    for point in POINTS:
        links = {tuple(p for p in t if p != point) for t in triples if point in t}
        heavy = adjacent[point]
        light = set(POINTS) - heavy - {point}
        assert len(links) == 15
        assert all(
            sum(p in e for e in links) == (4 if p in heavy else 1) for p in POINTS if p != point
        )
        core = {e for e in links if set(e) <= heavy}
        assert len(core) == 5
        assert all(sum(p in heavy for p in e) == 1 for e in links - core)
        assert {p for e in links - core for p in e if p in light} == light
        degrees = tuple(sorted(sum(p in e for e in core) for p in heavy))
        triangles = sum(
            all(e in core for e in itertools.combinations(t, 2))
            for t in itertools.combinations(sorted(heavy), 3)
        )
        types = {
            ((2, 2, 2, 2, 2), 0): "C5",
            ((1, 2, 2, 2, 3), 0): "C4-leaf",
            ((1, 2, 2, 2, 3), 1): "triangle-path2",
            ((1, 1, 2, 3, 3), 1): "triangle-distinct-leaves",
        }
        kind = types[(degrees, triangles)]
        records.append(
            {
                "point": point + 1,
                "type": kind,
                "heavy_points": sorted(p + 1 for p in heavy),
                "core_edges": labeled(core),
                "link_edges": labeled(links),
                "core_degree_sequence": list(degrees),
                "core_triangles": triangles,
            }
        )
    assert len({r["type"] for r in records}) == 1
    return records


def main():
    records = screen()
    survivors = [r for r in records if r["disposition"] == "survives necessary arithmetic"]
    assert [r["positive_steps"][:2] for r in survivors] == [[1, 3], [1, 5], [3, 7], [5, 7]]
    edges, adjacent = graph(1, 3)
    nonedges = [pair for pair in PAIRS if pair not in edges]
    maps = []
    for (a, b), multiplier in zip(((1, 3), (1, 5), (3, 7), (5, 7)), (1, 5, 3, 7), strict=True):
        point_map = [(multiplier * p) % 16 for p in POINTS]
        assert set(point_map) == set(POINTS)
        assert {tuple(sorted((point_map[p], point_map[q]))) for p, q in edges} == graph(a, b)[0]
        maps.append(
            {
                "target_positive_steps": [a, b, 8],
                "multiplier": multiplier,
                "point_permutation": [p + 1 for p in point_map],
            }
        )
    tight = [set(p - 1 for p in side) for side in survivors[0]["eight_cut"]["tight32_sides"]]
    paths = {tuple(sorted((p, q, c))) for p, q in nonedges for c in adjacent[p] & adjacent[q]}
    forbidden = {t for t in paths if any(set(t) <= side or not set(t) & side for side in tight)}
    assert len(paths) == 160 and len(forbidden) == 32 and len(tight) == 9
    allowed = {
        pair: [
            c
            for c in sorted(adjacent[pair[0]] & adjacent[pair[1]])
            if tuple(sorted((*pair, c))) not in forbidden
        ]
        for pair in nonedges
    }
    assert Counter(map(len, allowed.values())) == {1: 32, 2: 48}
    forced = {
        tuple(sorted((*pair, centers[0]))) for pair, centers in allowed.items() if len(centers) == 1
    }
    assert len(forced) == 32
    # The following 24 cases are choices of five orbit representatives for h,
    # not block families. No assumption of cover invariance is made.
    differences = [2, 4, 5, 6, 7]
    choices = [sorted(adjacent[0] & adjacent[d]) for d in differences]
    profiles = []
    rejected = []
    for centers in itertools.product(*choices):
        profile = labeled(
            {
                tuple(sorted((x, (x + d) % 16, (x + c) % 16)))
                for x in POINTS
                for d, c in zip(differences, centers, strict=True)
            }
        )
        try:
            check_profile(profile, edges, forbidden)
        except ValueError as error:
            rejected.append({"center_offsets": list(centers), "reason": str(error)})
            continue
        profiles.append(
            {
                "differences": differences,
                "center_offsets": list(centers),
                "excess_triples": profile,
                "point_links": point_links(profile, adjacent),
                "pair_excess_histogram": {1: 80, 4: 40},
                "point_excess_histogram": {15: 16},
            }
        )
    assert len(profiles) == 8 and len(rejected) == 16
    assert [p["center_offsets"] for p in profiles] == [
        list(c) for c in itertools.product((1,), (1, 3), (8, 13), (3,), (8, 15))
    ]
    control_cases = {}
    for name in ("missing", "duplicate", "bad_label", "bool_label", "non_path", "wrong_path"):
        damaged = copy.deepcopy(profiles[0]["excess_triples"])
        if name == "missing":
            damaged.pop()
        elif name == "duplicate":
            damaged[-1] = damaged[0]
        elif name == "bad_label":
            damaged[0][0] = 0
        elif name == "bool_label":
            damaged[0][0] = True
        elif name == "non_path":
            damaged[0] = next(
                [p + 1 for p in t]
                for t in TRIPLES
                if sum(pair in edges for pair in itertools.combinations(t, 2)) != 2
            )
            damaged.sort()
        else:
            candidate = next(t for t in labeled(paths - forbidden) if t not in damaged)
            damaged[0] = candidate
            damaged.sort()
        try:
            check_profile(damaged, edges, forbidden)
        except ValueError:
            control_cases[name] = "rejected"
        else:
            raise ValueError("damaged profile accepted: " + name)
    geometry = {
        "positive_steps": [1, 3, 8],
        "edges": labeled(edges),
        "survivor_isomorphisms": maps,
        "tight_balanced_cut_sides": labeled(tight),
        "forbidden_excess_paths": labeled(forbidden),
        "forced_excess_paths": labeled(forced),
        "nonedge_center_choices_after_tight_cuts": [
            {"pair": [p + 1 for p in pair], "centers": [c + 1 for c in centers]}
            for pair, centers in allowed.items()
        ],
        "forced_edge_load_histogram": dict(
            sorted(Counter(sum(set(e) <= set(t) for t in forced) for e in edges).items())
        ),
    }
    dump("screen.json", records)
    dump("geometry.json", geometry)
    dump("profiles.json", profiles)
    dump("rejected-orbit-choices.json", rejected)
    dump(
        "summary.json",
        {
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_sha256": sha(Path(__file__)),
            "python": platform.python_version(),
            "graphs_enumerated": 21,
            "outside_triangle_free_branch": 13,
            "nonedge_center_obstructions": 4,
            "labeled_survivors": 4,
            "survivor_isomorphism_types": 1,
            "nonedge_center_histogram": {1: 16, 2: 48, 3: 16},
            "distinct_from_clebsch": True,
            "max_seven_cut": 31,
            "max_eight_cut": 32,
            "tight_balanced_cuts": 9,
            "forbidden_excess_paths": 32,
            "forced_excess_paths_after_tight_cuts": 32,
            "binary_nonedge_choices_before_edge_balance": 48,
            "translation_orbit_choices_tested": 24,
            "constructed_excess_profiles": 8,
            "point_link_profile_core_census": dict(
                Counter(p["point_links"][0]["type"] for p in profiles)
            ),
            "point_link_cases_checked": 128,
            "damage_controls": control_cases,
            "solver_calls": 0,
            "cover_searches": 0,
            "cover_models_prepared": 0,
            "covers_constructed": 0,
            "seeds": None,
            "scope": (
                "Finite graph screen and eight arithmetic profiles; no cover existence claim."
            ),
            "cover_invariance_assumed": False,
            "all_excess_profiles_classified": False,
            "output_hashes": {
                name: sha(HERE / name)
                for name in (
                    "screen.json",
                    "geometry.json",
                    "profiles.json",
                    "rejected-orbit-choices.json",
                )
            },
        },
    )
    print(
        json.dumps(
            {
                "summary_sha256": sha(HERE / "summary.json"),
                "profiles": len(profiles),
                "forced_edge_load_histogram": geometry["forced_edge_load_histogram"],
            }
        )
    )


if __name__ == "__main__":
    main()
