# Document:    Global Five-Heavy Reachable DP Proof Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      d305bcf417b863d1089c9af3ae095e3155b81f80c5a9340ab357ec0476b4db5c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Generate recurrence DAGs and finite arithmetic controls; never invoke a solver."""

import hashlib
import itertools
import json
import math
import random
import struct
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/global-five-heavy-dp-plan-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mask(points):
    return sum(1 << (point - 1) for point in points)


def states(n, groups):
    return [mask(points) for k in range(groups + 1)
            for points in itertools.combinations(range(1, n + 1), 3 * k)]


def children(state):
    pivot = state & -state
    rest = [1 << i for i in range(state.bit_length()) if state & (1 << i) != pivot
            and state & (1 << i)]
    for left, right in itertools.combinations(rest, 2):
        triple = pivot | left | right
        yield state ^ triple, triple


def least_values(selected_states, weights):
    values = {0: 0}
    for state in selected_states[1:]:
        values[state] = max(values[parent] + weights[triple]
                            for parent, triple in children(state))
    return values


def save_dag(label, selected_states, triples):
    index = {state: i for i, state in enumerate(selected_states)}
    triple_id = {triple: i for i, triple in enumerate(triples)}
    rows = 0
    row_counts = Counter()
    threshold_fanout = [0] * len(triples)
    parent_fanout = [0] * len(selected_states)
    path = RAW / f"{label}-rows.uint32le"
    started = time.monotonic()
    with path.open("wb") as stream:
        for state in selected_states[1:]:
            for parent, triple in children(state):
                assert parent in index and parent.bit_count() + 3 == state.bit_count()
                stream.write(struct.pack("<III", index[state], index[parent], triple_id[triple]))
                threshold_fanout[triple_id[triple]] += 1
                parent_fanout[index[parent]] += 1
                row_counts[state.bit_count()] += 1
                rows += 1
    elapsed = time.monotonic() - started
    state_path = RAW / f"{label}-states.json"
    state_path.write_text(json.dumps(selected_states) + "\n")
    return {
        "states": len(selected_states), "state_histogram": dict(Counter(
            state.bit_count() for state in selected_states
        )), "rows": rows, "row_histogram": dict(row_counts),
        "rows_path": str(path.relative_to(ROOT)), "rows_sha256": sha(path),
        "rows_bytes": path.stat().st_size,
        "states_path": str(state_path.relative_to(ROOT)), "states_sha256": sha(state_path),
        "generation_seconds": elapsed,
        "threshold_fanout_min": min(threshold_fanout),
        "threshold_fanout_max": max(threshold_fanout),
        "threshold_fanout_sum": sum(threshold_fanout),
        "parent_fanout_max": max(parent_fanout),
        "inline_recurrence_coefficient_occurrences": 4 * rows,
        "dp_and_threshold_variables": len(selected_states) + 1120,
    }


def controls():
    truth = []
    for counts in itertools.product((5, 6, 7), repeat=5):
        weight = sum(5 * (count >= 6) + (count >= 7) for count in counts)
        forbidden = min(counts) >= 6 and sum(count >= 7 for count in counts) >= 2
        assert (weight > 26) == forbidden
        truth.append(forbidden)
    assert len(truth) == 243 and sum(truth) == 26
    for count in range(79):
        admitted = [(a, b) for a, b in itertools.product((0, 1), repeat=2)
                    if (count >= 6 if a else count <= 5)
                    and (count >= 7 if b else count <= 6)]
        assert admitted == [(int(count >= 6), int(count >= 7))]
    # Independent unpruned combinations of triple IDs, not the pivot recursion.
    small_states = states(9, 3)
    small_triples = [mask(t) for t in itertools.combinations(range(1, 10), 3)]
    partitions = {}
    for state in small_states[1:]:
        eligible = [triple for triple in small_triples if triple & state == triple]
        partitions[state] = [chosen for chosen in itertools.combinations(
            eligible, state.bit_count() // 3
        ) if all(a & b == 0 for a, b in itertools.combinations(chosen, 2))]
        k = state.bit_count() // 3
        assert len(partitions[state]) == math.factorial(3 * k) // (6 ** k * math.factorial(k))
    rng = random.Random(2026104)
    vectors = [{triple: value for triple in small_triples} for value in (0, 5, 6)]
    vectors += [{triple: rng.choice((0, 5, 6)) for triple in small_triples} for _ in range(9)]
    checked = 0
    for weights in vectors:
        values = least_values(small_states, weights)
        for state, choices in partitions.items():
            direct = max(sum(weights[triple] for triple in chosen) for chosen in choices)
            assert values[state] == direct
            checked += 1
    return {"threshold_counts_checked": 79, "partition_categories": 243,
            "forbidden_categories": 26, "allowed_categories": 217,
            "small_unpruned_subset_checks": checked, "small_weight_vectors": len(vectors),
            "maximum_small_partition_size": 9, "seed": 2026104}


