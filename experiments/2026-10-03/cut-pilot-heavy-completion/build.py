# Document:    Exact Strengthened Completion of the Cut-Pilot Heavy Tuple
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      85b19b7a21027d21392f2a9a90014eb604459306417279f9e56ca78258897dcc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = HERE.parent / "lookahead-heavy-strengthened"
PILOT = HERE.parent / "four-seven-template-cut-pilot"
RAW = ROOT / "experiments/scratch/cut-pilot-heavy-completion-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    assert not RAW.exists(), "new output required; no old experiment is replaced"
    seed = PILOT / "cycle-raw-best.txt"
    pilot_audit = load(PILOT / "audit.json")
    assert pilot_audit["passed"] and pilot_audit["raw_best"]["sha256"] == sha(seed)
    assert pilot_audit["checker_sha256"] == sha(PILOT / "audit.py")
    assert sha(seed) == "b48c3ce6653c92936ff824fc2d68e29b0ba080c985378c9c85b02418e6849c93"
    blocks = [tuple(map(int, line.split())) for line in seed.read_text().splitlines()]
    universe = list(it.combinations(range(1, 17), 5))
    ids = {b: i for i, b in enumerate(universe)}
    assert len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks)
    assert set(blocks) <= set(universe)
    assert Counter(p for b in blocks for p in b) == {p: 20 for p in range(1, 17)}
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    groups = [[b for b in blocks if a <= set(b)] for a in anchors]
    assert all(len(g) == 7 for g in groups)
    heavy = sorted({b for g in groups for b in g})
    assert len(heavy) == 28
    for anchor, group in zip(anchors, groups, strict=True):
        assert Counter(p for b in group for p in set(b) - anchor) == {
            p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor
        }
    ordinary = [b for b in universe if all(len(set(b) & a) <= 1 for a in anchors)]
    assert len(ordinary) == 1200 and set(blocks) - set(heavy) <= set(ordinary)
    assert all(all(len(set(b) & a) in (0, 1, 3) for a in anchors) for b in heavy)
    seed_triples = {t for b in blocks for t in it.combinations(b, 3)}
    assert len(seed_triples) == 550
    previous = load(PRIOR / "manifest.json")
    source_model = ROOT / previous["model"]
    assert sha(source_model) == previous["model_sha256"]
    base_manifest_path = ROOT / previous["base_manifest"]
    assert sha(base_manifest_path) == previous["base_manifest_sha256"]
    old_heavy = list(map(tuple, load(base_manifest_path)["heavy_blocks"]))
    prior_gate = HERE.parent / "native-ten-hole-completion-independent/strengthened-audit.json"
    gate = load(prior_gate)
    assert gate["passed"] and gate["model_sha256"] == sha(source_model)
    source = cp_model_pb2.CpModelProto()
    text_format.Parse(source_model.read_text(), source)
    assert len(source.variables) == 1200 and len(source.constraints) == 697
    assert [v.name for v in source.variables] == [f"block_{ids[b]}" for b in ordinary]
    proto = cp_model_pb2.CpModelProto()
    proto.CopyFrom(source)
    subsets = [()] + list(it.combinations(range(1, 17), 3))
    subsets += [(p,) for p in range(1, 17)] + list(it.combinations(range(1, 17), 2))
    assert len(subsets) == 697
    shifts = []
    for index, subset in enumerate(subsets):
        old_count = sum(set(subset) <= set(b) for b in old_heavy)
        new_count = sum(set(subset) <= set(b) for b in heavy)
        delta = old_count - new_count
        shifts.append(delta)
        row = proto.constraints[index].linear
        assert len(row.domain) == 2
        row.domain[0] += delta
        if row.domain[1] != cp_model.INT_MAX:
            row.domain[1] += delta
    restored = cp_model_pb2.CpModelProto()
    restored.CopyFrom(proto)
    for constraint, delta in zip(restored.constraints, shifts, strict=True):
        constraint.linear.domain[0] -= delta
        if constraint.linear.domain[1] != cp_model.INT_MAX:
            constraint.linear.domain[1] -= delta
    assert restored == source, "only the fixed-heavy bound shifts may change"
    model = cp_model.CpModel()
    model.proto.parse_text_format(text_format.MessageToString(proto))
    assert not model.validate()
    RAW.mkdir(parents=True)
    model_path = RAW / "model.pbtxt"
    model_path.write_text(text_format.MessageToString(proto))
    sidecar = load(PILOT / "cycle-raw-best.txt.lookahead.json")
    orbit = HERE.parent / "lookahead-cut-orbit/cut-pilot-best-audit.json"
    orbit_audit = load(orbit)
    assert orbit_audit["passed"] and orbit_audit["witness_sha256"] == sha(seed)
    for path in [HERE / "seed.txt", RAW / "seed.txt"]:
        path.write_bytes(seed.read_bytes())
    manifest = {
        "version": "v1.0.0",
        "builder_sha256": sha(Path(__file__)),
        "source_revision_sha256": sha(Path(__file__)),
        "ortools_version": ortools_version,
        "source_seed": str(seed.relative_to(ROOT)),
        "source_seed_sha256": sha(seed),
        "source_pilot_audit_sha256": sha(PILOT / "audit.json"),
        "source_native_sha256": pilot_audit["source_sha256"],
        "source_orbit_audit_sha256": sha(orbit),
        "source_model": str(source_model.relative_to(ROOT)),
        "source_model_sha256": sha(source_model),
        "source_manifest_sha256": sha(PRIOR / "manifest.json"),
        "source_builder_sha256": sha(PRIOR / "build.py"),
        "source_gate_sha256": sha(prior_gate),
        "model": str(model_path.relative_to(ROOT)),
        "model_sha256": sha(model_path),
        "variables": 1200,
        "rows": 697,
        "fixed_heavy_blocks": heavy,
        "fixed_heavy_global_ids": [ids[b] for b in heavy],
        "ordinary_global_ids": [ids[b] for b in ordinary],
        "template_ids_1based": sidecar["template_ids_1based"],
        "seed_holes": 10,
        "target_blocks": 64,
        "selected_ordinary": 36,
        "degree_rows": 16,
        "triple_rows": 560,
        "nonheavy_triple_upper_bounds": 556,
        "anchor_pair_equalities": 114,
        "hub_pair_bound_rows": 6,
        "all_six_hub_graphs_retained": True,
        "fixed_heavy_shifts_only": True,
        "ordinary_blocks_fixed": 0,
        "hints": False,
        "objective": False,
        "source_orbit_violations": orbit_audit["violated_maps"],
        "solve_launched": False,
        "scope": "Only this new fixed-heavy tuple in the regular degree20 four-sevenfold family. "
        "Passing the old cut orbit adds no restriction and is not proof of a completion.",
    }
    for path in [HERE / "manifest.json", RAW / "manifest.json"]:
        path.write_text(json.dumps(manifest, indent=2) + "\n")
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                k: manifest[k]
                for k in [
                    "variables",
                    "rows",
                    "model_sha256",
                    "template_ids_1based",
                    "source_seed_sha256",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
