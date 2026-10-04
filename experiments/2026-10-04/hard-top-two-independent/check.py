# Document:    Independent Hard Top-Two Serialized Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1cb195c67cfaa013eb93d08f0aaf90fa0b687405afc7149237fb1f78946b3edf
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "hard-top-two-extended-four-core"
MANIFEST_SHA = "91400d274bf722afa92b208021909b0900903b8e10d99f74a6e5e609acb8d833"
LO, HI = -(1 << 63), (1 << 63) - 1
SETS = {n: list(itertools.combinations(range(1, 17), n)) for n in (2, 3, 5)}
MASKS = {n: [sum(1 << (x - 1) for x in q) for q in SETS[n]] for n in SETS}
TRIPLE_ID = {t: 4488 + i for i, t in enumerate(SETS[3])}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def signature(terms, domain, literals=()):
    return tuple(sorted(terms)), tuple(domain), tuple(literals)


def expected_rows(cores):
    rows = [signature([(i, 1) for i in range(4368)], [64, 64])]
    for size, start in ((2, 4368), (3, 4488)):
        for offset, subset in enumerate(MASKS[size]):
            support = [i for i, mask in enumerate(MASKS[5]) if mask & subset == subset]
            assert len(support) == (364 if size == 2 else 78)
            rows.append(signature([(i, -1) for i in support] + [(start + offset, 1)], [0, 0]))
    for i in range(560):
        rows.append(signature([(4488 + i, 1)], [0, 0], [5048 + i]))
        rows.append(signature([(4488 + i, 1)], [1, HI], [-5048 - i - 1]))
    for i, pair in enumerate(SETS[2]):
        outside = [x for x in range(1, 17) if x not in pair]
        for j, x in enumerate(outside):
            rows.append(
                signature(
                    [
                        (TRIPLE_ID[tuple(sorted((*pair, x)))], -1),
                        (5608 + i, 1),
                        (5728 + 14 * i + j, 1),
                    ],
                    [0, HI],
                )
            )
        rows.append(
            signature(
                [(4368 + i, -3), (5608 + i, 2)] + [(5728 + 14 * i + j, 1) for j in range(14)],
                [LO, -12],
            )
        )
    for core in cores:
        rows.append(signature([(i, 1) for i in core], [LO, 55]))
    assert len(rows) == 3605
    return rows


def expected_variables():
    result = [(f"block_{i}", [0, 1]) for i in range(4368)]
    for size, lower in ((2, 5), (3, 0)):
        result.extend((f"count_{size}_" + "_".join(map(str, q)), [lower, 64]) for q in SETS[size])
    result.extend(("hole_" + "_".join(map(str, q)), [0, 1]) for q in SETS[3])
    result.extend(("z_" + "_".join(map(str, p)), [0, 64]) for p in SETS[2])
    result.extend(
        ("y_" + "_".join(map(str, (*p, x))), [0, 64])
        for p in SETS[2]
        for x in range(1, 17)
        if x not in p
    )
    assert len(result) == 7408
    return result


def model_check(proto, rows, hint):
    assert {field.name for field, _ in proto.ListFields()} == {
        "variables",
        "constraints",
        "objective",
        "solution_hint",
    }
    assert len(proto.variables) == 7408 and len(proto.constraints) == 3605
    for variable, (name, domain) in zip(proto.variables, expected_variables(), strict=True):
        assert {field.name for field, _ in variable.ListFields()} == {"name", "domain"}
        assert variable.name == name and list(variable.domain) == domain
    for index, (row, expected) in enumerate(zip(proto.constraints, rows, strict=True)):
        fields = {field.name for field, _ in row.ListFields()}
        assert fields <= {"linear", "enforcement_literal"} and "linear" in fields, index
        assert {field.name for field, _ in row.linear.ListFields()} == {"vars", "coeffs", "domain"}
        terms = list(zip(row.linear.vars, row.linear.coeffs, strict=True))
        assert len(terms) == len({var for var, _ in terms}), index
        assert signature(terms, row.linear.domain, row.enforcement_literal) == expected, index
    objective = proto.objective
    assert {field.name for field, _ in objective.ListFields()} <= {
        "vars",
        "coeffs",
        "offset",
        "scaling_factor",
    }
    assert list(objective.vars) == list(range(5048, 5608))
    assert (
        list(objective.coeffs) == [1] * 560
        and objective.offset == 0
        and objective.scaling_factor == 1
    )
    assert {field.name for field, _ in proto.solution_hint.ListFields()} == {"vars", "values"}
    assert list(proto.solution_hint.vars) == list(range(4368))
    assert list(proto.solution_hint.values) == hint and len(hint) == 4368 and sum(hint) == 64


