# Document:    H6 Anchored Pair Repair Independent Finite Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      31b08f225622dc8cff7450aa3f21b510ad4e04f234d553d6c45f8934b8c8d331
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independently enumerate pair supports; do not import or run producer code."""

import copy
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from covering64.core import verify_cover

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "h6-anchored-pair-repair"
INITIAL = HERE.parent / "native-h9-h10-reuse-pilot/seed-2026105901/search-final-raw64.txt"
INITIAL_SHA = "2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855"
PROFILE_SHA = "4f7163a2648c9dd72e7e98b0b341bb76108c288e14ff50631ffe3b173e47eeea"
SOURCE_SHA = "f008968d2afe25bc8f93aeb8376013bb7fc6cee1f86ab1f669865283395b82dc"
MANIFEST_SHA = "13b26e00b3743ad33cbd94553079d1bb60b6fdf43b5f2bc79dd8ceab1c3f9241"
POINTS = tuple(range(1, 17))
PAIRS = tuple(itertools.combinations(POINTS, 2))
TRIPLES = tuple(itertools.combinations(POINTS, 3))
UNIVERSE = tuple(itertools.combinations(POINTS, 5))
RANK = {block: index for index, block in enumerate(UNIVERSE)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    return json.loads(json.dumps(value))


def canonical(blocks):
    return "".join(" ".join(map(str, block)) + "\n" for block in sorted(blocks)).encode()


def recount(blocks, cores):
    assert len(blocks) == len(set(blocks))
    assert all(block in RANK for block in blocks)
    counts = {
        size: Counter(part for block in blocks for part in itertools.combinations(block, size))
        for size in (2, 3, 4)
    }
    d2max = d2sum = d3 = d4 = 0
    positive = []
    for pair in PAIRS:
        lam = counts[2][pair]
        outside = tuple(p for p in POINTS if p not in pair)
        third = {p: counts[3][tuple(sorted((*pair, p)))] for p in outside}
        assert sum(third.values()) == 3 * lam
        for point in outside:
            deficit = max(0, 13 - 3 * lam + third[point])
            d3 += deficit
            if deficit:
                positive.append(
                    {
                        "pair": list(pair),
                        "pair_count": lam,
                        "third_point": point,
                        "triple_count": third[point],
                        "deficit": deficit,
                    }
                )
        rows = []
        for a, b in itertools.combinations(outside, 2):
            rows.append(max(0, 12 - 3 * lam + third[a] + third[b]))
            d4 += max(0, 12 - 3 * lam + 2 * counts[4][tuple(sorted((*pair, a, b)))])
        d2max += max(rows)
        d2sum += sum(rows)
    ids = sorted(RANK[block] for block in blocks)
    overlaps = [len(set(ids) & set(core)) for core in cores]
    caps = all(a <= b for a, b in zip(overlaps, [55] * 4 + [56, 59]))
    holes = [list(t) for t in TRIPLES if counts[3][t] == 0]
    floor = min(counts[2][pair] for pair in PAIRS)
    return normalized(
        {
            "ids": ids,
            "cardinality": len(blocks),
            "hole_count": len(holes),
            "holes": holes,
            "minimum_pair_count": floor,
            "underfilled_pairs": [p for p in PAIRS if counts[2][p] < 5],
            "point_degrees": {p: sum(p in block for block in blocks) for p in POINTS},
            "pair_histogram": dict(Counter(counts[2][p] for p in PAIRS)),
            "triple_histogram": dict(Counter(counts[3][t] for t in TRIPLES)),
            "D2max": d2max,
            "D2sum": d2sum,
            "D3": d3,
            "D4": d4,
            "positive_D3_rows": positive,
            "six_named_overlaps": overlaps,
            "six_named_caps_apply": len(blocks) == 64,
            "six_named_caps_pass": caps if len(blocks) == 64 else None,
            "exact64_weak_qualified": len(blocks) == 64 and caps and floor >= 5 and d3 == d4 == 0,
        }
    )


def main():
    assert sha(INITIAL) == INITIAL_SHA
    assert sha(PRODUCER / "profile.json") == PROFILE_SHA
    assert sha(PRODUCER / "check.py") == SOURCE_SHA
    manifest_path = HERE.parent / "native-h9-h10-reuse-pilot/manifest.json"
    assert sha(manifest_path) == MANIFEST_SHA
    assert sha(ROOT / "src/covering64/core.py") == (
        "3b49b76a0fe243efe8bbba5fdc0887b754e7e3cd24c177dfc7531c2036f22beb"
    )
    standalone_path = ROOT / "scripts/check_cover.py"
    assert sha(standalone_path) == (
        "755fecdc6978f94afa7bbaad299fc55bcfd4d4afe831951bdc70d1e81698e950"
    )
    spec = importlib.util.spec_from_file_location("standalone_pair_repair", standalone_path)
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    manifest = json.loads(manifest_path.read_text())
    cores = manifest["core_rows"] + [manifest["sixth_cap"]["ids"]]
    family = tuple(tuple(map(int, line.split())) for line in INITIAL.read_text().splitlines())
    assert len(family) == len(set(family)) == 64 and INITIAL.read_bytes() == canonical(family)
    counts = Counter(pair for block in family for pair in itertools.combinations(block, 2))
    deficits = [pair for pair in PAIRS if counts[pair] < 5]
    assert deficits == [(4, 6), (5, 6), (10, 12)]
    carrier = tuple(sorted(set().union(*map(set, deficits))))
    assert len(carrier) == 5 and carrier not in family
    carriers = [block for block in UNIVERSE if all(set(p) <= set(block) for p in deficits)]
    assert carriers == [carrier]
    base = counts.copy()
    base.update(itertools.combinations(carrier, 2))
    one_rows = []
    for block in family:
        residual = base.copy()
        residual.subtract(itertools.combinations(block, 2))
        under = [pair for pair in PAIRS if residual[pair] < 5]
        assert under
        one_rows.append({"removed": block, "underfilled_pairs_after_removal": under})
    rejects = Counter()
    supports = []
    witnesses = []
    for dropped in itertools.combinations(family, 2):
        residual = base.copy()
        for block in dropped:
            residual.subtract(itertools.combinations(block, 2))
        if min(residual[p] for p in PAIRS) < 4:
            rejects["deficit_above_one"] += 1
            continue
        under = [pair for pair in PAIRS if residual[pair] < 5]
        forced = set().union(*map(set, under)) if under else set()
        if len(forced) > 5:
            rejects["support_above_five"] += 1
            continue
        assert len(forced) == 5
        addition = tuple(sorted(forced))
        assert addition not in family and addition != carrier
        blocks = tuple(sorted((set(family) - set(dropped)) | {carrier, addition}))
        row = {
            "removed": dropped,
            "fixed_addition": carrier,
            "forced_second_addition": addition,
            "remaining_deficient_pairs": under,
        }
        supports.append(row)
        witnesses.append(blocks)
    assert len(one_rows) == 64
    assert dict(rejects) == {"support_above_five": 1280, "deficit_above_one": 733}
    assert len(supports) == len(witnesses) == 3
    assert sum(rejects.values()) + len(supports) == 2016

    def record(path, blocks):
        assert path.read_bytes() == canonical(blocks)
        package = verify_cover(blocks)
        external = standalone.verify_cover(blocks, expected_blocks=len(blocks))
        actual = recount(blocks, cores)
        assert package["valid"] == external["valid"] == (actual["hole_count"] == 0)
        assert package["canonical_sha256"] == external["canonical_sha256"] == sha(path)
        assert sorted(map(tuple, package["uncovered"])) == sorted(map(tuple, external["uncovered"]))
        return normalized(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "profile": actual,
                "package": package,
                "standalone": external,
            }
        )

    candidates = []
    for index, (support, blocks) in enumerate(zip(supports, witnesses), 1):
        row = record(PRODUCER / f"candidate-{index:02}.txt", blocks)
        row.update(normalized(support))
        assert row["profile"]["minimum_pair_count"] == 5
        assert row["profile"]["D3"] == 1 and row["profile"]["D4"] == 0
        candidates.append(row)
    expected = normalized(
        {
            "passed": True,
            "initial_sha256": INITIAL_SHA,
            "manifest_sha256": MANIFEST_SHA,
            "source_sha256": SOURCE_SHA,
            "initial": record(INITIAL, family),
            "unique_all_three_pair_carrier": carrier,
            "unique_carrier_global_id": RANK[carrier],
            "add_only_65_partial": record(PRODUCER / "add-only-65.txt", (*family, carrier)),
            "one_swap_complete_proof_rows": one_rows,
            "one_swap_pair_floor_repair_exists": False,
            "anchored_two_swap_deletion_pairs": 2016,
            "anchored_two_swap_support_rejections": dict(rejects),
            "anchored_two_swap_surviving_supports": supports,
            "anchored_two_swap_candidates": candidates,
            "anchored_two_swap_weak_qualified_count": 0,
            "optimizer_launches": 0,
            "native_search_calls": 0,
            "package_verifier_sha256": sha(ROOT / "src/covering64/core.py"),
            "standalone_verifier_sha256": sha(standalone_path),
        }
    )
    producer = json.loads((PRODUCER / "profile.json").read_text())

    def compare(data):
        for key, value in expected.items():
            assert data[key] == value, key

    compare(producer)
    controls = []
    mutations = [
        ("missing_one_drop", lambda d: d["one_swap_complete_proof_rows"].pop()),
        ("missing_candidate", lambda d: d["anchored_two_swap_candidates"].pop()),
        ("duplicate_candidate", lambda d: d["anchored_two_swap_candidates"].append(candidates[0])),
        ("wrong_carrier", lambda d: d["unique_all_three_pair_carrier"].__setitem__(0, 1)),
        ("wrong_carrier_id", lambda d: d.__setitem__("unique_carrier_global_id", 0)),
        (
            "false_one_swap_claim",
            lambda d: d.__setitem__("one_swap_pair_floor_repair_exists", True),
        ),
        ("wrong_pair_count", lambda d: d.__setitem__("anchored_two_swap_deletion_pairs", 2015)),
        (
            "wrong_support_count",
            lambda d: d["anchored_two_swap_support_rejections"].__setitem__(
                "support_above_five", 1279
            ),
        ),
        ("wrong_weak_count", lambda d: d.__setitem__("anchored_two_swap_weak_qualified_count", 1)),
        (
            "non64_cap_verdict",
            lambda d: d["add_only_65_partial"]["profile"].__setitem__("six_named_caps_pass", True),
        ),
        (
            "damaged_candidate_D3",
            lambda d: d["anchored_two_swap_candidates"][1]["profile"].__setitem__("D3", 0),
        ),
        (
            "damaged_candidate_holes",
            lambda d: d["anchored_two_swap_candidates"][1]["profile"].__setitem__("hole_count", 0),
        ),
    ]
    for name, mutate in mutations:
        damaged = copy.deepcopy(producer)
        mutate(damaged)
        try:
            compare(damaged)
        except AssertionError:
            controls.append(name)
        else:
            raise AssertionError(f"damage control accepted: {name}")
    output = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "producer_profile_sha256": PROFILE_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "initial_sha256": INITIAL_SHA,
        "independently_recomputed_fields": sorted(expected),
        "rejected_damage_controls": controls,
        "one_swap_checked": 64,
        "anchored_two_swap_deletion_pairs_checked": 2016,
        "support_rejections": dict(rejects),
        "surviving_supports": normalized(supports),
        "families": [expected["initial"], expected["add_only_65_partial"], *candidates],
        "weak_qualified_candidates": 0,
        "optimizer_launches": 0,
        "native_search_calls": 0,
        "scope": (
            "No one-swap pair-floor repair. Exactly three B*-anchored exact two-swap "
            "pair-floor repairs, all failing D3. Unanchored two-swaps not excluded. "
            "The 65-block H3 family is partial. No global existence conclusion."
        ),
    }
    target = HERE / "review.json"
    assert not target.exists(), "preserve independent review receipt"
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    assert target.stat().st_size < 1_000_000
    print(
        json.dumps({"passed": True, "review_sha256": sha(target), "damage_controls": len(controls)})
    )


if __name__ == "__main__":
    main()
