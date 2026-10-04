#!/usr/bin/env python3
# Document:    Independent Partial Cover Structure Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Find a relabeled copy of the specified core, using only integer containment."""

import argparse
import hashlib
import json
import signal
import time
from collections import Counter
from itertools import combinations, permutations
from pathlib import Path


def read(path, expected):
    blocks = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        block = tuple(map(int, line.split()))
        if len(block) != 5 or len(set(block)) != 5 or not all(1 <= p <= 16 for p in block):
            raise ValueError("malformed block")
        blocks.append(tuple(sorted(block)))
    if len(blocks) != expected or len(set(blocks)) != expected:
        raise ValueError("wrong cardinality or duplicate block")
    return set(blocks)


def counts(blocks, size):
    return Counter(t for block in blocks for t in combinations(block, size))


def screen(candidate, core, seconds=20):
    start = time.monotonic()
    ctr, base = counts(candidate, 3), counts(core, 3)
    heavy = sorted(t for t, n in ctr.items() if n >= 6)
    core_groups = sorted(t for t, n in base.items() if n >= 6)
    if len(core_groups) != 5 or len(set().union(*map(set, core_groups))) != 15:
        raise ValueError("screen requires the audited five-disjoint-heavy core")
    source_center = (set(range(1, 17)) - set().union(*map(set, core_groups))).pop()
    families = [g for g in combinations(heavy, 5) if len(set().union(*map(set, g))) == 15]
    forbidden = [g for g in families if sum(ctr[t] >= 7 for t in g) >= 2]
    pair, core_pair = counts(candidate, 2), counts(core, 2)
    degree, core_degree = counts(candidate, 1), counts(core, 1)
    visited = 0
    mapping = {}
    witness = None

    def add(source, target):
        if degree[(target,)] < core_degree[(source,)]:
            return False
        for p, q in mapping.items():
            if pair[tuple(sorted((target, q)))] < core_pair[tuple(sorted((source, p)))]:
                return False
        for a, b in combinations(mapping, 2):
            if ctr[tuple(sorted((target, mapping[a], mapping[b])))] < base[
                    tuple(sorted((source, a, b)))]:
                return False
        mapping[source] = target
        for block in core:
            if source in block and all(p in mapping for p in block):
                if tuple(sorted(mapping[p] for p in block)) not in candidate:
                    del mapping[source]
                    return False
        return True

    def assign_group(index, targets):
        nonlocal visited, witness
        visited += 1
        if index == 5:
            transformed = {tuple(sorted(mapping[p] for p in b)) for b in core}
            if not transformed <= candidate:
                raise AssertionError("bad containment witness")
            witness = [mapping[p] for p in range(1, 17)]
            return True
        sources = core_groups[index]
        for target_group in targets:
            remaining = [g for g in targets if g != target_group]
            for values in permutations(target_group):
                assigned = []
                for source, target in zip(sources, values):
                    if not add(source, target):
                        break
                    assigned.append(source)
                if len(assigned) == 3 and assign_group(index + 1, remaining):
                    return True
                for source in assigned:
                    del mapping[source]
        return False

    def timeout(_signum, _frame):
        raise TimeoutError

    prior = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    completed = True
    try:
        for family in families:
            target_center = (set(range(1, 17)) - set().union(*map(set, family))).pop()
            mapping.clear()
            if add(source_center, target_center) and assign_group(0, list(family)):
                break
    except TimeoutError:
        completed = False
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior)
    return {
        "heavy_triples": [[list(t), ctr[t]] for t in heavy],
        "forbidden_five_heavy_profile": bool(forbidden), "forbidden_witnesses": forbidden,
        "contains_relabelled_core": True if witness else False if completed else None,
        "mapping_images_of_1_to_16": witness, "search_complete": completed,
        "five_disjoint_heavy_families": len(families), "group_nodes": visited,
        "elapsed_seconds": time.monotonic() - start, "seconds_budget": seconds,
        "useful_escape_structure": completed and witness is None and not forbidden,
        "scope": "Structure screen; passing does not establish extendability or covering.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("core", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=20)
    args = parser.parse_args()
    result = screen(read(args.candidate, 64), read(args.core, 60), args.seconds)
    result.update(candidate_sha256=hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
                  core_sha256=hashlib.sha256(args.core.read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
