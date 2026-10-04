# Document:    Independent Strong Core Release Preparation Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f219a35d7c88db24dfb6d6ba373d3fca31f9bb4dd2741c76f4ae6230243724a1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Independently check the strong-cap model delta, legal hint, and fixed budgets."""

import ast
import importlib.util
import json
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
SOURCE = DAY / "six-hole-strong-core-release"
SOURCE_SHA = "a570ebded365c26ffcc90ece8c3c27f72e182b4df5bb2ab46b813fa087738ebf"
MANIFEST_SHA = "7b7266c9ed7a6c57a0959afd9b396af40aa3e89b5155efac8e26c006aa8f274d"
spec = importlib.util.spec_from_file_location(
    "prior_release_gate", DAY / "six-hole-pool-release-independent/check.py"
)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
basis = old.basis
read, digest, dump = old.read, old.digest, old.dump
assignment, check_values, scan, verify = old.assignment, old.check_values, old.scan, old.verify


def expected(pool, hint, cores, partitions):
    model = old.expected(pool, hint, cores, partitions)
    for position in (1122, 1123):
        assert model.proto.constraints[position].linear.domain[1] == 59
        model.proto.constraints[position].linear.domain[1] = 55
    return model


def check_model(model, pool, hint, cores, partitions):
    assert not model.validate(), model.validate()
    assert str(model.proto) == str(expected(pool, hint, cores, partitions).proto)
    assert len(model.proto.variables) == 4948 and len(model.proto.constraints) == 1166
    assert list(model.proto.solution_hint.vars) == list(range(4948))
    values = list(model.proto.solution_hint.values)
    assert values == assignment(hint, partitions)
    assert check_values(model, values) == 911 and sum(values[4368:4928]) == 14


def selection(manifest):
    inventory = read(DAY / "heterogeneous-seed-inventory/inventory.json")
    profiles = read(DAY / "heterogeneous-profile-postcheck/audit.json")
    release = read(DAY / "six-hole-pool-release/result.json")
    audited_release = read(DAY / "six-hole-pool-release-independent/postcheck.json")
    assert profiles["passed"] and audited_release["passed"]
    assert audited_release["result_sha256"] == digest(DAY / "six-hole-pool-release/result.json")
    tuples = [(r["path"], r["sha256"], "original_inventory") for r in inventory["entries"]]
    tuples += [(r["path"], r["sha256"], "profile_postcheck") for r in profiles["checked_states"]]
    for case, audited in zip(release["cases"], audited_release["cases"], strict=True):
        assert case["name"] == audited["name"]
        rows = case["improvements"] + [case["final"]]
        checked = audited["saved"] + [audited["final"]]
        for raw, known in zip(rows, checked, strict=True):
            assert raw["sha256"] == known["sha256"] and raw["ids"] == known["ids"]
            tuples.append((raw["path"], raw["sha256"], "matched_release_postcheck"))
    records, seen = [], set()
    for path, checksum, origin in tuples:
        if path in seen:
            continue
        seen.add(path)
        assert digest(ROOT / path) == checksum == manifest["input_files"][path]
        ids = basis.parse_seed(ROOT / path)
        chosen = set(ids)
        overlaps = [len(chosen & set(core)) for core in manifest["core_rows"]]
        counts = [
            [
                len(chosen & set(basis.SUPPORT[basis.TRIPLES.index(tuple(triple))]))
                for triple in partition
            ]
            for partition in manifest["partitions"]
        ]
        core_ok = max(overlaps) <= 55
        profile_ok = all(
            5 * sum(c >= 6 for c in row) + sum(c >= 7 for c in row) <= 26 for row in counts
        )
        records.append(
            {
                "path": path,
                "sha256": checksum,
                "origin": origin,
                "holes": len(basis.profile(ids)["holes"]),
                "core_overlaps": overlaps,
                "partition_counts": counts,
                "both_core_caps_pass": core_ok,
                "both_profile_cuts_pass": profile_ok,
                "eligible": core_ok and profile_ok,
            }
        )
    assert len(records) == 36
    legal = sorted(
        (r for r in records if r["eligible"]),
        key=lambda r: (r["holes"], r["core_overlaps"][0], r["path"]),
    )
    assert len(legal) == 10
    saved = read(ROOT / manifest["hint_selection_path"])
    assert saved == {"candidates": records, "selected": legal[0], "optimizer_calls": 0}
    assert legal[0]["path"] == manifest["hint_source_path"]
    assert legal[0]["holes"] == 14 and legal[0]["core_overlaps"] == [1, 7]
    return {"candidate_paths": 36, "eligible_paths": 10, "selected": legal[0]}


