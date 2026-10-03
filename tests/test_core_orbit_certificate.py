# Document:    Core orbit certificate rejection controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5ad5b24e78bd1cadfee0badefce352bee165572a61c09085aec145987f645a73
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Exercise exact certificate checks independently of LP generation."""

import copy
import gzip
import json
import subprocess
import sys
from itertools import combinations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.check_core_orbit_certificate import check_data  # noqa: E402

CHECKER = ROOT / "scripts/check_core_orbit_certificate.py"
CERTIFICATE = ROOT / "experiments/2026-10-03/core-orbit/core-remove-3.json.gz"


@pytest.fixture(scope="module")
def certificate():
    return json.loads(gzip.decompress(CERTIFICATE.read_bytes()))


def test_complete_three_removal_certificate(certificate):
    result = check_data(certificate)
    assert result["complete_obstruction"] is True
    assert result["all_removal_sets_checked"] == 34220
    assert result["maximum_core_blocks_in_any_64_cover"] == 56


@pytest.mark.parametrize("damage", [
    "duplicate_core", "bad_generator", "nonpreserving_group", "zero_denominator",
    "duplicate_weight",
    "covered_weight", "over_capacity", "missing_orbit", "duplicate_orbit",
    "wrong_orbit_size", "boolean_orbit_size", "duplicate_removal", "false_claim",
])
def test_rejects_damaged_certificate(certificate, damage):
    data = copy.deepcopy(certificate)
    case = data["cases"][0]
    if damage == "duplicate_core":
        data["core_blocks"][1] = data["core_blocks"][0]
    elif damage == "bad_generator":
        data["generators"][0][0] = data["generators"][0][1]
    elif damage == "nonpreserving_group":
        swap = list(range(1, 17))
        swap[0], swap[6] = swap[6], swap[0]
        data["generators"] = [
            [swap[generator[swap[p - 1] - 1] - 1] for p in range(1, 17)]
            for generator in data["generators"]]
    elif damage == "zero_denominator":
        case["denominator"] = 0
    elif damage == "duplicate_weight":
        case["weights"].append(case["weights"][0])
    elif damage == "covered_weight":
        retained = next(b for i, b in enumerate(data["core_blocks"], 1)
                        if i not in case["removed"])
        triple = tuple(retained[:3])
        triple_index = list(combinations(range(1, 17), 3)).index(triple)
        case["weights"].append([triple_index, 1])
    elif damage == "over_capacity":
        case["weights"][0][1] = case["denominator"]
    elif damage == "missing_orbit":
        data["cases"].pop()
    elif damage == "duplicate_orbit":
        data["cases"].append(case)
    elif damage == "wrong_orbit_size":
        case["orbit_size"] = 1 if case["orbit_size"] != 1 else 2
    elif damage == "boolean_orbit_size":
        case["orbit_size"] = True
    elif damage == "duplicate_removal":
        case["removed"][1] = case["removed"][0]
    elif damage == "false_claim":
        case["weights"] = []
    expected = {
        "nonpreserving_group": "Point action does not preserve core",
        "over_capacity": "Dual exceeds an added block's capacity",
        "missing_orbit": "Some removal sets have no transported certificate",
        "duplicate_orbit": "Overlapping or duplicate removal orbits",
        "false_claim": "False completeness declaration",
    }.get(damage)
    with pytest.raises(ValueError, match=expected):
        check_data(data)


def test_valid_but_weak_certificate_is_inconclusive(certificate, tmp_path):
    data = copy.deepcopy(certificate)
    data["cases"][0]["weights"] = []
    data["claimed_complete"] = False
    path = tmp_path / "weak.json"
    path.write_text(json.dumps(data))
    result = subprocess.run([sys.executable, str(CHECKER), str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["valid_certificate"] is True
    assert output["complete_obstruction"] is False
    assert "maximum_core_blocks_in_any_64_cover" not in output


@pytest.mark.parametrize("filename,content", [
    ("bad.json", b"{broken"), ("bad.json.gz", b"not gzip"),
    ("truncated.json.gz", gzip.compress(b"{}")[:-3]),
])
def test_cli_rejects_unreadable_certificate(tmp_path, filename, content):
    path = tmp_path / filename
    path.write_bytes(content)
    result = subprocess.run([sys.executable, str(CHECKER), str(path)],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert json.loads(result.stdout)["valid_certificate"] is False
