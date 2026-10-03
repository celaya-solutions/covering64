# Document:    Independent Selected Heavy Hub Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      99288bf066b0b7caaea3df9977e0ae6a75d3cca64dafa52d591905850d3215eb
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

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = pathlib.Path(__file__).resolve().parent
RUN = pathlib.Path("experiments/scratch/selected-heavy-hubs-h9-20261003")
BASE = pathlib.Path("experiments/scratch/first-family-hint-r4-005-hub-lns-20261003")
UTILITY = ROOT.parent / "heavy-residual-independent/check.py"
SELECTED = [(1, 2, 3), (5, 11, 16), (7, 10, 13), (8, 9, 14)]
spec = importlib.util.spec_from_file_location("independent_linear_audit", UTILITY)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
require = audit.require


def model(path):
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(path.read_text(), proto)
    return proto


def hint_values(blocks, triples, candidate):
    selected = set(candidate)
    counts = collections.Counter(t for b in candidate for t in itertools.combinations(b, 3))
    local = collections.Counter(
        t for b in candidate if min(b) <= 3 for t in itertools.combinations(b, 3)
    )
    residual = {t: int(counts[t] > 0 and local[t] == 0) for t in triples if min(t) >= 4}
    values = {f"block_{i}": int(b in selected) for i, b in enumerate(blocks)}
    values.update({f"hole_{i}": int(counts[t] == 0) for i, t in enumerate(triples)})
    values.update(
        {f"residual_triple_{i}": residual[t] for i, t in enumerate(triples) if t in residual}
    )
    values.update(
        {
            f"residual_pair_need_{a}_{b}": (
                sum(v for t, v in residual.items() if {a, b} <= set(t)) + 2
            )
            // 3
            for a, b in itertools.combinations(range(4, 17), 2)
        }
    )
    for i, triple in enumerate(triples):
        values[f"heavy6_{i}"] = int(counts[triple] >= 6)
        values[f"heavy7_{i}"] = int(counts[triple] >= 7)
    graph = [(4, 5), (4, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)]
    for anchor in (2, 3):
        for pair in graph:
            values[f"local_hole_{anchor}_{pair}"] = int(
                not any(
                    {anchor, *pair} <= set(b) and len(set(b) & {1, 2, 3}) == 1 for b in candidate
                )
            )
        values[f"local_deficit_{anchor}"] = sum(
            values[f"local_hole_{anchor}_{pair}"] for pair in graph
        )
    for triple in SELECTED:
        tid = triples.index(triple)
        for point in range(1, 17):
            if point not in triple:
                q = sum(set(triple) | {point} <= set(b) for b in candidate)
                values[f"selected_hub_{tid}_{point}"] = int(counts[triple] >= 6 and q >= 2)
    return values