def vector_failures(proto, values):
    assert len(values) == 7408
    for var, value in zip(proto.variables, values, strict=True):
        assert type(value) is int and var.domain[0] <= value <= var.domain[1]
    failures = []
    for index, row in enumerate(proto.constraints):
        if not all(
            values[lit] == 1 if lit >= 0 else values[-lit - 1] == 0
            for lit in row.enforcement_literal
        ):
            continue
        lhs = sum(c * values[v] for v, c in zip(row.linear.vars, row.linear.coeffs, strict=True))
        if not row.linear.domain[0] <= lhs <= row.linear.domain[1]:
            failures.append(index)
    return failures


def canonical_hint(hint, cores):
    selected = [SETS[5][i] for i, value in enumerate(hint) if value]
    counts = {
        size: Counter(q for block in selected for q in itertools.combinations(block, size))
        for size in (2, 3)
    }
    pair_values = [counts[2][p] for p in SETS[2]]
    triple_values = [counts[3][t] for t in SETS[3]]
    hole_values = [int(value == 0) for value in triple_values]
    zs, ys, bad = [], [], []
    d2sum = 0
    for index, pair in enumerate(SETS[2]):
        values = [counts[3][tuple(sorted((*pair, x)))] for x in range(1, 17) if x not in pair]
        assert sum(values) == 3 * pair_values[index]
        ordered = sorted(values, reverse=True)
        z = ordered[1]
        tail = [max(0, value - z) for value in values]
        assert 2 * z + sum(tail) == ordered[0] + ordered[1]
        zs.append(z)
        ys.extend(tail)
        deficit = max(0, 12 - 3 * pair_values[index] + 2 * z + sum(tail))
        if deficit:
            bad.append({"pair": list(pair), "budget_deficit": deficit})
        d2sum += sum(
            max(0, 12 - 3 * pair_values[index] + a + b)
            for a, b in itertools.combinations(values, 2)
        )
    overlaps = [sum(hint[i] for i in core) for core in cores]
    return hint + pair_values + triple_values + hole_values + zs + ys, {
        "holes": sum(hole_values),
        "D2max": sum(row["budget_deficit"] for row in bad),
        "D2sum": d2sum,
        "core_overlaps": overlaps,
        "bad_budgets": bad,
    }


