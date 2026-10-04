#!/usr/bin/env python3
# Document:    Independent Matching Graph Five Diagnostic Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild two fixed graph-five models and replay registry maps without solving."""

import ast
import hashlib
import importlib.util
import itertools as it
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "matching-g5-lp"
RAW = ROOT / "experiments/scratch/matching-g5-lp-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_case(manifest):
    core = load(
        HERE.parent / "lp-guided-complete-sweep-independent/basis.py", "g5_independent_rows"
    )
    blocks, anchors, ordinary, heavy, broad = core.rebuild()
    rows = list(broad)
    for index, target in zip((622, 626, 630, 664, 668, 690), (7, 5, 5, 5, 5, 7), strict=True):
        oi, hi, lo, up = rows[index]
        assert (lo, up) == (5, 7)
        rows[index] = oi, hi, target, target
    fixed = tuple(blocks[i] for i in manifest["heavy_global_ids"])
    assert len(fixed) == len(set(fixed)) == 28 and list(fixed) == sorted(fixed)
    assert [list(block) for block in fixed] == manifest["heavy_blocks"]
    assert set(fixed) <= set(heavy)
    assert manifest["ordinary_global_ids"] == [blocks.index(block) for block in ordinary]
    shifted = core.shifted(rows, heavy, fixed)
    proto = cp_model_pb2.CpModelProto()
    for index in manifest["ordinary_global_ids"]:
        proto.variables.add(name=f"block_{index}", domain=[0, 1])
    for ids, coefficients, lower, upper in shifted:
        row = proto.constraints.add().linear
        row.vars.extend(ids)
        row.coeffs.extend(coefficients)
        row.domain.extend([lower, upper])
    return proto, shifted, fixed, anchors, ordinary


def main():
    output = HERE / "audit.json"
    assert not output.exists()
    top = json.loads((SOURCE / "manifest.json").read_text())
    assert (
        top["source_sha256"] == sha(SOURCE / "diagnostic.py") == sha(RAW / "diagnostic-frozen.py")
    )
    assert (
        top["optimization_calls"],
        top["proposed_runs"],
        top["seconds_each"],
        top["workers_each"],
    ) == (0, 2, 1, 1)
    for path, expected_hash in top["input_sha256"].items():
        assert sha(ROOT / path) == expected_hash
    tree = ast.parse((SOURCE / "diagnostic.py").read_text())
    time_limits, worker_limits, solve_calls = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "SetTimeLimit":
                time_limits.append(ast.literal_eval(node.args[0]))
            if node.func.attr == "SetNumThreads":
                worker_limits.append(ast.literal_eval(node.args[0]))
            if node.func.attr == "Solve":
                solve_calls.append(node.lineno)
    assert time_limits == [1000] and worker_limits == [1] and len(solve_calls) == 1
    catalog = load(HERE.parent / "lp-guided-first-link-registry-independent/check.py", "g5_scope")
    registry, representatives, lookup, graphs = catalog.load_catalog()
    assert graphs[5] == (2, 0, 0, 0, 0, 2)
    checked = []
    assert [entry["case"] for entry in top["cases"]] == ["soft-raw-17", "soft-score-19"]
    for entry, expected_holes in zip(top["cases"], (17, 19), strict=True):
        name = entry["case"]
        manifest_path = SOURCE / name / "manifest.json"
        assert sha(manifest_path) == entry["manifest_sha256"]
        manifest = json.loads(manifest_path.read_text())
        assert manifest["source_sha256"] == top["source_sha256"]
        assert (
            manifest["graph_index"],
            manifest["seconds"],
            manifest["workers"],
            manifest["seed"],
        ) == (5, 1, 1, 2026104)
        assert manifest["hub_excesses"] == [2, 0, 0, 0, 0, 2]
        assert manifest["hub_pair_targets"] == [7, 5, 5, 5, 5, 7]
        for name_file, field in (
            ("model.pbtxt", "model_sha256"),
            ("rows.json", "rows_sha256"),
            ("elastic-model.lp", "elastic_model_sha256"),
        ):
            assert sha(RAW / name / name_file) == manifest[field]
        proto, rows, fixed, anchors, ordinary = expected_case(manifest)
        actual = text_format.Parse(
            (RAW / name / "model.pbtxt").read_text(), cp_model_pb2.CpModelProto()
        )
        assert proto.SerializeToString(deterministic=True) == actual.SerializeToString(
            deterministic=True
        )
        assert rows == json.loads((RAW / name / "rows.json").read_text())
        assert len(rows) == manifest["rows"] == 697 and len(ordinary) == manifest["columns"] == 1200
        seed_path = SOURCE / name / "seed.txt"
        assert sha(seed_path) == manifest["seed_sha256"] == sha(ROOT / manifest["source_seed_path"])
        seed = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
        assert len(seed) == len(set(seed)) == 64
        assert all(
            len(block) == len(set(block)) == 5
            and tuple(sorted(block)) == block
            and set(block) <= set(range(1, 17))
            for block in seed
        )
        assert sorted(set(seed) - set(ordinary)) == list(fixed)
        triples = {triple for block in seed for triple in it.combinations(block, 3)}
        assert 560 - len(triples) == expected_holes
        canonical = "".join(" ".join(map(str, block)) + "\n" for block in fixed)
        assert hashlib.sha256(canonical.encode()).hexdigest() == manifest["heavy_sha256"]
        classes = []
        for group, anchor in enumerate(anchors):
            link = [block for block in fixed if anchor <= set(block)]
            assert len(link) == 7
            matches = catalog.classify(link, group, graphs[5], representatives, lookup)
            identifier = matches[0][0]
            assert identifier not in registry["proof_sources"]
            classes.append(identifier)
        assert classes == manifest["registry_link_classes"]
        damaged = cp_model_pb2.CpModelProto()
        damaged.CopyFrom(actual)
        damaged.constraints[622].linear.domain[0] += 1
        assert damaged.SerializeToString(deterministic=True) != proto.SerializeToString(
            deterministic=True
        )
        checked.append(
            {
                "case": name,
                "manifest_sha256": sha(manifest_path),
                "model_sha256": manifest["model_sha256"],
                "rows_sha256": manifest["rows_sha256"],
                "registry_classes": classes,
                "seed_holes": expected_holes,
                "shifted_rows_checked": 697,
                "ordinary_columns_checked": 1200,
            }
        )
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "runner_sha256": sha(SOURCE / "diagnostic.py"),
        "manifest_sha256": sha(SOURCE / "manifest.json"),
        "authorized_runs": 2,
        "seconds_each": 1,
        "workers_each": 1,
        "graph_index": 5,
        "hub_targets": [7, 5, 5, 5, 5, 7],
        "registry_sha256": sha(catalog.REGISTRY),
        "checked": checked,
        "damaged_models_rejected": 2,
        "source_review": "Elastic lower/upper slacks have positive unit objective, "
        "ordinary bounds [0,1], one GLOP Solve per exclusive case launch.",
        "scope": "Only these two fixed-heavy graph-five diagnostics are authorized.",
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
