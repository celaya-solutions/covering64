# Document:    Partial-Start Structural Diagnostics
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f2151f19d5ac69796aac848c8863c05a3a83f8a395bbe497af8d8c62e2049efc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
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
SOURCES = {
    "H9": {
        "path": "native-core-cap-escape-v2/seed-2026104201/search-final-best.txt",
        "sha256": "15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46",
        "holes": 9,
        "screen": "native-core-cap-escape-independent/relabel-screen.json",
        "screen_sha256": "121fe4d0352102def5371509510ffaefec1b15be5efa24af4b1a97a9e12be1a7",
    },
    "H12": {
        "path": "native-variable-cardinality/seed-2026104702/search-final-admissible64.txt",
        "sha256": "330788e4a6f24e1852b047f5cd2447bfa83da66ea8c6daba3287eb53088c4b00",
        "holes": 12,
        "screen": "native-variable-cardinality-relabel-screen/screen.json",
        "screen_sha256": "159ca06adb57ed636e52d19da8d42c36a35d26a56827bfcd840f8c2b91bc3e98",
    },
}
CORE_MANIFEST = DAY / "native-variable-cardinality/manifest.json"
CORE_MANIFEST_SHA = "f79075467ba41b46e53491c032044a23fe9766c680309055c1ff5d0697ec354b"


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
    assert sha(CORE_MANIFEST) == CORE_MANIFEST_SHA
    core_source = json.loads(CORE_MANIFEST.read_text())
    cores = core_source["core_rows"]
    assert len(cores) == 4
    assert all(
        len(core) == len(set(core)) == 60 and all(0 <= i < 4368 for i in core) for core in cores
    )
    profiles = {name: profile(name, source, cores) for name, source in SOURCES.items()}
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "python_version": sys.version,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "core_manifest_path": str(CORE_MANIFEST.relative_to(ROOT)),
        "core_manifest_sha256": CORE_MANIFEST_SHA,
        "core_rows": cores,
        "definitions": {
            "single": "max(0, 13 - 3*c(P) + c(P union {x})) for x outside P",
            "quad": "max(0, 12 - 3*c(P) + 2*c(P union {x,y})) for distinct x,y outside P",
            "two_triple": "max(0, 12 - 3*c(P) + c(P union {x}) + c(P union {y})) "
            "for distinct x,y outside P",
            "D3": "single.full_row_sum",
            "D4": "quad.full_row_sum",
            "D2max": "two_triple.sum_of_per_pair_maxima",
            "D2sum": "two_triple.full_row_sum",
        },
        "profiles": profiles,
        "same_label_block_overlap": len(set(profiles["H9"]["ids"]) & set(profiles["H12"]["ids"])),
        "point_histograms_differ": profiles["H9"]["point_histogram"]
        != profiles["H12"]["point_histogram"],
        "pair_histograms_differ": profiles["H9"]["pair_histogram"]
        != profiles["H12"]["pair_histogram"],
        "scope": "Read-only structural diagnostics of two saved noncovers, for comparing proposed "
        "partial starts. No optimizer was called and no new model constraints are proposed.",
    }
    (HERE / "diagnostic.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                name: {
                    key: row[key]
                    for key in (
                        "holes",
                        "point_histogram",
                        "pair_histogram",
                        "deficits",
                        "four_named_core_overlaps",
                    )
                }
                for name, row in profiles.items()
            },
            sort_keys=True,
        )
    )
    print("diagnostic_sha256", sha(HERE / "diagnostic.json"))


if __name__ == "__main__":
    main()