def projection_controls():
    profiles = 0
    digest = hashlib.sha256()
    for p in range(65):
        for first in range(p + 1):
            for second in range(first + 1):
                if not first + second <= 3 * p <= first + 13 * second:
                    continue
                tail, remainder = [], 3 * p - first - second
                for _ in range(12):
                    value = min(second, remainder)
                    tail.append(value)
                    remainder -= value
                values = [first, second, *tail]
                z = sorted(values, reverse=True)[1]
                ys = [max(0, value - z) for value in values]
                assert all(0 <= value <= 64 for value in [z, *ys])
                assert all(y + z >= t for y, t in zip(ys, values, strict=True))
                explicit = all(a + b <= 3 * p - 12 for a, b in itertools.combinations(values, 2))
                assert explicit == (2 * z + sum(ys) <= 3 * p - 12)
                assert 2 * z + sum(ys) == first + second
                digest.update(bytes([p, first, second, z, *ys]))
                profiles += 1
    histograms = 0
    for values in itertools.combinations_with_replacement([0, 1, 2, 63, 64], 14):
        top = max(a + b for a, b in itertools.combinations(values, 2))
        minimum = min(2 * z + sum(max(0, value - z) for value in values) for z in range(65))
        assert minimum == top
        histograms += 1
    binary_ties = 0
    for height in (1, 2, 6, 7, 63, 64):
        for mask in range(1 << 14):
            values = [height if mask & (1 << i) else 0 for i in range(14)]
            z = sorted(values, reverse=True)[1]
            assert 2 * z + sum(max(0, t - z) for t in values) == sum(
                sorted(values, reverse=True)[:2]
            )
            binary_ties += 1
    # Sum the13 strong rows involving a, then add the exact mass equation -3p+sum(t)=0.
    for a in range(14):
        coefficients = [0] * 15
        for b in range(14):
            if b != a:
                coefficients[0] += 3
                coefficients[a + 1] -= 1
                coefficients[b + 1] -= 1
        coefficients[0] -= 3
        for b in range(14):
            coefficients[b + 1] += 1
        assert coefficients == [36] + [-12 if b == a else 0 for b in range(14)]
    assert profiles == 31521 and histograms == 3060 and binary_ties == 98304
    return {
        "compatible_integer_profiles": profiles,
        "profile_sha256": digest.hexdigest(),
        "full_integer_z_minimization_histograms": histograms,
        "z_values_per_histogram": 65,
        "tied_position_profiles": binary_ties,
        "single_cut_linear_combinations": 14,
    }


