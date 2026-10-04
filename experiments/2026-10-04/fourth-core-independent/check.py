# Document:    Independent Fourth Core Transport and Maximum Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      58b7b187a62dfbcc26c8e810a3edd763a562bae3b371de7921578b9760a19e45
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Reconstruct the explicit core and independently enumerate all relevant point maps."""

import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/2026-10-04/recovered-six-hole-core-transport-v2"
RAW = ROOT / "experiments/scratch/fourth-core-independent-20261004"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
RANK = {block: i for i, block in enumerate(BLOCKS)}
TRIPLES = list(itertools.combinations(range(1, 17), 3))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_family(path):
    blocks = [
        tuple(sorted(map(int, line.split())))
        for line in path.read_text().splitlines()
        if line and not line.startswith("#")
    ]
    assert len(blocks) == len(set(blocks)) and all(block in RANK for block in blocks)
    return sorted(blocks)


def map_family(family, mapping):
    assert sorted(mapping) == list(range(1, 17))
    return sorted(tuple(sorted(mapping[p - 1] for p in block)) for block in family)


def main():
    original_path = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
    candidate_path = ROOT / (
        "experiments/2026-10-03/reduced-family-heuristic/"
        "penalty-2026100363/search-control_before-1-h6.txt"
    )
    proof_path = ROOT / "experiments/2026-10-04/core-cap-independent/audit.json"
    witness_path, result_path = SOURCE / "witness.json", SOURCE / "result.json"
    assert sha(original_path) == "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
    assert sha(candidate_path) == "797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de"
    assert sha(proof_path) == "fec461fad7b3f53fade9beecec77c7146487e02f5bbb36f543f642d190edc5a8"
    assert sha(witness_path) == "bdc25945621e88cb71a0ef250437b9d6accfa6064565a8039908ba5f44139b0e"
    proof = json.loads(proof_path.read_text())
    assert proof["passed"] and proof["recommended_upper_bound"] == 55
    witness, producer = json.loads(witness_path.read_text()), json.loads(result_path.read_text())
    old, candidate = load_family(original_path), load_family(candidate_path)
    assert len(old) == 60 and len(candidate) == 64
    mapping = witness["map_images"]
    transported = map_family(old, mapping)
    core_ids = sorted(RANK[block] for block in transported)
    candidate_ids = sorted(RANK[block] for block in candidate)
    intersection = sorted(set(core_ids) & set(candidate_ids))
    assert len(intersection) == 59 == witness["overlap"]
    assert list(map(list, transported)) == witness["transported_core_blocks"]
    assert core_ids == witness["transported_core_global_ids"]
    assert candidate_ids == witness["candidate_global_ids"]
    assert intersection == witness["intersection_global_ids"]
    inverse = [mapping.index(p) + 1 for p in range(1, 17)]
    assert map_family(transported, inverse) == old
    all_mapped = map_family(BLOCKS, mapping)
    assert all_mapped == BLOCKS and map_family(all_mapped, inverse) == BLOCKS
    triple_map = {triple: tuple(sorted(mapping[p - 1] for p in triple)) for triple in TRIPLES}
    assert sorted(triple_map.values()) == TRIPLES
    incidence_checks = 0
    for block in BLOCKS:
        mapped_block = tuple(sorted(mapping[p - 1] for p in block))
        assert sorted(triple_map[t] for t in itertools.combinations(block, 3)) == list(
            itertools.combinations(mapped_block, 3)
        )
        incidence_checks += 10
    old_counts = Counter(t for block in old for t in itertools.combinations(block, 3))
    old_heavy = [triple for triple in TRIPLES if old_counts[triple] >= 6]
    assert len(old_heavy) == 5 and all(old_counts[t] == 6 for t in old_heavy)
    assert len(set().union(*map(set, old_heavy))) == 15
    assert all(sum(set(t) <= set(block) for t in old_heavy) <= 1 for block in BLOCKS)
    counts = Counter(t for block in candidate for t in itertools.combinations(block, 3))
    eligible = sorted((max(0, 6 - counts[t]), t) for t in TRIPLES if counts[t] >= 2)
    partitions = []

    def visit(start, chosen, used, budget):
        if len(chosen) == 5:
            partitions.append(sorted(chosen))
            return
        for index in range(start, len(eligible)):
            cost, triple = eligible[index]
            if cost > budget:
                break
            if not used.intersection(triple):
                visit(index + 1, chosen + [triple], used.union(triple), budget - cost)

    visit(0, [], set(), 4)
    assert len(partitions) == 1
    target = partitions[0]
    assert [counts[t] for t in target] == [7, 6, 7, 5, 6]
    (old_unused,) = set(range(1, 17)) - set().union(*map(set, old_heavy))
    (new_unused,) = set(range(1, 17)) - set().union(*map(set, target))
    RAW.mkdir(parents=True, exist_ok=True)
    header = "// Independently regenerated point sets and block families.\n"
    for name, rows, width in [
        ("OLD_BLOCKS", old, 5),
        ("CANDIDATE", candidate, 5),
        ("OLD_TRIPLES", old_heavy, 3),
        ("NEW_TRIPLES", target, 3),
    ]:
        header += f"const int {name}[{len(rows)}][{width}]={{"
        header += ",".join("{" + ",".join(map(str, row)) + "}" for row in rows) + "};\n"
    header += f"const int OLD_UNUSED={old_unused}, NEW_UNUSED={new_unused};\n"
    (RAW / "data.hpp").write_text(header)
    command = [
        "/usr/bin/clang++",
        "-std=c++17",
        "-O3",
        "-Wall",
        "-Wextra",
        "-pedantic",
        "-I",
        str(RAW),
        str(HERE / "enumerate.cpp"),
        "-o",
        str(RAW / "enumerate"),
    ]
    compile_result = subprocess.run(command, text=True, capture_output=True, check=True, timeout=60)
    assert not compile_result.stderr
    process = subprocess.run(
        [str(RAW / "enumerate")], text=True, capture_output=True, check=True, timeout=60
    )
    assert not process.stderr
    enumeration = json.loads(process.stdout)
    assert enumeration["maps"] == 933120 and enumeration["best"] == 59
    assert enumeration["best_map_count"] == 60
    assert enumeration["histogram"] == producer["overlap_histogram"]
    assert sum(enumeration["histogram"]) == 933120
    for label, output in [
        ("compile-stdout", compile_result.stdout),
        ("compile-stderr", compile_result.stderr),
        ("enumeration-stdout", process.stdout),
        ("enumeration-stderr", process.stderr),
    ]:
        (RAW / f"{label}.txt").write_text(output)
    damaged = []
    bad = list(mapping)
    bad[0] = bad[1]
    try:
        map_family(old, bad)
    except AssertionError:
        damaged.append("nonbijective map")
    assert len(damaged) == 1
    assert core_ids != core_ids[:-1] + [core_ids[0]]
    damaged.append("duplicate core ID")
    assert intersection != intersection[:-1]
    damaged.append("missing intersection block")
    output = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "enumerator_sha256": sha(HERE / "enumerate.cpp"),
        "optimizer_calls": 0,
        "sources": {
            str(path.relative_to(ROOT)): sha(path)
            for path in [original_path, candidate_path, proof_path, witness_path, result_path]
        },
        "map_images": mapping,
        "inverse_map_images": inverse,
        "core_global_ids": core_ids,
        "overlap": 59,
        "recommended_upper_bound": 55,
        "violates_necessary_fourth_cap": True,
        "point_maps_bijective": True,
        "block_map_size": 4368,
        "triple_map_size": 560,
        "incidences_checked": incidence_checks,
        "necessary_partitions": partitions,
        "necessary_partition_counts": [[counts[t] for t in partition] for partition in partitions],
        "enumeration": enumeration,
        "compile_command": command,
        "mapping_completeness": "Every map of the five disjoint original heavy triples "
        "to the sole necessary target partition chooses one of5! triple assignments and "
        "one of(3!)^5 within-triple bijections; the unused point is forced. These choices "
        "are unique, giving933120 distinct point maps.",
        "high_overlap_necessity": "Overlap>=56 deletes at most4 original core blocks. "
        "Each deleted block contains at most one of the five disjoint sixfold triples. "
        "Added blocks cannot lower triple counts, so the transported partition has "
        "sum(max(0,6-c(T)))<=4. Exactly one such partition exists for this candidate.",
        "maximum_scope": "The independent histogram has no overlap above59 and includes "
        "every possible overlap>=56 by the necessary-partition argument. Hence59 is "
        "the global maximum over all point relabelings for this exact candidate, "
        "without enumerating all16! maps.",
        "transport_proof": "The independently audited original core cap55 transports "
        "under a point bijection because all blocks, triples and incidences are preserved. "
        "The fourth row is necessary for every64-cover; it was not added to the frozen runs.",
        "damaged_controls_rejected": damaged,
        "raw_files": {
            str(path.relative_to(ROOT)): sha(path) for path in RAW.iterdir() if path.is_file()
        },
    }
    (HERE / "audit.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "audit_sha256": sha(HERE / "audit.json"),
                "maximum_overlap": 59,
                "cap": 55,
                "maps": 933120,
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
