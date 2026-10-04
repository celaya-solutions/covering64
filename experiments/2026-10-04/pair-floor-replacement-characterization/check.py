# Document:    Pair-Floor One-Block Replacement Characterization
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      fbcb098aa622e70c7548d530b3fe06c27118c0b214a78a6a1a9e5a49b0bb5299
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import itertools
import json
import math
import platform
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "soft-pair-h12-relabel-novelty/final-family.txt"
INPUT_SHA = "cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970"
PROFILE = HERE.parent / "soft-pair-h12-relabel-novelty/diagnostic.json"
PROFILE_SHA = "2b2dd335c596222a3b6a597a6ee41edde500cc224172a866041378c9fd39d490"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: i for i, block in enumerate(BLOCKS)}
PAIRS = list(itertools.combinations(range(1, 17), 2))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(blocks):
    if len(blocks) != 64 or len(set(blocks)) != 64:
        raise ValueError("64 distinct blocks required")
    if blocks != sorted(blocks) or any(block not in RANK for block in blocks):
        raise ValueError("canonical five-point blocks with labels 1..16 required")


def main():
    output = HERE / "characterization.json"
    assert not output.exists(), "preserve completed characterization"
    assert sha(INPUT) == INPUT_SHA and sha(PROFILE) == PROFILE_SHA
    blocks = [tuple(map(int, line.split())) for line in INPUT.read_text().splitlines()]
    validate(blocks)
    counts = Counter(pair for block in blocks for pair in itertools.combinations(block, 2))
    assert len(counts) == 120 and min(counts.values()) == 5
    assert sum(counts.values()) == 640
    receipts = []
    for name, command in (
        ("package", ["uv", "run", "covering64", "verify"]),
        ("standalone", [sys.executable, "scripts/check_cover.py"]),
    ):
        checked = subprocess.run(
            command + [str(INPUT), "--expected-blocks", "64"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        data = json.loads(checked.stdout)
        assert checked.returncode == 1 and not checked.stderr
        assert data["blocks"] == 64 and data["valid"] is False
        assert len(data["uncovered"]) == 12 and data["canonical_sha256"] == INPUT_SHA
        path = HERE / f"input-{name}.json"
        path.write_text(checked.stdout)
        receipts.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path)})
    invalid = {
        "duplicate": sorted(blocks[:-1] + [blocks[0]]),
        "wrong_label": sorted([(0, 2, 3, 4, 5)] + blocks[1:]),
        "short_family": blocks[:-1],
        "wrong_order": blocks[::-1],
    }
    for damaged in invalid.values():
        try:
            validate(damaged)
        except ValueError:
            pass
        else:
            raise AssertionError("damaged input accepted")
    incumbent = set(blocks)
    outside = [(i, block, set(block)) for i, block in enumerate(BLOCKS) if block not in incumbent]
    assert len(outside) == 4304
    started = time.monotonic()
    rows, tested, eligible_total = [], 0, 0
    eligible_additions, histogram, eligible_by_size = set(), Counter(), Counter()
    for removed in blocks:
        critical = [pair for pair in itertools.combinations(removed, 2) if counts[pair] == 5]
        forced = set().union(*map(set, critical)) if critical else set()
        size = len(forced)
        histogram[size] += 1
        formula = math.comb(16 - size, 5 - size) - sum(forced <= set(block) for block in blocks)
        # Freshly count the remaining 63 blocks, independently of the critical-pair reduction.
        remaining = Counter(
            pair
            for block in blocks
            if block != removed
            for pair in itertools.combinations(block, 2)
        )
        assert len(remaining) == 120 and min(remaining.values()) >= 4
        direct_bits, forced_bits = bytearray(), bytearray()
        omission_controls = {point: None for point in forced}
        eligible = 0
        for incoming_id, incoming, incoming_set in outside:
            direct = remaining.copy()
            direct.update(itertools.combinations(incoming, 2))
            direct_ok = all(direct[pair] >= 5 for pair in PAIRS)
            forced_ok = forced <= incoming_set
            edge_ok = all(set(pair) <= incoming_set for pair in critical)
            assert direct_ok == forced_ok == edge_ok, (removed, incoming)
            direct_bits.append(direct_ok)
            forced_bits.append(forced_ok)
            tested += 1
            if direct_ok:
                eligible += 1
                eligible_additions.add(incoming_id)
            for point in forced:
                if (
                    omission_controls[point] is None
                    and not direct_ok
                    and forced - {point} <= incoming_set
                ):
                    omission_controls[point] = incoming_id
        assert eligible == formula
        assert all(value is not None for value in omission_controls.values())
        eligible_total += eligible
        eligible_by_size[size] += eligible
        rows.append(
            {
                "removed_block": removed,
                "removed_global_id": RANK[removed],
                "critical_pairs": critical,
                "forced_points": sorted(forced),
                "forced_size": size,
                "allowed_by_formula": formula,
                "allowed_by_direct_recount": eligible,
                "outside_additions_checked": len(outside),
                "direct_bitmap_sha256": hashlib.sha256(direct_bits).hexdigest(),
                "forced_bitmap_sha256": hashlib.sha256(forced_bits).hexdigest(),
                "omitted_endpoint_counterexample_ids": omission_controls,
            }
        )
    assert tested == 64 * 4304 == 275456
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "candidate_rankings": 0,
        "checker_sha256": sha(Path(__file__)),
        "input_path": str(INPUT.relative_to(ROOT)),
        "input_sha256": INPUT_SHA,
        "profile_sha256": PROFILE_SHA,
        "python_version": platform.python_version(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "input_minimum_pair_count": 5,
        "input_pair_histogram": dict(sorted(Counter(counts.values()).items())),
        "forced_size_histogram": dict(sorted(histogram.items())),
        "eligible_neighbors_by_forced_size": dict(sorted(eligible_by_size.items())),
        "eligible_neighbor_count": eligible_total,
        "distinct_eligible_added_blocks": len(eligible_additions),
        "all_replacements_checked": tested,
        "direct_recount_disagreements": 0,
        "elapsed_seconds": time.monotonic() - started,
        "malformed_input_controls_rejected": list(invalid),
        "verifiers": receipts,
        "blocks": rows,
        "scope": "Exact pair-floor-only characterization for one replacement of this fixed "
        "64-block H12 incumbent. No objective, ranking, optimizer, "
        "weaker/stronger-row eligibility, "
        "covering witness, multiblock reduction, or global conclusion is claimed.",
    }
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "passed",
                    "all_replacements_checked",
                    "forced_size_histogram",
                    "eligible_neighbors_by_forced_size",
                    "eligible_neighbor_count",
                    "distinct_eligible_added_blocks",
                    "elapsed_seconds",
                )
            },
            sort_keys=True,
        )
    )
    print("characterization_sha256", sha(output))


if __name__ == "__main__":
    main()
