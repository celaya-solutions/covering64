# Document:    Independent Regular Heavy Hub Bound and Escape Seed Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d9c971414c144b62a0be85ab70d8c290b796e5a7a8b6057aab0e99a173db6ed1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import hashlib
import itertools
import json
import pathlib
import subprocess
import sys

from covering64.core import read_blocks, verify_cover

ROOT = pathlib.Path(__file__).resolve().parent
SEED = pathlib.Path("experiments/2026-10-03/structured-hub-escape/candidate-h9.txt")
OLD = pathlib.Path("experiments/2026-10-03/first-family-independent/normalized-escape-h6.txt")


def require(value, message):
    if not value:
        raise ValueError(message)


def parse(raw):
    blocks = []
    for line in raw.splitlines():
        row = tuple(int(x) for x in line.split())
        require(
            len(row) == 5 and len(set(row)) == 5 and min(row) >= 1 and max(row) <= 16,
            "malformed block",
        )
        blocks.append(tuple(sorted(row)))
    require(len(blocks) == 64 and len(set(blocks)) == 64, "cardinality or duplicate")
    return sorted(blocks)


def inspect(blocks):
    coverage = collections.Counter(t for b in blocks for t in itertools.combinations(b, 3))
    points = collections.Counter(p for b in blocks for p in b)
    profiles = []
    for triple, count in sorted(coverage.items()):
        if count < 6:
            continue
        common = [b for b in blocks if set(triple) <= set(b)]
        pairs = [tuple(p for p in b if p not in triple) for b in common]
        degrees = collections.Counter(p for pair in pairs for p in pair)
        hubs = [p for p in range(1, 17) if degrees[p] >= 2]
        profiles.append(
            dict(
                triple=triple,
                multiplicity=count,
                outside_pairs=pairs,
                outside_degrees={p: degrees[p] for p in range(1, 17) if p not in triple},
                hubs=hubs,
            )
        )
    all_hubs = [p for profile in profiles for p in profile["hubs"]]
    heavy_points = [p for profile in profiles for p in profile["triple"]]
    n6 = sum(p["multiplicity"] == 6 for p in profiles)
    n7 = sum(p["multiplicity"] == 7 for p in profiles)
    h6 = sum(p["multiplicity"] == 6 and bool(p["hubs"]) for p in profiles)
    shape = all(
        (p["multiplicity"] == 7 and sorted(p["outside_degrees"].values()) == [1] * 12 + [2])
        or (
            p["multiplicity"] == 6
            and len(p["hubs"]) <= 1
            and max(p["outside_degrees"].values()) <= 3
        )
        for p in profiles
    )
    regular = list(sorted(points.values())) == [20] * 16
    filters = dict(
        regular=regular,
        maximum_seven=max(coverage.values()) <= 7,
        heavy_disjoint=len(set(heavy_points)) == len(heavy_points),
        link_shapes=shape,
        distinct_hubs=len(set(all_hubs)) == len(all_hubs),
        hubs_outside_heavy=set(all_hubs).isdisjoint(heavy_points),
        refined_count_bound=3 * n6 + 4 * n7 + h6 <= 16,
    )
    return dict(
        profiles=profiles,
        n6=n6,
        n7=n7,
        h6=h6,
        refined_sum=3 * n6 + 4 * n7 + h6,
        filters=filters,
        passes_explicit_filters=all(filters.values()),
        uncovered=[t for t in itertools.combinations(range(1, 17), 3) if coverage[t] == 0],
    )


