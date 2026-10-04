# Document:    Independent Audit of the Eight-Pair Construction Model
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      6fff3531f7fe3123f4641467e304ea99643befa8c28f8412e4fcdebff4f0920e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import importlib.util
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "pair_probe", Path(__file__).parents[1] / "scripts/independent_pair_partition.py"
)
SUBJECT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SUBJECT)


def audit(model, balanced):
    """Reconstruct every variable and row without the package incidence builder."""
    blocks = list(combinations(range(1, 17), 5))
    triples = list(combinations(range(1, 17), 3))
    proto = model.proto
    assert len(proto.variables) == 4368
    for i, variable in enumerate(proto.variables):
        assert variable.name == f"block_{i}"
        assert list(variable.domain) == [0, 1]
    rows = [(list(range(4368)), [64, 64])]
    for triple in triples:
        transversal = len({(x + 1) // 2 for x in triple}) == 3
        ids = [i for i, b in enumerate(blocks) if all(x in b for x in triple)]
        rows.append((ids, [1, 1 if transversal else 9223372036854775807]))
    if balanced:
        ids = [i for i, b in enumerate(blocks) if len({(x + 1) // 2 for x in b}) == 4]
        assert len(ids) == 2240
        rows.append((ids, [0, 0]))
    assert len(proto.constraints) == len(rows)
    for constraint, (ids, domain) in zip(proto.constraints, rows, strict=True):
        assert not constraint.enforcement_literal
        assert sorted(constraint.linear.vars) == ids
        assert list(constraint.linear.coeffs) == [1] * len(ids)
        assert list(constraint.linear.domain) == domain


@pytest.mark.parametrize("balanced", [False, True])
def test_every_model_row(balanced):
    universe, model, variables = SUBJECT.build_model(balanced)
    assert tuple(combinations(range(1, 17), 5)) == universe.blocks
    assert len(variables) == 4368
    audit(model, balanced)


@pytest.mark.parametrize("damage", ["variable", "coefficient", "coverage", "scope"])
def test_audit_rejects_damaged_model(damage):
    _, model, _ = SUBJECT.build_model(True)
    if damage == "variable":
        model.proto.variables[0].name = "block_1"
    elif damage == "coefficient":
        model.proto.constraints[1].linear.coeffs[0] = 2
    elif damage == "coverage":
        model.proto.constraints[1].linear.domain[0] = 0
    else:
        model.proto.constraints[len(model.proto.constraints) - 1].linear.domain[1] = 1
    with pytest.raises(AssertionError):
        audit(model, True)


def test_type_count_identity():
    counts = Counter()
    for block in combinations(range(1, 17), 5):
        kind = SUBJECT.block_type(block)
        transversals = sum(
            len({(p + 1) // 2 for p in t}) == 3 for t in combinations(block, 3)
        )
        counts[(kind, transversals)] += 1
    assert counts == {
        ((2, 2, 1), 4): 336,
        ((2, 1, 1, 1), 7): 2240,
        ((1, 1, 1, 1, 1), 10): 1792,
    }
    for a in range(65):
        for b in range(65 - a):
            c = 64 - a - b
            if 4 * a + 7 * b + 10 * c == 448:
                assert 2 * a + b == 64 and c == a
                if b == 0:
                    assert a == c == 32
