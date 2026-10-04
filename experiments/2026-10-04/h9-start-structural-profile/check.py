# Document:    H9 Start Structural and Radius Four Certificate Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3fab971e35140d39157221179086df894b118e995a63a1ebe00618832c3ddcbc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Count 4368 carriers and 512 hole masks; no optimizer or neighborhood search."""

import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
START = DAY / "weak-pair-h9-d23-neutral-queue/initial.txt"
START_SHA = "f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681"
MANIFEST = DAY / "weak-pair-h9-d23-neutral-queue/manifest.json"
MANIFEST_SHA = "64d63c5bee05e8ba8c5ca7bbb4f98b3258a6f3d6192297e792a4b62b12835d87"
NATIVE_AUDIT = DAY / "native-five-core-record-runtime-independent/postcheck.json"
NATIVE_AUDIT_SHA = "5d79cdfc0820086e14281538398506c674ce9ecb241e1b3b3739b7aabb067862"
LABELS = range(1, 17)
BLOCKS = list(itertools.combinations(LABELS, 5))
BLOCK_IDS = {block: index for index, block in enumerate(BLOCKS)}
TRIPLES = list(itertools.combinations(LABELS, 3))
PAIRS = list(itertools.combinations(LABELS, 2))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def parse(text):
    blocks = [tuple(map(int, line.split())) for line in text.splitlines() if line.strip()]
    if len(blocks) != 64 or len(set(blocks)) != 64:
        raise ValueError("expected 64 distinct blocks")
    if any(block not in BLOCK_IDS for block in blocks) or blocks != sorted(blocks):
        raise ValueError("expected sorted canonical five-blocks on labels 1..16")
    return blocks


