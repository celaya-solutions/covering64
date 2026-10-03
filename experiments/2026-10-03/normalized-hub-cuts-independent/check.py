# Document:    Independent Normalized Hub Cut Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d4cf698816a54bb4c762509a48809730146e4e051a9f15d48ee0f29bba89b02a
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
import re

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = pathlib.Path(__file__).resolve().parent
RUN = pathlib.Path("experiments/scratch/first-family-hint-r4-005-hub-lns-20261003")
PRIOR = pathlib.Path("experiments/scratch/first-family-hint-r4-005-heavy-residual-20261003")
AUDIT = ROOT.parent / "heavy-residual-independent/check.py"
spec = importlib.util.spec_from_file_location("frozen_independent_row_utilities", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
require = audit.require


def read_model(path):
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(path.read_text(), proto)
    return proto


def main():
    metadata = json.loads((RUN / "metadata.json").read_text())
    proto = read_model(RUN / "model.pbtxt")
    previous = read_model(PRIOR / "model.pbtxt")
    require(
        hashlib.sha256((PRIOR / "model.pbtxt").read_bytes()).hexdigest()
        == "a4e914f8de6eb39b3c2872e3db27cff70b22391641958206a639d330f28b3b14",
        "previous frozen audited model hash",
    )
    digest = hashlib.sha256((RUN / "model.pbtxt").read_bytes()).hexdigest()
    require(digest == metadata["model_sha256"], "model hash")
    require(len(proto.variables) == 6428 and len(proto.constraints) == 7254, "model size")
    require(list(proto.variables) == list(previous.variables), "unexpected new variables")
    for name, expected_hash in metadata["sources"].items():
        require(
            hashlib.sha256((RUN / name).read_bytes()).hexdigest() == expected_hash,
            f"frozen source hash {name}",
        )
    differences = [i for i in range(6929) if proto.constraints[i] != previous.constraints[i]]
    require(len(differences) == 1, "unexpected changes to previously audited base rows")
    require(
        previous.constraints[differences[0]].linear.domain[-1] == 6, "previous hole upper bound"
    )
    changed = proto.constraints[differences[0]]
    expected_hole_bound = {f"hole_{i}": 1 for i in range(560)}
    require(
        audit.actual_rows(proto, differences[0], differences[0] + 1)
        == collections.Counter([audit.row_key(expected_hole_bound, [audit.MIN, 9])]),
        "changed base row is not nine-hole budget",
    )
    require(not changed.enforcement_literal, "conditional hole budget")
    triples = list(itertools.combinations(range(1, 17), 3))
    blocks = list(itertools.combinations(range(1, 17), 5))
    expected_rows = []
    zero_rows = repeated_rows = 0
    for i, triple in enumerate(triples):
        if 4 in triple:
            expected_rows.append(audit.row_key({f"heavy6_{i}": 1}, [0, 0]))
            zero_rows += 1
        elif min(triple) >= 5:
            containing_hub = {
                f"block_{b}": 1 for b, block in enumerate(blocks) if set(triple) | {4} <= set(block)
            }
            expected_rows.append(
                audit.row_key(containing_hub, [audit.MIN, 1], [(f"heavy6_{i}", True)])
            )
            repeated_rows += 1
    require((zero_rows, repeated_rows) == (105, 220), "hub row categories")
    expected = collections.Counter(expected_rows)
    require(audit.actual_rows(proto, 6929, 7254) == expected, "hub cut reconstruction")
    assignment = dict(zip(proto.solution_hint.vars, proto.solution_hint.values, strict=True))
    require(len(proto.solution_hint.vars) == len(assignment) == 6428, "complete hint")
    require(audit.satisfies(proto, assignment), "saved hint violates a model constraint")
    candidate = [
        tuple(map(int, line.split())) for line in (RUN / "initial.txt").read_text().splitlines()
    ]
    independently_checked = ROOT.parent / "structured-hub-escape/candidate-h9.txt"
    require(
        (RUN / "initial.txt").read_bytes() == independently_checked.read_bytes(), "h9 seed identity"
    )
    require(
        hashlib.sha256(independently_checked.read_bytes()).hexdigest() == metadata["hint_sha256"],
        "h9 seed hash",
    )
    selected = set(candidate)
    total = collections.Counter(t for b in candidate for t in itertools.combinations(b, 3))
    local = collections.Counter(
        t for b in candidate if min(b) <= 3 for t in itertools.combinations(b, 3)
    )
    residual = {t: int(total[t] > 0 and local[t] == 0) for t in triples if min(t) >= 4}
    residual_values = {
        f"residual_triple_{i}": residual[t] for i, t in enumerate(triples) if t in residual
    }
    residual_values.update(
        {
            f"residual_pair_need_{a}_{b}": (
                sum(v for t, v in residual.items() if {a, b} <= set(t)) + 2
            )
            // 3
            for a, b in itertools.combinations(range(4, 17), 2)
        }
    )
    values = {f"block_{i}": int(b in selected) for i, b in enumerate(blocks)}
    values.update({f"hole_{i}": int(total[t] == 0) for i, t in enumerate(triples)})
    values.update(residual_values)
    for i, triple in enumerate(triples):
        values[f"heavy6_{i}"] = int(total[triple] >= 6)
        values[f"heavy7_{i}"] = int(total[triple] >= 7)
    for variable in proto.variables:
        if variable.name.startswith("local_hole_"):
            anchor, first, second = map(int, re.findall(r"\d+", variable.name))
            values[variable.name] = int(
                not any(
                    {anchor, first, second} <= set(b) and len(set(b) & {1, 2, 3}) == 1
                    for b in candidate
                )
            )
    for anchor in (2, 3):
        values[f"local_deficit_{anchor}"] = sum(
            v for name, v in values.items() if name.startswith(f"local_hole_{anchor}_")
        )
    require(
        len(values) == 6428
        and all(assignment[i] == values[v.name] for i, v in enumerate(proto.variables)),
        "independent complete hint derivation",
    )
    controls = []
    for label, row_index, alteration in [
        ("missing row", 6929, "delete"),
        ("allow heavy triple through hub", 6929, "bound"),
        ("wrong hub reuse bound", 7034, "bound"),
    ]:
        damaged = copy.deepcopy(proto)
        if alteration == "delete":
            del damaged.constraints[row_index]
        else:
            damaged.constraints[row_index].linear.domain[-1] += 1
        require(audit.actual_rows(damaged, 6929, 7254) != expected, "damaged cut accepted")
        controls.append(dict(control=label, rejected=True))
    enforced = next(i for i in range(6929, 7254) if proto.constraints[i].enforcement_literal)
    for label in ("wrong polarity", "wrong block coefficient"):
        damaged = copy.deepcopy(proto)
        if label == "wrong polarity":
            lit = damaged.constraints[enforced].enforcement_literal[0]
            damaged.constraints[enforced].enforcement_literal[0] = -lit - 1
        else:
            damaged.constraints[enforced].linear.coeffs[0] = 2
        require(audit.actual_rows(damaged, 6929, 7254) != expected, "damaged implication accepted")
        controls.append(dict(control=label, rejected=True))
    old_hint = dict(zip(previous.solution_hint.vars, previous.solution_hint.values, strict=True))
    require(not audit.satisfies(proto, old_hint), "old duplicate-hub hint accepted")
    controls.append(dict(control="old six-hole duplicate-hub hint", rejected=True))
    result = dict(
        complete=True,
        model_sha256=digest,
        variables=6428,
        constraints=7254,
        new_variables=0,
        new_rows=325,
        through_hub_zero_rows=zero_rows,
        repeated_hub_rows=repeated_rows,
        changed_prior_rows=differences,
        prior_change="hole upper bound increased from6 to9",
        all_6428_hint_values_independently_derived=True,
        all_7254_hint_constraints_evaluated=True,
        residual_rows_match_frozen_independent_audit=1105,
        candidate_sha256=metadata["hint_sha256"],
        frozen_sources=metadata["sources"],
        damaged_controls=controls,
        checker_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        independent_utility_sha256=hashlib.sha256(AUDIT.read_bytes()).hexdigest(),
    )
    (ROOT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
