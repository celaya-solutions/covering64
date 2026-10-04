# Document:    Proved Fixed-Heavy Pair and Triple Strengthening
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      ca07f4dade7260849a964020cf2ef087264bc3290ac8000d65c1e00074c9dbec
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools as it
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent / "lookahead-heavy-completion"
RAW = ROOT / "experiments/scratch/lookahead-heavy-strengthened-v1.0.0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not RAW.exists()
    prior = json.loads((BASE / "manifest.json").read_text())
    gate = HERE.parent / "native-ten-hole-completion-independent/audit.json"
    audit = json.loads(gate.read_text())
    assert audit["passed"] and prior["model_sha256"] == audit["model_sha256"]
    source = ROOT / prior["model"]
    assert sha(source) == prior["model_sha256"]
    heavy = list(map(tuple, prior["heavy_blocks"]))
    ordinary = list(map(tuple, prior["ordinary_blocks"]))
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    hubs = [4, 8, 12, 16]
    pairs = list(it.combinations(range(1, 17), 2))
    triples = list(it.combinations(range(1, 17), 3))
    heavy_triples = {tuple(sorted(a)) for a in anchors}
    counts = Counter(t for b in heavy for t in it.combinations(b, 3))
    pair_counts = Counter(p for b in heavy for p in it.combinations(b, 2))
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(source.read_text(), proto)
    assert len(proto.variables) == 1200 and len(proto.constraints) == 577
    for i, triple in enumerate(triples):
        if triple not in heavy_triples:
            proto.constraints[1 + i].linear.domain[1] = 2 - counts[triple]
    pair_domains = []
    for pair in pairs:
        anchor_points = [p for p in pair if p not in hubs]
        if not anchor_points:
            lower, upper = 5, 7
        else:
            point = anchor_points[0]
            other = pair[1] if pair[0] == point else pair[0]
            anchor = anchors[(point - 1) // 4]
            lower = upper = 7 if other in anchor else 6 if other == max(anchor) + 1 else 5
        row = proto.constraints.add().linear
        ids = [i for i, b in enumerate(ordinary) if set(pair) <= set(b)]
        row.vars.extend(ids)
        row.coeffs.extend([1] * len(ids))
        row.domain.extend([lower - pair_counts[pair], upper - pair_counts[pair]])
        pair_domains.append([list(pair), lower, upper])
    assert len(proto.constraints) == 697
    restored = cp_model_pb2.CpModelProto()
    restored.CopyFrom(proto)
    del restored.constraints[577:]
    for i in range(560):
        restored.constraints[1 + i].linear.domain[1] = cp_model.INT_MAX
    base_proto = cp_model_pb2.CpModelProto()
    text_format.Parse(source.read_text(), base_proto)
    assert restored == base_proto
    model = cp_model.CpModel()
    model.proto.parse_text_format(text_format.MessageToString(proto))
    assert not model.validate()
    RAW.mkdir(parents=True)
    path = RAW / "model.pbtxt"
    path.write_text(text_format.MessageToString(proto))
    manifest = {
        "version": "v1.0.0",
        "builder_sha256": sha(Path(__file__)),
        "base_manifest": str((BASE / "manifest.json").relative_to(ROOT)),
        "base_manifest_sha256": sha(BASE / "manifest.json"),
        "source_model_sha256": sha(source),
        "source_gate_sha256": sha(gate),
        "model": str(path.relative_to(ROOT)),
        "model_sha256": sha(path),
        "variables": 1200,
        "rows": 697,
        "anchor_pair_equalities": 114,
        "hub_pair_bounds": 6,
        "nonheavy_triple_upper_bounds": 556,
        "pair_domains_lexicographic": pair_domains,
        "scope": "Proved strengthening for the same regular four-sevenfold fixed-heavy family; "
        "all six hub residual graphs remain allowed.",
    }
    for out in [HERE / "manifest.json", RAW / "manifest.json"]:
        out.write_text(json.dumps(manifest, indent=2) + "\n")
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k: manifest[k] for k in ["variables", "rows", "model_sha256"]}))


if __name__ == "__main__":
    main()