def main():
    assert not (HERE / "profile.json").exists(), "preserve the frozen certificate"
    assert sha(START) == START_SHA and sha(MANIFEST) == MANIFEST_SHA
    assert sha(NATIVE_AUDIT) == NATIVE_AUDIT_SHA
    initial = parse(START.read_text())
    manifest = json.loads(MANIFEST.read_text())
    native = json.loads(NATIVE_AUDIT.read_text())
    assert native["passed"] and native["campaign_complete"]
    audited = next(row for row in native["families"] if row["sha256"] == START_SHA)
    assert [BLOCK_IDS[b] for b in initial] == audited["ids"] == manifest["initial"]["ids"]
    counts = {
        n: Counter(q for b in initial for q in itertools.combinations(b, n)) for n in (1, 2, 3, 4)
    }
    holes = [triple for triple in TRIPLES if counts[3][triple] == 0]
    assert len(holes) == 9
    triple_histogram = dict(sorted(Counter(counts[3][t] for t in TRIPLES).items()))
    assert triple_histogram == {0: 9, 1: 464, 2: 85, 3: 2}
    pair_histogram = dict(sorted(Counter(counts[2][p] for p in PAIRS).items()))
    points = []
    links19 = []
    for point in LABELS:
        degree = counts[1][(point,)]
        local_holes = [t for t in holes if point in t]
        histogram = dict(
            sorted(
                Counter(
                    counts[3][tuple(sorted((point, *pair)))]
                    for pair in itertools.combinations([v for v in LABELS if v != point], 2)
                ).items()
            )
        )
        points.append(
            {
                "point": point,
                "degree": degree,
                "holes": len(local_holes),
                "link_excess_above_one": 6 * degree - (105 - len(local_holes)),
            }
        )
        if degree == 19:
            links19.append(
                {
                    "point": point,
                    "degree": degree,
                    "hole_triples": local_holes,
                    "pair_multiplicity_histogram": histogram,
                    "neighbor_replication": {
                        other: counts[2][tuple(sorted((point, other)))]
                        for other in LABELS
                        if other != point
                    },
                    "blocks": [
                        [v for v in block if v != point] for block in initial if point in block
                    ],
                }
            )
    assert [row["point"] for row in links19] == [1, 8]
    assert {row["point"] for row in points if row["degree"] == 21} == {6, 16}
    d2max = d2sum = d3 = d4 = 0
    for pair in PAIRS:
        values = {v: counts[3][tuple(sorted((*pair, v)))] for v in LABELS if v not in pair}
        deficits = [
            max(0, 12 - 3 * counts[2][pair] + values[a] + values[b])
            for a, b in itertools.combinations(values, 2)
        ]
        d2max += max(deficits)
        d2sum += sum(deficits)
        d3 += sum(max(0, 13 - 3 * counts[2][pair] + count) for count in values.values())
        d4 += sum(
            max(0, 12 - 3 * counts[2][pair] + 2 * counts[4][tuple(sorted((*pair, a, b)))])
            for a, b in itertools.combinations(values, 2)
        )
    assert (d2max, d2sum, d3, d4) == (23, 29, 0, 0)

    carriers = []
    for block_id, block in enumerate(BLOCKS):
        hole_mask = sum(1 << i for i, hole in enumerate(holes) if set(hole) <= set(block))
        carriers.append(
            {
                "id": block_id,
                "block": block,
                "hole_mask": hole_mask,
                "hole_count": hole_mask.bit_count(),
            }
        )
    carrier_histogram = dict(sorted(Counter(row["hole_count"] for row in carriers).items()))
    assert carrier_histogram == {0: 3716, 1: 605, 2: 44, 3: 3}
    triple_carriers = [row for row in carriers if row["hole_count"] == 3]
    common_mask = (1 << 9) - 1
    for row in triple_carriers:
        common_mask &= row["hole_mask"]
    assert common_mask == 1 << holes.index((5, 9, 15))
    # Each state is a union of at most k carrier masks. Zero retains smaller unions.
    # Repeated masks are harmless; an optimal hole-only witness needs no repetition.
    patterns = sorted({row["hole_mask"] for row in carriers})
    reachable = {0}
    layers = [{"at_most_blocks": 0, "masks": [0], "maximum_holes_covered": 0}]
    for size in range(1, 5):
        reachable = {state | pattern for state in reachable for pattern in patterns}
        layers.append(
            {
                "at_most_blocks": size,
                "masks": sorted(reachable),
                "maximum_holes_covered": max(state.bit_count() for state in reachable),
            }
        )
    assert [row["maximum_holes_covered"] for row in layers] == [0, 3, 5, 7, 9]
    assert 511 not in layers[3]["masks"] and 511 in layers[4]["masks"]
    witness = [(1, 5, 7, 9, 15), (1, 5, 8, 13, 15), (2, 6, 8, 10, 13), (5, 9, 10, 12, 16)]
    witness_rows = [carriers[BLOCK_IDS[block]] for block in witness]
    assert set(holes) <= {t for block in witness for t in itertools.combinations(block, 3)}
    assert len(set(witness)) == 4 and not set(witness) & set(initial)

    # If a radius-four repair had a zero/one-hole adder, its other three adders
    # cover at most seven holes, yielding at most eight in total. Hence >=2 each.
    adders = [row for row in carriers if row["hole_count"] >= 2]
    assert len(adders) == 47 and not {row["block"] for row in adders} & set(initial)
    adder_triples = {t for row in adders for t in itertools.combinations(row["block"], 3)}
    forced = []
    potentially_removable = []
    private_rows = []
    for block in initial:
        private = [t for t in itertools.combinations(block, 3) if counts[3][t] == 1]
        obstructed = [t for t in private if t not in adder_triples]
        row = {
            "id": BLOCK_IDS[block],
            "block": block,
            "private_triples": private,
            "private_count": len(private),
            "unrestorable_private_triples": obstructed,
        }
        private_rows.append(row)
        if obstructed:
            forced.append(
                {"id": BLOCK_IDS[block], "block": block, "private_witness": obstructed[0]}
            )
        else:
            potentially_removable.append(row)
    assert len(forced) == 63 and len(potentially_removable) == 1
    assert potentially_removable[0]["block"] == (8, 9, 10, 12, 15)
    for row in forced:
        assert counts[3][row["private_witness"]] == 1
        assert row["private_witness"] not in adder_triples
        assert set(row["private_witness"]) <= set(row["block"])

    core_proofs = []
    max_multiplicity = max(counts[3].values())
    for index, core_ids in enumerate(manifest["core_rows"]):
        assert len(core_ids) == len(set(core_ids)) == 60
        core_counts = Counter(
            t for block_id in core_ids for t in itertools.combinations(BLOCKS[block_id], 3)
        )
        heavy = sorted((t, n) for t, n in core_counts.items() if n >= 6)
        assert len(heavy) == 5 and all(count == 6 for _, count in heavy)
        assert all(not set(a) & set(b) for (a, _), (b, _) in itertools.combinations(heavy, 2))
        lost = sum(count - max_multiplicity for _, count in heavy)
        assert lost == 15
        core_proofs.append(
            {
                "core_index": index,
                "core_ids": core_ids,
                "heavy_triples": [{"triple": t, "core_multiplicity": n} for t, n in heavy],
                "heavy_carrier_sets_disjoint": True,
                "minimum_missing_core_blocks_every_relabeling": lost,
                "maximum_overlap_every_relabeling": 60 - lost,
            }
        )
    verifications = []
    for name, command in (
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
    ):
        result = subprocess.run(
            [*command, str(START), "--expected-blocks", "64"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 1 and not result.stderr
        report = json.loads(result.stdout)
        assert not report["valid"] and report["blocks"] == 64
        assert sorted(map(tuple, report["uncovered"])) == holes
        assert report["canonical_sha256"] == START_SHA
        path = HERE / f"{name}-verification.json"
        path.write_text(result.stdout)
        verifications.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "command": [*command, str(START.relative_to(ROOT)), "--expected-blocks", "64"],
                "exit_code": result.returncode,
            }
        )
    damage_controls = []
    for name, damaged in (
        ("duplicate", [initial[0], *initial[:-1]]),
        ("short", initial[:-1]),
        ("out-of-range", [(0, *initial[0][1:]), *initial[1:]]),
        ("noncanonical", [initial[1], initial[0], *initial[2:]]),
    ):
        try:
            parse("\n".join(" ".join(map(str, b)) for b in damaged))
        except ValueError:
            damage_controls.append({"name": name, "rejected": True})
        else:
            raise AssertionError("damaged family accepted")
    result = {
        "passed": True,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "initial_path": str(START.relative_to(ROOT)),
        "initial_sha256": START_SHA,
        "initial_ids": [BLOCK_IDS[b] for b in initial],
        "manifest_sha256": MANIFEST_SHA,
        "native_runtime_audit_sha256": NATIVE_AUDIT_SHA,
        "holes": holes,
        "triple_multiplicities": triple_histogram,
        "pair_multiplicities": pair_histogram,
        "point_profiles": points,
        "degree19_links": links19,
        "weak_metrics": audited["weak_metrics"],
        "hole_pair_intersection_histogram": dict(
            sorted(
                Counter(len(set(a) & set(b)) for a, b in itertools.combinations(holes, 2)).items()
            )
        ),
        "carrier_histogram": carrier_histogram,
        "hole_mask_patterns": patterns,
        "all_three_hole_carriers": triple_carriers,
        "three_hole_carrier_common_hole": (5, 9, 15),
        "mask_dp_layers": layers,
        "minimum_blocks_covering_original_holes_only": 4,
        "hole_only_four_block_witness": witness_rows,
        "radius_four_adders": adders,
        "radius_four_adder_union_triples": sorted(adder_triples),
        "forced_original_blocks": forced,
        "forced_original_count": len(forced),
        "potentially_removable_originals": potentially_removable,
        "original_private_triples": private_rows,
        "radius_four_excluded": True,
        "exact64_minimum_blocks_outside_named_initial_family": 5,
        "exact64_maximum_overlap_with_named_initial_family": 59,
        "old_core_all_relabel_overlap_proofs": core_proofs,
        "verifications": verifications,
        "damage_controls": damage_controls,
        "optimizer_calls": 0,
        "native_search_calls": 0,
        "four_adder_tuples_enumerated": 0,
        "scope": "Finite radius-four exclusion around this exact initial family and "
        "max-multiplicity overlap bounds for each old60 core image. "
        "No unrestricted nonexistence claim, no new62-core all-relabel claim, "
        "and no claim that the four hole-only blocks repair removed-block holes.",
    }
    dump(HERE / "profile.json", result)
    print(
        json.dumps(
            {
                "passed": True,
                "profile_sha256": sha(HERE / "profile.json"),
                "radius_four_excluded": True,
                "forced_originals": len(forced),
                "exact64_named_initial_overlap_cap": 59,
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
