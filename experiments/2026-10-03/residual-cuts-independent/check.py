# Document:    Independent Saved Residual-Cut Model and Hint Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e7292b18e003eebfbbdafdd9b8112a6dec1f987912db1c6931fa72cec00e0158
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import copy
import hashlib
import itertools
import json
import pathlib

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = pathlib.Path(__file__).resolve().parent
RUN = pathlib.Path("experiments/scratch/first-family-hint-r4-000-residual-20261003")
MIN, MAX = -(2**63), 2**63 - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def row_key(coefficients, domain, enforcement=()):
    return tuple(sorted(coefficients.items())), tuple(domain), tuple(sorted(enforcement))


def actual_rows(proto):
    names = [variable.name for variable in proto.variables]
    result = []
    for constraint in proto.constraints[-1105:]:
        require(constraint.WhichOneof("constraint") == "linear", "new non-linear constraint")
        terms = collections.Counter()
        for variable, coefficient in zip(constraint.linear.vars, constraint.linear.coeffs):
            terms[names[variable]] += coefficient
        enforcement = [
            (names[literal] if literal >= 0 else names[-literal - 1], literal >= 0)
            for literal in constraint.enforcement_literal
        ]
        result.append(row_key(dict(terms), constraint.linear.domain, enforcement))
    return collections.Counter(result)


def satisfies(proto, assignment):
    for index, variable in enumerate(proto.variables):
        value = assignment[index]
        if not any(
            lo <= value <= hi for lo, hi in zip(variable.domain[::2], variable.domain[1::2])
        ):
            return False
    for constraint in proto.constraints:
        if not all(
            assignment[literal] == 1 if literal >= 0 else assignment[-literal - 1] == 0
            for literal in constraint.enforcement_literal
        ):
            continue
        kind = constraint.WhichOneof("constraint")
        if kind == "linear":
            value = sum(
                assignment[index] * coefficient
                for index, coefficient in zip(constraint.linear.vars, constraint.linear.coeffs)
            )
            if not any(
                lo <= value <= hi
                for lo, hi in zip(constraint.linear.domain[::2], constraint.linear.domain[1::2])
            ):
                return False
        elif kind == "table":
            table = constraint.table
            require(not table.vars and table.exprs, "legacy table format")
            values = tuple(
                expression.offset
                + sum(
                    assignment[index] * coefficient
                    for index, coefficient in zip(expression.vars, expression.coeffs)
                )
                for expression in table.exprs
            )
            size = len(values)
            present = values in [
                tuple(table.values[i : i + size]) for i in range(0, len(table.values), size)
            ]
            if present == table.negated:
                return False
        else:
            raise ValueError(f"unsupported saved constraint {kind}")
    return True


