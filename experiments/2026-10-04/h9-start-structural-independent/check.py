# Document:    Independent H9 Radius Four Certificate Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      c87bb113e81df70d115699f73628fe1aa6b30fdaf77a47fb0f85b1ba8fd9862d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount the finite certificate without importing its producer or any solver."""

import copy
import hashlib
import json
from collections import Counter
from itertools import combinations, combinations_with_replacement
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P = HERE.parent / "h9-start-structural-profile"
MANIFEST = HERE.parent / "weak-pair-h9-d23-neutral-queue/manifest.json"
PROFILE_SHA = "317797810b797e341ce62992334a8816e46e9051d33d41ab60c8078e0ee15d38"
UNIVERSE = list(combinations(range(1, 17), 5))
INDEX = {b: i for i, b in enumerate(UNIVERSE)}
TRIPLES = list(combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def same(a, b):
    """JSON text comparison also distinguishes Boolean and integer fields."""
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def parse_family(text):
    rows = [tuple(map(int, line.split())) for line in text.splitlines()]
    assert len(rows) == len(set(rows)) == 64
    assert rows == sorted(rows) and all(b in INDEX for b in rows)
    assert text == "".join(" ".join(map(str, b)) + "\n" for b in rows)
    return rows


def recount(family, manifest):
    mu = Counter(t for b in family for t in combinations(b, 3))
    holes = [t for t in TRIPLES if not mu[t]]
    holes_index = {t: i for i, t in enumerate(holes)}
    masks = [
        sum(1 << holes_index[t] for t in combinations(b, 3) if t in holes_index) for b in UNIVERSE
    ]
    patterns = sorted(set(masks))
    dp = {0}
    layers = []
    for depth in range(5):
        layers.append(
            {
                "at_most_blocks": depth,
                "masks": sorted(dp),
                "maximum_holes_covered": max(m.bit_count() for m in dp),
            }
        )
        dp = {a | b for a in dp for b in patterns}
    assert len(holes) == 9 and max(mu.values()) == 3
    assert layers[3]["maximum_holes_covered"] == 7
    assert (1 << 9) - 1 not in layers[3]["masks"]
    assert (1 << 9) - 1 in layers[4]["masks"]
    assert (
        max((a | b | c).bit_count() for a, b, c in combinations_with_replacement(patterns, 3)) == 7
    )

    def carrier_row(i):
        return {
            "id": i,
            "block": list(UNIVERSE[i]),
            "hole_mask": masks[i],
            "hole_count": masks[i].bit_count(),
        }

    adders = [i for i, mask in enumerate(masks) if mask.bit_count() >= 2]
    triples_in_adders = {t for i in adders for t in combinations(UNIVERSE[i], 3)}
    private = []
    forced = []
    for b in family:
        triples = [t for t in combinations(b, 3) if mu[t] == 1]
        protected = [t for t in triples if t not in triples_in_adders]
        private.append(
            {
                "id": INDEX[b],
                "block": list(b),
                "private_count": len(triples),
                "private_triples": [list(t) for t in triples],
                "unrestorable_private_triples": [list(t) for t in protected],
            }
        )
        if protected:
            forced.append({"id": INDEX[b], "block": list(b), "private_witness": list(protected[0])})
    assert len(adders) == 47 and len(forced) == 63
    assert len(forced) + 4 == 67 > 64
    three = [i for i, mask in enumerate(masks) if mask.bit_count() == 3]
    common = set(holes)
    for i in three:
        common &= set(combinations(UNIVERSE[i], 3))
    assert common == {(5, 9, 15)}

    core_proofs = []
    for index, ids in enumerate(manifest["core_rows"]):
        assert len(ids) == len(set(ids)) == 60
        counts = Counter(t for i in ids for t in combinations(UNIVERSE[i], 3))
        heavy = sorted(t for t in TRIPLES if counts[t] == 6)
        supports = [{i for i in ids if set(t) <= set(UNIVERSE[i])} for t in heavy]
        assert len(heavy) == 5 and all(len(s) == 6 for s in supports)
        assert all(not (a & b) for a, b in combinations(supports, 2))
        assert len(set().union(*supports)) == 30
        core_proofs.append(
            {
                "core_index": index,
                "core_ids": ids,
                "heavy_triples": [{"triple": list(t), "core_multiplicity": 6} for t in heavy],
                "heavy_carrier_sets_disjoint": True,
                "minimum_missing_core_blocks_every_relabeling": 5 * (6 - max(mu.values())),
                "maximum_overlap_every_relabeling": 60 - 5 * (6 - max(mu.values())),
            }
        )

    pair_mu = Counter(pair for b in family for pair in combinations(b, 2))
    point_profiles = []
    links19 = []
    for point in range(1, 17):
        links = [tuple(x for x in b if x != point) for b in family if point in b]
        pair_counts = Counter(pair for b in links for pair in combinations(b, 2))
        others = [p for p in range(1, 17) if p != point]
        point_holes = [t for t in holes if point in t]
        point_profiles.append(
            {
                "point": point,
                "degree": len(links),
                "holes": len(point_holes),
                "link_excess_above_one": sum(
                    max(0, pair_counts[p] - 1) for p in combinations(others, 2)
                ),
            }
        )
        if len(links) == 19:
            links19.append(
                {
                    "point": point,
                    "degree": 19,
                    "blocks": [list(b) for b in links],
                    "hole_triples": [list(t) for t in point_holes],
                    "neighbor_replication": {str(q): sum(q in b for b in links) for q in others},
                    "pair_multiplicity_histogram": {
                        str(k): v
                        for k, v in Counter(pair_counts[p] for p in combinations(others, 2)).items()
                    },
                }
            )
    return {
        "initial_ids": [INDEX[b] for b in family],
        "holes": [list(t) for t in holes],
        "triple_multiplicities": {str(k): v for k, v in Counter(mu[t] for t in TRIPLES).items()},
        "pair_multiplicities": {
            str(k): v for k, v in Counter(pair_mu[p] for p in combinations(range(1, 17), 2)).items()
        },
        "carrier_histogram": {str(k): v for k, v in Counter(m.bit_count() for m in masks).items()},
        "hole_pair_intersection_histogram": {
            str(k): v
            for k, v in Counter(len(set(a) & set(b)) for a, b in combinations(holes, 2)).items()
        },
        "hole_mask_patterns": patterns,
        "mask_dp_layers": layers,
        "all_three_hole_carriers": [carrier_row(i) for i in three],
        "three_hole_carrier_common_hole": list(next(iter(common))),
        "minimum_blocks_covering_original_holes_only": 4,
        "radius_four_adders": [carrier_row(i) for i in adders],
        "radius_four_adder_union_triples": [list(t) for t in sorted(triples_in_adders)],
        "original_private_triples": private,
        "forced_original_blocks": forced,
        "forced_original_count": len(forced),
        "potentially_removable_originals": [
            p for p in private if not p["unrestorable_private_triples"]
        ],
        "radius_four_excluded": True,
        "exact64_minimum_blocks_outside_named_initial_family": 5,
        "exact64_maximum_overlap_with_named_initial_family": 59,
        "old_core_all_relabel_overlap_proofs": core_proofs,
        "point_profiles": point_profiles,
        "degree19_links": links19,
    }, masks


def validate(profile, expected, masks):
    for key, value in expected.items():
        same(profile[key], value)
    witness = profile["hole_only_four_block_witness"]
    assert len(witness) == 4 and len({r["id"] for r in witness}) == 4
    mask = 0
    for row in witness:
        i = row["id"]
        assert type(i) is int and 0 <= i < len(UNIVERSE)
        same(
            row,
            {
                "id": i,
                "block": list(UNIVERSE[i]),
                "hole_mask": masks[i],
                "hole_count": masks[i].bit_count(),
            },
        )
        mask |= masks[i]
    assert mask == (1 << 9) - 1
    same(profile["optimizer_calls"], 0)
    same(profile["native_search_calls"], 0)
    assert "No unrestricted nonexistence claim" in profile["scope"]
    assert "no new62-core all-relabel claim" in profile["scope"]


def main():
    profile = read(P / "profile.json")
    assert sha(P / "profile.json") == PROFILE_SHA
    manifest = read(MANIFEST)
    assert sha(MANIFEST) == profile["manifest_sha256"]
    assert sha(P / "check.py") == profile["source_sha256"]
    initial_path = ROOT / profile["initial_path"]
    assert sha(initial_path) == profile["initial_sha256"] == manifest["initial"]["sha256"]
    family = parse_family(initial_path.read_text())
    expected, masks = recount(family, manifest)
    validate(profile, expected, masks)
    same(profile["weak_metrics"], manifest["initial"]["metrics"])
    same(profile["native_runtime_audit_sha256"], manifest["native_runtime_audit_sha256"])
    for verification in profile["verifications"]:
        path = ROOT / verification["path"]
        assert sha(path) == verification["sha256"]
        result = read(path)
        assert result["canonical_sha256"] == profile["initial_sha256"]
        assert result["blocks"] == 64 and result["valid"] is False

    damages = [
        ("hole omitted", lambda p: p["holes"].pop()),
        ("wrong carrier count", lambda p: p["carrier_histogram"].__setitem__("2", 43)),
        ("boolean carrier count", lambda p: p["carrier_histogram"].__setitem__("3", True)),
        ("missing pattern", lambda p: p["hole_mask_patterns"].pop()),
        ("false three-block cover", lambda p: p["mask_dp_layers"][3]["masks"].append(511)),
        ("wrong common hole", lambda p: p.__setitem__("three_hole_carrier_common_hole", [1, 2, 3])),
        ("eligible adder removed", lambda p: p["radius_four_adders"].pop()),
        ("adder damaged", lambda p: p["radius_four_adders"][0].__setitem__("hole_mask", 0)),
        ("restore set shortened", lambda p: p["radius_four_adder_union_triples"].pop()),
        (
            "private witness damaged",
            lambda p: p["forced_original_blocks"][0].__setitem__("private_witness", [1, 5, 7]),
        ),
        ("forced row omitted", lambda p: p["forced_original_blocks"].pop()),
        ("forced count damaged", lambda p: p.__setitem__("forced_original_count", 62)),
        (
            "overlap cap widened",
            lambda p: p.__setitem__("exact64_maximum_overlap_with_named_initial_family", 60),
        ),
        (
            "outside count lowered",
            lambda p: p.__setitem__("exact64_minimum_blocks_outside_named_initial_family", 4),
        ),
        (
            "old-core support damaged",
            lambda p: p["old_core_all_relabel_overlap_proofs"][0]["heavy_triples"][0].__setitem__(
                "core_multiplicity", 5
            ),
        ),
        (
            "old-core cap strengthened",
            lambda p: p["old_core_all_relabel_overlap_proofs"][0].__setitem__(
                "maximum_overlap_every_relabeling", 44
            ),
        ),
        (
            "hole-only witness duplicated",
            lambda p: p["hole_only_four_block_witness"].__setitem__(
                1, p["hole_only_four_block_witness"][0]
            ),
        ),
        ("scope widened", lambda p: p.__setitem__("scope", "Unrestricted nonexistence proved")),
    ]
    controls = []
    for name, mutate in damages:
        damaged = copy.deepcopy(profile)
        mutate(damaged)
        try:
            validate(damaged, expected, masks)
        except (AssertionError, KeyError, ValueError):
            controls.append({"case": name, "rejected": True})
        else:
            raise AssertionError(f"accepted damage: {name}")
    text = initial_path.read_text()
    lines = text.splitlines()
    malformed = {
        "duplicate block": "\n".join([lines[0], *lines[0:63]]) + "\n",
        "label zero": text.replace("1 2 3 9 16", "0 2 3 9 16", 1),
        "short block": "1 2 3 9\n" + "\n".join(lines[1:]) + "\n",
        "reversed block order": "\n".join(reversed(lines)) + "\n",
    }
    for name, content in malformed.items():
        try:
            parse_family(content)
        except (AssertionError, ValueError):
            controls.append({"case": name, "rejected": True})
        else:
            raise AssertionError(f"accepted malformed family: {name}")
    result = {
        "passed": True,
        "certificate_path": str(P.relative_to(ROOT) / "profile.json"),
        "certificate_sha256": PROFILE_SHA,
        "independent_source_sha256": sha(__file__),
        "initial_sha256": profile["initial_sha256"],
        "manifest_sha256": profile["manifest_sha256"],
        "independently_recomputed_fields": sorted(expected),
        "old_core_all_relabel_maximum_overlap": 45,
        "carrier_histogram": expected["carrier_histogram"],
        "distinct_hole_masks": len(expected["hole_mask_patterns"]),
        "three_mask_multisets_recounted": sum(
            1 for _ in combinations_with_replacement(expected["hole_mask_patterns"], 3)
        ),
        "maximum_holes_in_three_additions": 7,
        "four_block_hole_only_witness_checked": True,
        "eligible_adders": len(expected["radius_four_adders"]),
        "forced_original_blocks": 63,
        "forced_plus_necessary_additions": 67,
        "radius_four_excluded": True,
        "exact64_named_initial_maximum_overlap": 59,
        "damaged_controls": controls,
        "optimizer_calls": 0,
        "native_search_calls": 0,
        "four_adder_tuples_enumerated_by_this_replay": 0,
        "scope": profile["scope"],
    }
    (HERE / "review.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {"passed": True, "damaged_controls": len(controls), "recomputed_fields": len(expected)}
        )
    )


if __name__ == "__main__":
    main()
