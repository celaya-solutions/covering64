# Document:    Hole-Priority Final Relabel and Novelty Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      b86586befd74b5dbb04a7b5128f47eb13a8e121ed9f8398bbfd7a286bda5e8b1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import importlib.util
import itertools
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DAY = HERE.parent
POINTS = tuple(range(1, 17))
SETS = {size: list(itertools.combinations(POINTS, size)) for size in range(1, 6)}
RANK = {block: index for index, block in enumerate(SETS[5])}
HELPER = DAY / "six-hole-strong-core-release-independent/relabels.py"
HELPER_SHA = "9cdcd511eb94954bb45c1cf209c5d51517b46c11e46b44a22ce7221d9309f74a"
BINDINGS = {
    "soft-pair-hole-priority/manifest.json": (
        "d33005daaaa946d57c4fa5bb15f3bcb70eda9d86087dbb149f582ccc0c36f0b9"
    ),
    "soft-pair-hole-priority/result.json": (
        "2be90db6cca1297d732e32b888c87887b2eda7344ac619743899173d2f2aed75"
    ),
    "soft-pair-hole-priority-postcheck/postcheck.json": (
        "7d75f7a3e30bd8587727c6b6f90ff8702e15b1e092914866246bf647d699e9be"
    ),
    "soft-pair-h12-relabel-novelty/diagnostic.json": (
        "2b2dd335c596222a3b6a597a6ee41edde500cc224172a866041378c9fd39d490"
    ),
    "soft-pair-h12-relabel-novelty/relabel-screen.json": (
        "3f1dfad8d7599cd2507e6633af895bf0977446831c021c97a854c16b2d4be8ec"
    ),
    "pair-floor-replacement-characterization/manifest.json": (
        "645f5512210feb10ba658ec7440f199b83d4c60f33eb0aa7f8cd27ffb4ab20ec"
    ),
}
FINAL_SHA = "a00c567a97a00429063ec599728e8b16fe3ed2c230c9eaffdf99939d7632563c"
START_SHA = "cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def histogram(values):
    return dict(sorted(Counter(values).items()))


