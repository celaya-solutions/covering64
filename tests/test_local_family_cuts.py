# Document:    Local Family Cut Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import copy
import importlib.util
import json
from pathlib import Path

import pytest
from google.protobuf import text_format
from ortools.sat import cp_model_pb2

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CUTS = load("local_family_cuts")
BUILDER = load("first_family_search")


@pytest.fixture(scope="module")
def model(tmp_path_factory):
    data = json.loads(
        (ROOT / "experiments/2026-10-03/local-template-orbits/first-families.json").read_text()
    )
    record = next(row for row in data["representatives"] if row["id"] == "r4-000")
    _, original, _, _ = BUILDER.build_model(
        [tuple(b) for b in record["quadruples"]],
        14,
        require_outside_pair_bound=False,
        require_opposite_spoke=False,
    )
    path = tmp_path_factory.mktemp("local-cuts") / "model.pbtxt"
    original.ExportToFile(str(path))
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(path.read_text(), proto)
    return proto


def test_all_classified_families_and_damaged_family():
    path = ROOT / "experiments/2026-10-03/local-family-root-audit/replay.json"
    result = CUTS.audit_classification(path)
    assert result["families"] == 88
    assert result["maximum_pair_count"] == 2
    assert result["maximum_triple_count"] == 1
    data = json.loads(path.read_text())
    family = next(p["families"][0] for p in data["patterns"] if p["families"])
    with pytest.raises(ValueError, match="distinct"):
        CUTS.family_audit(family[:-1] + [family[0]])


def test_cut_rows_are_idempotent_and_preserve_relaxed_hint(model):
    changed = copy.deepcopy(model)
    first = CUTS.add_cuts(changed)
    assert first["cuts_added"] == 728
    assert CUTS.add_cuts(changed)["cuts_added"] == 0
    path = ROOT / "experiments/2026-10-03/first-family-independent/normalized-h14.txt"
    blocks = {tuple(map(int, line.split())) for line in path.read_text().splitlines()}
    selected = {i for i, b in enumerate(CUTS.BLOCKS) if b in blocks}
    for terms, upper in CUTS.expected_cuts():
        assert sum(n for i, n in terms if i in selected) <= upper


def test_unjustified_model_cannot_receive_cuts(model):
    damaged = copy.deepcopy(model)
    fixed = next(
        i
        for i, row in enumerate(damaged.constraints)
        if row.HasField("linear")
        and list(row.linear.vars) == [0]
        and list(row.linear.domain) == [1, 1]
    )
    del damaged.constraints[fixed]
    with pytest.raises(ValueError, match="assumption"):
        CUTS.add_cuts(damaged)
    damaged = copy.deepcopy(model)
    damaged.variables[0].name = "wrong_order"
    with pytest.raises(ValueError, match="lexicographic"):
        CUTS.add_cuts(damaged)
