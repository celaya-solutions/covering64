# Document:    Independent Four-Sevenfold First-Link Orbit Certificate Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e9ceae9848e28a2a9cf65738f28842dba5eb805b96723d7c560678fd969f1012
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import copy
import gzip
import hashlib
import itertools
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
ANCHORS = ((1, 2, 3), (5, 6, 7), (9, 10, 11), (13, 14, 15))
HUBS = (4, 8, 12, 16)
IDENTITY = tuple(range(1, 17))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normal_link(edges):
    require(len(edges) == 7, "wrong edge cardinality")
    require(
        all(
            len(e) == 2 and all(type(p) is int for p in e) and 4 <= e[0] < e[1] <= 16 for e in edges
        ),
        "malformed edge",
    )
    link = tuple(tuple(e) for e in edges)
    require(link == tuple(sorted(set(link))), "unsorted or duplicate edge")
    degrees = collections.Counter(p for e in link for p in e)
    require(all(degrees[p] == (2 if p == 4 else 1) for p in range(4, 17)), "wrong degrees")
    require(
        all(not set(e) <= set(a) for e in link for a in ANCHORS[1:]),
        "forbidden internal anchor edge",
    )
    return link


def all_pairings(points):
    if not points:
        yield ()
    else:
        first, *tail = points
        for second in tail:
            others = tuple(p for p in tail if p != second)
            for suffix in all_pairings(others):
                yield ((first, second), *suffix)


def independently_enumerate():
    # Enumerate all 62,370 unfiltered degree patterns, then reject forbidden edges.
    links = set()
    raw_count = 0
    forbidden = {e for a in ANCHORS[1:] for e in itertools.combinations(a, 2)}
    for leaves in itertools.combinations(range(5, 17), 2):
        rest = tuple(p for p in range(5, 17) if p not in leaves)
        for pairs in all_pairings(rest):
            raw_count += 1
            edges = tuple(sorted(((4, leaves[0]), (4, leaves[1]), *pairs)))
            if not forbidden.intersection(edges):
                links.add(normal_link(edges))
    terms = []
    for j in range(4):
        double_factorial = math.prod(range(1, 10 - 2 * j, 2))
        terms.append(
            (-1) ** j * math.comb(3, j) * 3**j * math.comb(12 - 2 * j, 2) * double_factorial
        )
    require(raw_count == 62370 and terms == [62370, -42525, 11340, -1215], "count formula")
    require(len(links) == sum(terms) == 29970, "link completeness")
    return links, terms


def hub_weight(case, i, j):
    pair = frozenset((i, j))
    if case == "cycle":
        return 1 if pair in [frozenset(e) for e in ((0, 1), (1, 2), (2, 3), (0, 3))] else 0
    return 2 if pair in [frozenset((0, 1)), frozenset((2, 3))] else 0


def pair_targets(case):
    targets = dict.fromkeys(itertools.combinations(range(1, 17), 2), 5)
    for anchors, hub in zip(ANCHORS, HUBS, strict=True):
        for edge in itertools.combinations(anchors, 2):
            targets[edge] = 7
        for point in anchors:
            targets[tuple(sorted((point, hub)))] = 6
    for i, j in itertools.combinations(range(4), 2):
        targets[(HUBS[i], HUBS[j])] += hub_weight(case, i, j)
    return targets


def build_group(case):
    # Exhaust all 24 group permutations; derive the stabilizer from weighted edges.
    group_perms = [
        g
        for g in itertools.permutations(range(4))
        if g[0] == 0
        and all(
            hub_weight(case, i, j) == hub_weight(case, g[i], g[j])
            for i, j in itertools.combinations(range(4), 2)
        )
    ]
    require(len(group_perms) == 2, "hub stabilizer order")
    perms = set()
    offsets = list(itertools.permutations(range(3)))
    for groups in group_perms:
        for choices in itertools.product(offsets, repeat=3):
            mapping = list(IDENTITY)
            for source in range(1, 4):
                for offset, target_offset in enumerate(choices[source - 1]):
                    mapping[4 * source + offset] = 4 * groups[source] + target_offset + 1
                mapping[4 * source + 3] = HUBS[groups[source]]
            perms.add(tuple(mapping))
    require(len(perms) == 432, "full group order")
    targets = pair_targets(case)
    for perm in perms:
        require(tuple(sorted(perm)) == IDENTITY and perm[:4] == (1, 2, 3, 4), "invalid permutation")
        require(
            {tuple(sorted(perm[p - 1] for p in a)) for a in ANCHORS} == set(ANCHORS),
            "anchor partition not preserved",
        )
        require(
            all(
                targets[tuple(sorted((perm[a - 1], perm[b - 1])))] == value
                for (a, b), value in targets.items()
            ),
            "pair labels not preserved",
        )
        inverse = tuple(perm.index(p) + 1 for p in IDENTITY)
        require(inverse in perms, "inverse missing")
    # Exhaustively establish closure, separately from the structural construction.
    require(
        all(tuple(a[p - 1] for p in b) in perms for a in perms for b in perms), "group not closed"
    )
    return perms, group_perms


def image(link, perm):
    return tuple(sorted(tuple(sorted((perm[a - 1], perm[b - 1]))) for a, b in link))


def expected_orbits(representatives, permutations, all_links):
    expected = {}
    seen = set()
    for representative in representatives:
        link = normal_link(representative["edges"])
        orbit = {image(link, perm) for perm in permutations}
        require(link == min(orbit), "representative is not canonical")
        require(not seen.intersection(orbit), "independent orbits overlap")
        require(orbit <= all_links, "orbit outside full link space")
        require(representative["orbit_size"] == len(orbit), "orbit size mismatch")
        require(representative["id"] not in expected, "duplicate representative id")
        expected[representative["id"]] = orbit
        seen.update(orbit)
    require(seen == all_links and len(expected) == 129, "orbit completeness")
    return expected


