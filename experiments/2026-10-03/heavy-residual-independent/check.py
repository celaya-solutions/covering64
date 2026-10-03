# Document:    Independent Combined Heavy and Residual Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      faf476ceb1929e23936daac5da3f2029414d4b37582f3c6329337308e5230e7b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import collections
import copy
import hashlib
import itertools
import json
import pathlib
import re
import subprocess
import sys

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

from covering64.core import read_blocks, verify_cover

ROOT = pathlib.Path(__file__).resolve().parent
RUN = pathlib.Path("experiments/scratch/first-family-hint-r4-005-heavy-residual-20261003")
MIN, MAX = -(2**63), 2**63 - 1


def require(condition, message):
    if not condition:
        raise ValueError(message)


def row_key(coefficients, domain, enforcement=()):
    return tuple(sorted(coefficients.items())), tuple(domain), tuple(sorted(enforcement))


def actual_rows(proto, start=3007, stop=4112):
    names = [variable.name for variable in proto.variables]
    result = []
    for constraint in proto.constraints[start:stop]:
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


def verify_sources(metadata):
    for name, digest in metadata["sources"].items():
        require(
            hashlib.sha256((RUN / name).read_bytes()).hexdigest() == digest,
            f"frozen source hash {name}",
        )


def audit_heavy(proto, assignment, blocks, triples, total):
    variables = []
    expected = []
    values = {}
    for index, triple in enumerate(triples):
        six, seven = f"heavy6_{index}", f"heavy7_{index}"
        variables.extend([(six, [0, 1]), (seven, [0, 1])])
        count = {f"block_{i}": 1 for i, block in enumerate(blocks) if set(triple) <= set(block)}
        expected.extend(
            [
                row_key(count, [MIN, 7]),
                row_key(count, [6, MAX], [(six, True)]),
                row_key(count, [MIN, 5], [(six, False)]),
                row_key(count, [7, 7], [(seven, True)]),
                row_key(count, [MIN, 6], [(seven, False)]),
            ]
        )
        values[six], values[seven] = int(total[triple] >= 6), int(total[triple] >= 7)
    for point in range(1, 17):
        expected.append(
            row_key(
                {f"heavy6_{i}": 1 for i, triple in enumerate(triples) if point in triple}, [MIN, 1]
            )
        )
    terms = {f"heavy6_{i}": 3 for i in range(560)}
    terms.update({f"heavy7_{i}": 1 for i in range(560)})
    expected.append(row_key(terms, [MIN, 16]))
    require(
        [(v.name, list(v.domain)) for v in proto.variables[5308:]] == variables,
        "heavy auxiliary variables or ordering",
    )
    require(
        len(expected) == 2817 and actual_rows(proto, 4112, 6929) == collections.Counter(expected),
        "heavy rows mismatch",
    )
    names = {v.name: i for i, v in enumerate(proto.variables)}
    require(
        all(assignment[names[name]] == value for name, value in values.items()),
        "heavy hint mismatch",
    )
    controls = []
    for name in ["heavy6_0", "heavy7_0"]:
        damaged = assignment.copy()
        damaged[names[name]] = 1 - damaged[names[name]]
        require(not satisfies(proto, damaged), "wrong heavy hint accepted")
        controls.append(dict(control=f"wrong hint {name}", rejected=True))
    for label, index, field, value in [
        ("wrong six threshold", 4113, "lower", 5),
        ("wrong six complement", 4114, "upper", 6),
        ("wrong seven threshold", 4115, "lower", 6),
        ("wrong seven complement", 4116, "upper", 7),
        ("wrong weighted bound", 6928, "upper", 17),
        ("wrong disjointness bound", 6912, "upper", 2),
    ]:
        damaged = copy.deepcopy(proto)
        damaged.constraints[index].linear.domain[0 if field == "lower" else -1] = value
        require(
            actual_rows(damaged, 4112, 6929) != collections.Counter(expected),
            "damaged heavy row accepted",
        )
        controls.append(dict(control=label, rejected=True))
    damaged = copy.deepcopy(proto)
    del damaged.constraints[4112]
    require(
        actual_rows(damaged, 4112, 6929) != collections.Counter(expected),
        "missing heavy row accepted",
    )
    controls.append(dict(control="missing heavy row", rejected=True))
    threshold_cases = 0
    for count in range(79):
        for six, seven in itertools.product((0, 1), repeat=2):
            encoded = (
                count <= 7
                and (count >= 6 if six else count <= 5)
                and (count == 7 if seven else count <= 6)
            )
            oracle = count <= 7 and six == int(count >= 6) and seven == int(count >= 7)
            require(encoded == oracle, "threshold truth table")
            threshold_cases += 1
    return dict(
        rows_reconstructed=2817,
        values_independently_checked=1120,
        threshold_cases=threshold_cases,
        damaged_controls=controls,
    )


