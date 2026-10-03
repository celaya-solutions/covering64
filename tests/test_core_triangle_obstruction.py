# Document:    Core triangle obstruction certificate controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      1560cb91e4d21713f0396a55775511b236424991e60cff89dcda43092314363a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_core_triangle_obstruction import check_data  # noqa: E402


@pytest.fixture(scope="module")
def certificate():
    path = ROOT / "experiments/2026-10-03/core-five-scan/five-removal-triangle.json"
    return json.loads(path.read_text())


def test_exact_triangle_obstruction(certificate):
    result = check_data(certificate)
    assert result["complete_obstruction"] is True
    assert result["tight_blocks"] == 50
    assert result["all_possible_blocks_checked"] == 4368
    assert result["exact_dual_bound"] == [9, 1]


@pytest.mark.parametrize("damage", [
    "duplicate_core", "duplicate_removed", "denominator", "duplicate_weight", "dual_sum",
    "bad_carriers", "unweighted_conflict", "wrong_conflict", "duplicate_special", "bool_weight",
])
def test_rejects_damaged_triangle(certificate, damage):
    data = copy.deepcopy(certificate)
    if damage == "duplicate_core":
        data["core_blocks"][1] = data["core_blocks"][0]
    elif damage == "duplicate_removed":
        data["removed"][1] = data["removed"][0]
    elif damage == "denominator":
        data["denominator"] = 0
    elif damage == "duplicate_weight":
        data["weights"].append(data["weights"][0])
    elif damage == "dual_sum":
        data["weights"][0][1] += 1
    elif damage == "bad_carriers":
        data["required_triples"][0] = [1, 2, 3]
    elif damage == "unweighted_conflict":
        data["conflict_triples"][0] = [1, 4, 6]
    elif damage == "wrong_conflict":
        data["conflict_triples"][0] = [1, 3, 4]
    elif damage == "duplicate_special":
        data["special_blocks"][1] = data["special_blocks"][0]
    elif damage == "bool_weight":
        data["weights"][0][1] = True
    with pytest.raises(ValueError):
        check_data(data)
