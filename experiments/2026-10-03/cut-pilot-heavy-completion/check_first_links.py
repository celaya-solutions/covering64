# Document:    Six-Hub-Graph First-Link Registry Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b8103449b21b73328b973b1e68e4e59625554b0588a4af500833785e2380c11f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import gzip
import hashlib
import itertools as it
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORBIT = HERE.parent / "four-seven-link-orbits"
REGISTRY = (
    HERE.parent / "four-seven-template-drat-exclusions-109/combined-first-link-exclusions.json"
)
ANCHORS = [tuple(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
HUB_PAIRS = list(it.combinations(range(4), 2))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(edges):
    return tuple(sorted(tuple(sorted(edge)) for edge in edges))


def weight(case, pair):
    pair = tuple(sorted(pair))
    if case == "cycle":
        return int(pair in [(0, 1), (1, 2), (2, 3), (0, 3)])
    return 2 * int(pair in [(0, 1), (2, 3)])


def main():
    source_check = json.loads((ORBIT / "independent-result.json").read_text())
    assert source_check["complete"]
    assert source_check["checker_sha256"] == sha(ORBIT / "independent_check.py")
    assert source_check["archive_sha256"] == sha(ORBIT / "relabelings.json.gz")
    assert source_check["metadata_sha256"] == sha(ORBIT / "result.json")
    registry = json.loads(REGISTRY.read_text())
    assert sha(REGISTRY) == "a757b484cf6424fb1e3b3d2838cf1476f39768475da4f3d7c50cc883451100dc"
    assert (
        registry["passed"] and registry["excluded_count"] == len(registry["proof_sources"]) == 109
    )
    complete = json.loads(gzip.decompress((ORBIT / "relabelings.json.gz").read_bytes()))
    metadata = json.loads((ORBIT / "result.json").read_text())
    tables, representatives = {}, {}
    for case in complete:
        table = {}
        for orbit in case["orbits"]:
            for mapping in orbit["maps"]:
                edges = key(mapping["edges"])
                assert edges not in table
                table[edges] = (orbit["id"], mapping["from_representative"])
        assert len(table) == 29970
        tables[case["case"]] = table
    for case in metadata["cases"]:
        representatives[case["case"]] = {r["id"]: key(r["edges"]) for r in case["representatives"]}
    seed_path = HERE / "seed.txt"
    seed = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
    heavy = [[b for b in seed if set(a) <= set(b)] for a in ANCHORS]
    assert all(len(group) == 7 for group in heavy)
    graphs = [
        v
        for v in it.product(range(3), repeat=6)
        if all(sum(v[i] for i, p in enumerate(HUB_PAIRS) if h in p) == 2 for h in range(4))
    ]
    assert len(graphs) == 6
    cases = []
    for number, graph in enumerate(graphs):
        case = "matching" if 2 in graph else "cycle"
        links = []
        for group in range(4):
            edges = key(set(b) - set(ANCHORS[group]) for b in heavy[group])
            transports = [
                p
                for p in it.permutations(range(4))
                if p[group] == 0
                and all(
                    graph[i] == weight(case, (p[a], p[b])) for i, (a, b) in enumerate(HUB_PAIRS)
                )
            ]
            assert len(transports) == 2
            matches = []
            for transport in transports:
                q = [4 * transport[(p - 1) // 4] + (p - 1) % 4 + 1 for p in range(1, 17)]
                normalized = key((q[a - 1], q[b - 1]) for a, b in edges)
                identifier, from_rep = tables[case][normalized]
                inverse = [from_rep.index(p) + 1 for p in range(1, 17)]
                mapping = [inverse[q[p - 1] - 1] for p in range(1, 17)]
                assert sorted(mapping) == list(range(1, 17))
                assert (
                    key((mapping[a - 1], mapping[b - 1]) for a, b in edges)
                    == representatives[case][identifier]
                )
                assert tuple(sorted(mapping[p - 1] for p in ANCHORS[group])) == (1, 2, 3)
                assert all(
                    graph[i]
                    == weight(case, ((mapping[4 * a + 3] - 4) // 4, (mapping[4 * b + 3] - 4) // 4))
                    for i, (a, b) in enumerate(HUB_PAIRS)
                )
                matches.append((identifier, mapping))
            assert matches[0][0] == matches[1][0], "transport choice changed orbit"
            identifier, mapping = matches[0]
            links.append(
                {
                    "anchor_group_zero_based": group,
                    "representative": identifier,
                    "excluded": identifier in registry["proof_sources"],
                    "physical_to_representative": mapping,
                    "physical_heavy_edges": edges,
                    "representative_edges": representatives[case][identifier],
                    "proof_sources": registry["proof_sources"].get(identifier, []),
                    "both_graph_transports_agree": True,
                }
            )
        cases.append(
            {
                "graph_index_zero_based": number,
                "case": case,
                "hub_excesses_in_lex_pair_order": graph,
                "links": links,
                "eliminated_by_registry": any(link["excluded"] for link in links),
            }
        )
    survivors = [c["graph_index_zero_based"] for c in cases if not c["eliminated_by_registry"]]
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "seed_sha256": sha(seed_path),
        "registry_sha256": sha(REGISTRY),
        "checked_exclusions": 109,
        "complete_link_archive_sha256": sha(ORBIT / "relabelings.json.gz"),
        "source_link_audit_sha256": sha(ORBIT / "independent-result.json"),
        "hub_group_pairs_zero_based": HUB_PAIRS,
        "cases": cases,
        "graphs_screened": 6,
        "links_classified": 24,
        "transport_checks": 48,
        "surviving_graph_indices_zero_based": survivors,
        "all_six_graphs_eliminated": not survivors,
        "scope": "Registry membership for the fixed heavy tuple under every hub graph. "
        "An open representative is not proof that the tuple has a completion.",
    }
    (HERE / "first-link-screen.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "surviving_graphs": survivors,
                "cases": [
                    {
                        "index": c["graph_index_zero_based"],
                        "case": c["case"],
                        "representatives": [x["representative"] for x in c["links"]],
                        "excluded": [x["representative"] for x in c["links"] if x["excluded"]],
                    }
                    for c in cases
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