def audit_candidate(candidate, local, metadata):
    normalized = pathlib.Path("experiments/2026-10-03/first-family-independent")
    mapping = json.loads((normalized / "normalized-escape-h6.json").read_text())
    normalized_path = normalized / "normalized-escape-h6.txt"
    require(list(read_blocks(normalized_path)) == candidate, "saved and normalized witness")
    source_path = pathlib.Path(mapping["source"])
    require(
        hashlib.sha256(source_path.read_bytes()).hexdigest() == mapping["source_sha256"],
        "normalization source hash",
    )
    source = read_blocks(source_path)
    point_map = {int(k): v for k, v in mapping["point_map"].items()}
    require(set(point_map) == set(range(1, 17)) == set(point_map.values()), "point permutation")
    require(
        sorted(tuple(sorted(point_map[p] for p in b)) for b in source) == sorted(candidate),
        "point-map image",
    )
    require(
        hashlib.sha256((normalized / mapping["mapping_source"]).read_bytes()).hexdigest()
        == mapping["mapping_source_sha256"],
        "prior mapping hash",
    )
    package = verify_cover(candidate)
    process = subprocess.run(
        [sys.executable, "scripts/check_cover.py", str(normalized_path), "--expected-blocks", "64"],
        text=True,
        capture_output=True,
        check=False,
    )
    require(process.returncode == 1, "partial witness standalone status")
    standalone = json.loads(process.stdout)
    require(
        [list(triple) for triple in package["uncovered"]]
        == standalone["uncovered"]
        == metadata["initial"]["package"]["uncovered"],
        "checker hole agreement",
    )
    require(
        package["canonical_sha256"] == standalone["canonical_sha256"] == metadata["hint_sha256"],
        "checker hash agreement",
    )
    require(
        package["blocks"] == 64 and len(package["uncovered"]) == 6,
        "candidate cardinality and holes",
    )
    require(set(package["replication"].values()) == {20}, "regular point degrees")
    total = collections.Counter(t for b in candidate for t in itertools.combinations(b, 3))
    heavy = [(t, n) for t, n in sorted(total.items()) if n >= 6]
    require(len(heavy) == 4 and all(n == 7 for _, n in heavy), "four sevenfold triples")
    require(len(set().union(*(set(t) for t, _ in heavy))) == 12, "heavy disjointness")
    expected_heavy = [
        (tuple(row["triple"]), row["multiplicity"]) for row in mapping["heavy_triples"]
    ]
    require(heavy == expected_heavy, "recorded heavy triples")
    old_seed = read_blocks(normalized / "normalized-h5.txt")
    require(
        {b for b in candidate if min(b) <= 3} == {b for b in old_seed if min(b) <= 3},
        "local families changed from h5 seed",
    )
    full_residual = [t for t in itertools.combinations(range(4, 17), 3) if local[t] == 0]
    pair_needs = {
        pair: (sum(set(pair) <= set(t) for t in full_residual) + 2) // 3
        for pair in itertools.combinations(range(4, 17), 2)
    }
    row = [pair_needs[(4, p)] for p in range(5, 17)]
    require(sum(row) == 25, "fixed-family full completion obstruction")
    controls = []
    for name, blocks in [
        ("duplicate block", [*candidate[:-1], candidate[0]]),
        ("repeated label", [(candidate[0][0],) * 5, *candidate[1:]]),
        ("outside label", [(0, *candidate[0][1:]), *candidate[1:]]),
    ]:
        try:
            verify_cover(blocks)
        except ValueError:
            controls.append(dict(control=name, package_rejected=True))
        else:
            raise ValueError("malformed witness accepted")
        raw = "".join(" ".join(map(str, b)) + "\n" for b in blocks)
        # Feed the standalone parser without reusing package parsing logic.
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "standalone_cover_audit", "scripts/check_cover.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            module.verify_cover(module.parse_witness(raw), expected_blocks=64)
        except module.InvalidWitness:
            controls[-1]["standalone_rejected"] = True
        else:
            raise ValueError("malformed standalone witness accepted")
    return dict(
        package=package,
        standalone=standalone,
        point_map_checked=True,
        local_families_match_h5=True,
        heavy_triples=mapping["heavy_triples"],
        weighted_heavy_sum=16,
        full_completion_hub_row=row,
        full_completion_hub_sum=25,
        full_completion_hub_budget=24,
        damaged_controls=controls,
    )


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
    require(len(proto.variables) == 6428 and len(proto.constraints) == 6929, "saved model size")
    expected_variables = [(name, [0, 1]) for name in residual_names.values()]
    expected_variables += [(name, [0, 4]) for name in need_names.values()]
    require(
        [(v.name, list(v.domain)) for v in proto.variables[4944:5308]] == expected_variables,
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
        len(assignment) == len(proto.solution_hint.vars) == 6428, "incomplete or duplicate hint"
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
    for name, index in names.items():
        if name.startswith("local_hole_"):
            anchor, first, second = map(int, re.findall(r"\d+", name))
            count = sum(
                {anchor, first, second} <= set(block) and len(set(block) & {1, 2, 3}) == 1
                for block in candidate
            )
            require(assignment[index] == int(count == 0), "local hole hint")
        elif name.startswith("local_deficit_"):
            anchor = name.rsplit("_", 1)[1]
            holes = [
                assignment[i] for n, i in names.items() if n.startswith(f"local_hole_{anchor}_")
            ]
            require(assignment[index] == sum(holes), "local deficit hint")
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
            lambda p: p.constraints[3007].enforcement_literal.__setitem__(0, -4945),
        ),
        (
            "wrong ceiling coefficient",
            lambda p: p.constraints[3865].linear.coeffs.__setitem__(0, 7),
        ),
        ("missing new row", lambda p: p.constraints.__delitem__(4111)),
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
    heavy_result = audit_heavy(proto, assignment, blocks, triples, total)
    candidate_result = audit_candidate(candidate, local, metadata)
    verify_sources(metadata)
    result = dict(
        heavy_audit=heavy_result,
        candidate_audit=candidate_result,
        complete=True,
        residual_variables=364,
        heavy_variables=1120,
        residual_constraints=1105,
        heavy_constraints=2817,
        saved_model_variables=len(proto.variables),
        saved_model_constraints=len(proto.constraints),
        all_6428_hint_values_complete=True,
        all_6929_hint_constraints_checked=True,
        auxiliary_values_match_independent_oracle=True,
        damaged_controls=controls,
        model_sha256=metadata["model_sha256"],
        source_hashes=metadata["sources"],
        runtime_solver_version=ortools.__version__,
        verifier_source_hashes={
            name: hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()
            for name in ["src/covering64/core.py", "scripts/check_cover.py"]
        },
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