def main():
    assert not (HERE / "gate.json").exists()
    manifest = read(SOURCE / "manifest.json")
    assert digest(SOURCE / "manifest.json") == MANIFEST_SHA
    assert digest(SOURCE / "run.py") == manifest["source_sha256"] == SOURCE_SHA
    assert manifest["ortools_version"] == ortools.__version__
    for mapping in (manifest["input_files"], manifest["proof_files"]):
        for relative, checksum in mapping.items():
            assert digest(ROOT / relative) == checksum
    old_manifest = read(old.SOURCE / "manifest.json")
    old_gate = read(DAY / "six-hole-pool-release-independent/gate.json")
    assert old_gate["passed"] and old_gate["manifest_sha256"] == digest(
        old.SOURCE / "manifest.json"
    )
    for relative, checksum in old_gate["independent_sources"].items():
        assert digest(ROOT / relative) == checksum
    assert manifest["previous_release_manifest_sha256"] == old.MANIFEST_SHA
    for key in (
        "core_rows",
        "partitions",
        "profile_rule",
        "threshold_indicators",
        "objective",
        "original_elite_global_ids",
        "hole_triple_ids",
        "hole_triples",
        "hole_carrier_global_ids",
        "sources",
        "variables",
        "rows",
        "block_variables",
        "budget",
        "profile_threshold_truth_table_sha256",
    ):
        assert manifest[key] == old_manifest[key]
    cap_path = ROOT / manifest["strong_core_audit_path"]
    cap = read(cap_path)
    assert (
        digest(cap_path)
        == manifest["strong_core_audit_sha256"]
        == "fec461fad7b3f53fade9beecec77c7146487e02f5bbb36f543f642d190edc5a8"
    )
    assert cap["passed"] and cap["optimizer_calls"] == 0 and cap["recommended_upper_bound"] == 55
    for relative, checksum in cap["sources"].items():
        assert digest(ROOT / relative) == checksum == manifest["input_files"][relative]
    assert manifest["strong_core_translations"] == cap["current_core_translations"]
    assert manifest["core_rows"] == [r["core_global_ids"] for r in cap["current_core_translations"]]
    assert manifest["core_upper_bound"] == 55
    assert digest(ROOT / manifest["hint_selection_path"]) == manifest["hint_selection_sha256"]
    selected = selection(manifest)
    hint = basis.parse_seed(ROOT / manifest["hint_source_path"])
    assert hint == manifest["hint"]
    assert digest(ROOT / manifest["hint_source_path"]) == manifest["hint_sha256"]
    assert manifest["hint_holes"] == 14 and manifest["hint_original_core_overlap"] == 1
    assert manifest["hint_composite_objective"] == 911 and manifest["seed"] == 2026104102
    assert manifest["optimization_calls"] == 0
    verified_hint = verify(ROOT / manifest["hint_source_path"], hint)
    params = cp_model.CpSolver().parameters
    params.max_time_in_seconds = 120
    params.num_search_workers = 4
    params.random_seed = 2026104102
    params.log_search_progress = True
    params.log_to_stdout = False
    models, reports = [], []
    for case, old_case in zip(manifest["cases"], old_manifest["cases"], strict=True):
        for key in ("name", "pool", "pool_size"):
            assert case[key] == old_case[key]
        assert set(hint) <= set(case["pool"])
        assert digest(ROOT / case["model_path"]) == case["model_sha256"]
        assert digest(ROOT / case["parameters_path"]) == case["parameters_sha256"]
        assert (ROOT / case["parameters_path"]).read_text() == str(params)
        model = cp_model.CpModel()
        model.proto.parse_text_format((ROOT / case["model_path"]).read_text())
        check_model(model, case["pool"], hint, manifest["core_rows"], manifest["partitions"])
        restored = model.clone()
        for position in (1122, 1123):
            restored.proto.constraints[position].linear.domain[1] = 59
        restored.proto.solution_hint.values.clear()
        restored.proto.solution_hint.values.extend(
            assignment(old_manifest["hint"], manifest["partitions"])
        )
        assert str(restored.proto) == (ROOT / old_case["model_path"]).read_text()
        models.append(model)
        reports.append(
            {
                "name": case["name"],
                "pool_size": case["pool_size"],
                "variables": 4948,
                "rows": 1166,
                "model_sha256": case["model_sha256"],
                "parameters_sha256": case["parameters_sha256"],
                "only_model_deltas": ["two core upper bounds 59 to 55", "complete legal hint"],
            }
        )
    source = ast.parse((SOURCE / "run.py").read_text())
    old_source = ast.parse((old.SOURCE / "run.py").read_text())
    for name in ("solver_for", "save_state", "SaveBest", "run"):
        current = next(n for n in source.body if getattr(n, "name", None) == name)
        previous = next(n for n in old_source.body if getattr(n, "name", None) == name)
        assert ast.dump(current) == ast.dump(previous)
    seed = next(
        n for n in source.body if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "SEED"
    )
    assert ast.literal_eval(seed.value) == 2026104102
    controls = []
    for label, mutate in (
        ("weak_original_core", lambda p: p.constraints[1122].linear.domain.__setitem__(1, 59)),
        ("unproved_core54", lambda p: p.constraints[1123].linear.domain.__setitem__(1, 54)),
        ("changed_hole_weight", lambda p: p.objective.coeffs.__setitem__(60, 64)),
        (
            "changed_hint",
            lambda p: p.solution_hint.values.__setitem__(0, 1 - p.solution_hint.values[0]),
        ),
        ("changed_profile", lambda p: p.constraints[1144].linear.domain.__setitem__(1, 25)),
        ("hidden_distance_row", lambda p: p.constraints.add().linear.domain.extend([0, 1])),
    ):
        damaged = models[0].clone()
        mutate(damaged.proto)
        assert basis.reject(
            lambda: check_model(
                damaged,
                manifest["cases"][0]["pool"],
                hint,
                manifest["core_rows"],
                manifest["partitions"],
            )
        )
        controls.append(label)
    dependencies = dict(old_gate["independent_sources"])
    dependencies[str(Path(__file__).relative_to(ROOT))] = digest(Path(__file__))
    gate = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "source_sha256": SOURCE_SHA,
        "checker_sha256": digest(Path(__file__)),
        "optimizer_calls": 0,
        "cases": reports,
        "hint_selection": selected,
        "hint_verifiers": verified_hint,
        "hint_all_five_heavy_scan": scan(hint),
        "independent_sources": dependencies,
        "damaged_controls_rejected": controls,
        "core_cap_audit_sha256": digest(cap_path),
        "scope": (
            "Preparation gate: proved cap55, legal hint, and seed are the only changes. "
            "No optimizer calls."
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
