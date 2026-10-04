# Document:    Heterogeneous Saved-State Inventory Checker
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      60d2be5800be9532f5ff78d3046c5264c0da4dde864476181ffa5d9742c16c96
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount ten saved partial states, with no optimizer or new core search."""

import json
import shutil
import subprocess
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASES = [
    ("unrestricted-old-3", "experiments/scratch/heuristic-tabu-2026100301-deficit-3.txt"),
    ("unrestricted-new-3", "experiments/2026-10-04/five-hole-unrestricted-repair/best.txt"),
    ("regular-5", "experiments/2026-10-04/lp-guided-best-lp/seed.txt"),
    (
        "regular-8",
        "experiments/2026-10-03/essential-regular-heuristic/pilot-2026100317-h8-u0-p0.txt",
    ),
    (
        "sqs-23",
        "experiments/scratch/sqs-pool-heuristic-20261003/pilot-2026104021/native/best-23.txt",
    ),
    (
        "native-cycle-12",
        "experiments/2026-10-03/four-seven-template-native-soft/cycle-raw-best.txt",
    ),
    ("g1-initial-13", "experiments/2026-10-04/nearest-step038-g1-lp/seed.txt"),
    ("g1-best-17", None),
    ("g5-raw-17", "experiments/2026-10-03/four-seven-template-native-soft/matching-raw-best.txt"),
    (
        "g5-score-19",
        "experiments/2026-10-03/four-seven-template-native-soft/matching-score-best.txt",
    ),
]
CORE_PATH = "experiments/2026-10-03/partial-core-holes/core.txt"
NEW_CORE_MAP = [1, 7, 2, 10, 15, 3, 8, 11, 4, 9, 12, 16, 14, 6, 5, 13]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    rows = [tuple(map(int, row.split())) for row in path.read_text().splitlines() if row.strip()]
    assert all(len(row) == 5 and len(set(row)) == 5 for row in rows)
    assert all(row == tuple(sorted(row)) and min(row) >= 1 and max(row) <= 16 for row in rows)
    assert len(set(rows)) == len(rows)
    return sorted(rows)


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def histogram(values):
    return {str(k): v for k, v in sorted(Counter(values).items())}


def main():
    universe = list(combinations(range(1, 17), 5))
    triples = list(combinations(range(1, 17), 3))
    core = read(ROOT / CORE_PATH)
    old_manifest_path = ROOT / "experiments/2026-10-04/nearest-step038-g1-lp/manifest.json"
    result_path = ROOT / "experiments/2026-10-04/g1-link-descent/result.json"
    old_manifest = json.loads(old_manifest_path.read_text())
    result = json.loads(result_path.read_text())
    assembled = sorted(
        [universe[i] for i in result["best_heavy_global_ids"]]
        + [tuple(b) for b in old_manifest["retained_ordinary_blocks"]]
    )
    assert len(assembled) == len(set(assembled)) == 64
    assembled_path = OUT / "g1-best-17.txt"
    assembled_path.write_text("".join(" ".join(map(str, b)) + "\n" for b in assembled))
    entries = []
    block_sets = []
    for name, source in CASES:
        witness = OUT / f"{name}.txt"
        if source is not None:
            shutil.copyfile(ROOT / source, witness)
        blocks = read(witness)
        assert len(blocks) == 64
        counts = Counter(t for b in blocks for t in combinations(b, 3))
        degrees = Counter(p for b in blocks for p in b)
        pairs = Counter(p for b in blocks for p in combinations(b, 2))
        missing = [t for t in triples if not counts[t]]
        canonical = "".join(" ".join(map(str, b)) + "\n" for b in blocks)
        canonical_hash = sha256(canonical.encode()).hexdigest()
        receipts = {}
        for key, command in [
            ("package", ["uv", "run", "covering64", "verify"]),
            ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
        ]:
            proc = subprocess.run(
                command + [str(witness), "--expected-blocks", "64"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            assert proc.returncode == 1 and not proc.stderr
            parsed = json.loads(proc.stdout)
            assert parsed["blocks"] == 64 and not parsed["valid"]
            assert parsed["canonical_sha256"] == canonical_hash
            assert {tuple(t) for t in parsed["uncovered"]} == set(missing)
            receipt = OUT / f"{name}-{key}.json"
            receipt.write_text(proc.stdout)
            receipts[key] = {
                "path": str(receipt.relative_to(ROOT)),
                "sha256": digest(receipt),
                "exit_code": proc.returncode,
            }
        mapping = (
            list(range(1, 17))
            if name == "unrestricted-old-3"
            else (NEW_CORE_MAP if name == "unrestricted-new-3" else None)
        )
        if mapping is not None:
            mapped = {tuple(sorted(mapping[p - 1] for p in b)) for b in core}
            assert len(mapped) == 60 and mapped <= set(blocks)
        entries.append(
            {
                "name": name,
                "path": str(witness.relative_to(ROOT)),
                "source_path": source,
                "source_sha256": digest(ROOT / source) if source else None,
                "sha256": digest(witness),
                "canonical_sha256": canonical_hash,
                "blocks": 64,
                "holes": len(missing),
                "uncovered": missing,
                "degree_histogram": histogram(degrees[p] for p in range(1, 17)),
                "pair_histogram": histogram(pairs[p] for p in combinations(range(1, 17), 2)),
                "triple_histogram": histogram(counts[t] for t in triples),
                "original_label_core_overlap": len(set(blocks) & set(core)),
                "known_checked_core_map_images": mapping,
                "core_search_performed": False,
                "verifiers": receipts,
            }
        )
        block_sets.append(set(blocks))
        print(name, len(missing), digest(witness), flush=True)
    assert len({entry["canonical_sha256"] for entry in entries}) == 10
    audit = {
        "source_sha256": digest(Path(__file__)),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "optimization_calls": 0,
        "entries": entries,
        "core_path": CORE_PATH,
        "core_sha256": digest(ROOT / CORE_PATH),
        "g1_assembly_inputs": {
            str(p.relative_to(ROOT)): digest(p) for p in [old_manifest_path, result_path]
        },
        "pairwise_common_blocks": [[len(a & b) for b in block_sets] for a in block_sets],
        "union_block_count": len(set.union(*block_sets)),
        "claim": "Ten 64-block partial states; no covering witness or lower-bound claim.",
    }
    dump(OUT / "inventory.json", audit)


if __name__ == "__main__":
    main()