def main():
    metadata = json.loads((RUN / "metadata.json").read_text())
    proto, base = model(RUN / "model.pbtxt"), model(BASE / "model.pbtxt")
    base_hash = hashlib.sha256((BASE / "model.pbtxt").read_bytes()).hexdigest()
    require(
        base_hash == "dbc6cae2d651f5fbb2f7d03074344147d664c18583c05a9c441cbfc45eb061b1",
        "previous independently audited model",
    )
    digest = hashlib.sha256((RUN / "model.pbtxt").read_bytes()).hexdigest()
    require(digest == metadata["model_sha256"], "model hash")
    require(len(proto.variables) == 6480 and len(proto.constraints) == 7534, "model size")
    restored = copy.deepcopy(proto)
    del restored.variables[6428:]
    del restored.constraints[7254:]
    del restored.solution_hint.vars[6428:]
    del restored.solution_hint.values[6428:]
    require(restored == base, "an original proto field changed")
    for name, expected_hash in metadata["sources"].items():
        require(
            hashlib.sha256((RUN / name).read_bytes()).hexdigest() == expected_hash,
            f"frozen source hash {name}",
        )
    blocks = list(itertools.combinations(range(1, 17), 5))
    triples = list(itertools.combinations(range(1, 17), 3))
    expected = []
    variable_names = []
    hubs = {}
    for triple in SELECTED:
        tid = triples.index(triple)
        six, seven = f"heavy6_{tid}", f"heavy7_{tid}"
        local = []
        for point in range(1, 17):
            if point in triple:
                continue
            hub = f"selected_hub_{tid}_{point}"
            variable_names.append(hub)
            hubs[triple, point] = hub
            local.append(hub)
            terms = {
                f"block_{i}": 1 for i, b in enumerate(blocks) if set(triple) | {point} <= set(b)
            }
            require(len(terms) == 12, "quadruple common block count")
            expected.extend(
                [
                    audit.row_key({hub: 1, six: -1}, [audit.MIN, 0]),
                    audit.row_key(terms, [2, audit.MAX], [(hub, True)]),
                    audit.row_key(terms, [audit.MIN, 1], [(six, True), (hub, False)]),
                    audit.row_key(terms, [audit.MIN, 3], [(six, True)]),
                    audit.row_key(terms, [audit.MIN, 2], [(seven, True)]),
                ]
            )
        expected.append(audit.row_key({name: 1 for name in local}, [audit.MIN, 1]))
    for point in range(1, 17):
        terms = {f"heavy6_{i}": 1 for i, t in enumerate(triples) if point in t}
        terms.update({name: 1 for (_, p), name in hubs.items() if p == point})
        expected.append(audit.row_key(terms, [audit.MIN, 1]))
    require(
        [(v.name, list(v.domain)) for v in proto.variables[6428:]]
        == [(name, [0, 1]) for name in variable_names],
        "new variable definitions",
    )
    expected = collections.Counter(expected)
    require(
        sum(expected.values()) == 280 and audit.actual_rows(proto, 7254, 7534) == expected,
        "selected hub row reconstruction",
    )
    assignment = dict(zip(proto.solution_hint.vars, proto.solution_hint.values, strict=True))
    require(len(assignment) == len(proto.solution_hint.vars) == 6480, "complete hint")
    require(audit.satisfies(proto, assignment), "saved hint violates domain or constraint")
    candidate_path = ROOT.parent / "structured-hub-escape/candidate-h9.txt"
    require((RUN / "initial.txt").read_bytes() == candidate_path.read_bytes(), "h9 seed identity")
    candidate = [tuple(map(int, line.split())) for line in candidate_path.read_text().splitlines()]
    values = hint_values(blocks, triples, candidate)
    require(
        len(values) == 6480
        and all(values[v.name] == assignment[i] for i, v in enumerate(proto.variables)),
        "independently derived complete hint",
    )
    expected_hubs = [name for name in variable_names if values[name]]
    require(
        expected_hubs == ["selected_hub_0_4", "selected_hub_457_12", "selected_hub_480_15"],
        "h9 active hubs",
    )
    truth_cases = 0
    for count, quad, hub in itertools.product(range(8), range(13), (0, 1)):
        six, seven = int(count >= 6), int(count >= 7)
        encoded = (
            hub <= six
            and (not hub or quad >= 2)
            and (not (six and not hub) or quad <= 1)
            and (not six or quad <= 3)
            and (not seven or quad <= 2)
        )
        oracle = (
            hub == int(count >= 6 and quad >= 2)
            and (count < 6 or quad <= 3)
            and (count < 7 or quad <= 2)
        )
        require(encoded == oracle, "reification truth table")
        truth_cases += 1
    controls = []
    for label, row, action in [
        ("missing row", 7254, "delete"),
        ("wrong forward threshold", 7255, "lower"),
        ("wrong complementary threshold", 7256, "upper"),
        ("wrong sixfold cap", 7257, "upper"),
        ("wrong sevenfold cap", 7258, "upper"),
        ("wrong per-triple hub count", 7319, "upper"),
        ("wrong packing bound", 7518, "upper"),
    ]:
        damaged = copy.deepcopy(proto)
        if action == "delete":
            del damaged.constraints[row]
        else:
            damaged.constraints[row].linear.domain[0 if action == "lower" else -1] += 1
        require(audit.actual_rows(damaged, 7254, 7534) != expected, "damaged model accepted")
        controls.append(dict(control=label, rejected=True))
    damaged = copy.deepcopy(proto)
    row = damaged.constraints[7256]
    row.enforcement_literal[1] = -row.enforcement_literal[1] - 1
    require(audit.actual_rows(damaged, 7254, 7534) != expected, "wrong polarity accepted")
    controls.append(dict(control="wrong complementary polarity", rejected=True))
    damaged = copy.deepcopy(proto)
    packing = damaged.constraints[7518]
    names = {v.name: i for i, v in enumerate(proto.variables)}
    unselected = names[f"heavy6_{triples.index((1, 4, 5))}"]
    offset = list(packing.linear.vars).index(unselected)
    del packing.linear.vars[offset]
    del packing.linear.coeffs[offset]
    require(audit.actual_rows(damaged, 7254, 7534) != expected, "omitted unselected heavy accepted")
    controls.append(dict(control="omit unselected heavy anchor from packing", rejected=True))
    for name in [expected_hubs[0], "selected_hub_0_5"]:
        damaged_hint = assignment.copy()
        damaged_hint[names[name]] = 1 - damaged_hint[names[name]]
        require(not audit.satisfies(proto, damaged_hint), "damaged hub hint accepted")
        controls.append(dict(control=f"wrong hub hint {name}", rejected=True))
    result = dict(
        complete=True,
        model_sha256=digest,
        base_model_sha256=base_hash,
        variables=6480,
        constraints=7534,
        added_variables=52,
        added_rows=280,
        all_original_proto_fields_preserved=True,
        rows_independently_reconstructed=280,
        all_6480_hint_values_independently_derived=True,
        all_7534_constraints_evaluated=True,
        active_hub_hints=expected_hubs,
        selected_triples=SELECTED,
        truth_table_cases=truth_cases,
        damaged_controls=controls,
        candidate_sha256=metadata["hint_sha256"],
        source_hashes=metadata["sources"],
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        utility_sha256=hashlib.sha256(UTILITY.read_bytes()).hexdigest(),
        scope=(
            "Conditional selected-triple hub encoding; point packing includes every heavy anchor."
        ),
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