def main():
    manifest = read(SOURCE / "manifest.json")
    assert sha(SOURCE / "manifest.json") == MANIFEST_SHA
    for path, digest in manifest["sources"].items():
        assert sha(ROOT / path) == digest
    for section in ("proof_bindings", "cover_preservation_receipts"):
        for path, digest in manifest[section].items():
            assert sha(HERE.parent / path) == digest
    for kind in ("model", "parameters", "guidance"):
        assert sha(ROOT / manifest[f"{kind}_path"]) == manifest[f"{kind}_sha256"]
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse((ROOT / manifest["model_path"]).read_text(), proto)
    parameters = sat_parameters_pb2.SatParameters()
    text_format.Parse((ROOT / manifest["parameters_path"]).read_text(), parameters)
    assert parameters == sat_parameters_pb2.SatParameters(
        max_time_in_seconds=120,
        num_search_workers=4,
        random_seed=2026104601,
        log_search_progress=True,
        log_to_stdout=False,
    )
    baseline = read(HERE.parent / "compact-pair-two-counts/manifest.json")
    fourth = read(HERE.parent / "fourth-core-independent/audit.json")
    cores = baseline["core_rows"] + [fourth["core_global_ids"]]
    assert manifest["core_rows"] == cores and manifest["core_caps"] == [55] * 4
    assert all(len(core) == len(set(core)) == 60 for core in cores)
    guidance = read(ROOT / manifest["guidance_path"])
    path = ROOT / guidance["candidate_path"]
    assert sha(path) == guidance["candidate_sha256"] == manifest["candidate_sha256"]
    selected = {
        tuple(map(int, line.split()))
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    assert len(selected) == 64 and selected <= set(SETS[5])
    hint = [int(block in selected) for block in SETS[5]]
    assert guidance["variable_indices"] == list(range(4368)) and guidance["values"] == hint
    assert (
        not guidance["feasible_warm_start"]
        and not manifest["guidance"]["has_feasible_auxiliary_extension"]
    )
    rows = expected_rows(cores)
    model_check(proto, rows, hint)
    values, actual = canonical_hint(hint, cores)
    assert actual["holes"] == 49 and actual["D2max"] == 74 and actual["D2sum"] == 170
    assert actual["core_overlaps"] == [0, 2, 2, 4]
    assert actual["bad_budgets"] == guidance["canonical_failed_budgets"]
    failures = vector_failures(proto, values)
    assert len(failures) == 74 and all(1801 <= i < 3601 and (i - 1801) % 15 == 14 for i in failures)
    damaged = []
    mutations = [
        ("fixed_block", lambda p: p.variables[0].domain.__setitem__(1, 0)),
        ("wrong_block_order_name", lambda p: setattr(p.variables[0], "name", "block_1")),
        ("missing_count_incidence", lambda p: p.constraints[1].linear.coeffs.__setitem__(0, 0)),
        (
            "wrong_hole_literal",
            lambda p: p.constraints[681].enforcement_literal.__setitem__(0, -5049),
        ),
        ("negative_y_domain", lambda p: p.variables[5728].domain.__setitem__(0, -1)),
        ("wrong_hinge_sign", lambda p: p.constraints[1801].linear.coeffs.__setitem__(0, 1)),
        ("one_z_instead_of_two", lambda p: p.constraints[1815].linear.coeffs.__setitem__(1, 1)),
        ("weakened_budget", lambda p: p.constraints[1815].linear.domain.__setitem__(1, -11)),
        ("fourth_cap56", lambda p: p.constraints[3604].linear.domain.__setitem__(1, 56)),
        (
            "core_objective_tiebreak",
            lambda p: (p.objective.vars.append(0), p.objective.coeffs.append(1)),
        ),
        ("duplicate_hint_position", lambda p: p.solution_hint.vars.__setitem__(1, 0)),
        ("extra_search_strategy", lambda p: p.search_strategy.add().variables.append(0)),
    ]
    for label, mutate in mutations:
        altered = cp_model_pb2.CpModelProto()
        altered.CopyFrom(proto)
        mutate(altered)
        try:
            model_check(altered, rows, hint)
        except AssertionError:
            damaged.append(label)
        else:
            raise AssertionError(f"damaged model accepted: {label}")
    controls = projection_controls()
    assert not manifest["runner_prepared"] and manifest["optimizer_calls"] == 0
    report = {
        "passed": True,
        "decision": "MODEL_PASS_ONLY",
        "launch_authorized": False,
        "optimizer_calls": 0,
        "checker_sha256": sha(__file__),
        "manifest_sha256": MANIFEST_SHA,
        "model_sha256": manifest["model_sha256"],
        "parameters_sha256": manifest["parameters_sha256"],
        "guidance_sha256": manifest["guidance_sha256"],
        "producer_source_sha256": manifest["source_sha256"],
        "variables_checked": 7408,
        "rows_checked": 3605,
        "block_variables": 4368,
        "row_counts": {
            "cardinality": 1,
            "exact_count_definitions": 680,
            "hole_channels": 1120,
            "hinges": 1680,
            "top_two_budgets": 120,
            "core_caps": 4,
        },
        "controls": controls,
        "damaged_models_rejected": damaged,
        "guidance": {
            "entries": 4368,
            "unhinted_auxiliaries": 3040,
            "feasible_extension": False,
            "canonical_failed_rows": failures,
            **actual,
        },
        "projection_proof": "For every distinct a,b, hinge inequalities and y>=0 give "
        "t_a+t_b<=2z+y_a+y_b<=2z+sum(y)<=3p-12. Conversely choose z as the second-largest "
        "of14 positions and y_x=max(0,t_x-z). Their sum is the top-two sum, even with ties. "
        "For integer t in[0,64] this gives integer z,y in[0,64]; the same construction works "
        "over reals. Thus existential projection exactly equals all91 strong rows per pair.",
        "single_cut_redundancy": "Sum13 strong rows containing a fixed position and add the "
        "exact count identity -3p+sum(t)=0. This yields36p-12t_a>=156, hence3p-t_a>=13, "
        "including over reals. Omitting1680 single rows therefore changes no projected solutions.",
        "scope": "Exact serialized model, domains, rows, objective, guidance and parameters pass. "
        "No runner exists in this frozen producer bundle; a separately bound runner and explicit "
        "root launch authorization are still required. This is not an infeasibility certificate.",
    }
    (HERE / "model-gate.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "decision": report["decision"],
                "model_gate_sha256": sha(HERE / "model-gate.json"),
                "optimizer_calls": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
