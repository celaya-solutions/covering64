# Document:    Independent Two-Point-Star V2 Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      570036bf9d3e6ee90660fcec59b1451ea060e4d6b18c9066ae7ae665d2707f50
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check every proto variable, row, hint, and objective; never invoke a solver."""

import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "two-point-star-repair-v2"
MANIFEST = "39e895e1bc69b5bc7295460f1151cd951c4c06c1e5691a1a90482b26d0807f74"
BASE_SHA = "f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
PAIRS = tuple(itertools.combinations(range(1, 17), 2))
MASKS = [sum(1 << (point - 1) for point in block) for block in BLOCKS]
MAX_INT = (1 << 63) - 1
MIN_INT = -(1 << 63)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_model(path):
    model = cp_model.CpModel()
    require(model.proto.parse_text_format(path.read_text()), "proto parsing failed")
    require(not model.validate(), "invalid CP model")
    return model


def row_check(row, indices, domain, enforcement=()):
    require(row.has_linear(), "nonlinear or unsupported row")
    require(list(row.enforcement_literal) == list(enforcement), "wrong row enforcement")
    require(list(row.linear.domain) == list(domain), "wrong row domain")
    actual = list(row.linear.vars)
    require(len(actual) == len(set(actual)) == len(indices), "row width/duplicates")
    require(
        set(actual) == set(indices) and list(row.linear.coeffs) == [1] * len(indices),
        "row incidence/coefficient mismatch",
    )


def audit_model(model, ids, pivot):
    proto, chosen = model.proto, set(ids)
    require(len(proto.variables) == 4928 and len(proto.constraints) == 1242, "model dimensions")
    require(
        not proto.assumptions and not proto.search_strategy and not proto.has_symmetry(),
        "unexpected assumptions/search/symmetry",
    )
    require(proto.has_objective() and not proto.has_floating_point_objective(), "objective kind")
    pivot_mask = sum(1 << (point - 1) for point in pivot)
    free, fixed_selected = 0, 0
    for index, block_mask in enumerate(MASKS):
        variable = proto.variables[index]
        free += bool(block_mask & pivot_mask)
        fixed_selected += not (block_mask & pivot_mask) and index in chosen
        domain = [0, 1] if block_mask & pivot_mask else [int(index in chosen)] * 2
        require(
            variable.name == f"b_{index}" and list(variable.domain) == domain,
            "block variable order/domain",
        )
    require(free == 2366 and fixed_selected == 29, "star dimensions")
    row_check(proto.constraints[0], range(4368), [64, 64])
    expected_hints = {index: int(index in chosen) for index in range(4368)}
    holes = []
    for index, triple in enumerate(TRIPLES):
        variable_id = 4368 + index
        variable = proto.variables[variable_id]
        require(variable.name == f"h_{index}" and list(variable.domain) == [0, 1], "hole variable")
        mask = sum(1 << (point - 1) for point in triple)
        incident = [i for i, block_mask in enumerate(MASKS) if block_mask & mask == mask]
        require(len(incident) == 78, "triple incidence count")
        row_check(proto.constraints[1 + 2 * index], incident, [0, 0], [variable_id])
        row_check(proto.constraints[2 + 2 * index], incident, [1, MAX_INT], [-variable_id - 1])
        uncovered = not bool(chosen.intersection(incident))
        expected_hints[variable_id] = int(uncovered)
        if uncovered:
            holes.append(list(triple))
    for index, pair in enumerate(PAIRS):
        mask = sum(1 << (point - 1) for point in pair)
        incident = [i for i, block_mask in enumerate(MASKS) if block_mask & mask == mask]
        require(len(incident) == 364, "pair incidence count")
        row_check(proto.constraints[1121 + index], incident, [5, MAX_INT])
    row_check(proto.constraints[1241], range(4368, 4928), [MIN_INT, 12])
    objective = proto.objective
    require(
        set(objective.vars) == set(range(4368, 4928))
        and len(objective.vars) == 560
        and list(objective.coeffs) == [1] * 560
        and objective.offset == 0
        and objective.scaling_factor == 1
        and not objective.domain,
        "hole objective",
    )
    hints = proto.solution_hint
    require(len(hints.vars) == len(hints.values) == len(set(hints.vars)) == 4928, "hint dimensions")
    require(dict(zip(hints.vars, hints.values, strict=True)) == expected_hints, "hint changed")
    require(len(holes) == 12, "baseline holes")
    values = [expected_hints[i] for i in range(4928)]
    return {
        "variables": 4928,
        "linear_rows": 1242,
        "free_blocks": free,
        "fixed_blocks": 2002,
        "fixed_selected": fixed_selected,
        "free_selected": 35,
        "exact_hole_channels": 560,
        "pair_floor_rows": 120,
        "holes": holes,
        "values": values,
    }


def expect_rejected(callback, label):
    try:
        callback()
    except (ValueError, AssertionError, TypeError, IndexError):
        return label
    raise ValueError("damaged control accepted: " + label)


def main():
    require(not (HERE / "gate.json").exists(), "preserve gate")
    manifest_path = PRODUCER / "manifest.json"
    require(sha(manifest_path) == MANIFEST, "manifest changed")
    manifest = json.loads(manifest_path.read_text())
    require(manifest["source_sha256"] == sha(PRODUCER / "run.py"), "source changed")
    require(manifest["ortools_version"] == ortools.__version__ == "9.15.6755", "solver version")
    require(
        (manifest["seconds"], manifest["workers"], manifest["watchdog"], manifest["grace"])
        == (60, 4, 80, 5),
        "solver budget",
    )
    require(manifest["search_launches_during_preparation"] == 0, "premature solver launch")
    runner = load("star_v2_under_audit", PRODUCER / "run.py")
    require(
        not (PRODUCER / "result.json").exists() and not any(runner.RAW.glob("run-*")),
        "run already launched",
    )
    require(sha(runner.BASE) == manifest["base_sha256"] == BASE_SHA, "center changed")
    oracle = load(
        "star_independent_oracle", HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    )
    ids = oracle.parse(runner.BASE)
    rows = []
    for number, entry in enumerate(manifest["entries"], 1):
        require(
            entry["number"] == number
            and entry["pivot"] == ([6, 14] if number == 1 else [1, 9])
            and entry["seed"] == 2026105300 + number,
            "entry order/pivot/seed",
        )
        path = ROOT / entry["model"]
        require(sha(path) == entry["model_sha256"], "model bytes changed")
        model = read_model(path)
        details = audit_model(model, ids, entry["pivot"])
        values = details.pop("values")
        runner.check_vector(model, values)
        require(
            entry["variables"] == details["variables"]
            and entry["rows"] == details["linear_rows"]
            and entry["fixed_selected"] == details["fixed_selected"]
            and entry["free_blocks"] == details["free_blocks"],
            "reported dimensions",
        )
        damaged_vectors = []
        mutations = [
            ("float values", list(map(float, values))),
            ("boolean values", list(map(bool, values))),
            ("truncated vector", values[:-1]),
            ("extra vector value", values + [0]),
            ("all zero", [0] * 4928),
            ("all one", [1] * 4928),
        ]
        for label, variable in (
            ("covered marked hole", next(i for i in range(4368, 4928) if not values[i])),
            ("hole marked covered", next(i for i in range(4368, 4928) if values[i])),
            (
                "fixed membership flipped",
                next(i for i in range(4368) if len(set(model.proto.variables[i].domain)) == 1),
            ),
        ):
            damaged = values.copy()
            damaged[variable] = 1 - damaged[variable]
            mutations.append((label, damaged))
        fractional = values.copy()
        fractional[next(i for i in range(4368, 4928) if values[i])] = 0.5
        mutations.append(("fractional uncovered indicator", fractional))
        for label, damaged in mutations:
            damaged_vectors.append(
                expect_rejected(lambda v=damaged: runner.check_vector(model, v), label)
            )
        damaged_models = []
        for label in (
            "variable order",
            "unfixed outside",
            "cardinality",
            "hole direction",
            "reverse channel",
            "pair floor",
            "hole bound",
            "objective coefficient",
            "objective offset",
            "assumption",
        ):
            altered = read_model(path)
            proto = altered.proto
            if label == "variable order":
                proto.variables[0].name = "b_1"
            elif label == "unfixed outside":
                index = next(i for i in range(4368) if len(set(proto.variables[i].domain)) == 1)
                proto.variables[index].domain[0], proto.variables[index].domain[1] = 0, 1
            elif label == "cardinality":
                proto.constraints[0].linear.domain[0] = 63
            elif label == "hole direction":
                proto.constraints[1].enforcement_literal[0] = -4369
            elif label == "reverse channel":
                proto.constraints[2].linear.domain[0] = 0
            elif label == "pair floor":
                proto.constraints[1121].linear.domain[0] = 4
            elif label == "hole bound":
                proto.constraints[1241].linear.domain[1] = 13
            elif label == "objective coefficient":
                proto.objective.coeffs[0] = 2
            elif label == "objective offset":
                proto.objective.offset = 1
            else:
                proto.assumptions.append(0)
            damaged_models.append(
                expect_rejected(lambda m=altered: audit_model(m, ids, entry["pivot"]), label)
            )
        rows.append(
            {
                "number": number,
                "pivot": entry["pivot"],
                "model_sha256": entry["model_sha256"],
                "exact_schema_audit": details,
                "positive_baseline_assignment": True,
                "damaged_vectors_rejected": damaged_vectors,
                "damaged_models_rejected": damaged_models,
            }
        )
    require(len(rows) == 2, "wrong number of runs")
    gate = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": MANIFEST,
        "producer_source_sha256": manifest["source_sha256"],
        "source_sha256": sha(__file__),
        "base_sha256": BASE_SHA,
        "ortools_version": ortools.__version__,
        "model_audits": rows,
        "budget": {
            "runs": 2,
            "seconds_each": 60,
            "workers": 4,
            "watchdog": 80,
            "grace": 5,
            "seeds": [2026105301, 2026105302],
            "relaunch": False,
            "same_center": True,
        },
        "solver_launches": 0,
        "launch_authority": (
            "Root only; stop if any dual-verified cover, timeout, or process failure."
        ),
        "encoding_proof": "Each hole Boolean is1 exactly when its triple has no selected block, "
        "using disjoint count=0 and count>=1 cases. The objective is their exact sum. "
        "Every global64 cover has pair count at least ceil(14/3)=5, but fixed outside-star "
        "memberships restrict these two experiments to their declared neighborhoods.",
        "scope": "No D3/D4/core restrictions are imposed. A partial may fail those diagnostics. "
        "UNKNOWN/timeouts are inconclusive. CP-SAT INFEASIBLE is not "
        "an independently checked theorem. "
        "No unrestricted lower-bound or existence claim follows from this gate.",
    }
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "decision": "GO",
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "models_checked": len(rows),
                "solver_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
