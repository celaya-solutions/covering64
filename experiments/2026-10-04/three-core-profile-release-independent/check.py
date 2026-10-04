# Document:    Independent Three Core Profile Preparation Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      52bf8dd57aaf464cd68cb022e643afc21e0b44dfe43ec565e903effb745b9f0f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check all three proved cuts, each legal hint, and the complete frozen models."""

import ast
import importlib.util
import json
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "three-core-profile-release"
SOURCE_SHA = "7c0fc47ad481e8a80631bea85855aa2648c53b0608a21fc9d9fbb58ed6cbf6ee"
MANIFEST_SHA = "546c44b04b7eded3aaac2d0a3a7c0450612f07530f2edbd85284d8c33479292d"
spec = importlib.util.spec_from_file_location(
    "strong_release_gate", DAY / "six-hole-strong-core-release-independent/check.py"
)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
basis = old.basis
read, digest, dump = old.read, old.digest, old.dump
assignment, scan, verify = old.assignment, old.scan, old.verify
LOW, HIGH = -(2**63), 2**63 - 1


def expected(pool, hint, cores, partitions):
    model = basis.expected_model(pool, hint)
    proto = model.proto
    for core in cores:
        row = proto.constraints.add()
        row.linear.vars.extend(core)
        row.linear.coeffs.extend([1] * 60)
        row.linear.domain.extend([LOW, 55])
    chosen = set(hint)
    for p, partition in enumerate(partitions):
        for position, triple in enumerate(partition):
            support = basis.SUPPORT[basis.TRIPLES.index(tuple(triple))]
            for threshold in (6, 7):
                index = 4928 + 10 * p + 2 * position + threshold - 6
                var = proto.variables.add()
                var.name = f"partition_{p}_triple_{position}_at_least_{threshold}"
                var.domain.extend([0, 1])
                for domain, literal in (
                    ([threshold, HIGH], index),
                    ([LOW, threshold - 1], -index - 1),
                ):
                    row = proto.constraints.add()
                    row.linear.vars.extend(support)
                    row.linear.coeffs.extend([1] * 78)
                    row.linear.domain.extend(domain)
                    row.enforcement_literal.append(literal)
                proto.solution_hint.vars.append(index)
                proto.solution_hint.values.append(int(len(chosen & set(support)) >= threshold))
        row = proto.constraints.add()
        row.linear.vars.extend(range(4928 + 10 * p, 4938 + 10 * p))
        row.linear.coeffs.extend([5, 1] * 5)
        row.linear.domain.extend([LOW, 26])
    proto.objective.vars.clear()
    proto.objective.coeffs.clear()
    proto.objective.vars.extend(cores[0] + list(range(4368, 4928)))
    proto.objective.coeffs.extend([1] * 60 + [65] * 560)
    return model


