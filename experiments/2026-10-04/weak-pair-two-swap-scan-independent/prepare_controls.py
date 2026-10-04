# Document:    Independent Two-Swap Forced-Support Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      9e699b7f446049d8954326581f621a02404108b48475778cebdc60759429bf62
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Finite control fixtures only; no neighborhood optimizer or full scan."""

import hashlib
import importlib.util
import itertools
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-two-swap-scan-independent-20261004"
ORACLE = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
BASE = HERE.parent / "weak-pair-swap-scan-runtime-independent/swap-881-1142.txt"
BASE_SHA = "44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = RAW / "control-expectations.json"
    assert not output.exists(), "preserve existing fixed controls"
    RAW.mkdir(parents=True, exist_ok=True)
    assert sha(BASE) == BASE_SHA
    spec = importlib.util.spec_from_file_location("fixed_independent_oracle", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    ids = oracle.parse(BASE)
    source = HERE.parent / "weak-pair-swap-scan/manifest.json"
    cores = json.loads(source.read_text())["core_rows"]
    baseline = oracle.analyze(ids, cores)
    assert baseline["legal"] and baseline["metrics"]["D2max"] == 29
    chosen = set(ids)
    absent = [i for i in range(4368) if i not in chosen]
    masks = oracle.MASKS[5]
    pair_masks = oracle.MASKS[2]
    pair_members = [
        {p for p, pair in enumerate(pair_masks) if pair & block == pair} for block in masks
    ]
    rng = random.Random(2026105001)
    outgoing_pairs = sorted(
        set(
            rng.sample(list(itertools.combinations(ids, 2)), 16)
            + [tuple(sorted((1142, i))) for i in ids[:12] if i != 1142]
        )
    )
    selected = {}
    inspected = 0
    for b, c in outgoing_pairs:
        candidates = set(rng.sample(absent, 24))
        for outgoing in (b, c):
            block = oracle.SUBSETS[5][outgoing]
            for removed in block:
                for added in oracle.POINTS:
                    if added not in block:
                        trial = tuple(sorted((set(block) - {removed}) | {added}))
                        index = oracle.RANK[trial]
                        if index not in chosen:
                            candidates.add(index)
        for a in sorted(candidates):
            inspected += 1
            counts = [
                value
                - int(p in pair_members[b])
                - int(p in pair_members[c])
                + int(p in pair_members[a])
                for p, value in enumerate(baseline["counts"][2])
            ]
            short = [p for p, value in enumerate(counts) if value < 5]
            worst = max((5 - counts[p] for p in short), default=0)
            support = 0
            for p in short:
                support |= pair_masks[p]
            category = (
                "deficit_gt1"
                if worst > 1
                else (
                    "support_gt5" if support.bit_count() > 5 else f"support_{support.bit_count()}"
                )
            )
            rows = selected.setdefault(category, [])
            if len(rows) < 5:
                rows.append(
                    {
                        "outgoing": [b, c],
                        "first_incoming": a,
                        "pair_counts": counts,
                        "worst_deficit": worst,
                        "support_mask": support,
                        "category": category,
                    }
                )
    fixtures = [row for category in sorted(selected) for row in selected[category]]
    completion_checks = 0
    final_snapshots = []
    for case in fixtures:
        b, c = case["outgoing"]
        a = case["first_incoming"]
        partial_ids = sorted((chosen - {b, c}) | {a})
        partial = oracle.analyze(partial_ids, cores)
        assert partial["counts"][2] == case["pair_counts"]
        feasible = []
        for d in absent:
            if d <= a:
                continue
            # Independent direct pair-floor check for every possible final block.
            passes = all(
                value + int(pair & masks[d] == pair) >= 5
                for pair, value in zip(pair_masks, case["pair_counts"], strict=True)
            )
            proposed = (
                case["worst_deficit"] <= 1
                and case["support_mask"].bit_count() <= 5
                and masks[d] & case["support_mask"] == case["support_mask"]
            )
            assert passes == proposed
            completion_checks += 1
            if passes:
                feasible.append(d)
        case["expected_completions"] = feasible
        case["partial"] = {"ids": partial_ids, **partial}
        for d in sorted(set(feasible[:1] + feasible[-1:])):
            final_ids = sorted((chosen - {b, c}) | {a, d})
            final_snapshots.append(
                {
                    "outgoing": [b, c],
                    "incoming": [a, d],
                    "ids": final_ids,
                    **oracle.analyze(final_ids, cores),
                }
            )
    assert any(case["category"] == "deficit_gt1" for case in fixtures)
    assert any(case["category"] == "support_gt5" for case in fixtures)
    assert final_snapshots, "need at least one pair-floor-completable control"
    record = {
        "source_sha256": sha(Path(__file__)),
        "oracle_sha256": sha(ORACLE),
        "base_path": str(BASE.relative_to(ROOT)),
        "base_sha256": BASE_SHA,
        "base_ids": ids,
        "baseline": baseline,
        "core_rows": cores,
        "control_seed": 2026105001,
        "finite_partial_states_considered": inspected,
        "fixtures": fixtures,
        "final_snapshots": final_snapshots,
        "completion_checks": completion_checks,
        "categories": {key: len(value) for key, value in selected.items()},
        "scope": "Finite reduction/counter controls, not a completed two-swap scan.",
        "optimizer_launches": 0,
    }
    output.write_text(json.dumps(record, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "fixtures": len(fixtures),
                "final_states": len(final_snapshots),
                "categories": record["categories"],
                "completion_checks": completion_checks,
                "sha256": sha(output),
            }
        )
    )


if __name__ == "__main__":
    main()
