# Document:    Independent Cycle Heavy Completion Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount the partial seed and check exactly 28 heavy-block fixes."""

import copy
import gzip
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "cycle-soft-heavy-completion"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(proto, base, ids):
    require(len(proto.variables) == 4768 and len(proto.constraints) == 4298, "dimensions")
    restored = copy.deepcopy(proto)
    del restored.constraints[4270:]
    require(restored == base, "base changed")
    for row, index in zip(proto.constraints[4270:], ids, strict=True):
        expected = cp_model_pb2.ConstraintProto()
        expected.linear.vars.append(index)
        expected.linear.coeffs.append(1)
        expected.linear.domain.extend([1, 1])
        require(row == expected, "heavy equality differs")


def main():
    meta = json.loads((INPUT / "manifest.json").read_text())
    require(sha(INPUT / "build.py") == meta["builder_sha256"], "builder changed")
    seed_path = ROOT / meta["source_seed"]
    require(sha(seed_path) == meta["source_seed_sha256"], "seed changed")
    blocks = [tuple(map(int, line.split())) for line in seed_path.read_text().splitlines()]
    require(len(set(blocks)) == len(blocks) == 64 and
            all(len(b) == len(set(b)) == 5 and tuple(sorted(b)) == b and
                all(1 <= p <= 16 for p in b) for b in blocks), "malformed seed")
    triples = Counter(t for b in blocks for t in itertools.combinations(b, 3))
    pairs = Counter(p for b in blocks for p in itertools.combinations(b, 2))
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    heavy = sorted(b for b in blocks if any(a <= set(b) for a in anchors))
    require(len(heavy) == 28 and sum(1 for p in range(1, 17)
                                    if sum(p in b for b in blocks) == 20) == 16,
            "seed degrees or heavy count")
    hole_count = 560 - len(triples)
    pair_error = 0
    cycle_edges = {(4, 8), (8, 12), (12, 16), (4, 16)}
    for p in itertools.combinations(range(1, 17), 2):
        target = 5
        if any(set(p) <= a for a in anchors):
            target = 7
        elif any(4 * g + 4 in p and bool(set(p) & a) for g, a in enumerate(anchors)):
            target = 6
        elif p in cycle_edges:
            target = 6
        pair_error += abs(pairs[p] - target)
    anchor_triples = {tuple(sorted(a)) for a in anchors}
    over = sum(max(0, value - 2) for t, value in triples.items() if t not in anchor_triples)
    score = 5 * hole_count + pair_error + 5 * over
    require(hole_count == meta["seed_holes"] == 12 and score == meta["seed_score"] == 92,
            "seed score differs")
    catalog_path = ROOT / meta["source_catalog"]
    require(sha(catalog_path) == meta["source_catalog_sha256"], "catalog changed")
    catalogs = json.loads(gzip.decompress(catalog_path.read_bytes()))
    for group, anchor in enumerate(anchors):
        edges = sorted(sorted(set(b) - anchor) for b in heavy if anchor <= set(b))
        require(len(edges) == 7 and edges ==
                catalogs[group]["templates"][meta["template_ids_1based"][group] - 1],
                "template identity differs")
    universe = list(itertools.combinations(range(1, 17), 5))
    ids = [universe.index(b) for b in heavy]
    require(ids == meta["fixed_ids"] and [list(b) for b in heavy] == meta["fixed_blocks"],
            "fixed block identity")
    base_path, model_path = ROOT / meta["source_base"], ROOT / meta["model"]
    require(sha(base_path) == meta["source_base_sha256"] ==
            "5cbaba3a581ab485a1ebd5adc3a328ff53c963a414fadc773bb9687abead02d9",
            "audited base changed")
    require(sha(model_path) == meta["model_sha256"], "model changed")
    base = text_format.Parse(base_path.read_text(), cp_model_pb2.CpModelProto())
    proto = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
    inspect(proto, base, ids)
    controls = []
    variants = []
    bad = copy.deepcopy(proto)
    bad.variables[0].domain[1] = 2
    variants.append(("base domain", bad))
    bad = copy.deepcopy(proto)
    del bad.constraints[-1]
    variants.append(("missing fix", bad))
    for name, field, value in [("wrong variable", "vars", 0),
                                ("wrong coefficient", "coeffs", -1),
                                ("wrong bound", "domain", 0)]:
        bad = copy.deepcopy(proto)
        getattr(bad.constraints[-1].linear, field)[0] = value
        variants.append((name, bad))
    bad = copy.deepcopy(proto)
    bad.solution_hint.vars.append(0)
    bad.solution_hint.values.append(1)
    variants.append(("new model field", bad))
    for name, bad in variants:
        try:
            inspect(bad, base, ids)
        except ValueError as error:
            controls.append({"control": name, "rejected": str(error)})
        else:
            raise ValueError("damaged model accepted")
    report = {"passed": True, "checker_sha256": sha(Path(__file__)),
              "manifest_sha256": sha(INPUT / "manifest.json"),
              "model_sha256": sha(model_path), "source_base_sha256": sha(base_path),
              "seed_sha256": sha(seed_path), "seed_holes": hole_count, "seed_score": score,
              "pair_l1": pair_error, "nonheavy_excess": over,
              "fixed_heavy_blocks": len(ids), "ordinary_blocks_fixed": 0,
              "variables": 4768, "constraints": 4298, "damaged_controls": controls,
              "scope": "One four-template combination only. All ordinary completion choices free. "
              "No solver call and no exclusion or covering witness."}
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