def main():
    assert not RAW.exists() and not (HERE / "result.json").exists()
    finite = controls()
    full = states(16, 5)
    triples = [mask(t) for t in itertools.combinations(range(1, 17), 3)]
    expected_states = sum(math.comb(16, 3 * k) for k in range(6))
    expected_rows = sum(math.comb(16, 3 * k) * math.comb(3 * k - 1, 2)
                        for k in range(1, 6))
    assert len(full) == expected_states == 21845 and expected_rows == 502516
    reachable = {state for state in full if state.bit_count() == 15}
    frontier = set(reachable)
    while frontier:
        following = {parent for state in frontier if state
                     for parent, _ in children(state)} - reachable
        reachable.update(following)
        frontier = following
    closed_form = {0} | {state for state in full if state and not (
        state & ((1 << (5 - state.bit_count() // 3)) - 1)
    )}
    assert reachable == closed_form
    trimmed = [state for state in full if state in reachable]
    assert len(trimmed) == 4410
    RAW.mkdir()
    full_meta = save_dag("full", full, triples)
    trimmed_meta = save_dag("reachable", trimmed, triples)
    assert full_meta["rows"] == 502516 and trimmed_meta["rows"] == 99917
    # Fixed-weight arithmetic passes measure row traversal only, not solver propagation.
    timings = []
    for value in (0, 5, 6):
        weights = dict.fromkeys(triples, value)
        started = time.monotonic()
        values = least_values(trimmed, weights)
        elapsed = time.monotonic() - started
        assert all(values[state] == value * (state.bit_count() // 3) for state in trimmed)
        timings.append({"uniform_weight": value, "seconds": elapsed,
                        "maximum_target_value": max(values[state] for state in trimmed
                                                    if state.bit_count() == 15)})
    theorem = ROOT / "experiments/2026-10-03/five-heavy-triples"
    theorem_result = json.loads((theorem / "result.json").read_text())
    assert theorem_result["complete"] and theorem_result["assignments_checked"] == 27040
    assert theorem_result["source_sha256"] == sha(theorem / "check.py")
    paths = [Path(__file__), theorem / "README.md", theorem / "check.py", theorem / "result.json",
             HERE.parent / "heterogeneous-profile-pool/run.py",
             HERE.parent / "three-core-profile-release/run.py"]
    report = {
        "passed": True, "optimizer_calls": 0, "full": full_meta, "reachable": trimmed_meta,
        "finite_controls": finite, "synthetic_dag_pass_timings": timings,
        "triple_indicators": 1120, "exact_threshold_half_reified_rows": 2240,
        "source_sha256": sha(__file__),
        "input_files": {str(path.relative_to(ROOT)): sha(path) for path in paths},
        "scope": "Encoding proof controls and fixed-weight arithmetic only. "
        "No construction optimizer, solver propagation benchmark, or covering-bound claim.",
    }
    (HERE / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
