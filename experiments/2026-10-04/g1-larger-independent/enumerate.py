#!/usr/bin/env python3
# Document:    Independent Graph One Larger Neighborhood Enumeration
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Direct finite graph enumeration, without optimization or runner imports."""

import importlib.util
import itertools as it
import json
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/g1-larger-independent-20261004"
path = HERE.parent / "g1-link-descent-independent/independent.py"
spec = importlib.util.spec_from_file_location("independent_g1_larger", path)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def main():
    output = HERE / "enumeration.json"
    assert not output.exists() and not RAW.exists()
    result_path = HERE.parent / "g1-link-descent/result.json"
    result = json.loads(result_path.read_text())
    blocks, anchors, _, heavy, _ = ind.basis()
    positions = {block: index for index, block in enumerate(heavy)}
    chosen = frozenset(positions[blocks[i]] for i in result["best_heavy_global_ids"])
    local = [frozenset(i for i in chosen if anchor <= set(heavy[i])) for anchor in anchors]
    triplets = [
        [triple for triple in it.combinations(block, 3) if frozenset(triple) not in anchors]
        for block in heavy
    ]
    counts = Counter(triple for i in chosen for triple in triplets[i])
    assert max(counts.values()) <= 2
    assert all(
        not ind.classify_link(group, tuple(heavy[i] for i in sorted(link)))[1]
        for group, link in enumerate(local)
    )

    def cap(removed, added):
        delta = Counter(triple for i in added for triple in triplets[i])
        delta.subtract(triple for i in removed for triple in triplets[i])
        return all(counts[triple] + value <= 2 for triple, value in delta.items())

    def open_link(group, selected):
        return not ind.classify_link(group, tuple(heavy[i] for i in sorted(selected)))[1]

    def switches(group, size):
        anchor = anchors[group]
        raw, allowed = 0, []
        for removed in it.combinations(sorted(local[group]), size):
            degree = Counter(p for i in removed for p in set(heavy[i]) - anchor)
            edges = list(it.combinations(sorted(degree), 2))
            for replacements in it.combinations(edges, size):
                if Counter(p for edge in replacements for p in edge) != degree:
                    continue
                incoming = [tuple(sorted(anchor | set(edge))) for edge in replacements]
                if any(block in {heavy[i] for i in chosen} for block in incoming):
                    continue
                raw += 1
                if any(block not in positions for block in incoming):
                    continue
                allowed.append((frozenset(removed), frozenset(positions[b] for b in incoming)))
        return raw, allowed

    states = {"proper_three": set(), "paired_two": set(), "whole_link": set()}
    accounting = {name: Counter() for name in states}
    twos = []
    for group in range(4):
        raw, moves = switches(group, 3)
        accounting["proper_three"]["raw"] += raw
        accounting["proper_three"]["in_heavy_universe"] += len(moves)
        for removed, added in moves:
            if not cap(removed, added):
                continue
            accounting["proper_three"]["passes_triple_cap"] += 1
            if open_link(group, local[group] - removed | added):
                states["proper_three"].add(tuple(sorted(chosen - removed | added)))
        two_raw, two_moves = switches(group, 2)
        assert two_raw == 40
        twos.append(two_moves)
    for a, b in it.combinations(range(4), 2):
        accounting["paired_two"]["raw"] += 1600
        for (remove_a, add_a), (remove_b, add_b) in it.product(twos[a], twos[b]):
            accounting["paired_two"]["in_heavy_universe"] += 1
            removed, added = remove_a | remove_b, add_a | add_b
            if not cap(removed, added):
                continue
            accounting["paired_two"]["passes_triple_cap"] += 1
            if open_link(a, local[a] - remove_a | add_a) and open_link(
                b, local[b] - remove_b | add_b
            ):
                states["paired_two"].add(tuple(sorted(chosen - removed | added)))

    def perfect_matchings(points):
        if not points:
            yield ()
            return
        first = points[0]
        for index in range(1, len(points)):
            edge = (first, points[index])
            for rest in perfect_matchings(points[1:index] + points[index + 1 :]):
                yield (edge,) + rest

    for group, anchor in enumerate(anchors):
        hub = max(anchor) + 1
        leaves = tuple(p for p in range(1, 17) if p not in anchor and p != hub)
        for pair in it.combinations(leaves, 2):
            remaining = tuple(p for p in leaves if p not in pair)
            for matching in perfect_matchings(remaining):
                accounting["whole_link"]["raw"] += 1
                edges = ((hub, pair[0]), (hub, pair[1])) + matching
                incoming = [tuple(sorted(anchor | set(edge))) for edge in edges]
                if any(block not in positions for block in incoming):
                    continue
                accounting["whole_link"]["in_heavy_universe"] += 1
                added = frozenset(positions[block] for block in incoming)
                if added == local[group]:
                    accounting["whole_link"]["unchanged"] += 1
                    continue
                if not cap(local[group], added):
                    continue
                accounting["whole_link"]["passes_triple_cap"] += 1
                if open_link(group, added):
                    states["whole_link"].add(tuple(sorted(chosen - local[group] | added)))
    RAW.mkdir()
    arrays = {name: np.array(sorted(values), dtype=np.int16) for name, values in states.items()}
    np.savez_compressed(RAW / "states.npz", **arrays)
    summary = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": ind.sha(__file__),
        "independent_basis_sha256": ind.sha(path),
        "source_result_sha256": ind.sha(result_path),
        "best_heavy_global_ids": result["best_heavy_global_ids"],
        "states_archive_sha256": ind.sha(RAW / "states.npz"),
        "neighborhoods": {
            name: {
                **dict(accounting[name]),
                "registry_safe_unique": len(values),
                "sorted_local_states_sha256": ind.digest(sorted(values)),
            }
            for name, values in states.items()
        },
        "scope": "Finite graph-one neighborhoods of the current branch best only.",
    }
    output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
