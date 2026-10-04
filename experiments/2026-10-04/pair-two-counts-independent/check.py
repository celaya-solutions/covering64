# Document:    Independent Compact Pair Two-Triple Count Model Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      a62d9e1e03fe620cf19a7e7391486553b6fd234d866072bf486b354a9907b534
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Rebuild every serialized row and exact auxiliary relation, without Solve."""

import argparse
import copy
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
POINTS = tuple(range(1, 17))
BLOCKS = list(itertools.combinations(POINTS, 5))
SUBSETS = {size: list(itertools.combinations(POINTS, size)) for size in [2, 3]}
RANK = {size: {subset: i for i, subset in enumerate(subsets)} for size, subsets in SUBSETS.items()}
OFFSETS = {2: 4368, 3: 4488}
HOLE_OFFSET = 5048
INT_MIN, INT_MAX = -(2**63), 2**63 - 1
MAPS = [
    list(range(1, 17)),
    [1, 7, 2, 10, 15, 3, 8, 11, 4, 9, 12, 16, 14, 6, 5, 13],
    [16, 15, 12, 5, 11, 8, 4, 7, 3, 6, 1, 2, 10, 14, 13, 9],
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def row_key(row):
    assert row.WhichOneof("constraint") == "linear"
    assert {field.name for field, _ in row.ListFields()} <= {"linear", "enforcement_literal"}
    assert len(row.linear.vars) == len(row.linear.coeffs)
    assert len(set(row.linear.vars)) == len(row.linear.vars)
    assert all(coefficient != 0 for coefficient in row.linear.coeffs)
    assert all(0 <= variable < 5608 for variable in row.linear.vars)
    return (
        tuple(sorted(zip(row.linear.vars, row.linear.coeffs, strict=True))),
        tuple(row.linear.domain),
        tuple(row.enforcement_literal),
    )


def expected_key(coefficients, lower, upper, literals=()):
    return (tuple(sorted(coefficients.items())), (lower, upper), tuple(literals))


def supports():
    result = {size: [[] for _ in subsets] for size, subsets in SUBSETS.items()}
    for block_id, block in enumerate(BLOCKS):
        for size in SUBSETS:
            for subset in itertools.combinations(block, size):
                result[size][RANK[size][subset]].append(block_id)
    assert all(len(row) == 364 for row in result[2])
    assert all(len(row) == 78 for row in result[3])
    return result


def core_rows():
    path = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
    assert sha(path) == "7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db"
    original = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    rank = {block: i for i, block in enumerate(BLOCKS)}
    return [
        sorted(rank[tuple(sorted(mapping[p - 1] for p in block))] for block in original)
        for mapping in MAPS
    ]


def expected_rows(carriers, cores):
    rows = [expected_key(dict.fromkeys(range(4368), 1), 64, 64)]
    for size in [2, 3]:
        for index, row in enumerate(carriers[size]):
            coeffs = dict.fromkeys(row, -1)
            coeffs[OFFSETS[size] + index] = 1
            rows.append(expected_key(coeffs, 0, 0))
    for index in range(560):
        count, hole = OFFSETS[3] + index, HOLE_OFFSET + index
        rows.append(expected_key({count: 1}, 0, 0, [hole]))
        rows.append(expected_key({count: 1}, 1, INT_MAX, [-hole - 1]))
    for triple_id, triple in enumerate(SUBSETS[3]):
        for pair in itertools.combinations(triple, 2):
            rows.append(
                expected_key(
                    {OFFSETS[2] + RANK[2][pair]: 3, OFFSETS[3] + triple_id: -1}, 13, INT_MAX
                )
            )
    for pair_id, pair in enumerate(SUBSETS[2]):
        outside = [point for point in POINTS if point not in pair]
        for a, b in itertools.combinations(outside, 2):
            ta = RANK[3][tuple(sorted((*pair, a)))]
            tb = RANK[3][tuple(sorted((*pair, b)))]
            rows.append(
                expected_key(
                    {OFFSETS[2] + pair_id: 3, OFFSETS[3] + ta: -1, OFFSETS[3] + tb: -1}, 12, INT_MAX
                )
            )
    for core in cores:
        rows.append(expected_key(dict.fromkeys(core, 1), INT_MIN, 55))
    assert len(rows) == 14404
    return rows


def failures(model, values):
    domains, rows = [], []
    for index, (variable, value) in enumerate(zip(model.variables, values, strict=True)):
        if not any(
            variable.domain[j] <= value <= variable.domain[j + 1]
            for j in range(0, len(variable.domain), 2)
        ):
            domains.append(index)
    for index, row in enumerate(model.constraints):
        if not all(
            values[lit] if lit >= 0 else not values[-lit - 1] for lit in row.enforcement_literal
        ):
            continue
        total = sum(
            values[var] * coefficient
            for var, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True)
        )
        if not any(
            row.linear.domain[j] <= total <= row.linear.domain[j + 1]
            for j in range(0, len(row.linear.domain), 2)
        ):
            rows.append(index)
    return {"domain_indices": domains, "constraint_indices": rows}


def main(target):
    target = target.resolve()
    manifest = read(target / "manifest.json")
    assert sha(target / "prepare.py") == manifest["source_sha256"]
    assert manifest["optimization_calls"] == 0
    assert manifest["budget"] == {"cases": 1, "seconds": 120, "workers": 4, "seed": 2026104301}
    for relative, expected in manifest["input_files"].items():
        assert sha(ROOT / relative) == expected, relative
    model_path, params_path = ROOT / manifest["model_path"], ROOT / manifest["parameters_path"]
    assert sha(model_path) == manifest["model_sha256"]
    assert sha(params_path) == manifest["parameters_sha256"]
    model = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
    params = text_format.Parse(params_path.read_text(), sat_parameters_pb2.SatParameters())
    assert {field.name for field, _ in model.ListFields()} == {
        "variables",
        "constraints",
        "objective",
        "solution_hint",
    }
    assert len(model.variables) == 5608 and len(model.constraints) == 14404
    assert len({variable.name for variable in model.variables}) == 5608
    for i, variable in enumerate(model.variables):
        assert {field.name for field, _ in variable.ListFields()} == {"name", "domain"}
        expected_domain = (
            [0, 1] if i < 4368 or i >= HOLE_OFFSET else ([5, 64] if i < 4488 else [0, 64])
        )
        assert list(variable.domain) == expected_domain
        if i < 4368:
            assert variable.name == f"block_{i}"
        elif i >= HOLE_OFFSET:
            assert variable.name == f"hole_{i - HOLE_OFFSET}"
        else:
            size = 2 if i < 4488 else 3
            assert variable.name == f"count_{size}_{i - OFFSETS[size]}"
    carriers, cores = supports(), core_rows()
    assert manifest["core_rows"] == cores
    expected = expected_rows(carriers, cores)
    actual = [row_key(row) for row in model.constraints]
    assert Counter(actual) == Counter(expected)
    assert actual == expected
    objective = model.objective
    assert set(field.name for field, _ in objective.ListFields()) <= {
        "vars",
        "coeffs",
        "offset",
        "scaling_factor",
    }
    assert objective.offset == 0 and objective.scaling_factor == 1
    assert len(set(objective.vars)) == len(objective.vars)
    assert dict(zip(objective.vars, objective.coeffs, strict=True)) == (
        dict.fromkeys(range(HOLE_OFFSET, HOLE_OFFSET + 560), 65) | dict.fromkeys(cores[0], 1)
    )
    hints = dict(zip(model.solution_hint.vars, model.solution_hint.values, strict=True))
    assert list(model.solution_hint.vars) == list(range(4368))
    assert len(hints) == 4368 and set(hints.values()) <= {0, 1} and sum(hints.values()) == 64
    hint_path = ROOT / manifest["hint_source_path"]
    assert sha(hint_path) == "797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de"
    hint = {tuple(map(int, line.split())) for line in hint_path.read_text().splitlines()}
    assert len(hint) == 64
    assert hints == {i: int(block in hint) for i, block in enumerate(BLOCKS)}
    assert not manifest["hint_is_complete"] and not manifest["hint_has_feasible_extension"]
    universe_path = ROOT / manifest["universe_path"]
    assert sha(universe_path) == manifest["universe_sha256"]
    universe = read(universe_path)
    assert universe == {
        "labels": list(POINTS),
        "blocks": list(map(list, BLOCKS)),
        "pairs": list(map(list, SUBSETS[2])),
        "triples": list(map(list, SUBSETS[3])),
    }
    counts = {size: [sum(hints[i] for i in row) for row in carriers[size]] for size in [2, 3]}
    values = [hints[i] for i in range(4368)] + counts[2] + counts[3]
    values += [int(count == 0) for count in counts[3]]
    hint_failures = failures(model, values)
    assert not hint_failures["domain_indices"]
    assert len(hint_failures["constraint_indices"]) == 66
    assert sum(1801 <= row < 3481 for row in hint_failures["constraint_indices"]) == 4
    assert sum(3481 <= row < 14401 for row in hint_failures["constraint_indices"]) == 62
    assert sum(values[HOLE_OFFSET:]) == 6
    assert [sum(hints[i] for i in core) for core in cores] == [2, 2, 0]
    assert {field.name for field, _ in params.ListFields()} == {
        "max_time_in_seconds",
        "num_search_workers",
        "random_seed",
        "log_search_progress",
        "log_to_stdout",
    }
    assert params.max_time_in_seconds == 120 and params.num_search_workers == 4
    assert (
        params.random_seed == 2026104301 and params.log_search_progress and not params.log_to_stdout
    )
    channels = []
    for count in range(65):
        valid = []
        for hole in [0, 1]:
            if (not hole or count == 0) and (hole or count >= 1):
                valid.append(hole)
        assert valid == [int(count == 0)]
        channels.append([count, valid[0]])
    mutations = []
    for label, index, mutate in [
        ("missing_pair_carrier", 1, lambda row: row.linear.coeffs.__setitem__(0, -2)),
        ("lost_hole_zero_direction", 681, lambda row: row.linear.domain.__setitem__(1, 1)),
        ("lost_hole_positive_direction", 682, lambda row: row.linear.domain.__setitem__(0, 0)),
        ("wrong_triple_lower_bound", 1801, lambda row: row.linear.domain.__setitem__(0, 12)),
        ("wrong_second_triple_weight", 3481, lambda row: row.linear.coeffs.__setitem__(1, -2)),
        ("disabled_cut", 1801, lambda row: row.enforcement_literal.append(0)),
        ("relaxed_core", 14401, lambda row: row.linear.domain.__setitem__(1, 56)),
    ]:
        damaged = copy.deepcopy(model.constraints[index])
        mutate(damaged)
        assert row_key(damaged) != expected[index], label
        mutations.append(label)
    assert Counter(actual[:-1]) != Counter(expected)
    mutations.append("missing_final_core_row")
    proof_path = ROOT / "experiments/2026-10-04/pair-two-necessary-cuts-independent/audit.json"
    assert sha(proof_path) == "db490b9d3cd3500eb2c85d36f803a73667ceed00e5251932608e7d1150e7099b"
    result = {
        "passed": True,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "manifest_sha256": sha(target / "manifest.json"),
        "model_sha256": sha(model_path),
        "parameters_sha256": sha(params_path),
        "variables": 5608,
        "constraints": 14404,
        "complete_row_multiset_equal": True,
        "row_order_equal": True,
        "count_definition_rows": 680,
        "exact_hole_rows": 1120,
        "pair_triple_rows": 1680,
        "pair_two_triple_rows": 10920,
        "core_cap_rows": 3,
        "global_dp_or_named_profile_rows": 0,
        "regularity_or_symmetry_rows": 0,
        "hint_path": str(hint_path.relative_to(ROOT)),
        "hint_sha256": sha(hint_path),
        "hint_scope": "4368 block-only guidance values; fails66cuts and is not a feasible hint.",
        "hint_auxiliary_values_unique": True,
        "derived_hint_failures": hint_failures,
        "derived_hint_holes": 6,
        "derived_hint_core_overlaps": [2, 2, 0],
        "hole_channels_checked": channels,
        "damaged_controls_rejected": mutations,
        "proof_sha256": sha(proof_path),
        "auxiliary_equivalence": "Count equalities fix every pair and triple count "
        "uniquely. Both hole directions uniquely set h(T)=[c(T)=0]. Count upper bounds "
        "are min(64, carrier count), so they lose no binary64-block family. Pair lower5, "
        "the two local cut families and three core caps are necessary for every64-cover.",
        "relaxation_scope": "Omitting globalDP and named profile filters imposes no extra "
        "restriction and preserves all64-covers. A separate degree-and-hub proof shows the "
        "pair cuts already imply the forbidden-profile exclusion. Saved families still need "
        "both cover verifiers and an independent global-profile screen.",
        "source_sha256": sha(target / "prepare.py"),
        "runner_exists": (target / "execute.py").exists(),
        "run_scope": "Prepared for one120-second run, fourworkers, seed2026104301. "
        "This preparation gate neither calls Solve nor authorizes a launch; "
        "there is no reviewed runner in this receipt.",
    }
    (HERE / "model-gate.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    main(parser.parse_args().target)
