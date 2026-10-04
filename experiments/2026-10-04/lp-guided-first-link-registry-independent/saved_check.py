#!/usr/bin/env python3
# Document:    Saved Heavy Campaign Registry Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebind 115 saved tuples, registry masks and broad-LP ranking without solves."""

import functools
import hashlib
import itertools as it
import json
from collections import Counter

from check import ANCHORS, DAY, HERE, ROOT, classify, load_catalog, sha


def main():
    output = HERE / "saved-audit.json"
    assert not output.exists()
    source = DAY / "lp-guided-first-link-registry/saved-screen.json"
    saved = json.loads(source.read_text())
    assert saved["passed"] and saved["optimization_calls"] == 0
    assert saved["source_sha256"] == sha(source.parent / "screen_saved.py")
    assert saved["helper_sha256"] == sha(HERE / "check.py")
    registry, representatives, lookup, graphs = load_catalog()
    blocks = list(it.combinations(range(1, 17), 5))

    @functools.cache
    def checked_classification(group, link, graph_id):
        return classify(link, group, graphs[graph_id], representatives, lookup)

    expected = []
    for campaign, count in (("nearest-heavy-master", 95), ("margin-heavy-master", 20)):
        path = DAY / campaign / "result.json"
        assert sha(path) == saved["input_sha256"][str(path.relative_to(ROOT))]
        result = json.loads(path.read_text())
        assert len(result["records"]) == count
        for original in result["records"]:
            ids = sorted(original["heavy_global_ids"])
            assert len(ids) == len(set(ids)) == 28
            chosen = [blocks[i] for i in ids]
            links = [tuple(block for block in chosen if anchor <= set(block)) for anchor in ANCHORS]
            cases, survivors = [], []
            for graph_id in range(6):
                classes = [checked_classification(group, link, graph_id)[0][0]
                           for group, link in enumerate(links)]
                excluded = [identifier for identifier in classes
                            if identifier in registry["proof_sources"]]
                if not excluded:
                    survivors.append(graph_id)
                cases.append({"graph": graph_id, "classes": classes, "excluded": excluded})
            canonical = "".join(" ".join(map(str, block)) + "\n" for block in chosen)
            canonical_hash = hashlib.sha256(canonical.encode()).hexdigest()
            assert original["lp"]["status"] == "OPTIMAL"
            expected.append({"campaign": campaign, "step": original["step"],
                             "heavy_global_ids": ids,
                             "canonical_heavy_sha256": canonical_hash,
                             "broad_elastic_objective": original["lp"]["objective"],
                             "surviving_graph_indices": survivors,
                             "surviving_graph_mask": sum(1 << graph_id for graph_id in survivors),
                             "cases": cases})
    assert expected == saved["records"]
    assert len({row["canonical_heavy_sha256"] for row in expected}) == 115
    eligible = sorted(
        (row for row in expected if row["surviving_graph_mask"]),
        key=lambda row: (row["broad_elastic_objective"], row["campaign"], row["step"]))
    assert len(eligible) == saved["eligible_saved_tuples"] == 51
    for actual, row in zip(saved["ranked_eligible"], eligible, strict=True):
        assert all(actual[key] == row[key] for key in actual)
    for actual, row in zip(saved["top_five_distinct_labeled_tuples"], eligible[:5], strict=True):
        assert {key: value for key, value in actual.items() if key != "maps"} == row
        chosen = [blocks[i] for i in row["heavy_global_ids"]]
        for graph_id, graph_maps in enumerate(actual["maps"]):
            assert tuple(graph_maps["excess_vector"]) == graphs[graph_id]
            for group, mapped in enumerate(graph_maps["links"]):
                link = tuple(block for block in chosen if ANCHORS[group] <= set(block))
                matches = checked_classification(group, link, graph_id)
                assert mapped["representative"] == matches[0][0]
                assert mapped["physical_to_representative"] in [mapping for _, mapping in matches]
    counts = dict(Counter(str(row["surviving_graph_mask"]) for row in expected))
    assert counts == saved["survivor_mask_counts"] == {"0": 64, "2": 37, "10": 1, "16": 11, "18": 2}
    report = {"passed": True, "optimizer_calls": 0, "checker_sha256": sha(__file__),
              "mapper_sha256": sha(HERE / "check.py"), "saved_screen_sha256": sha(source),
              "saved_tuples": 115, "eligible_distinct_labeled_tuples": 51,
              "survivor_mask_counts": counts,
              "top_five": [{key: row[key] for key in (
                  "campaign", "step", "broad_elastic_objective", "surviving_graph_mask")}
                  for row in eligible[:5]],
              "scope": "Readback uses the already independently audited mapper. Scores are broad "
                       "all-graph LP scores, not fixed-graph scores or whole-tuple classes."}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
