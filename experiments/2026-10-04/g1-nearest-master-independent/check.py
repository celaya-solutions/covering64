# Document:    Independent Fixed-g1 Nearest Master Preparation Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild the full master and registry nogoods without importing its builder."""

import importlib.util
import itertools as it
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "g1-nearest-master"
PLAN = ROOT / "experiments/scratch/g1-next-route-plan-20261004"
LOW, HIGH = -(2**63), 2**63 - 1
spec = importlib.util.spec_from_file_location(
    "independent_nearest_g1", DAY / "g1-link-descent-independent/independent.py"
)
ind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ind)


def read(path):
    return json.loads(Path(path).read_text())


def validate_nogood(nogood, blocks, anchors, global_ids):
    registry, representatives, lookup = ind.catalog_data()
    group = nogood["anchor_group_zero_based"]
    assert type(group) is int and 0 <= group < 4
    ids = nogood["heavy_global_ids"]
    assert len(ids) == len(set(ids)) == 7 and ids == sorted(ids)
    assert nogood["graph_index"] == 1 and nogood["upper_bound"] == 6
    assert nogood["heavy_local_ids"] == sorted(global_ids.index(i) for i in ids)
    selected = tuple(blocks[i] for i in ids)
    anchor = anchors[group]
    assert all(anchor <= set(block) for block in selected)
    matches = ind.catalog.classify(selected, group, ind.GRAPH, representatives, lookup)
    identifier = matches[0][0]
    receipt = nogood["registry"]
    assert receipt["anchor_group_zero_based"] == group
    assert receipt["representative"] == identifier and receipt["excluded"] is True
    assert receipt["proof_sources"] == registry["proof_sources"][identifier]
    assert receipt["proof_sources"]
    assert ind.catalog.edge_key(receipt["physical_heavy_edges"]) == ind.catalog.edge_key(
        set(block) - anchor for block in selected
    )
    assert ind.catalog.edge_key(receipt["representative_edges"]) == representatives["cycle"][
        identifier
    ]
    transports = [
        p for p in it.permutations(range(4)) if p[group] == 0
        and all(
            ind.GRAPH[i] == ind.catalog.canonical_weight("cycle", p[a], p[b])
            for i, (a, b) in enumerate(ind.catalog.PAIRS)
        )
    ]
    assert [tuple(t["group_transport"]) for t in receipt["both_transports"]] == transports
    for transport in receipt["both_transports"]:
        assert transport["representative"] == identifier
        assert transport["physical_to_representative"] in [mapping for _, mapping in matches]


def master(heavy, anchors, global_ids, cuts, nogoods, baseline):
    expected = cp_model_pb2.CpModelProto()
    for index in global_ids:
        expected.variables.add(name=f"block_{index}", domain=[0, 1])

    def add(coefficients, lower, upper):
        row = expected.constraints.add().linear
        for index, coefficient in enumerate(coefficients):
            if coefficient:
                row.vars.append(index)
                row.coeffs.append(coefficient)
        row.domain.extend([lower, upper])

    add([1] * 276, 28, 28)
    for anchor in anchors:
        for point in range(1, 17):
            if point not in anchor:
                target = 2 if point == max(anchor) + 1 else 1
                add([int(anchor | {point} <= set(block)) for block in heavy], target, target)
    for triple in it.combinations(range(1, 17), 3):
        if frozenset(triple) not in anchors:
            coefficients = [int(set(triple) <= set(block)) for block in heavy]
            if any(coefficients):
                add(coefficients, LOW, 2)
    assert len(expected.constraints) == 605
    for cut in cuts:
        assert len(cut["coefficients"]) == 276
        assert abs(cut["rhs"]) + sum(map(abs, cut["coefficients"])) < 2**60
        add(cut["coefficients"], cut["rhs"], HIGH)
    for nogood in nogoods:
        add([int(i in nogood["heavy_local_ids"]) for i in range(276)], LOW, 6)
    assert len(baseline) == len(set(baseline)) == 28
    for index, global_id in enumerate(global_ids):
        if global_id in baseline:
            expected.objective.vars.append(index)
            expected.objective.coeffs.append(-1)
    expected.objective.offset = 28
    expected.objective.scaling_factor = 1
    return expected