def profile(name, source, cores):
    path = DAY / source["path"]
    assert sha(path) == source["sha256"]
    assert sha(DAY / source["screen"]) == source["screen_sha256"]
    blocks = [
        tuple(map(int, line.split()))
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(blocks) == len(set(blocks)) == 64
    assert blocks == sorted(blocks) and all(block in RANK for block in blocks)
    ids = {RANK[block] for block in blocks}
    counts = {
        size: Counter(q for block in blocks for q in itertools.combinations(block, size))
        for size in (1, 2, 3, 4)
    }
    block_sets = [set(block) for block in blocks]
    for size in (1, 2, 3, 4):
        assert all(
            counts[size][q] == sum(set(q) <= block for block in block_sets) for q in SETS[size]
        )
    assert [sum(counts[size].values()) for size in (1, 2, 3, 4)] == [320, 640, 640, 320]
    holes = [triple for triple in SETS[3] if counts[3][triple] == 0]
    assert len(holes) == source["holes"]
    details = []
    for pair in SETS[2]:
        pair_count = counts[2][pair]
        outside = [x for x in POINTS if x not in pair]
        triples = {x: counts[3][tuple(sorted((*pair, x)))] for x in outside}
        assert sum(triples.values()) == 3 * pair_count
        single = [max(0, 13 - 3 * pair_count + triples[x]) for x in outside]
        quad = [
            max(0, 12 - 3 * pair_count + 2 * counts[4][tuple(sorted((*pair, a, b)))])
            for a, b in itertools.combinations(outside, 2)
        ]
        two = [
            max(0, 12 - 3 * pair_count + triples[a] + triples[b])
            for a, b in itertools.combinations(outside, 2)
        ]
        assert len(single) == 14 and len(quad) == len(two) == 91
        assert max(two) == max(0, 12 - 3 * pair_count + sum(sorted(triples.values())[-2:]))
        details.append(
            {
                "pair": pair,
                "count": pair_count,
                "triple_positions": [[x, triples[x]] for x in outside],
                **{
                    key: {
                        "maximum": max(rows),
                        "sum": sum(rows),
                        "violated_rows": sum(value > 0 for value in rows),
                    }
                    for key, rows in (("single", single), ("quad", quad), ("two_triple", two))
                },
            }
        )
    receipts = []
    for label, command in (
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", [sys.executable, "scripts/check_cover.py"]),
    ):
        checked = subprocess.run(
            command + [str(path), "--expected-blocks", "64"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(checked.stdout)
        assert checked.returncode == 1 and not checked.stderr
        assert payload["blocks"] == 64 and payload["valid"] is False
        assert payload["uncovered"] == [list(triple) for triple in holes]
        assert payload["canonical_sha256"] == source["sha256"]
        receipt = HERE / f"{name.lower()}-{label}.json"
        receipt.write_text(checked.stdout)
        receipts.append({"path": str(receipt.relative_to(ROOT)), "sha256": sha(receipt)})
    deficits = {
        key: {
            "sum_of_per_pair_maxima": sum(row[key]["maximum"] for row in details),
            "full_row_sum": sum(row[key]["sum"] for row in details),
            "violated_rows": sum(row[key]["violated_rows"] for row in details),
            "violated_pairs": sum(row[key]["maximum"] > 0 for row in details),
            "rows": 1680 if key == "single" else 10920,
        }
        for key in ("single", "quad", "two_triple")
    }
    overlaps = [len(ids & set(core)) for core in cores]
    assert max(overlaps) <= 55
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "relabel_screen_sha256": source["screen_sha256"],
        "cardinality": 64,
        "holes": len(holes),
        "uncovered_triples": holes,
        "point_histogram": histogram(counts[1][point] for point in SETS[1]),
        "pair_histogram": histogram(counts[2][pair] for pair in SETS[2]),
        "point_counts": [[point[0], counts[1][point]] for point in SETS[1]],
        "minimum_pair_count": min(counts[2][pair] for pair in SETS[2]),
        "deficits": deficits,
        "four_named_core_overlaps": overlaps,
        "pair_details": details,
        "verifiers": receipts,
        "ids": sorted(ids),
    }


def main():
    assert not (HERE / "diagnostic.json").exists(), "preserve finished diagnostic"
    for path, digest in BINDINGS.items():
        assert sha(DAY / path) == digest
    manifest = json.loads((DAY / "soft-pair-hole-priority/manifest.json").read_text())
    result = json.loads((DAY / "soft-pair-hole-priority/result.json").read_text())
    runtime = json.loads((DAY / "soft-pair-hole-priority-postcheck/postcheck.json").read_text())
    assert runtime["passed"]
    assert result["manifest_sha256"] == BINDINGS["soft-pair-hole-priority/manifest.json"]
    assert (
        result["gate_sha256"] == "e6eba94f19dcb3af6402f0dc65b8a451e74b8f22205c34a40e0d976b284930fd"
    )
    assert result["status"] in ("FEASIBLE", "OPTIMAL")
    for path, digest in result["raw_files"].items():
        assert sha(ROOT / path) == digest
    final_row = next(row for row in result["saved_states"] if row["label"] == "final")
    final_path = ROOT / final_row["witness_path"]
    assert sha(final_path) == final_row["witness_sha256"] == FINAL_SHA
    assert sha(HELPER) == HELPER_SHA
    spec = importlib.util.spec_from_file_location("frozen_relabel", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    controls = helper.selfcheck()
    assert controls["passed"]
    blocks = [tuple(map(int, line.split())) for line in final_path.read_text().splitlines()]
    assert blocks == sorted(blocks) and len(blocks) == len(set(blocks)) == 64
    assert all(block in RANK for block in blocks)
    screen = helper.check([RANK[block] for block in blocks])
    screen_path = HERE / "relabel-screen.json"
    screen_path.write_text(
        json.dumps(
            {
                "passed": True,
                "optimizer_calls": 0,
                "candidate_sha256": FINAL_SHA,
                "helper_sha256": HELPER_SHA,
                "helper_controls": controls,
                "screen": screen,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    archived = HERE / "final-family.txt"
    archived.write_bytes(final_path.read_bytes())
    assert sha(archived) == FINAL_SHA
    sources = {
        "start": {
            "path": "soft-pair-h12-relabel-novelty/final-family.txt",
            "sha256": START_SHA,
            "holes": 12,
            "screen": "soft-pair-h12-relabel-novelty/relabel-screen.json",
            "screen_sha256": BINDINGS["soft-pair-h12-relabel-novelty/relabel-screen.json"],
        },
        "final": {
            "path": str(archived.relative_to(DAY)),
            "sha256": FINAL_SHA,
            "holes": 12,
            "screen": str(screen_path.relative_to(DAY)),
            "screen_sha256": sha(screen_path),
        },
    }
    profiles = {
        name: profile(name, source, manifest["core_rows"]) for name, source in sources.items()
    }
    before, after = profiles["start"], profiles["final"]
    expected = {
        "holes": after["holes"],
        "D2max": after["deficits"]["two_triple"]["sum_of_per_pair_maxima"],
        "D2sum": after["deficits"]["two_triple"]["full_row_sum"],
        "D3": after["deficits"]["single"]["full_row_sum"],
        "D4": after["deficits"]["quad"]["full_row_sum"],
        "minimum_pair_count": after["minimum_pair_count"],
        "core_overlaps": after["four_named_core_overlaps"],
    }
    expected["canonical_objective"] = 15361 * expected["holes"] + expected["D2max"]
    assert expected == final_row["actual_metrics"]
    assert expected["D2max"] == expected["D2sum"] == 31
    assert expected["D3"] == expected["D4"] == 0
    start_ids, final_ids = set(before["ids"]), set(after["ids"])
    start_holes = set(map(tuple, before["uncovered_triples"]))
    final_holes = set(map(tuple, after["uncovered_triples"]))
    difference = {
        "shared_blocks": len(start_ids & final_ids),
        "removed_blocks": [SETS[5][i] for i in sorted(start_ids - final_ids)],
        "added_blocks": [SETS[5][i] for i in sorted(final_ids - start_ids)],
        "holes_filled": sorted(start_holes - final_holes),
        "new_holes": sorted(final_holes - start_holes),
        "unchanged_holes": sorted(start_holes & final_holes),
        "changed_point_counts": [
            [a[0], a[1], b[1]]
            for a, b in zip(before["point_counts"], after["point_counts"], strict=True)
            if a[1] != b[1]
        ],
        "changed_pair_counts": [
            [a["pair"], a["count"], b["count"]]
            for a, b in zip(before["pair_details"], after["pair_details"], strict=True)
            if a["count"] != b["count"]
        ],
        "changed_two_triple_deficits": [
            [a["pair"], a["two_triple"], b["two_triple"]]
            for a, b in zip(before["pair_details"], after["pair_details"], strict=True)
            if a["two_triple"] != b["two_triple"]
        ],
        "not_a_point_relabeling": before["deficits"]["two_triple"]
        != after["deficits"]["two_triple"],
        "not_a_point_relabeling_reason": "D2max and D2sum are point-relabel invariants "
        "and changed from 32 to 31.",
    }
    pair_counts = {tuple(row["pair"]): row["count"] for row in after["pair_details"]}
    forced_rows = []
    for block in blocks:
        critical = [pair for pair in itertools.combinations(block, 2) if pair_counts[pair] == 5]
        points = set().union(*map(set, critical)) if critical else set()
        count = math.comb(16 - len(points), 5 - len(points)) - sum(points <= set(b) for b in blocks)
        forced_rows.append(
            {
                "removed_block": block,
                "forced_points": sorted(points),
                "forced_size": len(points),
                "pair_floor_legal_additions": count,
            }
        )
    pair_floor = {
        "forced_size_histogram": dict(
            sorted(Counter(row["forced_size"] for row in forced_rows).items())
        ),
        "pair_floor_legal_neighbors": sum(row["pair_floor_legal_additions"] for row in forced_rows),
        "blocks": forced_rows,
        "method": "Apply the previously proved endpoint-union counting formula to freshly "
        "recounted D31 pair counts; no replacement ranking or optimization.",
    }
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "bound_inputs": BINDINGS,
        "producer_final": final_row,
        "archived_candidate_path": str(archived.relative_to(ROOT)),
        "archived_candidate_sha256": sha(archived),
        "profiles": profiles,
        "pair_floor_characterization": pair_floor,
        "difference": difference,
        "relabel_screen_path": str(screen_path.relative_to(ROOT)),
        "relabel_screen_sha256": sha(screen_path),
        "relabel_screen": screen,
        "no_actual_D2zero": True,
        "scope": "The final family remains a 12-hole noncover with D2max=D2sum=31. "
        "No hard-model zero-hint qualification is claimed. Relabel cap applies only to this "
        "saved 64-block family; no global lower-bound conclusion is made.",
    }
    (HERE / "diagnostic.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "diagnostic_sha256": sha(HERE / "diagnostic.json"),
                "difference": difference,
                "screen": screen,
                "pair_floor_histogram": pair_floor["forced_size_histogram"],
                "pair_floor_neighbors": pair_floor["pair_floor_legal_neighbors"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