def partitions(total, length, minimum=0):
    if length == 0:
        if total == 0:
            yield ()
        return
    for first in range(minimum, total // length + 1):
        for rest in partitions(total - first, length - 1, first):
            yield (first, *rest)


def bound_checks():
    profiles_checked = 0
    repeated_profiles = []
    for ab, ac, bc in itertools.product(range(7, 11), repeat=3):
        for repeated in range(14):
            profiles_checked += 1
            budgets = (ab + ac - 10 + repeated, ab + bc - 10 + repeated, ac + bc - 10 + repeated)
            if max(budgets) <= 5 and repeated:
                repeated_profiles.append((ab, ac, bc, repeated))
    require(repeated_profiles == [(7, 7, 7, 1)], "repeated-hub anchor budget")
    require([r for r in range(2, 13) if 12 + 2 * r <= 3 * 6] == [2, 3], "maximum hub multiplicity")
    endpoint_controls = {}
    for mu in (6, 7):
        allowed = []
        for degree in partitions(2 * mu, 13):
            if max(degree) > 3 or sum(d >= 2 for d in degree) > 1:
                continue
            if mu == 7 and min(degree) < 1:
                continue
            allowed.append(degree)
        expected = (
            [
                (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
                (0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2),
                (0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3),
            ]
            if mu == 6
            else [(1,) * 12 + (2,)]
        )
        require(sorted(allowed) == sorted(expected), "endpoint degree patterns")
        endpoint_controls[mu] = allowed
    # Without a repeated hub, budget constraints alone do allow an internal8 edge.
    require(max(8 + 7 - 10, 8 + 7 - 10, 7 + 7 - 10) == 5, "no-hub scope correction")
    return dict(
        anchor_budget_cases=profiles_checked,
        allowed_repeated_anchor_profiles=repeated_profiles,
        endpoint_patterns=endpoint_controls,
        no_hub_internal_eight_budget_control=True,
        hub_pair_excess=3,
        two_hubs_exceed_vertex_budget=6 > 5,
        heavy_point_plus_hub_exceeds_budget=4 + 3 > 5,
    )


def main():
    blocks = parse(SEED.read_text())
    require(blocks == sorted(read_blocks(SEED)), "independent and package parser agreement")
    result = inspect(blocks)
    require(
        result["passes_explicit_filters"] and len(result["uncovered"]) == 9,
        "new seed explicit filters",
    )
    require(
        (result["n6"], result["n7"], result["h6"], result["refined_sum"]) == (1, 3, 0, 15),
        "new seed heavy counts",
    )
    require([p["hubs"] for p in result["profiles"]] == [[4], [], [12], [15]], "new seed hubs")
    previous = parse(OLD.read_text())
    previous_profile = inspect(previous)
    require(not previous_profile["filters"]["distinct_hubs"], "duplicate-hub negative control")
    def local(rows):
        return {b for b in rows if min(b) <= 3}
    require(local(blocks) == local(previous), "fixed local families changed")
    removed = sorted(set(previous) - set(blocks))
    added = sorted(set(blocks) - set(previous))
    require(
        len(removed) == len(added) == 2 and all(min(b) >= 4 for b in removed + added),
        "outside swap form",
    )
    require(
        collections.Counter(p for b in removed for p in b)
        == collections.Counter(p for b in added for p in b),
        "swap degree preservation",
    )
    require(
        any(
            all(len(set(a) & set(b)) == 4 for a, b in zip(removed, order, strict=True))
            for order in itertools.permutations(added)
        ),
        "single point swap form",
    )
    local_triples = {t for b in local(blocks) for t in itertools.combinations(b, 3) if min(t) >= 4}
    absent = [t for t in itertools.combinations(range(4, 17), 3) if t not in local_triples]
    hub_row = [(sum({4, p} <= set(t) for t in absent) + 2) // 3 for p in range(5, 17)]
    require(sum(hub_row) == 25, "fixed-family obstruction")
    package = verify_cover(blocks)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(SEED), "--expected-blocks", "64"],
        text=True,
        capture_output=True,
        check=False,
    )
    standalone = json.loads(process.stdout)
    require(
        process.returncode == 1 and not package["valid"] and not standalone["valid"],
        "partial witness status",
    )
    require(
        [list(t) for t in result["uncovered"]]
        == standalone["uncovered"]
        == [list(t) for t in package["uncovered"]],
        "three hole recounts disagree",
    )
    require(package["canonical_sha256"] == standalone["canonical_sha256"], "checker hash")
    controls = []
    for label, broken in [
        ("duplicate", [*blocks[:-1], blocks[0]]),
        ("repeated label", [(1, 1, 2, 3, 4), *blocks[1:]]),
        ("outside label", [(0, 1, 2, 3, 4), *blocks[1:]]),
    ]:
        raw = "".join(" ".join(map(str, b)) + "\n" for b in broken)
        try:
            parse(raw)
        except ValueError:
            controls.append(dict(control=label, independent_rejected=True))
        else:
            raise ValueError("damaged witness accepted")
        try:
            verify_cover(broken)
        except ValueError:
            controls[-1]["package_rejected"] = True
        else:
            raise ValueError("package accepted damaged witness")
    result.update(
        complete=True,
        package=package,
        standalone=standalone,
        candidate=str(SEED),
        candidate_sha256=hashlib.sha256(SEED.read_bytes()).hexdigest(),
        previous_sha256=hashlib.sha256(OLD.read_bytes()).hexdigest(),
        duplicate_hub_negative_control=previous_profile,
        changed_outside_blocks=dict(removed=removed, added=added),
        local_families_unchanged=True,
        full_completion_hub_row=hub_row,
        full_completion_hub_sum=25,
        full_completion_hub_budget=24,
        bound_controls=bound_checks(),
        damaged_controls=controls,
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        verifier_source_hashes={
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                pathlib.Path("src/covering64/core.py"),
                pathlib.Path("scripts/check_cover.py"),
            ]
        },
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            dict(
                complete=True,
                holes=9,
                n6=1,
                n7=3,
                h6=0,
                refined_sum=15,
                hubs=[4, 12, 15],
                full_completion_hub_sum=25,
            )
        )
    )


if __name__ == "__main__":
    main()
