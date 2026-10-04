# Document:    Checked Matching-g5 Link Registry Classifier
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      4b0de989b3cec7de9933b4c6776d63a39bf330fc84bc3d45477d5542f2632787
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Transport physical heavy links into the audited first-link orbit registry."""

import gzip
import hashlib
import itertools as it
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "experiments/2026-10-03"
ORBIT = OLD / "four-seven-link-orbits"
REGISTRY = OLD / "four-seven-template-drat-exclusions-109/combined-first-link-exclusions.json"
ANCHORS = [tuple(range(4 * group + 1, 4 * group + 4)) for group in range(4)]
PAIRS = list(it.combinations(range(4), 2))
GRAPH = (2, 0, 0, 0, 0, 2)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def key(edges):
    return tuple(sorted(tuple(sorted(edge)) for edge in edges))


def matching_weight(pair):
    return 2 * int(tuple(sorted(pair)) in ((0, 1), (2, 3)))


class Registry:
    def __init__(self):
        source_check = json.loads((ORBIT / "independent-result.json").read_text())
        assert source_check["complete"]
        assert source_check["checker_sha256"] == sha(ORBIT / "independent_check.py")
        assert source_check["archive_sha256"] == sha(ORBIT / "relabelings.json.gz")
        assert source_check["metadata_sha256"] == sha(ORBIT / "result.json")
        assert sha(REGISTRY) == "a757b484cf6424fb1e3b3d2838cf1476f39768475da4f3d7c50cc883451100dc"
        self.registry = json.loads(REGISTRY.read_text())
        assert (
            self.registry["passed"]
            and self.registry["excluded_count"] == len(self.registry["proof_sources"]) == 109
        )
        archive = json.loads(gzip.decompress((ORBIT / "relabelings.json.gz").read_bytes()))
        self.table = {}
        for case in archive:
            if case["case"] != "matching":
                continue
            for orbit in case["orbits"]:
                for mapping in orbit["maps"]:
                    edges = key(mapping["edges"])
                    assert edges not in self.table
                    self.table[edges] = (orbit["id"], mapping["from_representative"])
        assert len(self.table) == 29970
        metadata = json.loads((ORBIT / "result.json").read_text())
        self.representatives = next(
            {row["id"]: key(row["edges"]) for row in case["representatives"]}
            for case in metadata["cases"]
            if case["case"] == "matching"
        )
        self.transports = {
            group: [
                permutation
                for permutation in it.permutations(range(4))
                if permutation[group] == 0
                and all(
                    GRAPH[index] == matching_weight((permutation[a], permutation[b]))
                    for index, (a, b) in enumerate(PAIRS)
                )
            ]
            for group in range(4)
        }
        assert all(len(permutations) == 2 for permutations in self.transports.values())
        self.cache = {}

    def link(self, group, edges):
        edges = key(edges)
        cache_key = (group, edges)
        if cache_key in self.cache:
            return self.cache[cache_key]
        matches = []
        for transport in self.transports[group]:
            physical = [
                4 * transport[(point - 1) // 4] + (point - 1) % 4 + 1 for point in range(1, 17)
            ]
            transported = key((physical[a - 1], physical[b - 1]) for a, b in edges)
            identifier, from_representative = self.table[transported]
            inverse = [from_representative.index(point) + 1 for point in range(1, 17)]
            mapping = [inverse[physical[point - 1] - 1] for point in range(1, 17)]
            assert sorted(mapping) == list(range(1, 17))
            assert (
                key((mapping[a - 1], mapping[b - 1]) for a, b in edges)
                == self.representatives[identifier]
            )
            assert tuple(sorted(mapping[point - 1] for point in ANCHORS[group])) == (1, 2, 3)
            assert all(
                GRAPH[index]
                == matching_weight(((mapping[4 * a + 3] - 4) // 4, (mapping[4 * b + 3] - 4) // 4))
                for index, (a, b) in enumerate(PAIRS)
            )
            matches.append(
                {
                    "representative": identifier,
                    "group_transport": transport,
                    "physical_to_representative": mapping,
                }
            )
        assert matches[0]["representative"] == matches[1]["representative"]
        identifier = matches[0]["representative"]
        result = {
            "anchor_group_zero_based": group,
            "physical_heavy_edges": edges,
            "representative": identifier,
            "representative_edges": self.representatives[identifier],
            "excluded": identifier in self.registry["proof_sources"],
            "proof_sources": self.registry["proof_sources"].get(identifier, []),
            "both_transports": matches,
        }
        self.cache[cache_key] = result
        return result

    def classify(self, heavy):
        assert len(heavy) == len(set(heavy)) == 28
        links = []
        for group, anchor in enumerate(ANCHORS):
            local = [block for block in heavy if set(anchor) <= set(block)]
            assert len(local) == 7
            links.append(self.link(group, (set(block) - set(anchor) for block in local)))
        return {
            "graph_index": 5,
            "hub_excesses": GRAPH,
            "links": links,
            "accepted": not any(link["excluded"] for link in links),
        }

    def input_paths(self):
        return [
            REGISTRY,
            ORBIT / "independent-result.json",
            ORBIT / "independent_check.py",
            ORBIT / "relabelings.json.gz",
            ORBIT / "result.json",
        ]
