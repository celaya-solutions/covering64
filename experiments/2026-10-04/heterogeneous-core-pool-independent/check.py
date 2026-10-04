# Document:    Independent Core-Avoiding Pool Delta Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      46ab4a5b261ac3ac4fdc3ebe80f9124da44be8036077bc86ffb26692aa607c45
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check exactly two declared construction restrictions and the changed hint."""

import ast
import importlib.util
import json
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
TARGET = DAY / "heterogeneous-core-pool"
BASE = DAY / "heterogeneous-pool"
MANIFEST_SHA = "9014372202dd8e31347f19f2b1cc53d23dace48e135605815778d07b9c30bd46"
spec = importlib.util.spec_from_file_location(
    "independent_pool_basis", DAY / "heterogeneous-pool-independent/check.py"
)
basis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(basis)
MAPS = [list(range(1, 17)), [1, 7, 2, 10, 15, 3, 8, 11, 4, 9, 12, 16, 14, 6, 5, 13]]


def expected(pool, hint, cores):
    model = basis.expected_model(pool, hint)
    for core in cores:
        row = model.proto.constraints.add()
        row.linear.vars.extend(core)
        row.linear.coeffs.extend([1] * 60)
        row.linear.domain.extend([-9223372036854775808, 59])
    return model


def check_model(model, pool, hint, cores):
    assert not model.validate(), model.validate()
    assert str(model.proto) == str(expected(pool, hint, cores).proto)
    values = list(model.proto.solution_hint.values)
    for row in model.proto.constraints:
        if all(values[v] if v >= 0 else not values[-v - 1] for v in row.enforcement_literal):
            total = sum(
                values[v] * c for v, c in zip(row.linear.vars, row.linear.coeffs, strict=True)
            )
            assert row.linear.domain[0] <= total <= row.linear.domain[1]
    assert sum(values[4368:]) == 5
    assert [sum(values[i] for i in core) for core in cores] == [0, 59]


def main():
    manifest_path = TARGET / "manifest.json"
    assert basis.digest(manifest_path) == MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text())
    previous = json.loads((BASE / "manifest.json").read_text())
    assert basis.digest(BASE / "manifest.json") == basis.MANIFEST_SHA
    assert json.loads((DAY / "heterogeneous-pool-independent/gate.json").read_text())["passed"]
    assert json.loads((DAY / "heterogeneous-pool-independent/postcheck.json").read_text())["passed"]
    assert basis.digest(TARGET / "run.py") == manifest["source_sha256"]
    for key in ("sources", "random_additions", "seed", "budget", "ortools_version"):
        assert manifest[key] == previous[key]
    assert manifest["budget"] == {"cases": 2, "seconds_per_case": 30, "workers": 4}
    for source in manifest["sources"]:
        path = ROOT / source["path"]
        assert basis.digest(path) == source["sha256"]
        assert basis.parse_seed(path) == source["ids"]
        assert all(source[k] == value for k, value in basis.profile(source["ids"]).items())
    core_path = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
    assert (
        basis.digest(core_path)
        == "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
    )
    core = [tuple(map(int, line.split())) for line in core_path.read_text().splitlines()]
    assert len(core) == len(set(core)) == 60 and all(b in basis.RANK for b in core)
    cores = []
    for mapping, source in zip(MAPS, manifest["sources"][:2], strict=True):
        assert sorted(mapping) == list(range(1, 17))
        transported = sorted(basis.RANK[tuple(sorted(mapping[p - 1] for p in b))] for b in core)
        assert len(set(transported)) == 60 and set(transported) <= set(source["ids"])
        cores.append(transported)
    assert manifest["core_rows"] == cores
    hint = manifest["hint"]
    assert hint == manifest["sources"][2]["ids"]
    eligible = [
        source
        for source in manifest["sources"]
        if all(len(set(source["ids"]) & set(c)) <= 59 for c in cores)
    ]
    assert min(eligible, key=lambda s: len(s["holes"]))["ids"] == hint
    # Unchanged helpers and run loop are independently tied to the earlier reviewed source.
    old_tree = ast.parse((BASE / "run.py").read_text())
    new_tree = ast.parse((TARGET / "run.py").read_text())
    old_defs = {n.name: n for n in old_tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    new_defs = {n.name: n for n in new_tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    for name in ("sha", "dump", "read_seed", "profile", "SaveBest"):
        assert ast.dump(old_defs[name]) == ast.dump(new_defs[name])
    new_run = new_defs["run"]
    extra_guard = ast.parse('assert core_rows() == manifest["core_rows"]').body[0]
    new_run.body = [n for n in new_run.body if ast.dump(n) != ast.dump(extra_guard)]
    assert ast.dump(new_run) == ast.dump(old_defs["run"])
    reports = []
    models = []
    assert not (ROOT / "experiments/scratch/heterogeneous-core-pool-20261004/start.json").exists()
    for case, old_case in zip(manifest["cases"], previous["cases"], strict=True):
        assert case["name"] == old_case["name"]
        assert case["pool"] == old_case["pool"]
        assert case["support_histogram"] == old_case["support_histogram"]
        path = ROOT / case["model_path"]
        assert basis.digest(path) == case["model_sha256"]
        model = cp_model.CpModel()
        model.proto.parse_text_format(path.read_text())
        check_model(model, case["pool"], hint, cores)
        models.append(model)
        reports.append(
            {
                "name": case["name"],
                "pool_size": len(case["pool"]),
                "variables": 4928,
                "rows": 1124,
                "extra_rows": 2,
                "hint_holes": 5,
                "hint_core_overlaps": [0, 59],
                "model_sha256": basis.digest(path),
            }
        )
    controls = []
    for name, mutate in [
        ("core_bound", lambda p: p.constraints[1122].linear.domain.__setitem__(1, 60)),
        ("core_coefficient", lambda p: p.constraints[1122].linear.coeffs.__setitem__(0, 0)),
        ("core_wrong_column", lambda p: p.constraints[1123].linear.vars.__setitem__(0, 0)),
        ("core_duplicate_column", lambda p: p.constraints[1123].linear.vars.__setitem__(0, 17)),
        ("hint_selected_block", lambda p: p.solution_hint.values.__setitem__(3, 0)),
        ("hint_hole", lambda p: p.solution_hint.values.__setitem__(4368, 1)),
        ("old_cardinality", lambda p: p.constraints[0].linear.domain.__setitem__(0, 63)),
        ("old_coverage", lambda p: p.constraints[2].linear.domain.__setitem__(0, 0)),
    ]:
        damaged = cp_model.CpModel()
        damaged.proto.copy_from(models[0].proto)
        mutate(damaged.proto)
        assert basis.reject(lambda: check_model(damaged, manifest["cases"][0]["pool"], hint, cores))
        controls.append(name)
    runner_spec = importlib.util.spec_from_file_location("core_pool_runner", TARGET / "run.py")
    runner = importlib.util.module_from_spec(runner_spec)
    runner_spec.loader.exec_module(runner)
    assert runner.core_rows() == cores
    for case, saved in zip(manifest["cases"], models, strict=True):
        rebuilt, _, _ = runner.build_model(case["pool"], hint)
        assert str(rebuilt.proto) == str(saved.proto)
    audit = {
        "passed": True,
        "manifest_sha256": MANIFEST_SHA,
        "optimizer_calls": 0,
        "source_sha256": manifest["source_sha256"],
        "checker_sha256": basis.digest(Path(__file__)),
        "basis_checker_sha256": basis.digest(DAY / "heterogeneous-pool-independent/check.py"),
        "parent_manifest_sha256": basis.MANIFEST_SHA,
        "transported_core_ids": cores,
        "core_maps": MAPS,
        "core_sha256": basis.digest(core_path),
        "models": reports,
        "budget": manifest["budget"],
        "damaged_controls_rejected": controls,
        "scope": "Exactly two declared core-avoidance restrictions; not a completeness reduction.",
    }
    basis.dump(HERE / "gate.json", audit)
    print(json.dumps({"passed": True, "sha256": basis.digest(HERE / "gate.json")}))


if __name__ == "__main__":
    main()