def validate_certificate(case_result, certificate, expected, permutations, all_links):
    case = case_result["case"]
    require(certificate["case"] == case, "certificate case mismatch")
    require(case_result["labeled_families"] == len(all_links), "claimed family count")
    reps = {r["id"]: normal_link(r["edges"]) for r in case_result["representatives"]}
    require(set(reps) == set(expected), "representative set mismatch")
    seen_ids = set()
    seen_links = set()
    mapped_count = 0
    for record in certificate["orbits"]:
        identifier = record["id"]
        require(identifier in expected and identifier not in seen_ids, "bad orbit id")
        seen_ids.add(identifier)
        sources = set()
        for item in record["maps"]:
            link = normal_link(item["edges"])
            require(link not in sources, "duplicate mapped family")
            sources.add(link)
            perm = tuple(item["from_representative"])
            require(perm in permutations, "mapping outside allowed group")
            require(image(reps[identifier], perm) == link, "incorrect forward map")
            inverse = tuple(perm.index(p) + 1 for p in IDENTITY)
            require(image(link, inverse) == reps[identifier], "incorrect inverse map")
            mapped_count += 1
        require(sources == expected[identifier], "missing or extra orbit member")
        require(not seen_links.intersection(sources), "overlapping archived orbits")
        seen_links.update(sources)
    require(seen_ids == set(expected) and seen_links == all_links, "incomplete archive")
    sizes = collections.Counter(len(orbit) for orbit in expected.values())
    require(
        {str(k): v for k, v in sizes.items()} == case_result["orbit_size_counts"],
        "orbit size histogram mismatch",
    )
    require(mapped_count == 29970, "mapping count")
    return mapped_count


def main():
    raw = ROOT / "relabelings.json.gz"
    metadata = json.loads((ROOT / "result.json").read_text())
    certificates = json.loads(gzip.decompress(raw.read_bytes()))
    require(digest(raw) == metadata["relabelings_sha256"], "archive hash")
    require(digest(ROOT / "source.py") == metadata["source_sha256"], "source snapshot hash")
    require([r["case"] for r in metadata["cases"]] == ["cycle", "matching"], "case list")
    require([r["case"] for r in certificates] == ["cycle", "matching"], "certificate list")
    links, terms = independently_enumerate()
    results = []
    for case_result, certificate in zip(metadata["cases"], certificates, strict=True):
        case = case_result["case"]
        permutations, group_perms = build_group(case)
        expected = expected_orbits(case_result["representatives"], permutations, links)
        mapped = validate_certificate(case_result, certificate, expected, permutations, links)
        controls = []

        def reject(name, result_copy, certificate_copy):
            try:
                validate_certificate(result_copy, certificate_copy, expected, permutations, links)
            except (ValueError, KeyError):
                controls.append({"control": name, "rejected": True})
            else:
                raise ValueError("damaged certificate accepted: " + name)

        broken = copy.deepcopy(certificate)
        broken["orbits"][0]["maps"][0]["edges"][0] = [4, 4]
        reject("repeated endpoint", case_result, broken)
        broken = copy.deepcopy(certificate)
        broken["orbits"][0]["maps"][0]["from_representative"] = list(reversed(IDENTITY))
        reject("mapping moves first anchor group", case_result, broken)
        broken = copy.deepcopy(certificate)
        broken["orbits"][0]["maps"].pop()
        reject("missing family", case_result, broken)
        broken = copy.deepcopy(certificate)
        broken["orbits"][0]["maps"].append(broken["orbits"][0]["maps"][0])
        reject("duplicate family", case_result, broken)
        broken = copy.deepcopy(certificate)
        broken["orbits"].pop()
        reject("missing orbit", case_result, broken)
        broken = copy.deepcopy(certificate)
        broken["orbits"][0]["maps"][0]["from_representative"] = list(
            next(
                p
                for p in permutations
                if image(case_result["representatives"][0]["edges"], p)
                != normal_link(broken["orbits"][0]["maps"][0]["edges"])
            )
        )
        reject("valid permutation with wrong image", case_result, broken)
        broken_result = copy.deepcopy(case_result)
        broken_result["labeled_families"] -= 1
        reject("incorrect completeness count", broken_result, certificate)
        broken_result = copy.deepcopy(case_result)
        broken_result["orbit_size_counts"]["432"] -= 1
        reject("incorrect size histogram", broken_result, certificate)
        results.append(
            dict(
                case=case,
                complete=True,
                labeled_families=len(links),
                independent_orbits=len(expected),
                explicit_maps_checked=mapped,
                group_order=len(permutations),
                hub_stabilizer=group_perms,
                pair_targets_checked_per_permutation=120,
                orbit_size_counts=case_result["orbit_size_counts"],
                damaged_controls=controls,
            )
        )
        print(
            json.dumps({k: v for k, v in results[-1].items() if k != "damaged_controls"}),
            flush=True,
        )
    result = dict(
        complete=True,
        checker_sha256=digest(pathlib.Path(__file__)),
        source_snapshot_sha256=digest(ROOT / "source.py"),
        archive_sha256=digest(raw),
        metadata_sha256=digest(ROOT / "result.json"),
        inclusion_exclusion_terms=terms,
        unfiltered_degree_patterns=62370,
        cases=results,
        scope="Complete label quotient of first heavy links in the "
        "regular four-sevenfold branch. No cover invariance is assumed; "
        "no covering existence or nonexistence claim.",
    )
    (ROOT / "independent-result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
