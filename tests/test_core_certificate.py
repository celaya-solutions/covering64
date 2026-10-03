# Document:    Standalone dual certificate controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Positive and damaged controls for solver-independent obstruction checks."""

import copy
import gzip
import importlib.util
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_core", ROOT / "scripts/check_core_certificate.py"
)
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


@pytest.fixture
def certificate():
    blocks = [tuple(map(int, line.split()))
              for line in (ROOT / "data/baselines/belic-1997.txt").read_text().splitlines()
              if line.strip() and not line.startswith("#")]
    counts = Counter(t for b in blocks for t in combinations(b, 3))
    core = [b for b in blocks
            if len({p for t in combinations(b, 3) if counts[t] == 1 for p in t}) == 5]
    covered = {t for b in core for t in combinations(b, 3)}
    missing = [i for i, t in enumerate(combinations(range(1, 17), 3)) if t not in covered]
    return {"v": 16, "k": 5, "t": 3, "target": 64, "core": core,
            "maximum_removed": 0, "records": [{"removed_core_indices": [],
                                                "weights": [[t, 1, 3] for t in missing],
                                                "lower_bound": [5, 1]}]}


def test_exact_positive_control(certificate, tmp_path):
    path = tmp_path / "certificate.json"
    path.write_text(json.dumps(certificate))
    result = CHECKER.check(path)
    assert result["valid"]
    assert result["minimum_exact_margin"] == "1"
    assert result["checked_neighborhoods"] == 1
    compressed = tmp_path / "certificate.json.gz"
    compressed.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    assert CHECKER.check(compressed)["valid"]


@pytest.mark.parametrize("damage", ["capacity", "false_sum", "duplicate_core", "missing_record",
                                    "repeated_weight", "bad_denominator", "bool_label"])
def test_damaged_controls(certificate, tmp_path, damage):
    bad = copy.deepcopy(certificate)
    record = bad["records"][0]
    if damage == "capacity":
        record["weights"] = [[t, n * 2, d] for t, n, d in record["weights"]]
        record["lower_bound"] = [10, 1]
    elif damage == "false_sum":
        record["lower_bound"] = [6, 1]
    elif damage == "duplicate_core":
        bad["core"][1] = bad["core"][0]
    elif damage == "missing_record":
        bad["records"] = []
    elif damage == "repeated_weight":
        record["weights"].append(record["weights"][0])
    elif damage == "bad_denominator":
        record["weights"][0][2] = 0
    elif damage == "bool_label":
        bad["core"][0] = [True, 2, 3, 4, 5]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        CHECKER.check(path)
