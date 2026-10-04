#!/usr/bin/env python3
# Document:    Independent Six Graph First Link Scope Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Replay orbit maps and derive finite mask-union nogoods without a solver."""

import gzip
import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
ORBIT = ROOT / "experiments/2026-10-03/four-seven-link-orbits"
REGISTRY = ROOT / ("experiments/2026-10-03/four-seven-template-drat-exclusions-109/"
                   "combined-first-link-exclusions.json")
ANCHORS = [frozenset(range(4 * group + 1, 4 * group + 4)) for group in range(4)]
PAIRS = list(it.combinations(range(4), 2))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def edge_key(edges):
    return tuple(sorted(tuple(sorted(edge)) for edge in edges))


def load_catalog():
    checked = json.loads((ORBIT / "independent-result.json").read_text())
    assert checked["complete"]
    for name, field in (("independent_check.py", "checker_sha256"),
                        ("relabelings.json.gz", "archive_sha256"),
                        ("result.json", "metadata_sha256")):
        assert sha(ORBIT / name) == checked[field]
    registry = json.loads(REGISTRY.read_text())
    assert sha(REGISTRY) == "a757b484cf6424fb1e3b3d2838cf1476f39768475da4f3d7c50cc883451100dc"
    assert registry["passed"]
    assert len(registry["proof_sources"]) == registry["excluded_count"] == 109
    metadata = json.loads((ORBIT / "result.json").read_text())
    representatives = {case["case"]: {entry["id"]: edge_key(entry["edges"])
                                      for entry in case["representatives"]}
                       for case in metadata["cases"]}
    archive = json.loads(gzip.decompress((ORBIT / "relabelings.json.gz").read_bytes()))
    lookup = {}
    for case in archive:
        table = {}
        for orbit in case["orbits"]:
            for entry in orbit["maps"]:
                key = edge_key(entry["edges"])
                assert key not in table
                table[key] = (orbit["id"], entry["from_representative"])
        assert len(table) == 29970
        lookup[case["case"]] = table
    graphs = [values for values in it.product(range(3), repeat=6)
              if all(sum(values[i] for i, pair in enumerate(PAIRS) if hub in pair) == 2
                     for hub in range(4))]
    assert len(graphs) == 6
    return registry, representatives, lookup, graphs


def canonical_weight(case, a, b):
    pair = tuple(sorted((a, b)))
    if case == "cycle":
        return int(pair in ((0, 1), (0, 3), (1, 2), (2, 3)))
    return 2 * int(pair in ((0, 1), (2, 3)))


