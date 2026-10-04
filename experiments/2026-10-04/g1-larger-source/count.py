# Document:    Fixed-g1 Next-Route Finite Candidate Assessment
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      96731328e124905deb6c7d57b1c48a99980717234ab47af0a09091cdeccdd33e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Enumerate candidate counts only; no optimization or durable-source mutation."""

import gzip
import importlib.util
import itertools as it
import json
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DAY = ROOT / "experiments/2026-10-04"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


run = load(DAY / "g1-link-descent/run.py", "planning_g1")
blocks, ordinary, heavy, _, rows, _ = run.basis()
source = json.loads((DAY / "g1-link-descent/result.json").read_text())
fixed = frozenset(blocks[i] for i in source["best_heavy_global_ids"])
allowed = set(heavy)
anchors = [frozenset(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
registry = run.registry_module.Registry()
block_ids = {b: i for i, b in enumerate(blocks)}
cache = json.loads(
    (ROOT / "experiments/scratch/g1-link-descent-20261004/final-cache.json").read_text()
)
cached_states = {tuple(r["heavy_global_ids"]) for r in cache.values()}
base_counts = Counter(t for b in fixed for t in it.combinations(b, 3))
started = time.monotonic()


def passes(removed, added):
    delta = Counter(t for b in added for t in it.combinations(b, 3))
    delta.subtract(t for b in removed for t in it.combinations(b, 3))
    return all(base_counts[t] + n <= 2 or frozenset(t) in anchors for t, n in delta.items())


def state_ids(state):
    return tuple(sorted(block_ids[b] for b in state))


def local_moves(group, size):
    anchor = anchors[group]
    local = sorted(b for b in fixed if anchor <= set(b))
    moves = []
    raw = 0
    for outgoing in it.combinations(local, size):
        degree = Counter(p for b in outgoing for p in set(b) - anchor)
        edges = list(it.combinations(sorted(degree), 2))
        for incoming_edges in it.combinations(edges, size):
            if Counter(p for e in incoming_edges for p in e) != degree:
                continue
            incoming = frozenset(tuple(sorted(anchor | set(e))) for e in incoming_edges)
            if len(incoming - fixed) != size:
                continue
            raw += 1
            if incoming <= allowed:
                moves.append((frozenset(outgoing), incoming))
    assert len(moves) == len(set(moves))
    return raw, moves


def summarize(name, moves):
    states = set()
    accepted = []
    reps = Counter()
    for removed, added in moves:
        state = fixed - removed | added
        assert len(state) == 28 and state <= allowed
        ids = state_ids(state)
        assert ids not in states
        states.add(ids)
        receipt = registry.classify(sorted(state))
        if receipt["accepted"]:
            accepted.append(ids)
            reps[tuple(x["representative"] for x in receipt["links"])] += 1
    result = {
        "structurally_valid": len(states),
        "registry_accepted": len(accepted),
        "registry_rejected": len(states) - len(accepted),
        "cached": sum(x in cached_states for x in accepted),
        "fresh_expected": sum(x not in cached_states for x in accepted),
        "representative_profiles": len(reps),
        "state_sha256": run.data_hash(sorted(states)),
        "accepted_sha256": run.data_hash(sorted(accepted)),
    }
    (HERE / (name + ".json.gz")).write_bytes(
        gzip.compress(json.dumps(sorted(accepted)).encode(), mtime=0)
    )
    return result, set(accepted)


twos = []
proper_three = []
per_anchor = []
for g in range(4):
    raw_two, two = local_moves(g, 2)
    raw_three, three = local_moves(g, 3)
    legal_three = [(a, b) for a, b in three if passes(a, b)]
    proper_three.extend(legal_three)
    twos.append(two)
    per_anchor.append(
        {
            "group": g,
            "raw_two": raw_two,
            "universe_two": len(two),
            "raw_three": raw_three,
            "universe_three": len(three),
            "legal_three": len(legal_three),
        }
    )
paired = []
cancellation = 0
for a, b in it.combinations(range(4), 2):
    for (oa, ia), (ob, ib) in it.product(twos[a], twos[b]):
        out, inc = oa | ob, ia | ib
        if passes(out, inc):
            paired.append((out, inc))
            cancellation += not passes(oa, ia) or not passes(ob, ib)
three_result, three_states = summarize("proper-three", proper_three)
pair_result, pair_states = summarize("paired-two", paired)
save(
    "larger.json",
    {
        "proper_three": three_result,
        "paired_two": pair_result,
        "per_anchor": per_anchor,
        "jointly_valid_individually_invalid": cancellation,
        "solver_calls": 0,
    },
)
print("larger", json.dumps({"proper_three": three_result, "paired_two": pair_result}), flush=True)

# Transport the complete audited 29970-link cycle catalog into each physical anchor.
whole = []
whole_states = set()
whole_distribution = Counter()
whole_rep_distribution = Counter()
for g, anchor in enumerate(anchors):
    transport = registry.transports[g][0]
    physical = [4 * transport[(p - 1) // 4] + (p - 1) % 4 + 1 for p in range(1, 17)]
    inverse = {p: i + 1 for i, p in enumerate(physical)}
    outgoing = frozenset(b for b in fixed if anchor <= set(b))
    counts = Counter()
    for canonical_edges, (representative, _) in registry.table.items():
        counts["catalog"] += 1
        if representative in registry.registry["proof_sources"]:
            counts["registry_rejected"] += 1
            continue
        incoming = frozenset(
            tuple(sorted(anchor | {inverse[a], inverse[b]})) for a, b in canonical_edges
        )
        assert len(incoming) == 7 and incoming <= allowed
        assert Counter(p for b in incoming for p in set(b) - anchor) == Counter(
            p for b in outgoing for p in set(b) - anchor
        )
        if incoming == outgoing:
            counts["unchanged"] += 1
            continue
        if not passes(outgoing, incoming):
            counts["global_cap_rejected"] += 1
            continue
        ids = state_ids(fixed - outgoing | incoming)
        assert ids not in whole_states
        whole_states.add(ids)
        whole_rep_distribution[representative] += 1
        distance = len(outgoing - incoming)
        whole_distribution[distance] += 1
        counts["accepted"] += 1
        counts["cached"] += ids in cached_states
    whole.append({"group": g, **counts})
(HERE / "whole-link.json.gz").write_bytes(
    gzip.compress(json.dumps(sorted(whole_states)).encode(), mtime=0)
)
whole_result = {
    "per_anchor": whole,
    "accepted": len(whole_states),
    "cached": len(whole_states & cached_states),
    "fresh_expected": len(whole_states - cached_states),
    "edge_replacement_counts": dict(sorted(whole_distribution.items())),
    "unique_changed_link_representatives": len(whole_rep_distribution),
    "proper_three_overlap": len(whole_states & three_states),
    "paired_two_overlap": len(whole_states & pair_states),
    "accepted_sha256": run.data_hash(sorted(whole_states)),
}
save("whole.json", whole_result)
print("whole", json.dumps(whole_result), flush=True)

# Expand top saved alternatives without solving, recording repeats with the known basin.
records = sorted(cache.values(), key=lambda r: (r["objective"], r["heavy_global_ids"]))
alternatives = [r for r in records if r["heavy_global_ids"] != source["best_heavy_global_ids"]][:5]
expanded = set()
per_alternative = []
for number, record in enumerate(alternatives, 1):
    chosen = [blocks[i] for i in record["heavy_global_ids"]]
    candidates, _ = run.generator.candidates(chosen, heavy)
    accepted = set()
    for state, _ in candidates:
        if registry.classify(state)["accepted"]:
            accepted.add(state_ids(state))
    expanded.update(accepted)
    per_alternative.append(
        {
            "rank": number,
            "objective": record["objective"],
            "heavy_global_ids": record["heavy_global_ids"],
            "generated": len(candidates),
            "accepted": len(accepted),
            "already_cached": len(accepted & cached_states),
            "has_current_best": tuple(source["best_heavy_global_ids"]) in accepted,
            "cumulative_unique": len(expanded),
            "cumulative_fresh": len(expanded - cached_states),
        }
    )
(HERE / "alternatives.json.gz").write_bytes(
    gzip.compress(json.dumps(sorted(expanded)).encode(), mtime=0)
)
alt_result = {
    "top_five": per_alternative,
    "union": len(expanded),
    "fresh": len(expanded - cached_states),
    "fresh_inside_proper_three": len((expanded - cached_states) & three_states),
    "fresh_inside_paired_two": len((expanded - cached_states) & pair_states),
    "fresh_inside_whole_link": len((expanded - cached_states) & whole_states),
}
save("alternatives.json", alt_result)
report = {
    "source_sha256": run.sha(__file__),
    "descent_result_sha256": run.sha(DAY / "g1-link-descent/result.json"),
    "baseline_objective": source["best_objective"],
    "proper_three": three_result,
    "paired_two": pair_result,
    "whole_link": whole_result,
    "saved_alternatives": alt_result,
    "solver_calls": 0,
    "seconds": time.monotonic() - started,
}
save("counts.json", report)
print("alternatives", json.dumps(alt_result), flush=True)
print("seconds", report["seconds"], flush=True)
