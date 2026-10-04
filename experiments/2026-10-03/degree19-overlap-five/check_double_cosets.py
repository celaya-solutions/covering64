# Document:    Direct Action-Orbit Check of Overlap-Five Double Coset Counts
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      858033c006c555ad4bdb94d14cdc4492cab6af383666e01674461939293ac39f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount every distinct H/K action by explicit graph components, not Burnside."""

import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parent
    source = folder / "factorization.json.gz"
    data = json.loads(gzip.decompress(source.read_bytes()))
    group = [tuple(mapping) for mapping in data["mapping_group"]]
    ids = {mapping: index for index, mapping in enumerate(group)}
    identity = tuple(range(14))
    subgroups = sorted({tuple(tuple(mapping) for mapping in item[
        "stabilizer_coordinate_permutations"]) for item in data["types"]})
    needed = {mapping for subgroup in subgroups for mapping in subgroup if mapping != identity}
    left = {mapping: [ids[tuple(mapping[point] for point in element)] for element in group]
            for mapping in needed}
    right = {mapping: [ids[tuple(element[point] for point in mapping)] for element in group]
             for mapping in needed}
    actions = {}
    records = []
    for hi, ki in itertools.product(range(len(subgroups)), repeat=2):
        h_group, k_group = subgroups[hi], subgroups[ki]
        moves = [left[mapping] for mapping in h_group if mapping != identity]
        moves += [right[mapping] for mapping in k_group if mapping != identity]
        visited = bytearray(len(group))
        histogram = Counter()
        for start in range(len(group)):
            if visited[start]:
                continue
            visited[start] = 1
            pending = [start]
            cursor = 0
            while cursor < len(pending):
                index = pending[cursor]
                cursor += 1
                for move in moves:
                    target = move[index]
                    if not visited[target]:
                        visited[target] = 1
                        pending.append(target)
            histogram[len(pending)] += 1
        assert sum(size * count for size, count in histogram.items()) == len(group)
        assert all((len(h_group) * len(k_group)) % size == 0 for size in histogram)
        count = sum(histogram.values())
        actions[(h_group, k_group)] = count
        records.append({"target_subgroup_index": hi, "source_subgroup_index": ki,
                        "orbits": count, "orbit_size_histogram": dict(histogram)})
    types = {item["id"]: item for item in data["types"]}
    total = 0
    for row in data["counts"]:
        h_group = tuple(tuple(mapping) for mapping in types[row["first_type"]][
            "stabilizer_coordinate_permutations"])
        k_group = tuple(tuple(mapping) for mapping in types[row["source_type"]][
            "stabilizer_coordinate_permutations"])
        assert actions[(h_group, k_group)] == row["ordered_classes"]
        total += actions[(h_group, k_group)]
    result = {"source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "factorization_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "distinct_coordinate_subgroups": len(subgroups),
              "explicit_action_component_counts": len(records),
              "matched_type_pairs": len(data["counts"]), "ordered_classes": total,
              "subgroups": subgroups, "records": records,
              "scope": "Independent counting algorithm on supplied finite groups; full "
                       "enumeration and normalization completeness still need separate audit."}
    (folder / "direct-orbit-check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ("subgroups", "records")}, indent=2))


if __name__ == "__main__":
    main()
