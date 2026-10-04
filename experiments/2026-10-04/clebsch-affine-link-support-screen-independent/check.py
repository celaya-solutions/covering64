# Document:    Independent Affine Link Support Certificate Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c626022595b23d03b0e92cdef9d12002d0616324a9e568c03f19963a8827a4e0
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild all supports with bitsets; no producer imports or solver calls."""

import copy
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "clebsch-affine-link-support-screen"
CONSTRUCTION = HERE.parent / "clebsch-point-link-construction"
PINS = {
    "screen.py": "0a0f33fdb0ca0e9a4b1c31b887fc6adfa0a4ab8491588b1c565cc428817d8bba",
    "cases.json": "03fc4ef1f9e3ad866cb4c2a3f0a2ac9ac78e65a7ca10bad9371ebbd258c3d923",
    "summary.json": "5f4641a4f34f6e5f0f2067ece1dbd949da7d4ebe7e9d65a31f2ede11f8228899",
    "files.json": "3161faf570667f96a9aef3b8632265234379ef42408bc627a09b26e899c71176",
}
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(1, 17), 3))
ROW_ID = {t: i for i, t in enumerate(TRIPLES)}
SUPPORT = [0] * len(TRIPLES)
AVOID_POINT = [0] * 17
for block_id, block in enumerate(BLOCKS):
    for triple in combinations(block, 3):
        SUPPORT[ROW_ID[triple]] |= 1 << block_id
    for point in set(range(1, 17)) - set(block):
        AVOID_POINT[point] |= 1 << block_id


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def canonical(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows)).encode()


def bits(mask):
    values = []
    while mask:
        low = mask & -mask
        values.append(low.bit_length() - 1)
        mask ^= low
    return values


def pool_hash(mask):
    return hashlib.sha256((" ".join(map(str, bits(mask))) + "\n").encode()).hexdigest()


def exact_equal(actual, expected, name):
    # JSON equality preserves booleans/floats instead of accepting them as integers.
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), name)


def supports(active, demand, rows):
    masks = {r: active & SUPPORT[r] for r in rows}
    deficient = [r for r in rows if masks[r].bit_count() < demand[r]]
    tight = [r for r in rows if demand[r] > 0 and masks[r].bit_count() == demand[r]]
    forced, reason = 0, {}
    for r in tight:
        for block in bits(masks[r] & ~forced):
            reason[block] = r
        forced |= masks[r]
    forced_load = {r: (forced & SUPPORT[r]).bit_count() for r in rows}
    conflicts = [r for r in rows if forced_load[r] > demand[r]]
    return masks, deficient, forced, reason, forced_load, conflicts


def replay(link, classes, profiles):
    point = link["point"]
    profile = {tuple(t) for t in profiles[str(link["profile_seed"])]}
    local = [
        tuple(sorted(link["canonical_to_actual"][x - 1] for x in b))
        for b in classes[link["class"]]["canonical_blocks"]
    ]
    partial = sorted(tuple(sorted((point, *b))) for b in local)
    require(
        hashlib.sha256(canonical(partial)).hexdigest() == link["partial_canonical_sha256"],
        "exact pinned partial",
    )
    incidence = Counter(t for b in local for t in combinations(b, 3))
    rows = [r for r, triple in enumerate(TRIPLES) if point not in triple]
    demand = {r: 1 + (TRIPLES[r] in profile) - incidence[TRIPLES[r]] for r in rows}
    require(
        len(rows) == 455 and min(demand.values()) >= 0 and sum(demand.values()) == 440,
        "initial residual equations",
    )
    active = AVOID_POINT[point]
    require(active.bit_count() == 3003, "complete point-avoiding domain")
    for r in rows:
        if demand[r] == 0:
            active &= ~SUPPORT[r]
    initial = supports(active, demand, rows)
    output = {
        key: link[key] for key in ("profile_seed", "point", "class", "partial_canonical_sha256")
    }
    output.update(
        {
            "initial_candidates": active.bit_count(),
            "initial_candidate_ids_sha256": pool_hash(active),
            "initial_deficient_rows": len(initial[1]),
            "initial_forced_blocks": initial[2].bit_count(),
            "initial_forced_conflict_rows": len(initial[5]),
            "rounds": [],
        }
    )
    fixed = 0
    while True:
        require(sum(demand.values()) == 10 * (44 - fixed.bit_count()), "remaining total")
        masks, deficient, forced, reason, forced_load, conflicts = supports(active, demand, rows)
        trace = {
            "active_candidates": active.bit_count(),
            "active_candidate_ids_sha256": pool_hash(active),
            "remaining_blocks": 44 - fixed.bit_count(),
            "remaining_demand_sum": sum(demand.values()),
        }
        output["rounds"].append(trace)

        def forcing(blocks):
            return [
                {
                    "block_id": b,
                    "triple": list(TRIPLES[reason[b]]),
                    "demand": demand[reason[b]],
                    "support_block_ids": bits(masks[reason[b]]),
                }
                for b in blocks
            ]

        if deficient:
            r = min(deficient)
            trace.update(
                {
                    "outcome": "insufficient_support",
                    "triple": list(TRIPLES[r]),
                    "demand": demand[r],
                    "support_block_ids": bits(masks[r]),
                }
            )
            break
        if conflicts:
            r = min(conflicts)
            relevant = bits(forced & SUPPORT[r])
            trace.update(
                {
                    "outcome": "forced_conflict",
                    "triple": list(TRIPLES[r]),
                    "demand": demand[r],
                    "forced_block_ids": relevant,
                    "forcing_rows": forcing(relevant),
                }
            )
            break
        if not forced:
            trace.update(
                {
                    "outcome": "survives_finite_screen",
                    "positive_rows": sum(demand[r] > 0 for r in rows),
                    "minimum_support_slack": min(
                        masks[r].bit_count() - demand[r] for r in rows if demand[r] > 0
                    ),
                }
            )
            break
        forced_ids = bits(forced)
        trace.update(
            {
                "outcome": "propagate_forced_blocks",
                "forced_block_ids": forced_ids,
                "forcing_rows": forcing(forced_ids),
            }
        )
        require(not fixed & forced, "only new forced blocks")
        fixed |= forced
        active &= ~forced
        for r in rows:
            demand[r] -= forced_load[r]
            require(demand[r] >= 0, "propagation nonnegative")
            if demand[r] == 0:
                active &= ~SUPPORT[r]
        require(len(output["rounds"]) <= 44, "finite strictly growing forced set")
    output["outcome"] = output["rounds"][-1]["outcome"]
    output["propagated_blocks"] = bits(fixed)
    return output


def damage_controls(expected):
    rejected = []

    def reject(label, original, changed):
        try:
            exact_equal(changed, original, label)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError("accepted damage " + label)

    support_case = next(r for r in expected if r["outcome"] == "insufficient_support")
    forced_case = next(r for r in expected if r["outcome"] == "forced_conflict")
    propagated = next(r for r in expected if len(r["rounds"]) > 1)
    survivor = next(r for r in expected if r["outcome"] == "survives_finite_screen")
    for key, value in [
        ("initial_candidates", 0),
        ("initial_deficient_rows", False),
        ("initial_candidate_ids_sha256", "0" * 64),
        ("partial_canonical_sha256", "0" * 64),
        ("point", True),
        ("propagated_blocks", [0]),
        ("outcome", "survives_finite_screen"),
    ]:
        changed = copy.deepcopy(support_case)
        changed[key] = value
        reject(key, support_case, changed)
    for key, value in [
        ("demand", 0),
        ("triple", [1, 2, 3]),
        ("support_block_ids", []),
        ("support_block_ids", [1682, 1682]),
    ]:
        changed = copy.deepcopy(support_case)
        changed["rounds"][-1][key] = value
        reject("support_" + key + "_" + str(len(rejected)), support_case, changed)
    changed = copy.deepcopy(forced_case)
    changed["rounds"][-1]["forcing_rows"][0]["support_block_ids"] = []
    reject("forcing_reason_missing_support", forced_case, changed)
    changed = copy.deepcopy(forced_case)
    changed["rounds"][-1]["forcing_rows"][0]["demand"] += 1
    reject("forcing_reason_wrong_demand", forced_case, changed)
    changed = copy.deepcopy(forced_case)
    changed["rounds"][-1]["forced_block_ids"] = []
    reject("missing_forced_conflict", forced_case, changed)
    changed = copy.deepcopy(propagated)
    changed["rounds"] = changed["rounds"][1:]
    reject("missing_propagation_round", propagated, changed)
    changed = copy.deepcopy(survivor)
    changed["rounds"][-1]["minimum_support_slack"] = 0
    reject("false_survival_slack", survivor, changed)
    reject("missing_case", expected, expected[:-1])
    reject("duplicate_case", expected, expected[:-1] + [expected[0]])
    return rejected


def main():
    require(not (HERE / "review.json").exists(), "preserve completed audit")
    for name, value in PINS.items():
        require(sha(PRODUCER / name) == value, "producer pin " + name)
    for name, value in read(PRODUCER / "files.json").items():
        require(sha(PRODUCER / name) == value, "producer index " + name)
    construction_review = HERE.parent / "clebsch-point-link-construction-independent/review.json"
    require(
        sha(construction_review)
        == "980a6894ab489bcdfd729d9c84562ce6f5b268786e88b91339754023312884a9",
        "construction review",
    )
    require(read(construction_review)["passed"] is True, "review passed")
    summary = read(PRODUCER / "summary.json")
    for name, key, digest in [
        (
            "classes.json",
            "construction_classes_sha256",
            "6916b285c1c53693b4f2f53bd0194afd6f2c936e1a10da3a236c5311ab86a2cc",
        ),
        (
            "recipe-point-maps.json",
            "construction_maps_sha256",
            "752b964d5a9de5b05c2f6f453711df12d2da628606ea65c986135583b041a9a2",
        ),
    ]:
        require(sha(CONSTRUCTION / name) == summary[key] == digest, "construction " + name)
    profiles_path = (
        ROOT / "experiments/2026-10-03/independent-geometry/independent-audit-seed-profiles.json"
    )
    require(
        sha(profiles_path)
        == summary["profile_file_sha256"]
        == "4e5ccb1563991e106f2a40e9c8160059eb48d44930bc53d7d4607d44fca208d5",
        "profiles",
    )
    classes = read(CONSTRUCTION / "classes.json")
    links = read(CONSTRUCTION / "recipe-point-maps.json")
    profiles = read(profiles_path)
    require(len(BLOCKS) == 4368 and len(TRIPLES) == 560, "full lex universes")
    require(all(mask.bit_count() == 78 for mask in SUPPORT), "each triple in78 pentads")
    expected = [replay(link, classes, profiles) for link in links]
    cases = read(PRODUCER / "cases.json")
    exact_equal(cases, expected, "all saved rounds and complete supports agree")
    outcomes = dict(Counter(row["outcome"] for row in expected))
    survivors = [
        {key: row[key] for key in ("profile_seed", "point", "class")}
        for row in expected
        if row["outcome"] == "survives_finite_screen"
    ]
    summary_fields = {
        "cases": len(expected),
        "outcomes": outcomes,
        "initial_insufficient_support_cases": sum(
            r["initial_deficient_rows"] > 0 for r in expected
        ),
        "initial_forced_conflict_cases": sum(
            r["initial_forced_conflict_rows"] > 0 for r in expected
        ),
        "initial_rejected_union": sum(
            bool(r["initial_deficient_rows"] or r["initial_forced_conflict_rows"]) for r in expected
        ),
        "initial_candidates_range": [
            min(r["initial_candidates"] for r in expected),
            max(r["initial_candidates"] for r in expected),
        ],
        "maximum_rounds": max(len(r["rounds"]) for r in expected),
        "survivors": survivors,
        "point_one_outcomes": {
            str(r["profile_seed"]): r["outcome"] for r in expected if r["point"] == 1
        },
    }
    for key, value in summary_fields.items():
        exact_equal(summary[key], value, "summary " + key)
    require(
        summary["source_sha256"] == PINS["screen.py"]
        and summary["cases_sha256"] == PINS["cases.json"]
        and summary["solver_calls"] == 0,
        "producer bindings",
    )
    require(
        outcomes
        == {"insufficient_support": 173, "forced_conflict": 76, "survives_finite_screen": 7},
        "terminal outcome count",
    )
    controls = damage_controls(expected)
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "producer_pins": PINS,
        "construction_review_sha256": sha(construction_review),
        "summary_replay": summary_fields,
        "block_universe_count": 4368,
        "complete_initial_domain_count_per_case": 3003,
        "rows_per_case": 455,
        "all_case_count": 256,
        "round_count": sum(len(r["rounds"]) for r in expected),
        "excluded_fixed_partials": 249,
        "surviving_fixed_partials": 7,
        "survival_does_not_establish_feasibility": True,
        "selected_point_one_partials_all_excluded": True,
        "malformed_controls_rejected": controls,
        "source_imported": False,
        "optimizer_calls": 0,
        "scope": (
            "Each exclusion applies only to the exact pinned20-block affine partial and "
            "its fixed recipe. Every point-avoiding pentad was in the initial domain. "
            "Other affine label maps, other local decompositions, unrestricted profiles, "
            "and general64-cover existence remain unresolved."
        ),
    }
    (HERE / "review.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "review_sha256": sha(HERE / "review.json"),
                "outcomes": outcomes,
                "controls": len(controls),
            }
        )
    )


if __name__ == "__main__":
    main()
