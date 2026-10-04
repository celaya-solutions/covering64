# Document:    H6 Anchored Pair Repair Finite Profile
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      422a8c4b64737fb160426059608bce7abf00d0aeaf4b7ba2b26271de7fe7fe11
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Profile one fixed add and its 2016 deletion-pair supports; no optimizer."""

import hashlib
import importlib.util
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
START = DAY / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
START_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
MANIFEST = DAY / "native-h9-h10-reuse-pilot/manifest.json"
MANIFEST_SHA = "13b26e00b3743ad33cbd94553079d1bb60b6fdf43b5f2bc79dd8ceab1c3f9241"
LABELS = range(1, 17)
BLOCKS = list(itertools.combinations(LABELS, 5))
IDS = {block: index for index, block in enumerate(BLOCKS)}
PAIRS = list(itertools.combinations(LABELS, 2))
TRIPLES = list(itertools.combinations(LABELS, 3))
ANCHOR = (4, 5, 6, 10, 12)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")


def profile(blocks, manifest):
    assert blocks == sorted(set(blocks)) and all(block in IDS for block in blocks)
    counts = {
        n: Counter(q for b in blocks for q in itertools.combinations(b, n)) for n in (1, 2, 3, 4)
    }
    holes = [t for t in TRIPLES if counts[3][t] == 0]
    d2max = d2sum = d3 = d4 = 0
    d3_rows = []
    for pair in PAIRS:
        values = {v: counts[3][tuple(sorted((*pair, v)))] for v in LABELS if v not in pair}
        deficits = [
            max(0, 12 - 3 * counts[2][pair] + values[a] + values[b])
            for a, b in itertools.combinations(values, 2)
        ]
        d2max += max(deficits)
        d2sum += sum(deficits)
        for point, count in values.items():
            deficit = max(0, 13 - 3 * counts[2][pair] + count)
            d3 += deficit
            if deficit:
                d3_rows.append(
                    {
                        "pair": pair,
                        "third_point": point,
                        "pair_count": counts[2][pair],
                        "triple_count": count,
                        "deficit": deficit,
                    }
                )
        d4 += sum(
            max(0, 12 - 3 * counts[2][pair] + 2 * counts[4][tuple(sorted((*pair, a, b)))])
            for a, b in itertools.combinations(values, 2)
        )
    ids = [IDS[b] for b in blocks]
    overlaps = [len(set(ids) & set(core)) for core in manifest["core_rows"]]
    overlaps.append(len(set(ids) & set(manifest["sixth_cap"]["ids"])))
    exact64 = len(blocks) == 64
    minpair = min(counts[2][pair] for pair in PAIRS)
    return {
        "ids": ids,
        "cardinality": len(blocks),
        "holes": holes,
        "hole_count": len(holes),
        "pair_histogram": dict(sorted(Counter(counts[2][p] for p in PAIRS).items())),
        "triple_histogram": dict(sorted(Counter(counts[3][t] for t in TRIPLES).items())),
        "point_degrees": {v: counts[1][(v,)] for v in LABELS},
        "underfilled_pairs": [p for p in PAIRS if counts[2][p] < 5],
        "minimum_pair_count": minpair,
        "D2max": d2max,
        "D2sum": d2sum,
        "D3": d3,
        "D4": d4,
        "positive_D3_rows": d3_rows,
        "six_named_overlaps": overlaps,
        "six_named_caps_apply": exact64,
        "six_named_caps_pass": all(a <= b for a, b in zip(overlaps, [55] * 4 + [56, 59]))
        if exact64
        else None,
        "exact64_weak_qualified": exact64 and minpair >= 5 and d3 == d4 == 0,
    }


def main():
    assert not (HERE / "profile.json").exists(), "preserve frozen profile"
    assert sha(START) == START_SHA and sha(MANIFEST) == MANIFEST_SHA
    manifest = json.loads(MANIFEST.read_text())
    spec = importlib.util.spec_from_file_location("standalone_h6", ROOT / "scripts/check_cover.py")
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    start = standalone.parse_witness(START.read_text())
    start = sorted(map(tuple, start))
    assert len(start) == len(set(start)) == 64

    def verify(path, blocks):
        package = verify_cover(blocks)
        separate = standalone.verify_cover(blocks, expected_blocks=len(blocks))
        assert package["canonical_sha256"] == separate["canonical_sha256"] == sha(path)
        assert package["uncovered"] == list(map(tuple, separate["uncovered"]))
        assert package["valid"] == separate["valid"]
        assert separate["cardinality_matches"] and separate["blocks"] == len(blocks)
        return {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha(path),
            "profile": profile(blocks, manifest),
            "package": package,
            "standalone": separate,
        }

    initial = verify(START, start)
    assert initial["profile"]["underfilled_pairs"] == [(4, 6), (5, 6), (10, 12)]
    assert initial["profile"]["hole_count"] == 6
    assert (initial["profile"]["D2max"], initial["profile"]["D3"], initial["profile"]["D4"]) == (
        14,
        80,
        72,
    )
    bad_pairs = initial["profile"]["underfilled_pairs"]
    endpoints = sorted(set().union(*(set(p) for p in bad_pairs)))
    assert tuple(endpoints) == ANCHOR
    all_pair_carriers = [b for b in BLOCKS if all(set(p) <= set(b) for p in bad_pairs)]
    assert all_pair_carriers == [ANCHOR] and ANCHOR not in start
    stage = sorted(start + [ANCHOR])
    stage_path = HERE / "add-only-65.txt"
    stage_path.write_text("".join(" ".join(map(str, b)) + "\n" for b in stage))
    stage_receipt = verify(stage_path, stage)
    stage_metrics = stage_receipt["profile"]
    assert stage_metrics["cardinality"] == 65 and stage_metrics["hole_count"] == 3
    assert (
        stage_metrics["minimum_pair_count"] == 5 and stage_metrics["D3"] == stage_metrics["D4"] == 0
    )
    pair_counts = Counter(p for b in stage for p in itertools.combinations(b, 2))
    one_swap_rows = []
    for block in start:
        losing = [p for p in itertools.combinations(block, 2) if pair_counts[p] == 5]
        assert losing
        one_swap_rows.append({"removed": block, "underfilled_pairs_after_removal": losing})
    assert min(len(row["underfilled_pairs_after_removal"]) for row in one_swap_rows) == 2
    rejections = Counter()
    candidates = []
    supports = []
    for first, second in itertools.combinations(start, 2):
        current = pair_counts.copy()
        for block in (first, second):
            for pair in itertools.combinations(block, 2):
                current[pair] -= 1
        deficient = [pair for pair in PAIRS if current[pair] < 5]
        if any(current[pair] < 4 for pair in PAIRS):
            rejections["deficit_above_one"] += 1
            continue
        needed = sorted(set().union(*(set(pair) for pair in deficient))) if deficient else []
        if len(needed) > 5:
            rejections["support_above_five"] += 1
            continue
        assert len(needed) == 5
        addition = tuple(needed)
        family = sorted((set(start) - {first, second}) | {ANCHOR, addition})
        assert len(family) == 64 and addition not in stage
        support = {
            "removed": [first, second],
            "fixed_addition": ANCHOR,
            "remaining_deficient_pairs": deficient,
            "forced_second_addition": addition,
        }
        supports.append(support)
        path = HERE / f"candidate-{len(candidates) + 1:02d}.txt"
        path.write_text("".join(" ".join(map(str, b)) + "\n" for b in family))
        candidates.append({**support, **verify(path, family)})
    assert len(candidates) == 3
    assert dict(rejections) == {"support_above_five": 1280, "deficit_above_one": 733}
    assert sum(rejections.values()) + len(candidates) == 2016
    assert [
        (
            row["profile"]["hole_count"],
            row["profile"]["D2max"],
            row["profile"]["D2sum"],
            row["profile"]["D3"],
            row["profile"]["D4"],
        )
        for row in candidates
    ] == [(11, 23, 48, 1, 0), (9, 21, 38, 1, 0), (11, 23, 48, 1, 0)]
    receipt = {
        "passed": True,
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "initial_sha256": START_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "initial": initial,
        "unique_all_three_pair_carrier": ANCHOR,
        "unique_carrier_global_id": IDS[ANCHOR],
        "add_only_65_partial": stage_receipt,
        "one_swap_pair_floor_repair_exists": False,
        "one_swap_complete_proof_rows": one_swap_rows,
        "anchored_two_swap_deletion_pairs": 2016,
        "anchored_two_swap_support_rejections": dict(rejections),
        "anchored_two_swap_surviving_supports": supports,
        "anchored_two_swap_candidates": candidates,
        "anchored_two_swap_weak_qualified_count": sum(
            row["profile"]["exact64_weak_qualified"] for row in candidates
        ),
        "package_verifier_sha256": sha(ROOT / "src/covering64/core.py"),
        "standalone_verifier_sha256": sha(ROOT / "scripts/check_cover.py"),
        "optimizer_launches": 0,
        "native_search_calls": 0,
        "scope": "No one-swap pair-floor repair of this initial family. Complete finite "
        "pair-support analysis only for two-swaps containing the fixed B* addition. "
        "No claim about other two-swaps, larger neighborhoods, or global existence. "
        "The 65-block H3 family is partial and is not the complete65 baseline.",
    }
    dump(HERE / "profile.json", receipt)
    print(
        json.dumps(
            {
                "passed": True,
                "profile_sha256": sha(HERE / "profile.json"),
                "anchored_candidates": 3,
                "weak_qualified": 0,
                "optimizer_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