def check_values(model, values):
    assert len(values) == len(model.proto.variables) == 4958 and all(v in (0, 1) for v in values)
    for row in model.proto.constraints:
        if all(values[i] if i >= 0 else not values[-i - 1] for i in row.enforcement_literal):
            total = sum(
                values[i] * c for i, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            assert row.linear.domain[0] <= total <= row.linear.domain[1]
    return sum(
        values[i] * c
        for i, c in zip(model.proto.objective.vars, model.proto.objective.coeffs, strict=True)
    )


def check_model(model, pool, hint, cores, partitions):
    assert not model.validate(), model.validate()
    assert str(model.proto) == str(expected(pool, hint, cores, partitions).proto)
    assert len(model.proto.variables) == 4958 and len(model.proto.constraints) == 1188
    assert list(model.proto.solution_hint.vars) == list(range(4958))
    values = list(model.proto.solution_hint.values)
    assert values == assignment(hint, partitions)
    assert check_values(model, values) == 65 * len(basis.profile(hint)["holes"]) + len(
        set(hint) & set(cores[0])
    )


def selection(manifest, post):
    records = []
    pools = {case["name"]: set(case["pool"]) for case in manifest["cases"]}
    for case in post["cases"]:
        for item in case["saved"] + [case["final"]]:
            path = ROOT / item["path"]
            assert digest(path) == item["sha256"] == manifest["input_files"][item["path"]]
            ids = basis.parse_seed(path)
            assert ids == item["ids"]
            chosen = set(ids)
            overlaps = [len(chosen & set(core)) for core in manifest["core_rows"]]
            counts = [
                [len(chosen & set(basis.SUPPORT[basis.TRIPLES.index(tuple(t))])) for t in part]
                for part in manifest["partitions"]
            ]
            core_ok = max(overlaps) <= 55
            profile_ok = all(
                5 * sum(c >= 6 for c in row) + sum(c >= 7 for c in row) <= 26 for row in counts
            )
            records.append(
                {
                    "path": item["path"],
                    "sha256": digest(path),
                    "origin": "strong_core_independent_postcheck",
                    "holes": len(basis.profile(ids)["holes"]),
                    "ids": ids,
                    "core_overlaps": overlaps,
                    "partition_counts": counts,
                    "all_core_caps_pass": core_ok,
                    "all_profile_cuts_pass": profile_ok,
                    "eligible": core_ok and profile_ok,
                    "pool_membership": {name: chosen <= pool for name, pool in pools.items()},
                    "missing_pool_ids": {
                        name: sorted(chosen - pool) for name, pool in pools.items()
                    },
                }
            )
    assert len(records) == len({r["path"] for r in records}) == 15
    selected = {
        name: min(
            (r for r in records if r["eligible"] and r["pool_membership"][name]),
            key=lambda r: (r["holes"], r["core_overlaps"][0], r["path"]),
        )
        for name in pools
    }
    saved = read(ROOT / manifest["hint_selection_path"])
    assert saved["candidates"] == records and saved["selected"] == selected
    assert (
        saved["ordering"] == ["holes", "original_core_overlap", "path"]
        and saved["optimizer_calls"] == 0
    )
    assert selected["full-4368"]["missing_pool_ids"]["adaptive-952"] == [1151, 1278, 2299]
    return selected


def main():
    assert not (HERE / "gate.json").exists()
    manifest = read(SOURCE / "manifest.json")
    assert digest(SOURCE / "manifest.json") == MANIFEST_SHA
    assert digest(SOURCE / "run.py") == manifest["source_sha256"] == SOURCE_SHA
    assert manifest["ortools_version"] == ortools.__version__
    for mapping in (manifest["input_files"], manifest["proof_files"]):
        for relative, checksum in mapping.items():
            assert digest(ROOT / relative) == checksum
    previous = read(old.SOURCE / "manifest.json")
    prior_gate = read(DAY / "six-hole-strong-core-release-independent/gate.json")
    assert prior_gate["passed"] and prior_gate["manifest_sha256"] == old.MANIFEST_SHA
    for relative, checksum in prior_gate["independent_sources"].items():
        assert digest(ROOT / relative) == checksum
    assert (
        manifest["previous_release_manifest_sha256"]
        == digest(old.SOURCE / "manifest.json")
        == old.MANIFEST_SHA
    )
    for key in (
        "profile_rule",
        "objective",
        "original_elite_global_ids",
        "hole_triple_ids",
        "hole_triples",
        "hole_carrier_global_ids",
        "sources",
        "block_variables",
        "budget",
        "profile_threshold_truth_table_sha256",
    ):
        assert manifest[key] == previous[key]
    assert manifest["variables"] == 4958 and manifest["rows"] == 1188
    assert manifest["seed"] == 2026104103 and manifest["optimization_calls"] == 0
    assert manifest["core_upper_bound"] == 55 and "hint" not in manifest
    third_path = ROOT / manifest["third_core_audit_path"]
    third = read(third_path)
    assert (
        digest(third_path)
        == manifest["third_core_audit_sha256"]
        == "6a3881254e8c659459174bb79630c2b78d946d35f40f52ca472149410820deb9"
    )
    assert (
        third["passed"]
        and third["recommended_upper_bound"] == 55
        and third["candidate_overlap"] == 60
    )
    for relative, checksum in third["sources"].items():
        assert digest(ROOT / relative) == checksum == manifest["input_files"][relative]
    assert manifest["third_core_map_images"] == third["map_images"]
    cores = previous["core_rows"] + [third["core_global_ids"]]
    assert manifest["core_rows"] == cores
    post_path = DAY / "six-hole-strong-core-release-independent/postcheck.json"
    post = read(post_path)
    assert (
        post["passed"] and digest(post_path) == third["sources"][str(post_path.relative_to(ROOT))]
    )
    new_partition = [[1, 2, 3], [5, 6, 7], [8, 12, 16], [9, 10, 11], [13, 14, 15]]
    assert (
        new_partition
        == post["cases"][1]["final"]["all_five_heavy_scan"]["five_heavy_obstructions"][0]["triples"]
    )
    partitions = previous["partitions"] + [new_partition]
    assert manifest["partitions"] == partitions
    assert all(
        len(part) == 5 and len(set(p for triple in part for p in triple)) == 15
        for part in partitions
    )
    assert manifest["threshold_indicators"] == [
        {
            "partition": p,
            "position": i,
            "threshold": threshold,
            "triple": triple,
            "variable_id": 4928 + 10 * p + 2 * i + threshold - 6,
        }
        for p, part in enumerate(partitions)
        for i, triple in enumerate(part)
        for threshold in (6, 7)
    ]
    truth = old.old.previous.truth_tables(
        read(DAY / "heterogeneous-profile-pool/threshold-truth-table.json"),
        zip(("original", "mapped", "third"), partitions),
    )
    assert digest(ROOT / manifest["hint_selection_path"]) == manifest["hint_selection_sha256"]
    selected = selection(manifest, post)
    parameters = cp_model.CpSolver().parameters
    parameters.max_time_in_seconds = 120
    parameters.num_search_workers = 4
    parameters.random_seed = 2026104103
    parameters.log_search_progress = True
    parameters.log_to_stdout = False
    models, reports = [], []
    for case, old_case, hole_count, overlaps in zip(
        manifest["cases"], previous["cases"], (13, 10), ([1, 7, 51], [1, 8, 55]), strict=True
    ):
        for key in ("name", "pool", "pool_size"):
            assert case[key] == old_case[key]
        chosen = selected[case["name"]]
        for case_key, chosen_key in (
            ("hint", "ids"),
            ("hint_source_path", "path"),
            ("hint_sha256", "sha256"),
            ("hint_holes", "holes"),
            ("hint_core_overlaps", "core_overlaps"),
        ):
            assert case[case_key] == chosen[chosen_key]
        assert case["hint_holes"] == hole_count and case["hint_core_overlaps"] == overlaps
        assert case["hint_composite_objective"] == 65 * hole_count + overlaps[0]
        assert set(case["hint"]) <= set(case["pool"])
        assert digest(ROOT / case["model_path"]) == case["model_sha256"]
        assert digest(ROOT / case["parameters_path"]) == case["parameters_sha256"]
        assert (ROOT / case["parameters_path"]).read_text() == str(parameters)
        model = cp_model.CpModel()
        model.proto.parse_text_format((ROOT / case["model_path"]).read_text())
        check_model(model, case["pool"], case["hint"], cores, partitions)
        reports.append(
            {
                "name": case["name"],
                "pool_size": case["pool_size"],
                "model_sha256": case["model_sha256"],
                "parameters_sha256": case["parameters_sha256"],
                "hint_holes": hole_count,
                "hint_core_overlaps": overlaps,
                "verifiers": verify(ROOT / case["hint_source_path"], case["hint"]),
            }
        )
        models.append(model)
    source = ast.parse((SOURCE / "run.py").read_text())
    previous_source = ast.parse((old.SOURCE / "run.py").read_text())
    for name in ("solver_for", "SaveBest", "run"):
        now = next(n for n in source.body if getattr(n, "name", None) == name)
        before = next(n for n in previous_source.body if getattr(n, "name", None) == name)
        if name == "run":
            before = ast.parse(
                ast.unparse(before).replace("manifest['hint']", "case['hint']")
            ).body[0]
        assert ast.dump(now) == ast.dump(before)
    controls = []
    for label, mutate in (
        (
            "missing_third_core_strength",
            lambda p: p.constraints[1124].linear.domain.__setitem__(1, 60),
        ),
        ("wrong_third_profile", lambda p: p.constraints[1187].linear.domain.__setitem__(1, 25)),
        ("one_sided_third_threshold", lambda p: p.constraints[1168].enforcement_literal.clear()),
        (
            "changed_hint",
            lambda p: p.solution_hint.values.__setitem__(0, 1 - p.solution_hint.values[0]),
        ),
        ("changed_hole_weight", lambda p: p.objective.coeffs.__setitem__(60, 64)),
        ("hidden_distance", lambda p: p.constraints.add().linear.domain.extend([0, 1])),
    ):
        damaged = models[0].clone()
        mutate(damaged.proto)
        assert basis.reject(
            lambda: check_model(
                damaged,
                manifest["cases"][0]["pool"],
                manifest["cases"][0]["hint"],
                cores,
                partitions,
            )
        )
        controls.append(label)
    dependencies = dict(prior_gate["independent_sources"])
    dependencies[str(Path(__file__).relative_to(ROOT))] = digest(Path(__file__))
    gate = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "source_sha256": SOURCE_SHA,
        "checker_sha256": digest(Path(__file__)),
        "optimizer_calls": 0,
        "cases": reports,
        "threshold_truth_tables": truth,
        "independent_sources": dependencies,
        "third_core_audit_sha256": digest(third_path),
        "damaged_controls_rejected": controls,
        "scope": (
            "Two bounded pilots using different legal hints; "
            "not a controlled pool-size comparison."
        ),
    }
    dump(HERE / "gate.json", gate)
    print(
        json.dumps(
            {"passed": True, "gate_sha256": digest(HERE / "gate.json"), "optimizer_calls": 0}
        )
    )


if __name__ == "__main__":
    main()
