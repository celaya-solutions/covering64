# Document:    Standalone Heavy-Template Excess-Budget Obstruction Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2feae766210b32a24e03c72260ae1d161e3ad965d16dfba38a98032e02df802f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check all ordinary completions of one uncovered triple with exact counts only."""

import copy
import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANCHORS = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
UNIVERSE = list(it.combinations(range(1, 17), 5))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pair_target(pair):
    anchor_point = next((point for point in pair if point % 4), None)
    require(anchor_point is not None, "hub-only pair cannot use a prescribed target")
    anchor = next(group for group in ANCHORS if anchor_point in group)
    other = next(point for point in pair if point != anchor_point)
    return 7 if other in anchor else 6 if other == max(anchor) + 1 else 5


def validate(data):
    require(data["point_degrees"] == 20, "wrong degree-family assumption")
    heavy = list(map(tuple, data["heavy_blocks"]))
    require(len(heavy) == len(set(heavy)) == 28 and heavy == sorted(heavy), "heavy inventory")
    require(all(block in UNIVERSE for block in heavy), "malformed heavy block")
    reconstructed = set()
    for group in ANCHORS:
        local = [block for block in heavy if group <= set(block)]
        require(len(local) == 7, "incomplete heavy template")
        outside = Counter(point for block in local for point in set(block) - group)
        require(
            outside
            == {
                point: 2 if point == max(group) + 1 else 1
                for point in range(1, 17)
                if point not in group
            },
            "template degrees",
        )
        reconstructed.update(local)
    require(reconstructed == set(heavy), "unclassified heavy block")
    target = tuple(data["uncovered_triple"])
    require(target == (3, 11, 15), "wrong target")
    require(not any(set(target) <= set(block) for block in heavy), "target already covered")
    support = list(map(tuple, data["support_blocks"]))
    require(len(support) == len(set(support)) == 7 and set(support) <= set(heavy), "support set")
    ordinary = [block for block in UNIVERSE if all(len(set(block) & a) <= 1 for a in ANCHORS)]
    require(len(ordinary) == 1200, "ordinary universe")
    candidates = [block for block in ordinary if set(target) <= set(block)]
    require(len(candidates) == data["ordinary_candidate_count"] == 18, "candidate count")
    require(
        [tuple(r["block"]) for r in data["blocked_candidates"]] == candidates,
        "candidate inventory incomplete or duplicate",
    )
    for record, block in zip(data["blocked_candidates"], candidates, strict=True):
        pair = tuple(record["pair"])
        require(pair in list(it.combinations(range(1, 17), 2)), "malformed pair")
        target_count = pair_target(pair)
        require(target_count == record["pair_target"] == 5, "pair target")
        histogram = Counter(triple for b in support + [block] for triple in it.combinations(b, 3))
        terms = [
            [list(t), n] for t, n in sorted(histogram.items()) if set(pair) <= set(t) and n > 1
        ]
        excess = sum(n - 1 for t, n in terms)
        require(terms == record["excess_triples"], "excess terms")
        require(excess == record["partial_excess"], "excess claim")
        budget = 3 * target_count - 14
        require(budget == record["excess_budget"] == 1 and excess > budget, "no obstruction")
    return {
        "heavy_blocks": 28,
        "support_blocks": 7,
        "target": list(target),
        "ordinary_blocks": 1200,
        "blocked_candidates": 18,
    }


def main():
    data = json.loads((HERE / "heavy-obstruction.json").read_text())
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(data["manifest_sha256"] == sha(HERE / "manifest.json"), "manifest changed")
    require(data["heavy_blocks"] == manifest["fixed_blocks"], "fixed tuple changed")
    result = validate(data)
    controls = []
    mutations = [
        ("wrong degree", lambda d: d.update(point_degrees=21)),
        ("missing candidate", lambda d: d["blocked_candidates"].pop()),
        (
            "duplicate candidate",
            lambda d: d["blocked_candidates"].__setitem__(1, d["blocked_candidates"][0]),
        ),
        ("missing support", lambda d: d["support_blocks"].pop()),
        ("hub-only pair", lambda d: d["blocked_candidates"][0].update(pair=[4, 8])),
        ("wrong pair target", lambda d: d["blocked_candidates"][0].update(pair_target=6)),
        ("wrong excess", lambda d: d["blocked_candidates"][0].update(partial_excess=1)),
        ("damaged heavy block", lambda d: d["heavy_blocks"][0].__setitem__(4, 12)),
    ]
    for label, mutation in mutations:
        damaged = copy.deepcopy(data)
        mutation(damaged)
        try:
            validate(damaged)
        except ValueError:
            controls.append({"control": label, "rejected": True})
        else:
            raise ValueError("damaged certificate accepted: " + label)
    result.update(
        passed=True,
        checker_sha256=sha(Path(__file__)),
        certificate_sha256=sha(HERE / "heavy-obstruction.json"),
        manifest_sha256=sha(HERE / "manifest.json"),
        damaged_controls=controls,
        scope="One native degree20 heavy tuple only. Every candidate for one missing "
        "triple exceeds a proved anchor-pair excess budget. No solver or hub-pair assumption.",
    )
    (HERE / "heavy-obstruction-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
