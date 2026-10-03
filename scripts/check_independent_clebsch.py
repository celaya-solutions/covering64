#!/usr/bin/env python3
# Document:    Independent Clebsch Matrix and Profile Certificate Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      1423c1a7b1ec182292afb77b62da9125ed3a775cfb17a6459157449ae7cc1ad7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Standard-library matrix audit; never imports the producer or invokes a solver."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
from collections import Counter
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reference_geometry():
    """Four-cube plus antipodal diagonals, transported to the archived labels."""
    vertices = tuple(itertools.product((0, 1), repeat=4))
    labels = {
        v: 1 + sum((bit ^ (sum(v) % 2)) * 2**i for i, bit in enumerate(v))
        for v in vertices
    }
    edges = {
        tuple(sorted((labels[u], labels[v])))
        for u, v in itertools.combinations(vertices, 2)
        if sum(a != b for a, b in zip(u, v, strict=True)) in (1, 4)
    }
    neighbors = {
        p: {q for q in range(1, 17) if tuple(sorted((p, q))) in edges}
        for p in range(1, 17)
    }
    require(len(edges) == 40, "reference edge count")
    require(all(len(s) == 5 for s in neighbors.values()), "reference degree")
    for p, q in itertools.combinations(range(1, 17), 2):
        require(
            len(neighbors[p] & neighbors[q]) == (0 if (p, q) in edges else 2),
            "reference common-neighbor count",
        )
    triples = tuple(itertools.combinations(range(1, 17), 3))
    paths = {t for t in triples if sum(p in edges for p in itertools.combinations(t, 2)) == 2}
    require(len(paths) == 160, "reference path count")
    return edges, paths


def canonical_tuples(values, width, name):
    require(isinstance(values, (list, tuple)), f"{name} must be a sequence")
    result = []
    for value in values:
        require(isinstance(value, (list, tuple)) and len(value) == width, f"malformed {name}")
        require(all(type(x) is int and 1 <= x <= 16 for x in value), f"invalid {name} label")
        item = tuple(value)
        require(tuple(sorted(set(item))) == item, f"noncanonical {name}")
        result.append(item)
    require(result == sorted(set(result)), f"duplicate or unordered {name}")
    return result


