# Document:    Independent Reduced Campaign Metric Audit
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b1c557a198a21dd0ecdba15d716b6505b8b3be5f3333bffa8d1b48a5a7343cf3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount recorded snapshots and check native metric and diversity claims."""

import argparse
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path


def structural_penalties(blocks, triples):
    """Independently count full-regular-cover defects from raw block containment."""
    pairs = Counter(pair for block in blocks for pair in combinations(block, 2))
    heavy = [triple for triple, count in triples.items() if count >= 6]
    result = {
        "h6": 0,
        "heavy_overlap": sum(len(set(a) & set(b)) for a, b in combinations(heavy, 2)),
        "repeated_point_excess": 0,
        "repeated_incidence_excess": 0,
        "endpoint_shape_distance": 0,
        "hub_inside_heavy": 0,
        "hub_collision": 0,
        "internal_pair_deficit": 0,
        "hub_internal_pair_excess": 0,
        "hub_cross_pair_deviation": 0,
        "refined_count_overflow": 0,
        "generic_pair_deficit": sum(
            max(0, 5 - pairs[pair]) for pair in combinations(range(1, 17), 2)
        ),
    }
    patterns = {
        6: [[0] + [1] * 12, [0] * 2 + [1] * 10 + [2], [0] * 3 + [1] * 9 + [3]],
        7: [[1] * 12 + [2]],
    }
    roles = Counter()
    for triple in heavy:
        multiplicity = triples[triple]
        outside = [point for point in range(1, 17) if point not in triple]
        degree = {
            point: sum(set(triple) | {point} <= set(block) for block in blocks) for point in outside
        }
        repeated = [point for point in outside if degree[point] >= 2]
        result["h6"] += int(multiplicity == 6 and bool(repeated))
        result["repeated_point_excess"] += max(0, len(repeated) - 1)
        result["repeated_incidence_excess"] += sum(max(0, value - 3) for value in degree.values())
        if multiplicity in patterns:
            ordered = sorted(degree.values())
            result["endpoint_shape_distance"] += min(
                sum(abs(a - b) for a, b in zip(ordered, pattern, strict=True))
                for pattern in patterns[multiplicity]
            )
        for pair in combinations(triple, 2):
            result["internal_pair_deficit"] += max(0, 7 - pairs[pair])
            if repeated:
                result["hub_internal_pair_excess"] += max(0, pairs[pair] - 7)
        for hub in repeated:
            roles[hub] += 1
            result["hub_inside_heavy"] += sum(hub in other for other in heavy)
            for anchor in triple:
                result["hub_cross_pair_deviation"] += abs(pairs[tuple(sorted((anchor, hub)))] - 6)
    result["hub_collision"] = sum(max(0, count - 1) for count in roles.values())
    histogram = Counter(triples.values())
    result["refined_count_overflow"] = max(
        0, 3 * histogram[6] + 4 * histogram[7] + result["h6"] - 16
    )
    return result


def recount(path, score_version=None):
    if score_version not in (None, "1.3"):
        raise ValueError("unsupported score version")
    rows = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(rows) == 64 and len(set(rows)) == 64
    assert all(len(set(row)) == 5 and tuple(sorted(row)) == row for row in rows)
    assert all(1 <= p <= 16 for row in rows for p in row)
    assert Counter(p for row in rows for p in row) == Counter(dict.fromkeys(range(1, 17), 20))
    blocks = set(rows)
    triples = Counter(t for block in blocks for t in combinations(block, 3))
    histogram = Counter(triples.values())
    heavy = [t for t, count in triples.items() if count >= 6]
    disjoint = [
        part for part in combinations(heavy, 5) if len(set().union(*(set(t) for t in part))) == 15
    ]
    forbidden = any(sum(triples[t] >= 7 for t in part) >= 2 for part in disjoint)
    overflow = max(0, 4 * histogram[7] + 3 * histogram[6] - 16)
    excess = sum(max(0, n - 7) for n in triples.values())
    penalty = overflow + 5 * excess + forbidden
    local = [
        tuple(p for p in block if p > 3) for block in blocks if len(set(block) & {1, 2, 3}) == 1
    ]
    local_triples = {t for block in local for t in combinations(block, 3)}
    needs = Counter(
        pair
        for t in set(combinations(range(4, 17), 3)) - local_triples
        for pair in combinations(t, 2)
    )
    lower = [sum((n + 2) // 3 for pair, n in needs.items() if p in pair) for p in range(4, 17)]
    family_overflow = sum(max(0, n - (24 if i == 0 else 28)) for i, n in enumerate(lower))
    hubs = Counter()
    invalid = 0
    for triple, count in triples.items():
        if count != 7:
            continue
        degree = Counter(
            p for block in blocks if set(triple) <= set(block) for p in block if p not in triple
        )
        if sorted(degree.values()) == [1] * 12 + [2]:
            hubs[next(p for p, n in degree.items() if n == 2)] += 1
        else:
            invalid += 1
    extension = structural_penalties(blocks, triples) if score_version == "1.3" else {}
    penalty += sum(value for name, value in extension.items() if name != "h6")
    return blocks, {
        "holes": 560 - len(triples),
        "n6": histogram[6],
        "n7": histogram[7],
        "triples_above7": sum(n > 7 for n in triples.values()),
        "max_triple_multiplicity": max(triples.values()),
        "heavy_count_overflow": overflow,
        "heavy_penalty": penalty,
        "disjoint_five_heavy": bool(disjoint),
        "forbidden_five_heavy": forbidden,
        "family_pair_row_bounds": lower,
        "family_pair_row_overflow": family_overflow,
        "passes_heavy_filters": penalty == 0,
        "passes_scored_filters": penalty == 0 and family_overflow == 0,
        "mu7_hub_diagnostics": {
            "invalid_link_graphs": invalid,
            "repeated_hubs": sum(max(0, n - 1) for n in hubs.values()),
            "hub_counts_by_point": [hubs[p] for p in range(1, 17)],
        },
        **extension,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    assert not args.output.exists(), "refusing to overwrite audit"
    metadata = json.loads((args.campaign / "metadata.json").read_text())
    score_version = metadata.get("score_version")
    lines = (args.campaign / "stdout.jsonl").read_text().splitlines()
    events = [json.loads(line) for line in lines]
    assert events[-1]["event"] == "finish", "campaign is not complete"
    scored = "heavy_penalty_weight" in metadata
    heavy_weight = metadata.get("heavy_penalty_weight", 0)
    family_weight = metadata.get("family_penalty_weight", 0)
    entries, reservoir = [], []
    best_score = float("inf")
    diverse = Counter()
    for event in events:
        if event["event"] != "snapshot":
            continue
        path = Path(event["path"])
        blocks, metrics = recount(path, score_version=score_version)
        metrics["score"] = (
            metrics["holes"]
            + heavy_weight * metrics["heavy_penalty"]
            + family_weight * metrics["family_pair_row_overflow"]
        )
        for key, value in metrics.items():
            if scored or key in event:
                assert event[key] == value, (path, key, event.get(key), value)
        role = event["role"]
        if (
            role not in {"control_before", "control_after", "diverse", "final"}
            and metrics["score"] < best_score
        ):
            best_score = metrics["score"]
            reservoir = [(score, old) for score, old in reservoir if score <= best_score + 1]
            if len(reservoir) == 32:
                reservoir.pop(0)
            reservoir.append((metrics["score"], blocks))
        elif role == "diverse":
            assert metrics["score"] <= best_score + 1
            assert all(len(blocks - old) >= 4 for _, old in reservoir)
            diverse[metrics["holes"]] += 1
            assert diverse[metrics["holes"]] <= 8
            if len(reservoir) == 32:
                reservoir.pop(0)
            reservoir.append((metrics["score"], blocks))
        entries.append(
            {
                "path": str(path),
                "role": role,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                **metrics,
            }
        )
    finish = events[-1]
    assert sum(diverse.values()) == finish["diverse_saved"]
    raw = min(entries, key=lambda item: item["holes"])
    heavy = min(
        (r for r in entries if r["passes_heavy_filters"]),
        key=lambda item: item["holes"],
        default=None,
    )
    qualified = min(
        (r for r in entries if r["passes_scored_filters"]),
        key=lambda item: item["holes"],
        default=None,
    )
    assert raw["holes"] == finish["best_holes"]
    if scored:
        assert best_score == finish["best_score"]
        assert (heavy["holes"] if heavy else -1) == finish["best_heavy_qualifying_holes"]
        assert (qualified["holes"] if qualified else -1) == finish["best_qualifying_holes"]
    scope = "Metrics of saved states only; passing filters does not prove completion. "
    scope += (
        "Full heavy/hub penalties affect qualification and score."
        if score_version == "1.3"
        else "Hub diagnostics do not affect qualification or score."
    )
    result = {
        "scope": scope,
        "score_version": score_version,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_source_hashes": metadata["source_hashes"],
        "snapshots": len(entries),
        "diverse_saved": sum(diverse.values()),
        "best_raw": raw,
        "best_heavy_qualified": heavy,
        "best_scored_filters": qualified,
        "records": entries,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ["snapshots", "diverse_saved"]}))


if __name__ == "__main__":
    main()
