# Document:    D29 Swap-Tie Independent Relabel Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      43003ca4dc2d89c416638f4def635b04d87723a682bed8268b9585328c10e477
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import importlib.util
import itertools
import json
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
AUDIT = DAY / "weak-pair-swap-scan-runtime-independent/postcheck.json"
AUDIT_SHA = "a491a5ae273d2eab20bff3c3992771ce130d3293236eee62d9c05c6214e1207c"
MODEL = DAY / "soft-pair-hole-priority/manifest.json"
MODEL_SHA = "d33005daaaa946d57c4fa5bb15f3bcb70eda9d86087dbb149f582ccc0c36f0b9"
EXPECTED = {
    1142: "44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a",
    1143: "bb531f3efbbc9142af38de6360add63f90f319da05e727b130c1917c64123f35",
    1154: "6761d808f4484b5ac7d50d841e2cf743ed5d94f34485b0b5c585e3fb488d5eb7",
    1359: "1ce67c49ba812463d5f964754775816f0ebd323d06a43fb6adf4789ae07d2da2",
}


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
    output = HERE / "screen.json"
    assert not output.exists(), "preserve completed screen"
    assert sha(AUDIT) == AUDIT_SHA and sha(MODEL) == MODEL_SHA and sha(HELPER) == HELPER_SHA
    audit = json.loads(AUDIT.read_text())
    assert audit["passed"] and audit["complete_neighborhood"]
    ties = audit["best_ties"]
    assert len(ties) == 4 and {row["incoming"] for row in ties} == set(EXPECTED)
    assert all(row["outgoing"] == 881 for row in ties)
    cores = json.loads(MODEL.read_text())["core_rows"]
    spec = importlib.util.spec_from_file_location("frozen_relabel", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    controls = helper.selfcheck()
    assert controls["passed"]
    checked = []
    for row in ties:
        path = ROOT / row["path"]
        assert sha(path) == row["sha256"] == EXPECTED[row["incoming"]]
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks)
        assert all(block in RANK for block in blocks)
        screen = helper.check([RANK[block] for block in blocks])
        screen_path = HERE / f"incoming-{row['incoming']}-relabel.json"
        screen_path.write_text(
            json.dumps(
                {"candidate_sha256": sha(path), "helper_sha256": HELPER_SHA, "screen": screen},
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        source = {
            "path": str(path.relative_to(DAY)),
            "sha256": sha(path),
            "holes": 12,
            "screen": str(screen_path.relative_to(DAY)),
            "screen_sha256": sha(screen_path),
        }
        actual = profile(f"incoming-{row['incoming']}", source, cores)
        expected = {
            "cardinality": 64,
            "holes": actual["holes"],
            "D2max": actual["deficits"]["two_triple"]["sum_of_per_pair_maxima"],
            "D2sum": actual["deficits"]["two_triple"]["full_row_sum"],
            "D3": actual["deficits"]["single"]["full_row_sum"],
            "D4": actual["deficits"]["quad"]["full_row_sum"],
            "minimum_pair_count": actual["minimum_pair_count"],
            "core_overlaps": actual["four_named_core_overlaps"],
        }
        assert expected == row["metrics"]
        assert expected["D2max"] == expected["D2sum"] == 29
        assert expected["D3"] == expected["D4"] == 0 and expected["minimum_pair_count"] == 5
        checked.append(
            {
                "incoming": row["incoming"],
                "outgoing": row["outgoing"],
                "path": row["path"],
                "sha256": row["sha256"],
                "profile": actual,
                "screen": screen,
                "screen_path": str(screen_path.relative_to(ROOT)),
                "screen_sha256": sha(screen_path),
            }
        )
    distances = [
        [
            a["incoming"],
            b["incoming"],
            64 - len(set(a["profile"]["ids"]) & set(b["profile"]["ids"])),
        ]
        for a, b in itertools.combinations(checked, 2)
    ]
    assert all(row[2] == 1 for row in distances)
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(Path(__file__)),
        "runtime_audit_sha256": AUDIT_SHA,
        "core_manifest_sha256": MODEL_SHA,
        "helper_sha256": HELPER_SHA,
        "helper_controls": controls,
        "representative_incoming": 1142,
        "representative_sha256": EXPECTED[1142],
        "families": checked,
        "pairwise_replacement_distances": distances,
        "scope": "Four saved D29/H12 weak-pair-qualified ties, all remaining noncovers. "
        "Each old-core cap certificate applies only to its exact 64-block family. "
        "No hard D2zero qualification, new optimizer, or global lower-bound claim.",
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "screen_sha256": sha(output),
                "families": [
                    {
                        "incoming": row["incoming"],
                        "partitions": row["screen"]["necessary_partition_count"],
                        "cap55": row["screen"][
                            "all_relabel_cap55_certified_by_necessary_condition"
                        ],
                    }
                    for row in checked
                ],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
