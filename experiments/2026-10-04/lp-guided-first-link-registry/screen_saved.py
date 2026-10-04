# Document:    Registry Screen of Saved Nearest and Margin Heavy Tuples
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7bb1bff17669063148329836653d141b795c7880215f13de59a59997ddef137f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rank existing saved tuples by old broad LP scores after registry screening."""

import importlib.util
import json
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DAY = HERE.parent
HELPER = DAY / "lp-guided-first-link-registry-independent/check.py"


def main():
    spec = importlib.util.spec_from_file_location("independent_link_catalog", HELPER)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    registry, representatives, lookup, graphs = checker.load_catalog()
    blocks = list(combinations(range(1, 17), 5))
    inputs = {}
    records = []
    mapping_cache = {}
    all_maps = {}
    for campaign, expected in [("nearest-heavy-master", 95), ("margin-heavy-master", 20)]:
        path = DAY / campaign / "result.json"
        inputs[str(path.relative_to(ROOT))] = sha256(path.read_bytes()).hexdigest()
        source = json.loads(path.read_text())
        assert len(source["records"]) == expected
        for record in source["records"]:
            ids = tuple(sorted(record["heavy_global_ids"]))
            assert len(ids) == len(set(ids)) == 28
            fixed = [blocks[i] for i in ids]
            links = [[b for b in fixed if a <= set(b)] for a in checker.ANCHORS]
            assert all(len(link) == 7 for link in links)
            cases, maps = [], []
            survivors = []
            for g, graph in enumerate(graphs):
                classes, classified_maps = [], []
                for group, link in enumerate(links):
                    key = (group, tuple(link), g)
                    if key not in mapping_cache:
                        mapping_cache[key] = checker.classify(
                            link, group, graph, representatives, lookup
                        )
                    matches = mapping_cache[key]
                    identifier, point_map = matches[0]
                    classes.append(identifier)
                    classified_maps.append(
                        {
                            "anchor_group": group,
                            "representative": identifier,
                            "physical_to_representative": point_map,
                            "two_transports_agree": True,
                        }
                    )
                excluded = [x for x in classes if x in registry["proof_sources"]]
                if not excluded:
                    survivors.append(g)
                cases.append({"graph": g, "classes": classes, "excluded": excluded})
                maps.append({"graph": g, "excess_vector": graph, "links": classified_maps})
            canonical = "".join(" ".join(map(str, b)) + "\n" for b in fixed)
            heavy_sha = sha256(canonical.encode()).hexdigest()
            all_maps[heavy_sha] = maps
            assert record["lp"]["status"] == "OPTIMAL"
            records.append(
                {
                    "campaign": campaign,
                    "step": record["step"],
                    "heavy_global_ids": ids,
                    "canonical_heavy_sha256": heavy_sha,
                    "broad_elastic_objective": record["lp"]["objective"],
                    "surviving_graph_indices": survivors,
                    "surviving_graph_mask": sum(1 << g for g in survivors),
                    "cases": cases,
                }
            )
    eligible = sorted(
        (r for r in records if r["surviving_graph_mask"]),
        key=lambda r: (r["broad_elastic_objective"], r["campaign"], r["step"]),
    )
    unique = []
    seen = set()
    for row in eligible:
        if row["canonical_heavy_sha256"] not in seen:
            seen.add(row["canonical_heavy_sha256"])
            unique.append(row)
    top = [row | {"maps": all_maps[row["canonical_heavy_sha256"]]} for row in unique[:5]]
    result = {
        "passed": True,
        "optimization_calls": 0,
        "saved_tuples_screened": len(records),
        "registry_exclusions": 109,
        "distinct_labeled_tuples": len(all_maps),
        "eligible_saved_tuples": len(eligible),
        "eligible_distinct_labeled_tuples": len(unique),
        "survivor_mask_counts": dict(
            sorted(Counter(r["surviving_graph_mask"] for r in records).items())
        ),
        "records": records,
        "top_five_distinct_labeled_tuples": top,
        "ranked_eligible": [
            {
                key: row[key]
                for key in (
                    "campaign",
                    "step",
                    "canonical_heavy_sha256",
                    "broad_elastic_objective",
                    "surviving_graph_mask",
                    "surviving_graph_indices",
                )
            }
            for row in unique
        ],
        "helper_sha256": sha256(HELPER.read_bytes()).hexdigest(),
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "input_sha256": inputs,
        "scope": "Existing broad all-graph LP objectives only. No new LP calls, no fixed-graph "
        "fitness evaluation, no whole-tuple isomorphism reduction, and no cover claim.",
    }
    (HERE / "saved-screen.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "saved_tuples_screened",
                    "eligible_saved_tuples",
                    "eligible_distinct_labeled_tuples",
                    "survivor_mask_counts",
                )
            }
        )
    )
    print(json.dumps(result["ranked_eligible"][:5]))


if __name__ == "__main__":
    main()
