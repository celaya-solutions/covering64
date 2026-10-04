# Document:    Independent Relabeled-Core Deficit Filter Review
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      6a0177fa7ece17dfccce4eb727166976a9b81820d0b5a7ca15c4c3964dfcf27c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check the source assumptions and compare the filter with exhaustive small controls."""

import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCANNER = HERE.parent / "six-hole-strong-core-release-independent/relabels.py"
CORE = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    assert not (HERE / "audit.json").exists()
    assert sha(SCANNER) == "9cdcd511eb94954bb45c1cf209c5d51517b46c11e46b44a22ce7221d9309f74a"
    assert sha(CORE) == "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
    core = [tuple(map(int, line.split())) for line in CORE.read_text().splitlines()]
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    assert len(core) == len(set(core)) == 60 and all(block in blocks for block in core)
    counts = Counter(triple for block in core for triple in itertools.combinations(block, 3))
    heavy = sorted(triple for triple, count in counts.items() if count >= 6)
    assert len(heavy) == 5 and all(counts[triple] == 6 for triple in heavy)
    assert len(set(itertools.chain.from_iterable(heavy))) == 15
    assert max(sum(set(triple) <= set(block) for triple in heavy) for block in blocks) == 1
    spec = importlib.util.spec_from_file_location("reviewed_filter", SCANNER)
    scanner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scanner)
    support = list(dict.fromkeys(heavy + [triples[i] for i in (1, 31, 71, 137, 241, 377, 503)]))
    controls = []
    for shift in range(8):
        counts = Counter({triple: (index + shift) % 8 for index, triple in enumerate(support)})
        actual, nodes = scanner.partitions(counts)
        expected = sorted(
            sorted(triples.index(triple) for triple in chosen)
            for chosen in itertools.combinations(support, 5)
            if len(set(itertools.chain.from_iterable(chosen))) == 15
            and sum(max(0, 6 - counts[triple]) for triple in chosen) <= 4
        )
        assert [record["triple_ids"] for record in actual] == expected
        controls.append({"shift": shift, "support": len(support),
                         "partitions": len(expected), "recursive_nodes": nodes})
    boundary = []
    for first_count in (0, 1, 2, 5, 6, 7):
        counts = Counter({triple: 6 for triple in heavy})
        counts[heavy[0]] = first_count
        actual, _ = scanner.partitions(counts)
        assert bool(actual) == (first_count >= 2)
        assert len(actual) <= 1
        boundary.append({"first_count": first_count, "accepted": bool(actual)})
    audit = {
        "passed": True, "optimization_calls": 0, "source_sha256": sha(__file__),
        "scanner_sha256": sha(SCANNER), "core_sha256": sha(CORE),
        "core_blocks": 60, "core_disjoint_triples": heavy, "each_core_triple_count": 6,
        "universe_blocks_checked": len(blocks), "maximum_disjoint_triples_per_block": 1,
        "pruned_vs_unpruned_controls": controls, "deficit_boundary_controls": boundary,
        "necessary_condition": "For overlap at least56 with a relabeled60-block core, "
        "five disjoint triples have total max(0,6-count) at most4.",
        "contrapositive": "No such partition implies overlap at most55 for every core relabeling.",
        "positive_partition_is_inconclusive": True,
        "scope": "Source-assumption checks, proof review, and arithmetic enumeration controls. "
        "No construction search, no new covering witness, and no unrestricted bound.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