def classify(link, group, graph, representatives, lookup):
    case = "matching" if max(graph) == 2 else "cycle"
    physical_edges = edge_key(set(block) - ANCHORS[group] for block in link)
    matches = []
    for transport in it.permutations(range(4)):
        if transport[group] != 0:
            continue
        if any(graph[i] != canonical_weight(case, transport[a], transport[b])
               for i, (a, b) in enumerate(PAIRS)):
            continue
        point_map = {point: 4 * transport[(point - 1) // 4] + (point - 1) % 4 + 1
                     for point in range(1, 17)}
        normalized = edge_key((point_map[a], point_map[b]) for a, b in physical_edges)
        identifier, from_representative = lookup[case][normalized]
        assert sorted(from_representative) == list(range(1, 17))
        inverse = {physical: original for original, physical
                   in enumerate(from_representative, start=1)}
        final = {point: inverse[point_map[point]] for point in range(1, 17)}
        assert len(set(final.values())) == 16
        assert edge_key((final[a], final[b]) for a, b in physical_edges) == (
            representatives[case][identifier])
        for anchor in ANCHORS:
            mapped = frozenset(final[p] for p in anchor)
            assert mapped in ANCHORS
            assert final[max(anchor) + 1] == max(mapped) + 1
        assert frozenset(final[p] for p in ANCHORS[group]) == ANCHORS[0]
        assert all(graph[i] == canonical_weight(case, (final[4 * a + 4] - 1) // 4,
                                                (final[4 * b + 4] - 1) // 4)
                   for i, (a, b) in enumerate(PAIRS))
        matches.append((identifier, [final[p] for p in range(1, 17)]))
    assert len(matches) == 2 and matches[0][0] == matches[1][0]
    return matches


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    registry, representatives, lookup, graphs = load_catalog()
    all_blocks = list(it.combinations(range(1, 17), 5))
    results = []
    for name in ("best-5p575883", "nearest-step-038"):
        directory = DAY / "lp-guided-first-link-registry" / name
        record = json.loads((directory / "first-link-screen.json").read_text())
        pins = [tuple(map(int, line.split()))
                for line in (directory / "seed.txt").read_text().splitlines()]
        assert len(pins) == len(set(pins)) == 28
        assert all(len(block) == len(set(block)) == 5 and tuple(sorted(block)) == block
                   and set(block) <= set(range(1, 17)) for block in pins)
        assert record["seed_sha256"] == sha(directory / "seed.txt")
        assert record["registry_sha256"] == sha(REGISTRY)
        links = [sorted(block for block in pins if anchor <= set(block)) for anchor in ANCHORS]
        assert all(len(link) == 7 for link in links)
        for anchor, link in zip(ANCHORS, links, strict=True):
            assert Counter(p for block in link for p in set(block) - anchor) == {
                p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor}
        masks, cases = [0] * 4, []
        for graph_id, graph in enumerate(graphs):
            saved = record["cases"][graph_id]
            assert tuple(saved["hub_excesses_in_lex_pair_order"]) == graph
            classified = []
            for group, link in enumerate(links):
                matches = classify(link, group, graph, representatives, lookup)
                identifier = matches[0][0]
                excluded = identifier in registry["proof_sources"]
                old = saved["links"][group]
                assert (old["representative"], old["excluded"]) == (identifier, excluded)
                assert old["physical_to_representative"] in [mapping for _, mapping in matches]
                assert old["proof_sources"] == registry["proof_sources"].get(identifier, [])
                if excluded:
                    masks[group] |= 1 << graph_id
                classified.append({"group": group, "representative": identifier,
                                   "excluded": excluded})
            assert saved["eliminated_by_registry"] == any(row["excluded"] for row in classified)
            cases.append({"graph_index": graph_id, "links": classified})
        survivors = [i for i in range(6) if not any(mask & (1 << i) for mask in masks)]
        assert survivors == record["surviving_graph_indices_zero_based"]
        assert record["all_six_graphs_eliminated"] == (not survivors)
        covering_subsets = []
        for size in range(1, 5):
            for subset in it.combinations(range(4), size):
                union = 0
                for group in subset:
                    union |= masks[group]
                if union == 63:
                    covering_subsets.append(subset)
            if covering_subsets:
                break
        nogoods = [{"anchor_groups": list(subset), "mask": 63,
                    "block_global_ids": sorted(all_blocks.index(block) for group in subset
                                               for block in links[group]),
                    "maximum_selected": 7 * len(subset) - 1}
                   for subset in covering_subsets]
        assert bool(nogoods) == (not survivors)
        results.append({"name": name, "seed_sha256": sha(directory / "seed.txt"),
                        "screen_sha256": sha(directory / "first-link-screen.json"),
                        "anchor_blocked_masks": masks, "surviving_graphs": survivors,
                        "cases": cases, "minimum_union_nogoods": nogoods})
    assert results[0]["surviving_graphs"] == []
    assert results[1]["surviving_graphs"] == [1]
    report = {"passed": True, "solver_calls": 0, "checker_sha256": sha(__file__),
              "registry_sha256": sha(REGISTRY),
              "orbit_archive_sha256": sha(ORBIT / "relabelings.json.gz"),
              "orbit_metadata_sha256": sha(ORBIT / "result.json"),
              "orbit_audit_sha256": sha(ORBIT / "independent-result.json"),
              "graphs": graphs, "transport_checks": 96, "results": results,
              "scope": "Registry exclusions and union nogoods are conditional on the "
                       "regular four-sevenfold family; an open mask does not prove completion."}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "results": [{k: v for k, v in row.items() if k != "cases"}
                                                   for row in results]}, indent=2))


if __name__ == "__main__":
    main()
