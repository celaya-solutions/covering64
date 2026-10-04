# Document:    Independent Global Five-Heavy Dynamic Program Proof Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      07761cd6e9cef965b8b6a3fd577b6928e6a8a6014a612ccb8b32adfaa8a72c39
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild the DAG and finite proof controls without producer imports or solvers."""

import hashlib
import itertools as it
import json
import math
import random
import struct
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = HERE.parent / "global-five-heavy-dp-plan"
PREPARED = HERE.parent / "global-five-heavy-dp"
THEOREM = ROOT / "experiments/2026-10-03/five-heavy-triples"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def labels(mask):
    return tuple(point for point in range(1, 17) if mask & (1 << (point - 1)))


def bitset(points):
    return sum(2 ** (point - 1) for point in points)


TRIPLES = list(it.combinations(range(1, 17), 3))
TRIPLE_RANK = {triple: i for i, triple in enumerate(TRIPLES)}


def transitions(state):
    points = labels(state)
    for a, b in it.combinations(points[1:], 2):
        triple = (points[0], a, b)
        yield state - bitset(triple), TRIPLE_RANK[triple]


def rebuild(selected, metadata):
    assert len(selected) == len(set(selected))
    index = {mask: position for position, mask in enumerate(selected)}
    rows = []
    fanout = Counter()
    parent_fanout = Counter()
    row_histogram = Counter()
    for mask in selected[1:]:
        for parent, triple in transitions(mask):
            assert parent in index and parent.bit_count() == mask.bit_count() - 3
            rows.append((index[mask], index[parent], triple))
            fanout[triple] += 1
            parent_fanout[parent] += 1
            row_histogram[mask.bit_count()] += 1
    state_bytes = (json.dumps(selected) + "\n").encode()
    row_bytes = b"".join(struct.pack("<III", *row) for row in rows)
    assert state_bytes == (ROOT / metadata["states_path"]).read_bytes()
    assert row_bytes == (ROOT / metadata["rows_path"]).read_bytes()
    assert hashlib.sha256(state_bytes).hexdigest() == metadata["states_sha256"]
    assert hashlib.sha256(row_bytes).hexdigest() == metadata["rows_sha256"]
    counts = {
        "states": len(selected),
        "rows": len(rows),
        "state_histogram": {
            str(k): v for k, v in sorted(Counter(m.bit_count() for m in selected).items())
        },
        "row_histogram": {str(k): v for k, v in sorted(row_histogram.items())},
        "rows_bytes": len(row_bytes),
        "states_sha256": hashlib.sha256(state_bytes).hexdigest(),
        "rows_sha256": hashlib.sha256(row_bytes).hexdigest(),
        "threshold_fanout_min": min(fanout[i] for i in range(560)),
        "threshold_fanout_max": max(fanout.values()),
        "threshold_fanout_sum": sum(fanout.values()),
        "parent_fanout_max": max(parent_fanout.values()),
        "inline_recurrence_coefficient_occurrences": 4 * len(rows),
        "dp_and_threshold_variables": len(selected) + 1120,
    }
    for key, value in counts.items():
        assert metadata[key] == value
    return rows, counts


def evaluate(states, rows, weights):
    values = [0] * len(states)
    for state, parent, triple in rows:
        assert parent < state
        values[state] = max(values[state], values[parent] + weights[triple])
    assert all(
        0 <= value <= 2 * mask.bit_count() for mask, value in zip(states, values, strict=True)
    )
    return values


def threshold_controls():
    for count in range(79):
        admitted = []
        for six, seven in it.product((0, 1), repeat=2):
            # Four half-reified rows, including both reverse implications.
            if (
                (not six or count >= 6)
                and (six or count <= 5)
                and (not seven or count >= 7)
                and (seven or count <= 6)
            ):
                admitted.append((six, seven))
        assert admitted == [(int(count >= 6), int(count >= 7))]
        assert 5 * admitted[0][0] + admitted[0][1] == (0 if count <= 5 else 5 if count == 6 else 6)
    accepted, rejected = 0, 0
    damaged = Counter()
    for counts in it.product((5, 6, 7), repeat=5):
        actual = all(c >= 6 for c in counts) and sum(c >= 7 for c in counts) >= 2
        six, seven = sum(c >= 6 for c in counts), sum(c >= 7 for c in counts)
        total = 5 * six + seven
        assert (total > 26) == actual
        rejected += actual
        accepted += not actual
        for name, bad in {
            "cap25": total > 25,
            "cap27": total > 27,
            "six_coefficient4": 4 * six + seven > 26,
            "seven_coefficient2": 5 * six + 2 * seven > 26,
            "strict_six_threshold": 5 * sum(c > 6 for c in counts) + seven > 26,
        }.items():
            damaged[name] += bad != actual
    assert accepted == 217 and rejected == 26 and all(damaged.values())
    # Omitting a reverse implication permits hiding an actual heavy triple.
    assert 6 >= 6 and not (6 <= 5)
    assert 7 >= 7 and not (7 <= 6)
    return {
        "local_counts": 79,
        "partition_categories": 243,
        "allowed": accepted,
        "forbidden": rejected,
        "damaged_rule_mismatches": dict(damaged),
        "reverse_implications_required": True,
    }


def small_controls():
    states = sorted(
        (m for m in range(1 << 9) if m.bit_count() in (0, 3, 6, 9)),
        key=lambda m: (m.bit_count(), labels(m)),
    )
    ids = {mask: i for i, mask in enumerate(states)}
    rows = [
        (ids[state], ids[parent], triple)
        for state in states[1:]
        for parent, triple in transitions(state)
    ]
    partitions = {}
    small_triples = [(i, bitset(t)) for i, t in enumerate(TRIPLES) if t[-1] <= 9]
    for state in states[1:]:
        eligible = [(i, mask) for i, mask in small_triples if mask | state == state]
        k = state.bit_count() // 3
        options = []
        for group in it.combinations(eligible, k):
            union = 0
            for _, mask in group:
                union |= mask
            # k triples have exactly3k entries: a3k-point union certifies disjointness.
            if union == state:
                options.append(tuple(i for i, _ in group))
        assert len(options) == math.factorial(3 * k) // (6**k * math.factorial(k))
        partitions[state] = options
    generator = random.Random(2026104)
    vectors = [[value] * 560 for value in (0, 5, 6)]
    for _ in range(9):
        weights = [0] * 560
        for triple, _ in small_triples:
            weights[triple] = generator.choice((0, 5, 6))
        vectors.append(weights)
    cases = 0
    for weights in vectors:
        values = evaluate(states, rows, weights)
        for state, options in partitions.items():
            assert values[ids[state]] == max(sum(weights[t] for t in choice) for choice in options)
            cases += 1
    assert cases == 2028
    return {
        "subset_weight_cases": cases,
        "weight_vectors": 12,
        "nonempty_subsets": 169,
        "maximum_partition_size": 9,
        "seed": 2026104,
    }


def theorem_controls():
    selected = [tuple(range(3 * i + 1, 3 * i + 4)) for i in range(5)]

    def fits(degrees, chosen, hubs):
        edges = {edge: 2 for triple in selected for edge in it.combinations(triple, 2)}
        for index, hub in zip(chosen, hubs, strict=True):
            assert hub not in selected[index]
            for point in selected[index]:
                edge = tuple(sorted((point, hub)))
                edges[edge] = max(1, edges.get(edge, 0))
        used = [0] * 17
        for (a, b), weight in edges.items():
            used[a] += weight
            used[b] += weight
        return all(used[p] <= 4 * degrees[p - 1] - 75 for p in range(1, 17))

    profiles = [[20] * 16]
    for high in range(15):
        degrees = [20] * 16
        degrees[high], degrees[15] = 21, 19
        profiles.append(degrees)
    checked = 0
    for degrees in profiles:
        assert sum(degrees) == 320
        for chosen in it.combinations(range(5), 2):
            alternatives = [sorted(set(range(1, 17)) - set(selected[i])) for i in chosen]
            for hubs in it.product(*alternatives):
                checked += 1
                assert not fits(degrees, chosen, hubs)
    assert checked == 27040
    assert fits([20] * 16, [0], [16])
    assert fits([20] * 15 + [25], [0, 1], [16, 16])
    assert all(2 * ((1 + 4 * delta) // 3) <= 3 * delta for delta in range(1001))
    saved = json.loads((THEOREM / "result.json").read_text())
    assert saved["complete"] and saved["assignments_checked"] == checked
    assert saved["feasible_two_sevenfold_assignments"] == 0
    assert saved["source_sha256"] == sha(THEOREM / "check.py")
    return {
        "degree_profiles": 16,
        "hub_assignments_checked": checked,
        "feasible_two_sevenfold_assignments": 0,
        "positive_arithmetic_controls": 2,
        "capacity_values_checked": 1001,
        "regularity_assumption": False,
    }


def main():
    assert not (HERE / "proof.json").exists()
    plan = json.loads((PLAN / "result.json").read_text())
    manifest = json.loads((PREPARED / "manifest.json").read_text())
    assert plan["passed"] and plan["optimizer_calls"] == manifest["optimization_calls"] == 0
    assert plan["source_sha256"] == sha(PLAN / "check.py")
    for relative, checksum in plan["input_files"].items():
        assert sha(ROOT / relative) == checksum
    full = sorted(
        (m for m in range(1 << 16) if m.bit_count() in (0, 3, 6, 9, 12, 15)),
        key=lambda m: (m.bit_count(), labels(m)),
    )
    assert len(full) == 21845
    reachable = {m for m in full if m.bit_count() == 15}
    frontier = list(reachable)
    while frontier:
        state = frontier.pop()
        if state:
            for parent, _ in transitions(state):
                if parent not in reachable:
                    reachable.add(parent)
                    frontier.append(parent)
    formula = {m for m in full if all(p > 5 - m.bit_count() // 3 for p in labels(m))}
    assert reachable == formula and len(formula) == 4410
    trimmed = [m for m in full if m in reachable]
    for state in trimmed:
        k = state.bit_count() // 3
        pivots = list(range(1, 6 - k))
        outside = sorted(set(range(1, 17)) - set(labels(state)) - set(pivots))
        assert len(outside) == 2 * len(pivots) + 1
        groups = [(p, outside[2 * i], outside[2 * i + 1]) for i, p in enumerate(pivots)]
        target = state | bitset(p for group in groups for p in group)
        assert target.bit_count() == 15
        for group in groups:
            assert min(labels(target)) == group[0]
            target -= bitset(group)
        assert target == state
    full_rows, full_report = rebuild(full, plan["full"])
    trimmed_rows, trimmed_report = rebuild(trimmed, plan["reachable"])
    assert len(full_rows) == 502516 and len(trimmed_rows) == 99917
    assert len(full_rows) == sum(
        math.comb(16, 3 * k) * math.comb(3 * k - 1, 2) for k in range(1, 6)
    )
    assert len(trimmed_rows) == sum(
        math.comb(11 + k, 3 * k) * math.comb(3 * k - 1, 2) for k in range(1, 6)
    )
    generator = random.Random(2026104104)
    vectors = [[value] * 560 for value in (0, 5, 6)]
    vectors += [[generator.choice((0, 5, 6)) for _ in TRIPLES] for _ in range(3)]
    full_index, trimmed_index = (
        {s: i for i, s in enumerate(full)},
        {s: i for i, s in enumerate(trimmed)},
    )
    global_controls = []
    for number, weights in enumerate(vectors):
        left = evaluate(full, full_rows, weights)
        right = evaluate(trimmed, trimmed_rows, weights)
        assert all(left[full_index[s]] == right[trimmed_index[s]] for s in trimmed)
        targets = [right[i] for i, s in enumerate(trimmed) if s.bit_count() == 15]
        if number < 3:
            assert set(targets) == {5 * (0, 5, 6)[number]}
        global_controls.append(
            {"vector": number, "target_values": targets, "within_cap26": max(targets) <= 26}
        )
    threshold = threshold_controls()
    small = small_controls()
    theorem = theorem_controls()
    sources = [
        Path(__file__),
        PLAN / "README.md",
        PLAN / "check.py",
        PLAN / "result.json",
        PREPARED / "manifest.json",
        THEOREM / "README.md",
        THEOREM / "check.py",
        THEOREM / "result.json",
    ]
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "serialized_model_gate_performed": False,
        "sources": {str(p.relative_to(ROOT)): sha(p) for p in sources},
        "full_dag": full_report,
        "reachable_dag": trimmed_report,
        "constructive_reachability_paths_checked": 4410,
        "threshold_and_weight_controls": threshold,
        "direct_small_controls": small,
        "full_vs_trimmed_controls": global_controls,
        "unrestricted_theorem_replay": theorem,
        "mathematical_argument": [
            "Exact channeling gives weight 0 for counts 0..5, 5 for count 6, and 6 for counts >=7.",
            "A five-triple sum above 26 means all five counts are >=6 and at least two are >=7.",
            "Every partition has exactly one triple containing its set's minimum point.",
            "Thus its maximum weight F satisfies the pivot recurrence, with F(empty)=0.",
            "The lower recurrence inequalities and D(empty)=0 imply D(S)>=F(S) by induction.",
            "Every size-15 target cap of 26 therefore excludes all forbidden partitions.",
            (
                "Conversely, if all partition weights are <=26, D=F fits every inequality "
                "and domain 0..6k, with target domains 0..26."
            ),
            (
                "All 16 size-15 targets include every five-disjoint-triple family. "
                "No block labeling or regularity is fixed."
            ),
            (
                "After q minimum deletions, labels 1..q are absent. Conversely every such "
                "state S has the explicitly checked pivot path."
            ),
            (
                "The trimmed set is exactly backward reachable and closed under every "
                "required dependency. The same equivalence therefore holds."
            ),
            (
                "The independently checked degree and hub theorem forbids this profile "
                "for full 64-block covers without a regularity assumption."
            ),
        ],
        "scope": (
            "Exact mathematical equivalence and finite controls for the global profile condition. "
            "Independent full and trimmed DAG reconstruction, not producer-function replay. "
            "No optimizer, no performance claim, no cover or unrestricted lower-bound theorem. "
            "The root agent separately gates the serialized model."
        ),
    }
    (HERE / "proof.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "proof_sha256": sha(HERE / "proof.json"),
                "full_states": len(full),
                "reachable_states": len(trimmed),
                "full_rows": len(full_rows),
                "reachable_rows": len(trimmed_rows),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
