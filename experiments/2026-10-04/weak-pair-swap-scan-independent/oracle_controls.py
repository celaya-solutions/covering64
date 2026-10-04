# Document:    Independent Weak-Pair Fixed Swap Recounts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      3192eb0907ee488baa708af573ecd84dacc0568cfddad213739cccafc1ab6e3a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Create direct-count expectations for a finite declared set of control swaps."""

import hashlib
import json
from pathlib import Path

import oracle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-swap-scan-independent-20261004"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = RAW / "oracle-snapshots.json"
    oracle.require(not output.exists(), "preserve prior oracle snapshots")
    RAW.mkdir(parents=True, exist_ok=True)
    cases = json.loads((HERE / "cases.json").read_text())
    core_source = ROOT / "experiments/2026-10-04/soft-pair-h12-start/manifest.json"
    cores = json.loads(core_source.read_text())["core_rows"]
    bases = {}
    for name in ("old_h12", "cp_final"):
        source = ROOT / cases[name]["path"]
        oracle.require(sha(source) == cases[name]["sha256"], "changed base")
        ids = oracle.parse(source)
        bases[name] = {"ids": ids, **oracle.analyze(ids, cores)}
        oracle.require(bases[name]["legal"], "control base illegal")
    snapshots, dependency_checks = [], 0
    for case in cases["cases"]:
        base = bases[case["base"]]
        outgoing, incoming = case["out"], case["in"]
        oracle.require(outgoing in base["ids"] and incoming not in base["ids"], "bad case")
        ids = sorted((set(base["ids"]) - {outgoing}) | {incoming})
        after = oracle.analyze(ids, cores)
        outmask, inmask = (oracle.MASKS[5][i] for i in (outgoing, incoming))
        oracle.require((outmask & inmask).bit_count() == case["intersection"], "overlap")
        affected = [
            i
            for i, pair in enumerate(oracle.MASKS[2])
            if pair & outmask == pair or pair & inmask == pair
        ]
        for size in (2, 3, 4):
            for index, mask in enumerate(oracle.MASKS[size]):
                delta = int(mask & inmask == mask) - int(mask & outmask == mask)
                oracle.require(
                    after["counts"][size][index] == base["counts"][size][index] + delta,
                    "direct count delta mismatch",
                )
                dependency_checks += 1
        for index in range(120):
            if index not in affected:
                oracle.require(
                    after["pair_metrics"][index] == base["pair_metrics"][index],
                    "changed row outside affected union",
                )
        snapshots.append({"case": case, "ids": ids, "affected_pairs": affected, **after})
    oracle.require(len(snapshots) == 50, "unexpected fixed control count")
    old, new = bases["old_h12"]["metrics"], bases["cp_final"]["metrics"]
    oracle.require(
        old["holes"] == new["holes"] == 12 and old["D2max"] == 34 and new["D2max"] == 32,
        "positive control changed",
    )
    record = {
        "bases": bases,
        "snapshots": snapshots,
        "core_rows": cores,
        "core_source_sha256": sha(core_source),
        "oracle_sha256": sha(HERE / "oracle.py"),
        "source_sha256": sha(Path(__file__)),
        "cases_sha256": sha(HERE / "cases.json"),
        "dependency_checks": dependency_checks,
        "optimizer_launches": 0,
    }
    output.write_text(json.dumps(record, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "fixed_cases": len(snapshots),
                "dependency_checks": dependency_checks,
                "snapshot_sha256": sha(output),
            }
        )
    )


if __name__ == "__main__":
    main()