def check_graph(graph):
    require(isinstance(graph, dict), "graph must be an object")
    edges, _ = reference_geometry()
    actual = canonical_tuples(graph.get("edges"), 2, "edge")
    require(set(actual) == edges, "graph differs from four-cube reference")
    expected_words = [2 * x + sum((x // 2**i) % 2 for i in range(4)) % 2 for x in range(16)]
    require(graph.get("words") == expected_words, "graph word-to-label ordering differs")
    require(all(type(x) is int for x in graph["words"]), "graph word has noninteger type")
    return edges


def check_profile(profile):
    edges, paths = reference_geometry()
    actual = canonical_tuples(profile, 3, "profile triple")
    require(len(actual) == 80, "profile must have eighty distinct triples")
    require(set(actual) <= paths, "profile contains a non-path triple")
    pair_load = dict.fromkeys(itertools.combinations(range(1, 17), 2), 0)
    for triple in actual:
        for pair in itertools.combinations(triple, 2):
            pair_load[pair] += 1
    require(
        all(n == (4 if pair in edges else 1) for pair, n in pair_load.items()),
        "profile has wrong pair loads",
    )
    return set(actual)


def balanced_cut_summary(edges):
    """Necessary cut bounds for simple degree-five pair-excess graphs.

    A block split a+(5-a) has 10-3*a*(5-a)/2 internal triples.
    Summing and using complete coverage yields cut<=32 for 8+8 and,
    after the odd-degree parity condition, cut<=31 for 7+9.
    """
    actual = set(canonical_tuples(sorted(edges), 2, "cut edge"))
    require(len(actual) == 40, "cut graph must have forty edges")
    require(all(sum(p in edge for edge in actual) == 5 for p in range(1, 17)),
            "cut graph must have degree five")
    histograms = {}
    for size in (7, 8):
        histogram = Counter()
        for points in itertools.combinations(range(1, 17), size):
            if size == 8 and 1 not in points:
                continue
            part = set(points)
            histogram[sum((u in part) != (v in part) for u, v in actual)] += 1
        histograms[size] = dict(sorted(histogram.items()))
    return {
        "cut_histograms": histograms,
        "maximum_cut_7_9": max(histograms[7]),
        "maximum_cut_8_8": max(histograms[8]),
        "necessary_bounds_pass": max(histograms[7]) <= 31 and max(histograms[8]) <= 32,
        "scope": "necessary full-cover condition, not sufficiency",
    }


def reference_recipe_profiles():
    """Reconstruct the 1,024 recipes through graph common-neighbor squares."""
    edges, _ = reference_geometry()
    words = [2 * x + sum((x // 2**i) % 2 for i in range(4)) % 2 for x in range(16)]
    neighbors = {p: {q for q in range(1, 17) if tuple(sorted((p, q))) in edges}
                 for p in range(1, 17)}
    squares = {
        tuple(sorted((p, q, *sorted(neighbors[p] & neighbors[q]))))
        for p, q in itertools.combinations(range(1, 17), 2) if (p, q) not in edges
    }
    require(len(squares) == 40, "reference square count")
    colors = {}
    for edge in edges:
        a, b = edge
        agreement = [i for i in range(5) if (words[a - 1] // 2**i) % 2
                     == (words[b - 1] // 2**i) % 2]
        require(len(agreement) == 1, "reference edge color")
        colors[edge] = agreement[0]
    links = {edge: {} for edge in edges}
    for square in squares:
        inside = [edge for edge in itertools.combinations(square, 2) if edge in edges]
        a, b = sorted({colors[edge] for edge in inside})
        winner = a if (b - a) % 5 in (1, 2) else b
        first, second = [edge for edge in inside if colors[edge] == winner]
        links[first][second] = square
        links[second][first] = square
    require(all(len(link) == 2 for link in links.values()), "reference auxiliary degree")
    unseen = set(edges)
    alternatives = []
    while unseen:
        start = min(unseen)
        cycle = [start, min(links[start])]
        while len(cycle) < 4:
            choices = set(links[cycle[-1]]) - set(cycle)
            require(len(choices) == 1, "reference cycle ambiguity")
            cycle.append(choices.pop())
        require(start in links[cycle[-1]], "reference cycle not closed")
        unseen.difference_update(cycle)
        choices = [set(), set()]
        for source, target in zip(cycle, cycle[1:] + cycle[:1], strict=True):
            square = links[source][target]
            for bit, positive in enumerate((target, source)):
                for point in set(square) - set(positive):
                    choices[bit].add(tuple(sorted((*positive, point))))
        alternatives.append(choices)
    require(len(alternatives) == 10, "reference ten cycles")
    profiles = []
    for bits in range(1024):
        profile = set().union(*(choices[(bits // 2**index) % 2]
                                for index, choices in enumerate(alternatives)))
        profile = tuple(sorted(profile))
        check_profile(profile)
        profiles.append(profile)
    require(len(set(profiles)) == 1024, "reference recipes are not distinct")
    return profiles


def audit_profile_certificate(record, seed_profiles=None):
    """Replay all orientation hashes, finite group orbits and explicit maps."""
    body = record["body"]
    canonical = (json.dumps(body, sort_keys=True, separators=(",", ":")) + "\n").encode()
    require(hashlib.sha256(canonical).hexdigest() == record["SHA256"], "certificate body hash")
    require(body["format"] == "clebsch-regular-tournament-orbits-v1", "certificate format")
    require(body["fixed_tournament_order"] == list(range(5)), "fixed tournament changed")
    check_graph({"edges": body["clebsch_edges"], "words": body["vertex_words"]})
    edges, _ = reference_geometry()
    profiles = reference_recipe_profiles()
    index_of = {profile: index for index, profile in enumerate(profiles)}

    def transform(profile, permutation):
        return tuple(sorted(tuple(sorted(permutation[p - 1] for p in triple))
                            for triple in profile))

    actions = [tuple(action["permutation"]) for action in body["actions"]]
    require(len(actions) == len(set(actions)) == 80, "action count or duplicate action")
    for permutation in actions:
        require(sorted(permutation) == list(range(1, 17)), "action is not a point permutation")
        require(all(type(p) is int for p in permutation), "noninteger permutation label")
        require({tuple(sorted(permutation[p - 1] for p in edge)) for edge in edges} == edges,
                "action changes graph")
    action_set = set(actions)
    require(tuple(range(1, 17)) in action_set, "action group lacks identity")
    require(all(tuple(a[b[p] - 1] for p in range(16)) in action_set
                for a in actions for b in actions), "action group is not closed")
    rows = body["profiles"]
    require(len(rows) == 1024, "missing profile record")
    require([row["bits"] for row in rows] == list(range(1024)), "profile bit ordering")
    for profile, row in zip(profiles, rows, strict=True):
        content = "".join(" ".join(map(str, triple)) + "\n" for triple in profile).encode()
        require(hashlib.sha256(content).hexdigest() == row["sha256"], "recipe profile hash")
    orbits = body["orbits"]
    require(len(orbits) == 16, "orbit count")
    seen = set()
    for number, orbit in enumerate(orbits):
        require(orbit["index"] == number, "orbit ordering")
        representative = profiles[orbit["representative_bits"]]
        images = {transform(representative, action) for action in actions}
        require(images <= set(index_of), "profile family not closed")
        members = {index_of[image] for image in images}
        require(orbit["member_bits"] == sorted(members), "orbit membership incomplete")
        require(orbit["size"] == len(members), "wrong orbit size")
        require(not seen & members, "overlapping orbits")
        seen.update(members)
        for bits in members:
            row = rows[bits]
            require(row["orbit"] == number, "wrong profile orbit")
            action = row["action_to_representative"]
            require(type(action) is int and 0 <= action < 80, "invalid map index")
            require(transform(profiles[bits], actions[action]) == representative,
                    "explicit map does not reach representative")
        normalizer = orbit["seed_normalizing_permutation"]
        require(sorted(normalizer) == list(range(1, 17)), "invalid seed normalizer")
        require({tuple(sorted(normalizer[p - 1] for p in edge)) for edge in edges} == edges,
                "seed normalizer changes graph")
        if seed_profiles is not None:
            seeded = seed_profiles[str(orbit["seed"])]
            check_profile(seeded)
            require(transform(seeded, normalizer) in images, "seed normalizer misses orbit")
    require(seen == set(range(1024)), "orbit list does not cover all recipes")
    histogram = dict(sorted(Counter(orbit["size"] for orbit in orbits).items()))
    require(histogram == {16: 4, 80: 12}, "orbit size histogram")
    require(body["counts"] == {"profiles": 1024, "actions": 80, "orbits": 16,
                               "orbit_size_histogram": {"16": 4, "80": 12}}, "count metadata")
    return {"valid": True, "profiles": 1024, "actions": 80, "orbits": 16,
            "orbit_size_histogram": histogram, "seed_maps_checked": seed_profiles is not None,
            "scope": "fixed-tournament recipe under the 80 supplied point actions only",
            "solver_invoked": False, "body_sha256": record["SHA256"]}


def parse_pbtxt(source):
    """Parse only text-protobuf messages, string/int scalars and scalar lists.

    Unsupported tokens and unsupported model fields fail closed. This is not a
    general protobuf parser; its small accepted language is the archived model.
    """
    token_pattern = re.compile(r'\s+|"(?:[^"\\]|\\.)*"|[A-Za-z_]\w*|-?\d+|[{}:\[\],]')
    tokens = []
    end = 0
    for match in token_pattern.finditer(source):
        require(match.start() == end, "unsupported pbtxt syntax")
        token = match.group()
        if not token.isspace():
            tokens.append(token)
        end = match.end()
    require(end == len(source), "trailing unsupported pbtxt syntax")
    position = 0

    def take():
        nonlocal position
        require(position < len(tokens), "truncated pbtxt")
        token = tokens[position]
        position += 1
        return token

    def scalar(token):
        if token.startswith('"'):
            return json.loads(token)
        require(re.fullmatch(r"-?\d+", token) is not None, "unsupported pbtxt scalar")
        return int(token)

    def message(nested=False):
        result = {}
        while position < len(tokens):
            key = take()
            if key == "}":
                require(nested, "unmatched closing message")
                return result
            require(re.fullmatch(r"[A-Za-z_]\w*", key) is not None, "invalid field name")
            delimiter = take()
            if delimiter == "{":
                values = [message(True)]
            else:
                require(delimiter == ":", "missing field delimiter")
                value = take()
                if value == "[":
                    values = []
                    value = take()
                    if value != "]":
                        while True:
                            values.append(scalar(value))
                            value = take()
                            if value == "]":
                                break
                            require(value == ",", "invalid scalar list separator")
                            value = take()
                else:
                    values = [scalar(value)]
            result.setdefault(key, []).extend(values)
        require(not nested, "unclosed pbtxt message")
        return result

    return message()


def expected_rows(profile=None):
    edges, paths = reference_geometry()
    selected_profile = None if profile is None else check_profile(profile)
    blocks = tuple(itertools.combinations(range(1, 17), 5))
    points = {p: [] for p in range(1, 17)}
    pairs = {p: [] for p in itertools.combinations(range(1, 17), 2)}
    triples = {t: [] for t in itertools.combinations(range(1, 17), 3)}
    for index, block in enumerate(blocks):
        for p in block:
            points[p].append(index)
        for p in itertools.combinations(block, 2):
            pairs[p].append(index)
        for t in itertools.combinations(block, 3):
            triples[t].append(index)
    rows = [(list(range(len(blocks))), [64, 64])]
    rows += [(ids, [20, 20]) for ids in points.values()]
    rows += [(ids, [5 + int(pair in edges)] * 2) for pair, ids in pairs.items()]
    for triple, ids in triples.items():
        bounds = (
            [1, 1 + int(triple in paths)]
            if selected_profile is None else [1 + int(triple in selected_profile)] * 2
        )
        rows.append((ids, bounds))
    return rows


def audit_document(document, *, graph=None, profile=None):
    if graph is not None:
        check_graph(graph)
    require(set(document) == {"variables", "constraints"}, "unexpected or missing model field")
    variables = document["variables"]
    require(len(variables) == 4368, "model must contain every lexicographic block variable")
    for index, variable in enumerate(variables):
        require(variable == {"name": [f"block_{index}"], "domain": [0, 1]},
                f"wrong variable name/order/domain at {index}")
    rows = expected_rows(profile)
    require(len(document["constraints"]) == len(rows), "wrong constraint count")
    for number, (constraint, (ids, bounds)) in enumerate(
        zip(document["constraints"], rows, strict=True)
    ):
        require(set(constraint) == {"linear"} and len(constraint["linear"]) == 1,
                f"row {number} has hidden or missing constraint fields")
        row = constraint["linear"][0]
        expected = {"vars": ids, "coeffs": [1] * len(ids), "domain": bounds}
        require(row == expected, f"row {number} differs from independent incidence matrix")
    return {
        "valid": True,
        "scope": "restricted Clebsch model matrix audit, not an infeasibility proof",
        "graph_reference": "four-cube plus antipodal diagonals",
        "variables": 4368,
        "constraints": len(rows),
        "nonzero_coefficients": sum(len(ids) for ids, _ in rows),
        "edges": 40,
        "induced_paths": 160,
        "fixed_excess_profile": profile is not None,
        "solver_invoked": False,
    }


def audit_model(source, *, graph=None, profile=None):
    report = audit_document(parse_pbtxt(source), graph=graph, profile=profile)
    report["model_sha256"] = hashlib.sha256(source.encode()).hexdigest()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--profile", type=Path)
    args = parser.parse_args()
    try:
        graph = None if args.metadata is None else json.loads(args.metadata.read_text())["graph"]
        profile = None if args.profile is None else json.loads(args.profile.read_text())
        report = audit_model(args.model.read_text(), graph=graph, profile=profile)
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(json.dumps({"valid": False, "error": str(error)}))
        return 1
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
