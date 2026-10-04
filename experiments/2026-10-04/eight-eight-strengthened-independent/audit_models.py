# Document:    Independent Strengthened Eight Plus Eight Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      ddba92b0ce2c995e711272130674054fba3c92eae23441ded8710ba0e8c63379
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Rebuild every added row from set membership; prohibit all solver calls."""

import copy
import hashlib
import importlib.util
import itertools
import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRODUCER = HERE.parent / "eight-eight-strengthened"
ORIGINAL = HERE.parent / "eight-eight-extensions"
OLD_AUDITOR = HERE.parent / "eight-eight-extensions-independent/audit.py"
OLD_AUDITOR_SHA = "8b90b9b02e5e329bb0acf10f72e86407b5cc67e65f65a6c22a472287a39ad027"
BLOCKS = list(itertools.combinations(range(1, 17), 5))
SETS = list(map(set, BLOCKS))
LO, HI = -(1 << 63), (1 << 63) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_old():
    assert sha(OLD_AUDITOR) == OLD_AUDITOR_SHA
    spec = importlib.util.spec_from_file_location("old_independent_eight_eight", OLD_AUDITOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_added_rows(groups, kinds):
    allowed = {i for group in groups for i in group["ids"]}
    rows = []

    def add(category, coefficients, bounds):
        row = cp_model_pb2.ConstraintProto()
        ordered = sorted(coefficients)
        row.linear.vars.extend(ordered)
        row.linear.coeffs.extend(coefficients[i] for i in ordered)
        row.linear.domain.extend(bounds)
        rows.append((category, row))

    for half, kind in enumerate(kinds):
        points = set(range(8 * half + 1, 8 * half + 9))
        other = set(range(1, 17)) - points
        quads = [set(g["base"]) for g in groups if len(g["base"]) == 4 and set(g["base"]) <= points]
        pair_columns = [i for i in sorted(allowed) if len(SETS[i] & points) == 2]
        single_columns = [i for i in sorted(allowed) if len(SETS[i] & points) == 1]
        assert len(pair_columns) == 672 and len(single_columns) == 64
        for pair in itertools.combinations(sorted(points), 2):
            pair_set = set(pair)
            q = sum(pair_set <= quad for quad in quads)
            columns = [i for i in pair_columns if SETS[i] & points == pair_set]
            assert len(columns) == 24
            if kind == "A":
                assert q in (0, 2)
                bound = 1 if q == 2 else 0
                add(
                    "pair_exact_one" if bound else "pair_exact_zero",
                    dict.fromkeys(columns, 1),
                    [bound, bound],
                )
                if q == 2:
                    for p in sorted(other):
                        triple = pair_set | {p}
                        add(
                            "triple_upper_two",
                            {i: 1 for i, b in enumerate(SETS) if triple <= b},
                            [LO, 2],
                        )
            else:
                assert q in (1, 2, 3)
                add("pair_lower_" + str(q - 1), dict.fromkeys(columns, 1), [q - 1, HI])
        for p in sorted(points):
            pair_incident = [i for i in pair_columns if p in SETS[i]]
            single_incident = [i for i in single_columns if p in SETS[i]]
            assert len(pair_incident) == 168 and len(single_incident) == 8
            coeffs = dict.fromkeys(pair_incident, 1)
            assert not set(coeffs) & set(single_incident)
            coeffs.update(dict.fromkeys(single_incident, 2))
            add("rounded_point", coeffs, [7, HI])
            if kind == "A":
                add("singleton_exact_one", dict.fromkeys(single_incident, 1), [1, 1])
                add("point_degree_twenty", {i: 1 for i, b in enumerate(SETS) if p in b}, [20, 20])
    return rows


def damage_controls(proto, expected, categories):
    cases = {
        "variable_domain": lambda p: p.variables[0].domain.__setitem__(1, 2),
        "prefix_group_bound": lambda p: p.constraints[1].linear.domain.__setitem__(1, 2),
        "prefix_cover_coefficient": lambda p: p.constraints[65].linear.coeffs.__setitem__(0, 2),
        "added_row_removed": lambda p: p.constraints.pop(),
        "added_row_enforcement": lambda p: p.constraints[625].enforcement_literal.append(0),
        "objective": lambda p: p.objective.vars.append(0),
        "hint": lambda p: p.solution_hint.vars.append(0),
    }
    for name in sorted(set(categories)):
        index = 625 + categories.index(name)
        cases[name + "_bound"] = lambda p, i=index: p.constraints[i].linear.domain.__setitem__(
            0, p.constraints[i].linear.domain[0] + 1
        )
        cases[name + "_coefficient"] = lambda p, i=index: p.constraints[
            i
        ].linear.coeffs.__setitem__(0, p.constraints[i].linear.coeffs[0] + 1)
        cases[name + "_support"] = lambda p, i=index: p.constraints[i].linear.vars.pop()
    out = {}
    for name, mutate in cases.items():
        damaged = copy.deepcopy(proto)
        mutate(damaged)
        assert damaged != proto
        try:
            assert damaged == expected
        except AssertionError:
            out[name] = "rejected"
        else:
            raise AssertionError("damaged model accepted: " + name)
    return out


def main():
    manifest_path = PRODUCER / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    original_manifest = json.loads((ORIGINAL / "manifest.json").read_text())
    assert sha(PRODUCER / "run.py") == manifest["source_sha256"]
    assert manifest["common_sha256"] == original_manifest["common_sha256"]
    assert (manifest["seconds"], manifest["workers"], manifest["watchdog"], manifest["grace"]) == (
        120,
        4,
        145,
        5,
    )
    assert [e["kinds"] for e in manifest["entries"]] == ["AA", "AB", "BB"]
    assert [e["seed"] for e in manifest["entries"]] == [2026105501, 2026105502, 2026105503]
    assert manifest["search_launches_during_preparation"] == 0
    assert manifest["ortools_version"] == ortools.__version__ == "9.15.6755"
    proof_root = HERE.parent / "eight-eight-redundant-cut-plan"
    expected_proofs = {
        "README.md": "a2f9e7ff44be987f1e88165abe38b0a670f13947f2e7374090823cf38d729955",
        "check.py": "618f5cb4549d289db1c3beb52a5755e5eda729db1e6a168faa6d2e934082a6af",
        "checks.json": "e28bfd4a1a1532829c9511f172c659d3418fe4fb0dbbee4ab66860bf3e682225",
    }
    assert manifest["proof_files"] == {
        str((proof_root / name).relative_to(ROOT)): h for name, h in expected_proofs.items()
    }
    assert all(sha(proof_root / name) == h for name, h in expected_proofs.items())
    receipts = []
    with patch.object(
        cp_model.CpSolver, "solve", side_effect=AssertionError("Solver launch forbidden")
    ):
        old = load_old()
        assert sha(old.RUN.COMMON_PATH) == manifest["common_sha256"]
        for entry, original_entry in zip(manifest["entries"], original_manifest["entries"]):
            path = ROOT / entry["model"]
            groups_path = ROOT / entry["groups"]
            assert sha(path) == entry["model_sha256"]
            assert sha(groups_path) == entry["groups_sha256"]
            groups = json.loads(groups_path.read_text())
            assert groups == old.independent_groups(entry["kinds"])
            assert groups_path.read_bytes() == (ROOT / original_entry["groups"]).read_bytes()
            assert sha(ROOT / original_entry["model"]) == original_entry["model_sha256"]
            original = text_format.Parse(
                (ROOT / original_entry["model"]).read_text(), cp_model_pb2.CpModelProto()
            )
            old.audit_proto(original, groups, entry["kinds"])
            actual = text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())
            prefix = copy.deepcopy(actual)
            del prefix.constraints[625:]
            assert prefix == original
            expected = old.expected_proto(groups)
            added = expected_added_rows(groups, entry["kinds"])
            for _, row in added:
                expected.constraints.add().CopyFrom(row)
            assert actual == expected
            assert len(actual.variables) == entry["variables"] == 4368
            assert (
                len(actual.constraints)
                == entry["rows"]
                == {"AA": 1113, "AB": 905, "BB": 697}[entry["kinds"]]
            )
            assert not old.COMMON.read_model(path).validate()
            categories = [kind for kind, _ in added]
            receipts.append(
                {
                    "kinds": entry["kinds"],
                    "model_sha256": sha(path),
                    "rows": len(actual.constraints),
                    "groups_sha256": sha(groups_path),
                    "original_prefix_exactly_equal": True,
                    "original_model_independently_reaudited": True,
                    "added_row_categories": dict(sorted(Counter(categories).items())),
                    "damage_controls": damage_controls(actual, expected, categories),
                }
            )
    result = {
        "passed": True,
        "manifest_sha256": sha(manifest_path),
        "producer_sha256": sha(PRODUCER / "run.py"),
        "old_auditor_sha256": sha(OLD_AUDITOR),
        "audit_source_sha256": sha(Path(__file__)),
        "proof_files": manifest["proof_files"],
        "model_receipts": receipts,
        "solver_calls": 0,
        "scope": "Exact serialized model delta only; complete runner gate is a separate receipt.",
    }
    target = HERE / "model-audit.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "receipt_sha256": sha(target),
                "damaged_models_rejected": sum(len(r["damage_controls"]) for r in receipts),
            }
        )
    )


if __name__ == "__main__":
    main()