def main():
    assert not (HERE / "audit.json").exists()
    manifest = read(SOURCE / "manifest.json")
    assert manifest["source_sha256"] == ind.sha(SOURCE / "run.py")
    for path, expected in manifest["input_files"].items():
        assert ind.sha(ROOT / path) == expected
    blocks, anchors, ordinary, heavy, rows = ind.basis()
    global_ids = [blocks.index(block) for block in heavy]
    assert global_ids == manifest["heavy_global_ids"]
    assert [blocks.index(block) for block in ordinary] == manifest["ordinary_global_ids"]
    assert ind.digest(rows) == manifest["unconditional_rows_sha256"]
    family_sha = ind.digest({
        "rows": rows, "ordinary_global_ids": manifest["ordinary_global_ids"], "graph_index": 1
    })
    assert family_sha == manifest["family_sha256"] and manifest["graph_index"] == 1
    assert manifest["hub_pair_targets"] == [5, 6, 6, 6, 6, 5]
    certificate_path = DAY / "g1-whole-link-certificates-independent/audit.json"
    certificate = read(certificate_path)
    bundle_path = ROOT / certificate["bundle_path"]
    assert certificate["passed"] and ind.sha(bundle_path) == certificate["bundle_sha256"]
    assert certificate["family_sha256"] == family_sha
    assert certificate["graph_index"] == 1 and certificate["replayed_graph_specific_planes"] == 1000
    bundle = read(bundle_path)
    broad = read(PLAN / "broad-cuts-reference.json")["cuts"]
    assert len(broad) == 353 and len(bundle["cuts"]) == 1000
    screen = read(DAY / "g1-larger-independent/audit.json")
    envelope = read(PLAN / "envelope-results.json")
    assert screen["passed"] and screen["envelope_results_sha256"] == ind.sha(
        PLAN / "envelope-results.json"
    )
    assert envelope["broad_reference_sha256"] == ind.sha(PLAN / "broad-cuts-reference.json")
    nogoods = read(ROOT / manifest["nogoods_path"])
    assert ind.sha(ROOT / manifest["nogoods_path"]) == manifest["nogoods_sha256"]
    assert len(nogoods) == len({tuple(n["heavy_global_ids"]) for n in nogoods}) == 19
    for nogood in nogoods:
        validate_nogood(nogood, blocks, anchors, global_ids)
    baseline = manifest["baseline_record"]
    previous = read(DAY / "g1-link-descent/result.json")
    previous_audit = read(DAY / "g1-link-descent-independent/postcheck.json")
    assert previous_audit["passed"] and previous_audit["result_sha256"] == ind.sha(
        DAY / "g1-link-descent/result.json"
    )
    assert baseline == previous["trajectory"][-1]
    assert baseline["heavy_global_ids"] == manifest["baseline_heavy_global_ids"]
    assert baseline["objective"] == manifest["baseline_elastic_objective"] == 7.52051548546158
    residual = ind.check_vector(baseline)
    expected = master(heavy, anchors, global_ids, broad + bundle["cuts"], nogoods,
                      baseline["heavy_global_ids"])
    actual = text_format.Parse(
        (ROOT / manifest["master_path"]).read_text(), cp_model_pb2.CpModelProto()
    )
    assert ind.sha(ROOT / manifest["master_path"]) == manifest["master_sha256"]
    assert actual.SerializeToString(deterministic=True) == expected.SerializeToString(
        deterministic=True
    )
    assert len(actual.variables) == 276 and len(actual.constraints) == 1977
    assert manifest["budget"] == {
        "admitted_lps": 50, "master_proposals": 150, "each_master_seconds": 2,
        "each_lp_seconds": 1, "combined_solver_seconds": 120, "wall_seconds": 160,
        "workers": 1, "seed": 2026104070
    }
    damaged = cp_model_pb2.CpModelProto()
    damaged.CopyFrom(actual)
    damaged.objective.coeffs[0] = 1
    assert damaged.SerializeToString(deterministic=True) != expected.SerializeToString(
        deterministic=True
    )
    damaged.CopyFrom(actual)
    damaged.constraints[-1].linear.domain[1] = 7
    assert damaged.SerializeToString(deterministic=True) != expected.SerializeToString(
        deterministic=True
    )
    report = {
        "passed": True, "optimizer_calls": 0,
        "source_sha256": ind.sha(SOURCE / "run.py"),
        "manifest_sha256": ind.sha(SOURCE / "manifest.json"),
        "checker_sha256": ind.sha(__file__), "master_sha256": manifest["master_sha256"],
        "certificate_audit_sha256": ind.sha(certificate_path),
        "family_sha256": family_sha, "graph_index": 1,
        "master_variables": 276, "master_rows": 1977, "base_rows": 605,
        "broad_cuts": 353, "g1_cuts": 1000, "registry_nogoods": 19,
        "baseline_residual_recounted": residual, "damaged_controls_rejected": 2,
        "objective": "28 minus overlap with frozen baseline; no radius constraint",
        "source_review": [
            "Registry is checked before LP; each rejected link adds a g1-only seven-block nogood",
            "Master objective stays fixed at original baseline throughout the run",
            "All learned signed-row planes use exact fixed-g1 rows and remain g1-only",
            "One worker, 2s/master, 1s/LP, 150 proposals and 50 admitted LP maxima",
            "Pre-master guards116.8solver/153wall and pre-LP guards118.9solver/156wall",
            "UNKNOWN and all master stops without candidates are inconclusive",
            "Stop on recovered exact primal, unresolved zero, unresolved exact cut or LP",
        ],
        "scope": "Preparation only; no optimization or full-family exclusion claim.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
