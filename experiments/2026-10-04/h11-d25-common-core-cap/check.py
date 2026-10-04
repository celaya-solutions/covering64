# Document:    Independent H11 D25 Common Core Overlap Cap
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2504126e3245d67dc2d723e158770df4dec340c7afe311a088d5e2015fc8e586
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Pin the common core and check every block carrier without a solver."""

import copy
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from covering64.core import verify_cover

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "weak-pair-neutral-queue-runtime-independent/postcheck.json"
SOURCE_SHA = "fd044b1f88955403181b2d6ac739526c2d27ded14b0cff66f36a59d40a1cdde3"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
BLOCKSETS = list(map(set, BLOCKS))
TRIPLES = set(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(rows):
    return "".join(" ".join(map(str, row)) + "\n" for row in sorted(rows))


def normalize(rows, count, width):
    assert isinstance(rows, list) and len(rows) == count
    for row in rows:
        assert isinstance(row, (list, tuple)) and len(row) == width
        assert all(type(p) is int and 1 <= p <= 16 for p in row)
        assert list(row) == sorted(set(row))
    tuples = [tuple(row) for row in rows]
    assert tuples == sorted(set(tuples))
    return tuples


def check_certificate(payload, expected_core):
    core = normalize(payload["core"], 62, 5)
    assert core == expected_core
    holes = normalize(payload["holes"], 15, 3)
    covered = {t for block in core for t in itertools.combinations(block, 3)}
    assert holes == sorted(TRIPLES - covered)
    counts = payload["carrier_counts"]
    assert isinstance(counts, list) and len(counts) == 4368
    assert all(type(c) is int and c >= 0 for c in counts)
    assert counts == [sum(set(t) <= b for t in holes) for b in BLOCKSETS]
    assert max(counts) == 2
    assert all(len(set(a) & set(b)) <= 1 for a, b in itertools.combinations(holes, 2))
    assert all(len(set().union(*map(set, ts))) >= 6 for ts in itertools.combinations(holes, 3))
    required_outside = (len(holes) + max(counts) - 1) // max(counts)
    assert type(payload["minimum_outside"]) is int
    assert type(payload["exact_64_overlap_cap"]) is int
    assert payload["minimum_outside"] == required_outside == 8
    assert payload["exact_64_overlap_cap"] == 64 - required_outside == 56


def main():
    assert sha(SOURCE) == SOURCE_SHA
    data = json.loads(SOURCE.read_text())
    assert data["passed"] is True
    bank = [
        f for f in data["families"] if (f["metrics"]["holes"], f["metrics"]["D2max"]) == (11, 25)
    ]
    assert len(bank) == 28 and len({f["sha256"] for f in bank}) == 28
    spec = importlib.util.spec_from_file_location(
        "standalone_core_cap", ROOT / "scripts/check_cover.py"
    )
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    member_receipts = []
    for family in bank:
        ids = family["ids"]
        assert isinstance(ids, list) and len(ids) == 64
        assert all(type(i) is int and 0 <= i < 4368 for i in ids)
        assert ids == sorted(set(ids))
        rows = [BLOCKS[i] for i in ids]
        path = ROOT / family["path"]
        assert canonical(rows).encode() == path.read_bytes()
        assert sha(path) == family["sha256"]
        package = verify_cover(rows)
        separate = standalone.verify_cover(rows, expected_blocks=64)
        assert package["valid"] is False and separate["valid"] is False
        assert len(package["uncovered"]) == separate["uncovered_count"] == 11
        assert separate["cardinality_matches"] is True
        assert package["canonical_sha256"] == separate["canonical_sha256"] == family["sha256"]
        member_receipts.append(
            {
                "path": family["path"],
                "sha256": family["sha256"],
                "ids": ids,
                "fresh_missing_triples": 11,
                "dual_verifiers_agree": True,
                "saved_audited_D2max": 25,
            }
        )
    common_ids = sorted(set.intersection(*(set(f["ids"]) for f in bank)))
    assert len(common_ids) == 62
    core = [BLOCKS[i] for i in common_ids]
    covered = {t for b in core for t in itertools.combinations(b, 3)}
    holes = sorted(TRIPLES - covered)
    counts = [sum(set(t) <= b for t in holes) for b in BLOCKSETS]
    payload = {
        "core": [list(b) for b in core],
        "holes": [list(t) for t in holes],
        "carrier_counts": counts,
        "minimum_outside": 8,
        "exact_64_overlap_cap": 56,
    }
    check_certificate(payload, core)
    package = verify_cover(core)
    separate = standalone.verify_cover(core, expected_blocks=62)
    assert not package["valid"] and not separate["valid"] and separate["cardinality_matches"]
    assert (
        sorted(map(tuple, package["uncovered"]))
        == sorted(map(tuple, separate["uncovered"]))
        == holes
    )
    all_package = verify_cover(BLOCKS)
    all_separate = standalone.verify_cover(BLOCKS, expected_blocks=4368)
    assert all_package["valid"] and all_separate["valid"]

    bad = []

    def damage(name, mutate):
        record = copy.deepcopy(payload)
        mutate(record)
        bad.append((name, record))

    damage("core_duplicate", lambda x: x["core"].__setitem__(1, x["core"][0]))
    damage("core_removed", lambda x: x["core"].pop())
    damage("core_zero_label", lambda x: x["core"][0].__setitem__(0, 0))
    damage("core_label_17", lambda x: x["core"][0].__setitem__(4, 17))
    damage("core_boolean_label", lambda x: x["core"][0].__setitem__(0, True))
    damage("core_repeated_label", lambda x: x["core"][0].__setitem__(0, x["core"][0][1]))
    damage("core_wrong_width", lambda x: x["core"][0].pop())
    damage("hole_removed", lambda x: x["holes"].pop())
    damage("hole_duplicate", lambda x: x["holes"].__setitem__(1, x["holes"][0]))
    covered_triple = min(covered)
    damage("covered_triple_as_hole", lambda x: x["holes"].__setitem__(0, list(covered_triple)))
    damage("carrier_removed", lambda x: x["carrier_counts"].pop())
    damage("carrier_count_changed", lambda x: x["carrier_counts"].__setitem__(0, counts[0] + 1))
    damage("carrier_boolean", lambda x: x["carrier_counts"].__setitem__(0, False))
    damage("outside_bound_weakened", lambda x: x.__setitem__("minimum_outside", 7))
    damage("overlap_cap_weakened", lambda x: x.__setitem__("exact_64_overlap_cap", 57))
    damage("outside_bound_float", lambda x: x.__setitem__("minimum_outside", 8.0))
    damage("overlap_cap_float", lambda x: x.__setitem__("exact_64_overlap_cap", 56.0))
    damage_controls = {}
    for name, record in bad:
        try:
            check_certificate(record, core)
        except AssertionError:
            damage_controls[name] = "rejected"
        else:
            raise AssertionError("damaged certificate accepted: " + name)

    core_path, holes_path, counts_path = (
        HERE / "core-62.txt",
        HERE / "holes-15.txt",
        HERE / "carrier-counts.json",
    )
    core_path.write_text(canonical(core))
    holes_path.write_text(canonical(holes))
    counts_path.write_text(json.dumps(counts, separators=(",", ":")) + "\n")
    result = {
        "passed": True,
        "source_postcheck_path": str(SOURCE.relative_to(ROOT)),
        "source_postcheck_sha256": sha(SOURCE),
        "checker_sha256": sha(Path(__file__)),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python_version": sys.version.split()[0],
        "package_verifier_sha256": sha(Path(verify_cover.__code__.co_filename)),
        "standalone_verifier_sha256": sha(ROOT / "scripts/check_cover.py"),
        "bank": member_receipts,
        "bank_size": 28,
        "core_ids": common_ids,
        "core_path": str(core_path.relative_to(ROOT)),
        "core_sha256": sha(core_path),
        "holes_path": str(holes_path.relative_to(ROOT)),
        "holes_sha256": sha(holes_path),
        "carrier_counts_path": str(counts_path.relative_to(ROOT)),
        "carrier_counts_sha256": sha(counts_path),
        "carrier_order": (
            "All combinations of five labels from 1..16 in lexicographic order; "
            "index 0 based."
        ),
        "carrier_histogram": dict(sorted(Counter(counts).items())),
        "hole_pair_intersection_histogram": dict(
            sorted(
                Counter(len(set(a) & set(b)) for a, b in itertools.combinations(holes, 2)).items()
            )
        ),
        "hole_triple_union_histogram": dict(
            sorted(
                Counter(
                    len(set().union(*map(set, ts))) for ts in itertools.combinations(holes, 3)
                ).items()
            )
        ),
        "core_dual_verifiers": {"package": package, "standalone": separate},
        "positive_control": {
            "description": "Entire 4368-block universe; valid cover, not a 64-block candidate.",
            "package_valid": all_package["valid"],
            "standalone_valid": all_separate["valid"],
        },
        "minimum_outside_core": 8,
        "exact_64_overlap_cap": 56,
        "dual_certificate": {
            "hole_weight_numerator": 1,
            "hole_weight_denominator": 2,
            "hole_count": 15,
            "maximum_block_load_numerator": 2,
            "maximum_block_load_denominator": 2,
            "required_outside_fractional_numerator": 15,
            "required_outside_fractional_denominator": 2,
            "integer_rounding": "ceil(15/2) = 8",
        },
        "damage_controls": damage_controls,
        "solver_calls": 0,
        "scope": (
            "Every exact 64 cover has overlap at most 56 with this pinned core; "
            "invariant under relabeling. No global nonexistence claim."
        ),
    }
    output = HERE / "certificate.json"
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "core_sha256": sha(core_path),
                "certificate_sha256": sha(output),
                "damaged_controls_rejected": len(damage_controls),
            }
        )
    )


if __name__ == "__main__":
    main()
