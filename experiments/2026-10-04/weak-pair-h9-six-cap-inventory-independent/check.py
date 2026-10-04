# Document:    Independent H9 Six-Named-Cap Inventory Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      8dd47a6320e8086fa54cb1f99020eaa2aa9881a6f2186ace31bfb01097989947
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount 21 already saved families under a conditional sixth overlap cap."""

import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

from covering64.core import verify_cover

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normal(value):
    return json.loads(json.dumps(value))


def main():
    path = HERE / "inventory.json"
    assert sha(path) == "de1653eca6de927e511efd316d0893f870e9e8731afc6bd5091a72042c287b55"
    inventory = json.loads(path.read_text())
    runtime_path = BASE / "weak-pair-h9-d23-neutral-queue-runtime-independent/postcheck.json"
    assert (
        sha(runtime_path)
        == inventory["prior_runtime_sha256"]
        == ("89142fc4522bf21bbf4c34dd06a855113474b54d73b6f793250d207d72ec47f6")
    )
    runtime = json.loads(runtime_path.read_text())
    manifest_path = BASE / "weak-pair-h9-d23-neutral-queue/manifest.json"
    assert sha(manifest_path) == "64d63c5bee05e8ba8c5ca7bbb4f98b3258a6f3d6192297e792a4b62b12835d87"
    manifest = json.loads(manifest_path.read_text())
    oracle_path = BASE / "weak-pair-swap-scan-independent/oracle.py"
    assert sha(oracle_path) == "7fc14c0e2078894a03cc8945c94cb8f9987e79f4780d49558d311e83f0d0ba92"
    oracle = load("direct_six_cap_oracle", oracle_path)
    standalone = load("standalone_six_cap_cover", ROOT / "scripts/check_cover.py")
    assert (
        inventory["initial_sha256"]
        == manifest["initial"]["sha256"]
        == ("f5f24d57738763380c715769eef4328d7f1950a8ae6d0eedd8e9ff16dc3fc681")
    )
    sixth = set(inventory["sixth_core_ids"])
    assert sixth == set(manifest["initial"]["ids"]) and len(sixth) == 64
    assert inventory["sixth_overlap_threshold"] == 59
    assert inventory["sixth_cap_proof_status"] == "pending independent proof"
    assert inventory["old_five_thresholds"] == [55, 55, 55, 55, 56]
    assert len(inventory["families"]) == len(runtime["families"]) == 21
    assert [f["sha256"] for f in inventory["families"]] == [
        f["sha256"] for f in runtime["families"]
    ]
    qualified, multiplicity_rows = [], []
    for row in inventory["families"]:
        witness = ROOT / row["path"]
        assert sha(witness) == row["sha256"]
        ids = oracle.parse(witness)
        assert ids == row["ids"] and len(ids) == 64
        direct = oracle.analyze(ids, manifest["core_rows"])
        assert direct["metrics"] == row["metrics"]
        assert row["old_four_and_weak_pass"] is direct["legal"]
        fifth = len(set(ids) & set(manifest["observed_fifth_core"]["ids"]))
        overlap = len(set(ids) & sixth)
        passes = direct["legal"] and fifth <= 56 and overlap <= 59
        assert row["fifth_overlap"] == fifth and row["sixth_overlap"] == overlap
        assert row["conditional_six_caps_and_weak_pass"] is passes
        blocks = [oracle.SUBSETS[5][index] for index in ids]
        counts = Counter(triple for block in blocks for triple in itertools.combinations(block, 3))
        assert max(counts.values()) == max(direct["counts"][3])
        multiplicity_rows.append(
            {
                "sha256": row["sha256"],
                "maximum_triple_multiplicity": max(counts.values()),
                "sixth_overlap": overlap,
                "conditional_six_caps_and_weak_pass": passes,
            }
        )
        if passes:
            package = normal(verify_cover(blocks))
            separate = normal(standalone.verify_cover(blocks, expected_blocks=64))
            assert package["valid"] == separate["valid"] == (direct["metrics"]["holes"] == 0)
            assert package["uncovered"] == separate["uncovered"]
            assert separate["canonical_sha256"] == package["canonical_sha256"] == row["sha256"]
            assert row["fresh_dual_verifiers"] == {"package": package, "standalone": separate}
            qualified.append(row)
    qualified.sort(key=lambda f: (f["metrics"]["holes"], f["metrics"]["D2max"], f["ids"]))
    assert len(qualified) == inventory["qualified_count"] == 1
    assert (
        qualified[0]["sha256"]
        == inventory["selected_sha256"]
        == ("a0a737c4010f68fcd5bfba8ccc7c20b4b8d9f06a96bb0086c7a63dbfc43f5ecc")
    )
    supplement_path = HERE / "triple-multiplicity.json"
    assert (
        sha(supplement_path) == "6dc7dc61a8b0f33b7fc8b98d2262f25afdb82eaee284448b1aa715ec58f5858e"
    )
    supplement = json.loads(supplement_path.read_text())
    assert supplement["base_inventory_sha256"] == sha(path)
    assert supplement["families"] == multiplicity_rows
    assert supplement["histogram"] == {"3": 21}
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "inventory_sha256": sha(path),
        "runtime_sha256": sha(runtime_path),
        "manifest_sha256": sha(manifest_path),
        "oracle_sha256": sha(oracle_path),
        "triple_multiplicity_supplement_sha256": sha(supplement_path),
        "package_verifier_sha256": sha(ROOT / "src/covering64/core.py"),
        "standalone_verifier_sha256": sha(ROOT / "scripts/check_cover.py"),
        "families_recounted": 21,
        "qualified_count": 1,
        "selected_sha256": qualified[0]["sha256"],
        "selected_metrics": qualified[0]["metrics"],
        "selected_fifth_overlap": qualified[0]["fifth_overlap"],
        "selected_sixth_overlap": qualified[0]["sixth_overlap"],
        "maximum_triple_multiplicity_histogram": {"3": 21},
        "scope": (
            "Finite saved-family recount under a conditional sixth named-image overlap cap. "
            "This checker does not prove the sixth cap or any all-relabel cap."
        ),
        "optimizer_launches": 0,
    }
    output = HERE / "check.json"
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "check_sha256": sha(output), "qualified_count": 1}))


if __name__ == "__main__":
    main()
