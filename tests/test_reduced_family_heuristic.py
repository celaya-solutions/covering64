# Document:    Reduced Family Heuristic Controls
# Version:     v1.3.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e28e9722cbbac6491c7445017fbd9534edc93a402ffade0c6400b3565fe090a5
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import json
import runpy
import shutil
import subprocess
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
START = ROOT / "experiments/2026-10-03/reduced-family-heuristic/inputs/seed27.txt"
AUDIT = runpy.run_path(str(START.parent.parent / "audit_campaign_metrics.py"))["recount"]


def test_independent_reduced_starter_check():
    process = subprocess.run(["uv", "run", "python", "scripts/verify_reduced_family_heuristic.py",
                              str(START)], cwd=ROOT, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["holes"] == 27
    assert result["degree20"] is True
    assert result["outside_blocks"] == 18
    assert result["normalized_heavy_blocks"] == 7
    assert all(check["result"]["valid"] is False for check in result["checks"])


@pytest.mark.parametrize(("heavy_weight", "family_weight", "seed_name"), [
    (0, 0, "seed27.txt"), (1, 2, "seed27.txt"), (1, 2, "multiplicity8-control.txt"),
    (1, 2, "one-seven-four-six-control.txt"),
    (1, 2, "hub-collision-control.txt"),
    (1, 2, "../penalty-2026100363/search-qualifying_improvement-21-h13.txt"),
    (1, 2, "../strong-penalty-2026100365/search-diverse-13-h13.txt"),
])
def test_native_family_moves_and_rollbacks(tmp_path, heavy_weight, family_weight, seed_name):
    compiler = shutil.which("clang++")
    if compiler is None:
        pytest.skip("C++ compiler unavailable")
    binary = tmp_path / "search"
    compiled = subprocess.run([compiler, "-std=c++17", "-O2", "-o", str(binary),
                               str(ROOT / "scripts/reduced_family_heuristic.cpp")],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    inputs = START.parent
    command = [str(binary), str(inputs / seed_name), *(str(inputs / f"{kind}.txt")
               for kind in ["pg", "r4", "r6"]), "2026100361", "0.2", str(tmp_path / "control"),
               str(heavy_weight), str(family_weight)]
    process = subprocess.run(command, capture_output=True, text=True)
    assert process.returncode == 0, process.stderr
    events = [json.loads(row) for row in process.stdout.splitlines()]
    if seed_name == "multiplicity8-control.txt":
        assert events[0]["max_triple_multiplicity"] == 8
        assert events[0]["passes_heavy_filters"] is False
        assert events[0]["heavy_penalty"] >= 5
    if seed_name == "one-seven-four-six-control.txt":
        assert events[0]["disjoint_five_heavy"] is True
        assert events[0]["forbidden_five_heavy"] is False
        assert events[0]["heavy_count_overflow"] == 0
        assert events[0]["h6"] == 2
        assert events[0]["refined_count_overflow"] == 2
    if seed_name == "hub-collision-control.txt":
        assert events[0]["hub_collision"] > 0
    if seed_name.endswith("search-qualifying_improvement-21-h13.txt"):
        assert events[0]["hub_inside_heavy"] > 0
        assert events[0]["internal_pair_deficit"] > 0
        assert events[0]["generic_pair_deficit"] > 0
    if seed_name.endswith("search-diverse-13-h13.txt"):
        assert events[0]["h6"] == 0
        assert events[0]["hub_inside_heavy"] > 0
    finish = events[-1]
    assert finish["event"] == "finish"
    assert finish["rollback_audits"] == 4
    assert finish["pg_automorphisms"] == 5616
    assert all(n > 0 for n in finish["applied_by_mode"])
    assert all(n > 0 for n in finish["trades_by_size"])
    controls = [r for r in events if r["event"] == "snapshot" and r["role"] == "control_after"]
    assert {row["mode"] for row in controls} == {0, 1, 2, 3}
    reservoir = []
    best_score = float("inf")
    diverse_counts = Counter()
    heavy_qualifying, qualifying = [], []
    for event in [row for row in events if row["event"] == "snapshot"]:
        checked = subprocess.run(["uv", "run", "python",
                                  "scripts/verify_reduced_family_heuristic.py", event["path"]],
                                 cwd=ROOT, capture_output=True, text=True)
        assert checked.returncode == 0, checked.stderr
        result = json.loads(checked.stdout)
        assert result["holes"] == event["holes"]
        blocks = {tuple(map(int, row.split()))
                  for row in Path(event["path"]).read_text().splitlines()}
        local = [block[1:] for block in blocks if len({1, 2, 3} & set(block)) == 1]
        local_triples = {triple for block in local for triple in combinations(block, 3)}
        uncovered = set(combinations(range(4, 17), 3)) - local_triples
        pair_needs = Counter(pair for triple in uncovered for pair in combinations(triple, 2))
        lower = [sum((count + 2) // 3 for pair, count in pair_needs.items() if p in pair)
                 for p in range(4, 17)]
        assert event["family_pair_row_bounds"] == lower
        assert event["family_pair_row_overflow"] == sum(
            max(0, n - (24 if i == 0 else 28)) for i, n in enumerate(lower))
        triple_counts = Counter(t for block in blocks for t in combinations(block, 3))
        histogram = Counter(triple_counts.values())
        heavy = [set(t) for t, n in triple_counts.items() if n >= 6]
        disjoint_parts = [part for part in combinations(heavy, 5)
                          if len(set().union(*part)) == 15]
        disjoint_five = bool(disjoint_parts)
        forbidden_five = any(sum(triple_counts[tuple(sorted(t))] >= 7 for t in part) >= 2
                             for part in disjoint_parts)
        overflow = max(0, 4 * histogram[7] + 3 * histogram[6] - 16)
        excess = sum(max(0, n - 7) for n in triple_counts.values())
        penalty = overflow + 5 * excess + forbidden_five
        _, independently_recounted = AUDIT(Path(event["path"]), score_version="1.3")
        expanded_keys = ["heavy_overlap", "repeated_point_excess", "repeated_incidence_excess",
                         "endpoint_shape_distance", "hub_inside_heavy", "hub_collision",
                         "internal_pair_deficit", "hub_internal_pair_excess",
                         "hub_cross_pair_deviation", "refined_count_overflow",
                         "generic_pair_deficit"]
        for key in ["h6", *expanded_keys]:
            assert event[key] == independently_recounted[key]
        penalty += sum(independently_recounted[key] for key in expanded_keys)
        assert event["n6"] == histogram[6] and event["n7"] == histogram[7]
        assert event["triples_above7"] == sum(n > 7 for n in triple_counts.values())
        assert event["max_triple_multiplicity"] == max(triple_counts.values())
        assert event["disjoint_five_heavy"] == disjoint_five
        assert event["forbidden_five_heavy"] == forbidden_five
        assert event["heavy_count_overflow"] == overflow and event["heavy_penalty"] == penalty
        assert event["passes_heavy_filters"] == (penalty == 0)
        assert event["passes_scored_filters"] == (
            penalty == 0 and event["family_pair_row_overflow"] == 0)
        hubs = Counter()
        invalid_links = 0
        for triple, count in triple_counts.items():
            if count != 7:
                continue
            degree = Counter(p for block in blocks if set(triple) <= set(block)
                             for p in block if p not in triple)
            if sorted(degree.values()) == [1] * 12 + [2]:
                hubs[next(p for p, n in degree.items() if n == 2)] += 1
            else:
                invalid_links += 1
        assert event["mu7_hub_diagnostics"] == {
            "invalid_link_graphs": invalid_links,
            "repeated_hubs": sum(max(0, n - 1) for n in hubs.values()),
            "hub_counts_by_point": [hubs[p] for p in range(1, 17)],
        }
        assert event["score"] == (event["holes"] + heavy_weight * penalty
                                  + family_weight * event["family_pair_row_overflow"])
        if event["role"] not in {"control_before", "control_after"}:
            if event["passes_heavy_filters"]:
                heavy_qualifying.append(event["holes"])
            if event["passes_scored_filters"]:
                qualifying.append(event["holes"])
        if event["role"] not in {"control_before", "control_after", "diverse", "final"} \
                and event["score"] < best_score:
            best_score = event["score"]
            reservoir = [(score, old) for score, old in reservoir if score <= best_score + 1]
            if len(reservoir) == 32:
                reservoir.pop(0)
            reservoir.append((event["score"], blocks))
        elif event["role"] == "diverse":
            assert event["score"] <= best_score + 1
            assert all(len(blocks - old) >= 4 for _, old in reservoir)
            diverse_counts[event["holes"]] += 1
            assert diverse_counts[event["holes"]] <= 8
            if len(reservoir) == 32:
                reservoir.pop(0)
            reservoir.append((event["score"], blocks))
    assert sum(diverse_counts.values()) == finish["diverse_saved"]
    assert finish["best_score"] == best_score
    assert finish["best_heavy_qualifying_holes"] == min(heavy_qualifying, default=-1)
    assert finish["best_qualifying_holes"] == min(qualifying, default=-1)
    before_trade = next(row for row in events if row["event"] == "snapshot"
                        and row["role"] == "control_before" and row["mode"] == 3)
    after_trade = next(row for row in controls if row["mode"] == 3)
    before = {row for row in Path(before_trade["path"]).read_text().splitlines()
              if len({1, 2, 3} & set(map(int, row.split()))) == 1}
    after = {row for row in Path(after_trade["path"]).read_text().splitlines()
             if len({1, 2, 3} & set(map(int, row.split()))) == 1}
    assert len(before - after) == len(after - before)
    assert len(before - after) in {4, 6}


@pytest.mark.parametrize("damage", ["duplicate_block", "duplicate_point", "label", "token"])
def test_reduced_checker_rejects_damaged_seed(tmp_path, damage):
    rows = START.read_text().splitlines()
    if damage == "duplicate_block":
        rows[1] = rows[0]
    elif damage == "duplicate_point":
        points = rows[0].split()
        points[1] = points[0]
        rows[0] = " ".join(points)
    elif damage == "label":
        rows[0] = "17 " + " ".join(rows[0].split()[1:])
    else:
        rows[0] += " damaged"
    path = tmp_path / "bad.txt"
    path.write_text("\n".join(rows) + "\n")
    process = subprocess.run(["uv", "run", "python", "scripts/verify_reduced_family_heuristic.py",
                              str(path)], cwd=ROOT, capture_output=True, text=True)
    assert process.returncode != 0
