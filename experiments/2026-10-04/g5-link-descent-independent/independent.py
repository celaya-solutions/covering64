#!/usr/bin/env python3
# Document:    Independent Graph Five Link Descent Basis
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independent row, neighborhood and catalog reconstruction; no optimizer."""

import functools
import hashlib
import importlib.util
import itertools as it
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "g5-link-descent"
RAW = ROOT / "experiments/scratch/g5-link-descent-20261004"
GRAPH = (2, 0, 0, 0, 0, 2)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


core = load(HERE.parent / "lp-guided-complete-sweep-independent/basis.py", "independent_g5_rows")
catalog = load(
    HERE.parent / "lp-guided-first-link-registry-independent/check.py", "independent_g5_map"
)
digest, shifted, INF = core.digest, core.shifted, core.INF


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@functools.cache
def basis():
    blocks, anchors, ordinary, heavy, general = core.rebuild()
    rows = list(general)
    expected = {622: 7, 626: 5, 630: 5, 664: 5, 668: 5, 690: 7}
    for row_index, target in expected.items():
        ordinary_ids, heavy_ids, lower, upper = rows[row_index]
        assert (lower, upper) == (5, 7)
        rows[row_index] = (ordinary_ids, heavy_ids, target, target)
    changes = [i for i, (a, b) in enumerate(zip(general, rows, strict=True)) if a != b]
    assert changes == list(expected)
    return blocks, anchors, ordinary, heavy, rows


@functools.cache
def catalog_data():
    registry, representatives, lookup, graphs = catalog.load_catalog()
    assert tuple(graphs[5]) == GRAPH
    return registry, representatives, lookup


@functools.cache
def classify_link(group, link):
    registry, representatives, lookup = catalog_data()
    matches = catalog.classify(link, group, GRAPH, representatives, lookup)
    identifier = matches[0][0]
    return identifier, identifier in registry["proof_sources"]


def classify(chosen):
    _, anchors, _, _, _ = basis()
    links = [tuple(sorted(block for block in chosen if anchor <= set(block))) for anchor in anchors]
    assert all(len(link) == 7 for link in links)
    return [classify_link(group, link) for group, link in enumerate(links)]


def neighbors(chosen):
    _, anchors, _, heavy, _ = basis()
    return core.neighbors(chosen, anchors, heavy)


def validate_receipt(chosen, receipt):
    _, anchors, _, _, _ = basis()
    registry, representatives, lookup = catalog_data()
    assert receipt["graph_index"] == 5 and tuple(receipt["hub_excesses"]) == GRAPH
    assert len(receipt["links"]) == 4
    reasons = []
    for group, (anchor, saved) in enumerate(zip(anchors, receipt["links"], strict=True)):
        local = tuple(sorted(block for block in chosen if anchor <= set(block)))
        maps = catalog.classify(local, group, GRAPH, representatives, lookup)
        identifier, excluded = classify_link(group, local)
        assert saved["anchor_group_zero_based"] == group
        assert saved["representative"] == identifier and saved["excluded"] == excluded
        assert catalog.edge_key(saved["physical_heavy_edges"]) == catalog.edge_key(
            set(block) - anchor for block in local
        )
        assert (
            catalog.edge_key(saved["representative_edges"])
            == representatives["matching"][identifier]
        )
        assert saved["proof_sources"] == registry["proof_sources"].get(identifier, [])
        assert len(saved["both_transports"]) == 2
        expected_transports = [
            p
            for p in it.permutations(range(4))
            if p[group] == 0
            and all(
                GRAPH[i] == catalog.canonical_weight("matching", p[a], p[b])
                for i, (a, b) in enumerate(catalog.PAIRS)
            )
        ]
        assert [
            tuple(t["group_transport"]) for t in saved["both_transports"]
        ] == expected_transports
        for transport in saved["both_transports"]:
            assert transport["representative"] == identifier
            assert transport["physical_to_representative"] in [mapping for _, mapping in maps]
        if excluded:
            reasons.append(
                {
                    "anchor_group_zero_based": group,
                    "representative": identifier,
                    "proof_sources": saved["proof_sources"],
                }
            )
    assert receipt["accepted"] == (not reasons)
    return reasons


def validate_ranking(chosen, ranked, family_sha, cuts):
    blocks, _, _, heavy, rows = basis()
    hids = {block: i for i, block in enumerate(heavy)}
    expected = neighbors(chosen)
    seen, order, rejected = set(), [], 0
    for rank, record in enumerate(ranked):
        candidate = tuple(blocks[i] for i in record["heavy_global_ids"])
        assert candidate in expected and candidate not in seen
        seen.add(candidate)
        assert record["rank"] == rank and list(candidate) == sorted(candidate)
        assert record["heavy_local_ids"] == [hids[block] for block in candidate]
        assert all(record[field] == value for field, value in expected[candidate].items())
        assert record["heavy_sha256"] == digest(candidate)
        assert record["shifted_rows_sha256"] == digest(shifted(rows, heavy, candidate))
        violations = [
            max(0, cut["rhs"] - sum(cut["coefficients"][hids[block]] for block in candidate))
            for cut in cuts
        ]
        assert record["cut_violation_numerators"] == violations
        assert record["maximum_cut_lower_bound"] == [max(violations), 1000]
        order.append((max(violations), record["heavy_global_ids"]))
        reasons = validate_receipt(candidate, record["registry"])
        assert record["accepted"] == (not reasons) and record["rejection_reasons"] == reasons
        rejected += bool(reasons)
        assert record["cache_key"] == digest(
            {
                "family_sha256": family_sha,
                "heavy_sha256": record["heavy_sha256"],
                "shifted_rows_sha256": record["shifted_rows_sha256"],
            }
        )
    assert len(seen) == len(expected) and order == sorted(order)
    return len(expected) - rejected, rejected


def check_vector(record):
    blocks, _, ordinary, heavy, rows = basis()
    assert sha(ROOT / record["vector_path"]) == record["vector_sha256"]
    assert sha(ROOT / record["dual_path"]) == record["dual_sha256"]
    values = json.loads((ROOT / record["vector_path"]).read_text())
    dual = json.loads((ROOT / record["dual_path"]).read_text())
    assert len(values) == len(ordinary) == 1200 and len(dual) == 697
    assert all(math.isfinite(v) and -1e-7 <= v <= 1 + 1e-7 for v in values)
    assert all(math.isfinite(v) for v in dual)
    candidate = tuple(blocks[i] for i in record["heavy_global_ids"])
    concrete = shifted(rows, heavy, candidate)
    assert digest(concrete) == record["shifted_rows_sha256"]
    residual = 0.0
    for ids, coefficients, lower, upper in concrete:
        value = math.fsum(c * values[i] for i, c in zip(ids, coefficients, strict=True))
        residual += max(0.0, lower - value)
        if upper != INF:
            residual += max(0.0, value - upper)
    if record["status"] == "OPTIMAL":
        assert abs(residual - record["objective"]) <= 1e-5
    if "recomputed_l1_residual" in record:
        assert abs(residual - record["recomputed_l1_residual"]) <= 1e-5
    return residual