def main():
    model_path = RUN / "model.pbtxt"
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(model_path.read_text(), proto)
    metadata = json.loads((RUN / "metadata.json").read_text())
    require(
        hashlib.sha256(model_path.read_bytes()).hexdigest() == metadata["model_sha256"],
        "saved model hash",
    )
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    pairs = list(itertools.combinations(range(4, 17), 2))
    outside = [index for index, block in enumerate(blocks) if min(block) >= 4]
    residual_names = {
        triple: f"residual_triple_{index}"
        for index, triple in enumerate(triples)
        if min(triple) >= 4
    }
    need_names = {pair: f"residual_pair_need_{pair[0]}_{pair[1]}" for pair in pairs}
    require(len(proto.variables) == 5308 and len(proto.constraints) == 4112, "saved model size")
    expected_variables = [(name, [0, 1]) for name in residual_names.values()]
    expected_variables += [(name, [0, 4]) for name in need_names.values()]
    require(
        [(v.name, list(v.domain)) for v in proto.variables[-364:]] == expected_variables,
        "auxiliary variables or ordering",
    )
    require(
        all(proto.variables[index].name == f"block_{index}" for index in range(4368)),
        "block variable ordering",
    )
    expected = []
    for index, triple in enumerate(triples):
        if triple not in residual_names:
            continue
        local = {
            f"block_{i}": 1
            for i, block in enumerate(blocks)
            if min(block) <= 3 and set(triple) <= set(block)
        }
        name = residual_names[triple]
        expected.append(row_key(local, [0, 0], [(name, True)]))
        expected.append(row_key({f"hole_{index}": 1}, [0, 0], [(name, True)]))
        expected.append(row_key({**local, f"hole_{index}": 1}, [1, MAX], [(name, False)]))
    for pair, name in need_names.items():
        terms = {
            residual_name: -1
            for triple, residual_name in residual_names.items()
            if set(pair) <= set(triple)
        }
        terms[name] = 3
        expected.append(row_key(terms, [0, MAX]))
        expected.append(row_key(terms, [MIN, 2]))
        terms = {f"block_{index}": 1 for index in outside if set(pair) <= set(blocks[index])}
        terms[name] = -1
        expected.append(row_key(terms, [0, MAX]))
    for point in range(4, 17):
        terms = {name: 1 for pair, name in need_names.items() if point in pair}
        terms.update({f"block_{index}": -4 for index in outside if point in blocks[index]})
        expected.append(row_key(terms, [MIN, 0]))
    require(
        len(expected) == 1105 and actual_rows(proto) == collections.Counter(expected),
        "saved new-row mismatch",
    )
    assignment = dict(zip(proto.solution_hint.vars, proto.solution_hint.values))
    require(
        len(assignment) == len(proto.solution_hint.vars) == 5308, "incomplete or duplicate hint"
    )
    candidate = [
        tuple(map(int, line.split())) for line in (RUN / "initial.txt").read_text().splitlines()
    ]
    selected = set(candidate)
    total = collections.Counter(
        triple for block in candidate for triple in itertools.combinations(block, 3)
    )
    local = collections.Counter(
        triple
        for block in candidate
        if min(block) <= 3
        for triple in itertools.combinations(block, 3)
    )
    residual = {triple: int(total[triple] > 0 and local[triple] == 0) for triple in residual_names}
    values = {name: residual[triple] for triple, name in residual_names.items()}
    values.update(
        {
            name: (sum(value for triple, value in residual.items() if set(pair) <= set(triple)) + 2)
            // 3
            for pair, name in need_names.items()
        }
    )
    names = {variable.name: index for index, variable in enumerate(proto.variables)}
    require(
        all(assignment[names[name]] == value for name, value in values.items()), "auxiliary hint"
    )
    require(
        all(assignment[i] == int(block in selected) for i, block in enumerate(blocks)),
        "block hint mismatch",
    )
    require(
        all(assignment[4368 + i] == int(total[triple] == 0) for i, triple in enumerate(triples)),
        "hole hint mismatch",
    )
    require(satisfies(proto, assignment), "saved complete hint violates model")
    controls = []
    for name in [next(iter(residual_names.values())), next(iter(need_names.values()))]:
        damaged = assignment.copy()
        damaged[names[name]] = 1 - damaged[names[name]] if name.startswith("residual_triple") else 4
        require(not satisfies(proto, damaged), "damaged auxiliary hint accepted")
        controls.append(dict(control=f"wrong hint {name}", rejected=True))
    for label, action in [
        (
            "wrong iff polarity",
            lambda p: p.constraints[-1105].enforcement_literal.__setitem__(0, -4945),
        ),
        (
            "wrong ceiling coefficient",
            lambda p: p.constraints[-247].linear.coeffs.__setitem__(0, 7),
        ),
        ("missing new row", lambda p: p.constraints.__delitem__(-1)),
    ]:
        damaged = copy.deepcopy(proto)
        action(damaged)
        try:
            rejected = actual_rows(damaged) != collections.Counter(expected)
        except ValueError:
            rejected = True
        require(rejected, "damaged rows accepted")
        controls.append(dict(control=label, rejected=True))
    damaged = assignment.copy()
    full = {triple: int(local[triple] == 0) for triple in residual_names}
    for triple, name in residual_names.items():
        damaged[names[name]] = full[triple]
    for pair, name in need_names.items():
        damaged[names[name]] = (
            sum(value for triple, value in full.items() if set(pair) <= set(triple)) + 2
        ) // 3
    require(not satisfies(proto, damaged), "unconditional full-cover hint accepted")
    controls.append(dict(control="ignore actual partial holes", rejected=True))
    result = dict(
        complete=True,
        new_variables=364,
        new_constraints=1105,
        saved_model_variables=len(proto.variables),
        saved_model_constraints=len(proto.constraints),
        all_5308_hint_values_complete=True,
        all_4112_hint_constraints_checked=True,
        auxiliary_values_match_independent_oracle=True,
        damaged_controls=controls,
        model_sha256=metadata["model_sha256"],
        source_hashes=metadata["sources"],
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
