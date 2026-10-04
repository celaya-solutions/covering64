# Document:    Cycle Soft-Best Heavy-Template Completion Diagnostic
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      061ad98668f43391b35437068138e980e651a8b3aa93a7614fe6edca8af5039d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Fix only 28 heavy blocks in the unchanged audited 4,768-variable cycle base."""

import gzip
import hashlib
import itertools
import json
import subprocess
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/cycle-soft-heavy-completion-v1.0.1"
SOFT = HERE.parent / "four-seven-template-native-soft"
BASE = HERE.parent / "four-seven-template-cp-proposal"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    require(not RAW.exists(), "new preparation required")
    summary = load(SOFT / "summary.json")
    require(sha(SOFT / "pilot-audit.json") == summary["pilot_audit_sha256"], "pilot audit changed")
    require(sha(SOFT / "diagnose.py") == summary["checker_sha256"], "pilot summary checker changed")
    best = next(c for c in summary["cases"] if c["name"] == "cycle")["bests"]["raw"]
    source_seed = SOFT / "cycle-raw-best.txt"
    require(sha(source_seed) == best["sha256"], "best state changed")
    blocks = [tuple(map(int, line.split())) for line in source_seed.read_text().splitlines()]
    require(len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks), "seed inventory")
    require(
        all(
            len(b) == 5 and tuple(sorted(set(b))) == b and all(1 <= p <= 16 for p in b)
            for b in blocks
        ),
        "seed labels",
    )
    require(Counter(p for b in blocks for p in b) == {p: 20 for p in range(1, 17)}, "seed degrees")
    covered = {t for b in blocks for t in itertools.combinations(b, 3)}
    holes = set(itertools.combinations(range(1, 17), 3)) - covered
    require(len(holes) == best["holes"] == 12, "seed hole count")
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    groups = [[b for b in blocks if anchor <= set(b)] for anchor in anchors]
    require(all(len(g) == 7 for g in groups), "heavy template size")
    heavy = sorted({b for g in groups for b in g})
    require(len(heavy) == 28, "heavy template overlap")
    inputs = next(c for c in load(SOFT / "seeds.json")["cases"] if c["name"] == "cycle")
    catalog_path = ROOT / inputs["source_catalog_path"]
    require(sha(catalog_path) == inputs["source_catalog_sha256"], "catalog changed")
    catalogs = json.loads(gzip.decompress(catalog_path.read_bytes()))
    template_ids = []
    for group, (anchor, selected) in enumerate(zip(anchors, groups, strict=True)):
        edges = sorted([sorted(set(b) - anchor) for b in selected])
        matches = [i + 1 for i, t in enumerate(catalogs[group]["templates"]) if sorted(t) == edges]
        require(len(matches) == 1, "heavy template absent or duplicated")
        template_ids.append(matches[0])
    require(template_ids == best["template_ids_1based"], "template identity changed")
    manifest, audit = load(BASE / "manifest.json"), load(BASE / "independent-audit.json")
    require(
        audit["passed"] and sha(BASE / "manifest.json") == audit["manifest_sha256"],
        "base audit changed",
    )
    metadata = next(c for c in manifest["cases"] if c["case"] == "cycle")
    source_base = ROOT / metadata["source_base"]
    require(sha(source_base) == metadata["source_base_sha256"], "cycle base changed")
    original = cp_model_pb2.CpModelProto()
    text_format.Parse(source_base.read_text(), original)
    require(
        len(original.variables) == 4768 and len(original.constraints) == 4270, "base dimensions"
    )
    universe = list(itertools.combinations(range(1, 17), 5))
    ids = {b: i for i, b in enumerate(universe)}
    fixed_ids = [ids[b] for b in heavy]
    proto = cp_model_pb2.CpModelProto()
    proto.CopyFrom(original)
    for index in fixed_ids:
        row = proto.constraints.add().linear
        row.vars.append(index)
        row.coeffs.append(1)
        row.domain.extend([1, 1])
    stripped = cp_model_pb2.CpModelProto()
    stripped.CopyFrom(proto)
    del stripped.constraints[4270:]
    require(stripped == original, "prior proto changed")
    model = cp_model.CpModel()
    model.proto.parse_text_format(text_format.MessageToString(proto))
    require(not model.validate(), "invalid completion model")
    RAW.mkdir(parents=True)
    model_path = RAW / "cycle-heavy-completion.pbtxt"
    model_path.write_text(text_format.MessageToString(proto))
    (HERE / "cycle-seed.txt").write_bytes(source_seed.read_bytes())
    (RAW / "cycle-seed.txt").write_bytes(source_seed.read_bytes())
    result = {
        "version": "v1.0.1",
        "builder_sha256": sha(Path(__file__)),
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "ortools_version": ortools_version,
        "case": "cycle",
        "source_seed": str(source_seed.relative_to(ROOT)),
        "source_seed_sha256": sha(source_seed),
        "seed_holes": 12,
        "seed_score": best["score"],
        "pilot_summary_sha256": sha(SOFT / "summary.json"),
        "pilot_audit_sha256": sha(SOFT / "pilot-audit.json"),
        "template_ids_1based": template_ids,
        "fixed_ids": fixed_ids,
        "fixed_blocks": heavy,
        "source_catalog": str(catalog_path.relative_to(ROOT)),
        "source_catalog_sha256": sha(catalog_path),
        "source_base": str(source_base.relative_to(ROOT)),
        "source_base_sha256": sha(source_base),
        "base_manifest_sha256": sha(BASE / "manifest.json"),
        "base_audit_sha256": sha(BASE / "independent-audit.json"),
        "model": str(model_path.relative_to(ROOT)),
        "model_sha256": sha(model_path),
        "variables": 4768,
        "preserved_rows": 4270,
        "added_equalities": 28,
        "rows": 4298,
        "original_proto_preserved": True,
        "ordinary_blocks_fixed": 0,
        "scope": "Prepared restricted heavy-combination completion diagnostic only. "
        "No solve, exclusion or cover.",
    }
    for path in [HERE / "manifest.json", RAW / "manifest.json"]:
        path.write_text(json.dumps(result, indent=2) + "\n")
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "prepared": True,
                "variables": 4768,
                "rows": 4298,
                "fixed_heavy": 28,
                "template_ids": template_ids,
                "model_sha256": result["model_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
