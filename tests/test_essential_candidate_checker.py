# Document:    Essential Candidate Recount and Invariant Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      9c59b718b6a5d0abda2d27a71555739a44982314abdeb4e5962c29a57529a843
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "essential_candidate_checker", ROOT / "scripts/verify_essential_heuristic.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)
FOLDER = ROOT / "experiments/2026-10-03/essential-regular-heuristic"
BASE = (FOLDER / "pilot-2026100317-h8-u0-p0.txt").read_text()


def test_recount_essential_regular_seed():
    result = CHECKER.analyze(BASE)
    assert result["holes"] == 8
    assert result["unsupported_count"] == result["pair_deficit"] == 0
    assert result["degree20"] is True
    assert result["pair_histogram"] == {5: 92, 6: 16, 7: 12}
    assert result.get("heavy_excess") == 2


def test_point_relabeling_and_block_reordering_preserve_fingerprint():
    rows = [tuple(int(x) % 16 + 1 for x in row.split()) for row in BASE.splitlines()]
    text = "".join(" ".join(map(str, sorted(row))) + "\n" for row in reversed(rows))
    before = CHECKER.analyze(BASE)
    after = CHECKER.analyze(text)
    assert before["invariant_fingerprint"] == after["invariant_fingerprint"]
    assert before["canonical_sha256"] != after["canonical_sha256"]


def test_saved_diversity_seeds_have_distinct_fingerprints():
    paths = sorted(FOLDER.glob("diversity-2026100318-variant-*-h8-u0-p0.txt"))
    assert len(paths) == 7
    assert len({CHECKER.analyze(p.read_text())["invariant_sha256"] for p in paths}) == 7


def test_damaged_heavy_score_filename_is_rejected(tmp_path):
    path = tmp_path / "incorrect-heavy-e0-h8-u0-p0.txt"
    path.write_text(BASE)
    with pytest.raises(ValueError, match="heavy score"):
        CHECKER.verify(path)


@pytest.mark.parametrize("damage", ["duplicate_block", "duplicate_point", "out_of_range", "junk"])
def test_invalid_candidates_rejected(damage):
    rows = BASE.splitlines()
    if damage == "duplicate_block":
        rows[1] = rows[0]
    elif damage == "duplicate_point":
        tokens = rows[0].split()
        tokens[1] = tokens[0]
        rows[0] = " ".join(tokens)
    elif damage == "out_of_range":
        rows[0] = "17 " + " ".join(rows[0].split()[1:])
    else:
        rows[0] += " junk"
    with pytest.raises(ValueError):
        CHECKER.analyze("\n".join(rows) + "\n")
