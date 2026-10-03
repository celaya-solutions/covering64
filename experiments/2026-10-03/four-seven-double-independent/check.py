# Document:    Independent Four Sevenfold Double Variable Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      5c6e812e502998e75e7e97a1e515e134d051d7567c6fc8d7ae5bd3bd7f1a2330
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import copy
import hashlib
import importlib.util
import itertools
import json
import pathlib
from fractions import Fraction

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = pathlib.Path(__file__).resolve().parent
SAVED = pathlib.Path("experiments/scratch/four-seven-lp-20261003")
BASE_AUDIT = ROOT.parent / "four-seven-independent/check.py"
spec = importlib.util.spec_from_file_location("frozen_full_model_row_audit", BASE_AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
require = audit.require


def read_model(path):
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(path.read_text(), proto)
    return proto


def rational_satisfies(proto, values):
    if len(values) != len(proto.variables):
        return False
    for variable, value in zip(proto.variables, values, strict=True):
        domain = variable.domain
        if not any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)):
            return False
    for row in proto.constraints:
        if row.WhichOneof("constraint") != "linear" or row.enforcement_literal:
            return False
        value = sum(
            values[i] * coefficient
            for i, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True)
        )
        if not any(
            row.linear.domain[i] <= value <= row.linear.domain[i + 1]
            for i in range(0, len(row.linear.domain), 2)
        ):
            return False
    return True


def check_case(case):
    base = read_model(SAVED / case / "model.pbtxt")
    trusted = read_model(
        pathlib.Path("experiments/scratch/four-seven-independent-models") / f"{case}.pbtxt"
    )
    require(base == trusted, "base differs from independently reconstructed full model")
    path = SAVED / "strengthened" / case / "model.pbtxt"
    proto = read_model(path)
    require(len(proto.variables) == 4768 and len(proto.constraints) == 4270, "model size")
    restored = copy.deepcopy(proto)
    del restored.variables[4368:]
    del restored.constraints[3593:]
    require(restored == base, "original proto field changed")
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    eligible, fixed, heavy = {}, {}, {}
    for tid, triple in enumerate(triples):
        if triple in audit.ANCHORS:
            heavy[triple] = 7
        elif all(len(set(triple) & set(group)) <= 1 for group in audit.ANCHORS):
            eligible[triple] = f"double_triple_{tid}"
        else:
            group, hub = next(
                (a, h)
                for a, h in zip(audit.ANCHORS, audit.HUBS, strict=True)
                if len(set(triple) & set(a)) == 2
            )
            fixed[triple] = 2 if hub in triple else 1
    require((len(eligible), len(fixed), len(heavy)) == (400, 156, 4), "triple classes")
    require(collections.Counter(fixed.values()) == {1: 144, 2: 12}, "fixed counts")
    require(
        [(v.name, list(v.domain)) for v in proto.variables[4368:]]
        == [(name, [0, 1]) for name in eligible.values()],
        "double variable order or bounds",
    )
    expected = []
    for triple, name in eligible.items():
        terms = {f"block_{i}": 1 for i, b in enumerate(blocks) if set(triple) <= set(b)}
        terms[name] = -1
        expected.append(audit.key(terms, [1, 1]))
    for triple, value in fixed.items():
        expected.append(
            audit.key(
                {f"block_{i}": 1 for i, b in enumerate(blocks) if set(triple) <= set(b)},
                [value, value],
            )
        )
    double_count = 640 - sum(fixed.values()) - sum(heavy.values()) - len(eligible)
    require(double_count == 44, "double count identity")
    expected.append(audit.key({name: 1 for name in eligible.values()}, [44, 44]))
    demands = {}
    for pair, count in audit.independent_targets(case).items():
        terms = {name: 1 for t, name in eligible.items() if set(pair) <= set(t)}
        known = sum(value for t, value in {**fixed, **heavy}.items() if set(pair) <= set(t))
        demand = 3 * count - known - len(terms)
        demands[pair] = demand
        expected.append(audit.key(terms, [demand, demand]))
    require(
        sum(demands.values()) == 132 and sum(value == 0 for value in demands.values()) == 12,
        "pair demand accounting",
    )
    added = copy.deepcopy(proto)
    del added.constraints[:3593]
    expected = collections.Counter(expected)
    require(
        sum(expected.values()) == 677 and audit.actual_rows(added) == expected,
        "double rows mismatch",
    )
    require(expected[audit.key({}, [0, 0])] == 12, "explicit zero rows")
    witness = ROOT.parent / "four-seven-lp" / f"{case}-witness.json"
    document = json.loads(witness.read_text())
    values = [Fraction(0) for _ in range(4768)]
    for i, numerator, denominator in document["nonzero_weights"]:
        values[i] = Fraction(numerator, denominator)
    reported_path = ROOT.parent / "four-seven-lp" / f"{case}-double-values.json"
    reported = json.loads(reported_path.read_text())
    require(
        reported["original_witness_sha256"] == hashlib.sha256(witness.read_bytes()).hexdigest(),
        "original fractional witness hash",
    )
    require(set(reported["values"]) == set(eligible.values()), "reported double names")
    for index, (triple, name) in enumerate(eligible.items(), 4368):
        value = sum(values[i] for i, b in enumerate(blocks) if set(triple) <= set(b)) - 1
        require(value == Fraction(*reported["values"][name]), "fractional double value")
        values[index] = value
    require(sum(values[4368:]) == 44 and rational_satisfies(proto, values), "rational extension")
    controls = []
    for label, index in [
        ("wrong double link", 3593),
        ("wrong fixed triple", 3993),
        ("wrong total doubles", 4149),
        ("wrong pair demand", 4150),
    ]:
        damaged = copy.deepcopy(added)
        damaged.constraints[index - 3593].linear.domain[0] += 1
        require(audit.actual_rows(damaged) != expected, "damaged row accepted")
        controls.append(dict(control=label, rejected=True))
    damaged = copy.deepcopy(added)
    del damaged.constraints[-1]
    require(audit.actual_rows(damaged) != expected, "missing pair row accepted")
    controls.append(dict(control="missing pair row", rejected=True))
    damaged_values = list(values)
    damaged_values[4368] += Fraction(1, 17)
    require(not rational_satisfies(proto, damaged_values), "wrong rational double accepted")
    controls.append(dict(control="corrupt fractional double", rejected=True))
    return dict(
        complete=True,
        variables=4768,
        constraints=4270,
        added_variables=400,
        added_rows=677,
        full_prior_proto_preserved=True,
        all_677_rows_independently_reconstructed=True,
        all_4768_relaxed_variable_bounds_checked=True,
        all_4270_rows_checked_with_exact_fractions=True,
        all_400_double_values_independently_derived=True,
        fixed_single_triples=144,
        fixed_double_triples=12,
        zero_pair_rows=12,
        double_weight="44",
        integral_assignment=all(v.denominator == 1 for v in values),
        model_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        witness_sha256=hashlib.sha256(witness.read_bytes()).hexdigest(),
        double_values_sha256=hashlib.sha256(reported_path.read_bytes()).hexdigest(),
        damaged_controls=controls,
    )


def main():
    result = dict(
        complete=True,
        cases={case: check_case(case) for case in ("cycle", "matching")},
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        independent_base_audit_sha256=hashlib.sha256(BASE_AUDIT.read_bytes()).hexdigest(),
        scope=(
            "Valid integer full-cover lift; exact fractional feasibility "
            "does not give an integer cover."
        ),
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
