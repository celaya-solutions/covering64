# Document:    Independent Complete Circulant Excess Enumeration and Orbits
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      beb59710b3306cafaa3d210b0a7b45fc8c83f95a71c5a666869e8ff4ea33b9d2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Integer propagation/backtracking and complete graph automorphisms; no cover search."""

import hashlib
import itertools
import json
import time
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "circulant-all-excess-profiles"
PINS = {
    "enumerate.py": "73a8f632af2318c1cba856bbda5de211331484929144f19fc0c4ec0530e661fa",
    "geometry.json": "c1c9e6d640141238e03e2a37fb37155c1ee8f67868dd59fca8844fd93ec0a1a9",
    "profiles.json": "9e29e1aa6769950297656c4b4a14bef14f04bd182500dfc15e56ffb38b9fef9e",
}
POINTS = tuple(range(1, 17))
PAIRS = tuple(itertools.combinations(POINTS, 2))


def require(test, message):
    if not test:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def reference():
    adjacent = {p: {((p - 1 + offset) % 16) + 1 for offset in (1, 3, 8, -3, -1)} for p in POINTS}
    edges = {pair for pair in PAIRS if pair[1] in adjacent[pair[0]]}
    tight = []
    cut_histogram = Counter()
    for side in itertools.combinations(POINTS, 8):
        if 1 not in side:
            continue
        vertices = set(side)
        cut = sum((p in vertices) != (q in vertices) for p, q in edges)
        cut_histogram[cut] += 1
        if cut == 32:
            tight.append(side)
    require(
        len(edges) == 40 and len(tight) == 9 and max(cut_histogram) == 32, "graph and tight cuts"
    )
    forced, choices = [], []
    for p, q in PAIRS:
        if (p, q) in edges:
            continue
        centers = []
        for center in sorted(adjacent[p] & adjacent[q]):
            triple = {p, q, center}
            if not any(triple <= set(side) or not triple & set(side) for side in tight):
                centers.append(center)
        require(len(centers) in (1, 2), "one or two centers after tight cuts")
        (forced if len(centers) == 1 else choices).append([p, q, centers])
    require(len(forced) == 32 and len(choices) == 48, "center choice counts")
    forced_paths = {tuple(sorted((p, q, centers[0]))) for p, q, centers in forced}
    base_paths = [set((p, q, centers[0])) for p, q, centers in choices]
    other_paths = [set((p, q, centers[1])) for p, q, centers in choices]
    matrix, targets = [], []
    for edge in sorted(edges):
        pair = set(edge)
        matrix.append(
            [
                int(pair <= other) - int(pair <= base)
                for base, other in zip(base_paths, other_paths, strict=True)
            ]
        )
        targets.append(
            4 - sum(pair <= set(t) for t in forced_paths) - sum(pair <= t for t in base_paths)
        )
    return adjacent, edges, tight, forced, choices, matrix, targets


def enumerate_integer(matrix, targets):
    # Each +/-1 row is rewritten as a cardinality equation on literals.
    # Bounds propagation is exact; two disjoint branches exhaust every unknown bit.
    rows = []
    for coefficients, target in zip(matrix, targets, strict=True):
        require(set(coefficients) <= {-1, 0, 1}, "unit coefficients")
        literals = [
            (i, int(coefficient == 1)) for i, coefficient in enumerate(coefficients) if coefficient
        ]
        rows.append((literals, target + coefficients.count(-1)))
    solutions = set()
    stats = Counter()

    def visit(values):
        stats["nodes"] += 1
        while True:
            changed = False
            active = []
            for literals, target in rows:
                count = sum(values[i] == sign for i, sign in literals if values[i] != -1)
                unknown = [(i, sign) for i, sign in literals if values[i] == -1]
                need = target - count
                if need < 0 or need > len(unknown):
                    stats["pruned"] += 1
                    return
                if not unknown:
                    continue
                if need in (0, len(unknown)):
                    for i, sign in unknown:
                        values[i] = sign if need else 1 - sign
                        stats["forced_assignments"] += 1
                    changed = True
                else:
                    active.append((min(need, len(unknown) - need), len(unknown), unknown))
            if not changed:
                break
        if -1 not in values:
            mask = sum(bit << i for i, bit in enumerate(values))
            require(mask not in solutions, "duplicate complete assignment")
            require(
                all(
                    sum(c * values[i] for i, c in enumerate(row)) == target
                    for row, target in zip(matrix, targets, strict=True)
                ),
                "integer leaf equations",
            )
            solutions.add(mask)
            return
        if active:
            selected = min(active, key=lambda item: (item[0], item[1], item[2]))
            variable = min(i for i, _ in selected[2])
        else:
            variable = values.index(-1)
        stats["branches"] += 1
        for bit in (0, 1):
            branch = values.copy()
            branch[variable] = bit
            visit(branch)

    visit([-1] * 48)
    return sorted(solutions), dict(stats)


def verify_rref(geometry, matrix, targets):
    # This validates the saved algebra as an extra check. The independent
    # enumeration above never consumes this matrix, its pivots, or its free bits.
    rref = [[Fraction(value) for value in row] for row in geometry["rref"]]
    pivots = geometry["pivots"]
    require(len(rref) == 40 and all(len(row) == 49 for row in rref), "rref shape")
    require(len(pivots) == 30 and pivots == sorted(set(pivots)), "pivot count")
    require(geometry["free_columns"] == [i for i in range(48) if i not in pivots], "free columns")
    require(
        all(
            all(rref[i][pivot] == int(i == j) for j, pivot in enumerate(pivots)) for i in range(30)
        ),
        "pivot identity",
    )
    require(all(not any(row) for row in rref[30:]), "zero trailing rref rows")
    for row, rhs in zip(matrix, targets, strict=True):
        reconstructed = [
            sum(Fraction(row[pivots[k]]) * rref[k][i] for k in range(30)) for i in range(49)
        ]
        require(reconstructed == row + [rhs], "original equation reconstruction")
    # A modular rank lower bound of thirty proves the original rational row
    # space has dimension thirty, since its rows lie in the thirty-dimensional
    # displayed RREF space. This is not used to enumerate assignments.
    prime = 101
    work = [[entry % prime for entry in row] for row in matrix]
    rank = 0
    for column in range(48):
        selected = next((i for i in range(rank, 40) if work[i][column]), None)
        if selected is None:
            continue
        work[rank], work[selected] = work[selected], work[rank]
        inv = pow(work[rank][column], -1, prime)
        work[rank] = [(v * inv) % prime for v in work[rank]]
        for i in range(rank + 1, 40):
            multiple = work[i][column]
            work[i] = [(a - multiple * b) % prime for a, b in zip(work[i], work[rank], strict=True)]
        rank += 1
    require(rank == 30, "independent modular rank lower bound")
    return rank


def automorphisms(adjacent, edges):
    root = 1
    neighborhood = sorted(adjacent[root])
    outside = sorted(set(POINTS) - adjacent[root] - {root})
    patterns = {frozenset(adjacent[p] & adjacent[root]): p for p in outside}
    require(len(patterns) == 10, "outside neighborhood signatures uniquely identify vertices")
    stabilizer = []
    for targets in itertools.permutations(neighborhood):
        mapping = {root: root, **dict(zip(neighborhood, targets, strict=True))}
        for pattern, point in patterns.items():
            image = patterns.get(frozenset(mapping[p] for p in pattern))
            if image is None:
                break
            mapping[point] = image
        if len(mapping) != 16 or set(mapping.values()) != set(POINTS):
            continue
        if all({mapping[p] for p in adjacent[q]} == adjacent[mapping[q]] for q in POINTS):
            stabilizer.append(tuple(mapping[p] for p in POINTS))
    require(len(stabilizer) == 2, "complete stabilizer enumeration")
    all_maps = sorted(
        {
            tuple(((p - 1 + shift) % 16) + 1 for p in mapping)
            for shift in range(16)
            for mapping in stabilizer
        }
    )
    require(len(all_maps) == 32, "complete automorphism count")
    for mapping in all_maps:
        require(
            {tuple(sorted(mapping[p - 1] for p in edge)) for edge in edges} == edges,
            "full automorphism edge check",
        )
    return stabilizer, all_maps


def profile_paths(mask, forced, choices):
    return {tuple(sorted((p, q, centers[0]))) for p, q, centers in forced} | {
        tuple(sorted((p, q, centers[(mask >> i) & 1]))) for i, (p, q, centers) in enumerate(choices)
    }


def action(mapping, forced, choices):
    image = lambda items: tuple(sorted(mapping[p - 1] for p in items))  # noqa: E731
    require(
        {image((p, q, centers[0])) for p, q, centers in forced}
        == {tuple(sorted((p, q, centers[0]))) for p, q, centers in forced},
        "forced paths invariant",
    )
    lookup = {tuple(choice[:2]): i for i, choice in enumerate(choices)}
    permutation, flipped = [], 0
    for p, q, centers in choices:
        pair = image((p, q))
        index = lookup[pair]
        options = choices[index][2]
        require({mapping[c - 1] for c in centers} == set(options), "choice center action")
        permutation.append(index)
        if mapping[centers[0] - 1] == options[1]:
            flipped |= 1 << index
    require(set(permutation) == set(range(48)), "choice action bijection")
    return permutation, flipped


def transform(mask, permutation, flipped):
    out = flipped
    while mask:
        lowest = mask & -mask
        out ^= 1 << permutation[lowest.bit_length() - 1]
        mask -= lowest
    return out


def main():
    start = time.monotonic()
    for name, digest in PINS.items():
        require(sha(PRODUCER / name) == digest, "producer pin " + name)
    geometry = json.loads((PRODUCER / "geometry.json").read_text())
    saved = json.loads((PRODUCER / "profiles.json").read_text())["choice_masks"]
    require(all(type(mask) is int and 0 <= mask < 2**48 for mask in saved), "saved mask domains")
    require(saved == sorted(set(saved)), "saved masks canonical")
    adjacent, edges, tight, forced, choices, matrix, targets = reference()
    for key, value in {
        "edges": [list(e) for e in sorted(edges)],
        "tight_cuts": [list(c) for c in tight],
        "forced": forced,
        "choices": choices,
        "matrix": matrix,
        "targets": targets,
    }.items():
        require(geometry[key] == value, "independent geometry " + key)
    solutions, stats = enumerate_integer(matrix, targets)
    require(
        solutions == saved and len(solutions) == 1300, "exact independent solution set equality"
    )
    rank = verify_rref(geometry, matrix, targets)
    core_types = {
        ((2, 2, 2, 2, 2), 0): "C5",
        ((1, 2, 2, 2, 3), 0): "C4-leaf",
        ((1, 2, 2, 2, 3), 1): "triangle-path2",
        ((1, 1, 2, 3, 3), 1): "triangle-distinct-leaves",
    }
    link_tally = Counter()
    profile_tallies = {}
    for mask in solutions:
        paths = profile_paths(mask, forced, choices)
        require(len(paths) == 80, "eighty distinct paths")
        pair_counts = Counter(pair for path in paths for pair in itertools.combinations(path, 2))
        require(
            all(pair_counts[pair] == (4 if pair in edges else 1) for pair in PAIRS),
            "all pair excess sums",
        )
        require(
            all(sum(p in path for path in paths) == 15 for p in POINTS), "all point excess sums"
        )
        type_tally = Counter()
        for point in POINTS:
            heavy = adjacent[point]
            links = {tuple(v for v in path if v != point) for path in paths if point in path}
            core = {edge for edge in links if set(edge) <= heavy}
            require(len(core) == 5 and len(links) == 15, "point-link edge counts")
            require(
                all(sum(v in heavy for v in edge) == 1 for edge in links - core),
                "all noncore edges attach leaves to core",
            )
            degrees = tuple(sorted(sum(v in edge for edge in core) for v in heavy))
            triangles = sum(
                all(edge in core for edge in itertools.combinations(triple, 2))
                for triple in itertools.combinations(sorted(heavy), 3)
            )
            require((degrees, triangles) in core_types, "known point-link core type")
            kind = core_types[(degrees, triangles)]
            type_tally[kind] += 1
            link_tally[kind] += 1
        profile_tallies[mask] = dict(sorted(type_tally.items()))
    stabilizer, maps = automorphisms(adjacent, edges)
    actions = [action(mapping, forced, choices) for mapping in maps]
    solution_set = set(solutions)
    orbit_sets = defaultdict(set)
    fixed_counts = [0] * len(maps)
    for mask in solutions:
        images = set()
        for index, (permutation, flipped) in enumerate(actions):
            image = transform(mask, permutation, flipped)
            require(image in solution_set, "automorphism preserves full solution set")
            images.add(image)
            fixed_counts[index] += image == mask
        require(32 % len(images) == 0, "orbit-stabilizer")
        orbit_sets[min(images)].update(images)
    orbits = [
        {
            "representative_mask": representative,
            "members": sorted(members),
            "size": len(members),
            "stabilizer_size": 32 // len(members),
            "point_link_type_counts": profile_tallies[representative],
        }
        for representative, members in sorted(orbit_sets.items())
    ]
    require(sum(len(members) for members in orbit_sets.values()) == 1300, "orbit partition")
    require(sum(fixed_counts) == 32 * len(orbits), "Burnside orbit check")
    require(
        all(
            profile_tallies[mask] == profile_tallies[representative]
            for representative, members in orbit_sets.items()
            for mask in members
        ),
        "point-link census preserved by profile orbit",
    )
    original_profiles = HERE.parent / "circulant-pair-graph-screen/profiles.json"
    require(
        sha(original_profiles)
        == "dec757aef695e80546c0408a5ebe116cb4666e9472e1e3b429d07bef2990a908",
        "original eight profile pin",
    )
    original_mapping = []
    by_paths = {frozenset(profile_paths(mask, forced, choices)): mask for mask in solutions}
    orbit_representative = {
        mask: representative for representative, members in orbit_sets.items() for mask in members
    }
    for index, entry in enumerate(json.loads(original_profiles.read_text())):
        mask = by_paths[frozenset(tuple(t) for t in entry["excess_triples"])]
        original_mapping.append(
            {
                "profile_index": index,
                "choice_mask": mask,
                "orbit_representative": orbit_representative[mask],
            }
        )
    # Controls exercise solution-set completeness and exact incidence. A changed
    # assignment is chosen outside the known full solution set, not guessed.
    controls = {}
    bad_lists = {
        "omitted_mask": saved[:-1],
        "duplicate_mask": saved + [saved[0]],
        "reversed_order": list(reversed(saved)),
        "bool_mask": [True] + saved[1:],
    }
    for name, damaged in bad_lists.items():
        require(damaged != solutions, "damaged solution set accepted")
        controls[name] = "rejected"
    bad_mask = next(
        saved[0] ^ (1 << i) for i in range(48) if (saved[0] ^ (1 << i)) not in solution_set
    )
    require(
        any(
            sum(coefficient * ((bad_mask >> i) & 1) for i, coefficient in enumerate(row)) != target
            for row, target in zip(matrix, targets, strict=True)
        ),
        "damaged mask incidence control",
    )
    controls["changed_choice"] = "rejected"
    dump(
        "automorphisms.json",
        {
            "stabilizer": stabilizer,
            "all_maps": maps,
            "outside_signatures_unique": True,
            "neighbor_bijections_tested": 120,
            "fixed_profile_counts": fixed_counts,
        },
    )
    dump("orbits.json", orbits)
    audit = {
        "passed": True,
        "producer_pins": PINS,
        "checker_sha256": sha(Path(__file__)),
        "profiles": len(solutions),
        "integer_enumeration": stats,
        "rational_rank_verified": rank,
        "free_dimension": 48 - rank,
        "automorphism_group_size": 32,
        "orbit_count": len(orbits),
        "orbit_size_histogram": dict(sorted(Counter(o["size"] for o in orbits).items())),
        "original_eight_profiles": original_mapping,
        "point_link_core_tally": dict(sorted(link_tally.items())),
        "profile_core_census_patterns": len({tuple(t.items()) for t in profile_tallies.values()}),
        "damage_controls": controls,
        "optimizer_calls": 0,
        "cover_searches": 0,
        "elapsed_seconds": time.monotonic() - start,
        "scope": "All arithmetic excess profiles for this one graph; no cover existence claim.",
        "output_hashes": {name: sha(HERE / name) for name in ("automorphisms.json", "orbits.json")},
    }
    dump("audit.json", audit)
    print(
        json.dumps(
            {
                "audit_sha256": sha(HERE / "audit.json"),
                "profiles": len(solutions),
                "orbits": len(orbits),
                "orbit_sizes": audit["orbit_size_histogram"],
                "enumeration": stats,
            }
        )
    )


if __name__ == "__main__":
    main()
