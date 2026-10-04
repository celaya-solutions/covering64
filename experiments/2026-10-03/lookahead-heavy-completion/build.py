# Document:    Hub-Unrestricted Fixed-Heavy Completion Builder
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      d18e5ced492a654ca251fc260f57e08ac9c7081123f4463367ff6940a0d983d3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Fix the audited heavy tuple and freely select 36 of all 1,200 ordinary blocks."""

import hashlib
import itertools as it
import json
import subprocess
from collections import Counter
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/lookahead-heavy-completion-v1.0.0"
SOURCE = (
    ROOT
    / "experiments/scratch/four-seven-template-native-lookahead-v1.2.0/pilots/cycle-raw-best.txt"
)
SEED_SHA = "8bfb962deaeeede2032d9efac1783f7eaabde38aada16c8f5fecdd2f19f84ef3"
AUDIT = HERE.parent / "four-seven-template-native-lookahead/pilot-audit.json"
SUMMARY = HERE.parent / "four-seven-template-native-lookahead/summary.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def construct(blocks):
    universe = list(it.combinations(range(1, 17), 5))
    require(len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks), "seed inventory")
    require(set(blocks) <= set(universe), "seed labels")
    require(Counter(p for b in blocks for p in b) == {p: 20 for p in range(1, 17)}, "seed degrees")
    anchors = [set(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
    groups = [[b for b in blocks if a <= set(b)] for a in anchors]
    require(all(len(g) == 7 for g in groups), "heavy group inventory")
    heavy = sorted({b for g in groups for b in g})
    require(len(heavy) == 28, "heavy inventory")
    for anchor, group in zip(anchors, groups, strict=True):
        require(
            Counter(p for b in group for p in set(b) - anchor)
            == {p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor},
            "heavy outside degrees",
        )
    ordinary = [b for b in universe if all(len(set(b) & a) <= 1 for a in anchors)]
    require(len(ordinary) == 1200 and not set(ordinary) & set(heavy), "ordinary universe")
    require(set(blocks) - set(heavy) <= set(ordinary), "seed ordinary legality")
    triple_counts = Counter(t for b in heavy for t in it.combinations(b, 3))
    degrees = Counter(p for b in heavy for p in b)
    global_ids = {b: i for i, b in enumerate(universe)}
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{global_ids[b]}") for b in ordinary]
    model.add(sum(variables) == 36)
    # Include every triple, even rows that are already satisfied by fixed heavy blocks.
    for triple in it.combinations(range(1, 17), 3):
        selected = [variables[i] for i, b in enumerate(ordinary) if set(triple) <= set(b)]
        if selected:
            model.add_linear_constraint(sum(selected), 1 - triple_counts[triple], cp_model.INT_MAX)
        else:
            row = model.proto.constraints.add().linear
            row.domain.extend([1 - triple_counts[triple], cp_model.INT_MAX])
    for point in range(1, 17):
        model.add(
            sum(variables[i] for i, b in enumerate(ordinary) if point in b) == 20 - degrees[point]
        )
    require(not model.validate(), "model validation")
    return model, {
        "heavy_blocks": heavy,
        "heavy_global_ids": [global_ids[b] for b in heavy],
        "ordinary_blocks": ordinary,
        "ordinary_global_ids": [global_ids[b] for b in ordinary],
        "heavy_degrees": [degrees[p] for p in range(1, 17)],
        "heavy_uncovered_triples": sum(
            triple_counts[t] == 0 for t in it.combinations(range(1, 17), 3)
        ),
    }


def main():
    require(not RAW.exists(), "output exists; do not overwrite")
    require(sha(SOURCE) == SEED_SHA, "seed changed")
    summary = json.loads(SUMMARY.read_text())
    require(sha(AUDIT) == summary["pilot_audit_sha256"], "primary audit changed")
    blocks = [tuple(map(int, line.split())) for line in SOURCE.read_text().splitlines()]
    holes = set(it.combinations(range(1, 17), 3)) - {
        t for b in blocks for t in it.combinations(b, 3)
    }
    require(len(holes) == 10, "seed hole count")
    model, metadata = construct(blocks)
    require(
        len(model.proto.variables) == 1200 and len(model.proto.constraints) == 577, "dimensions"
    )
    RAW.mkdir(parents=True)
    path = RAW / "model.pbtxt"
    require(model.export_to_file(str(path)), "model export")
    (HERE / "seed.txt").write_bytes(SOURCE.read_bytes())
    (RAW / "seed.txt").write_bytes(SOURCE.read_bytes())
    metadata.update(
        {
            "version": "v1.0.0",
            "builder_sha256": sha(Path(__file__)),
            "source_seed": str(SOURCE.relative_to(ROOT)),
            "source_seed_sha256": SEED_SHA,
            "source_audit": str(AUDIT.relative_to(ROOT)),
            "source_audit_sha256": sha(AUDIT),
            "source_summary_sha256": sha(SUMMARY),
            "seed_holes": len(holes),
            "model": str(path.relative_to(ROOT)),
            "model_sha256": sha(path),
            "ortools_version": ortools.__version__,
            "git_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "variables": 1200,
            "rows": 577,
            "fixed_heavy": 28,
            "selected_ordinary": 36,
            "triple_rows": 560,
            "degree_rows": 16,
            "pair_rows": 0,
            "hints": False,
            "objective": False,
            "scope": "Only this fixed heavy tuple and native 1,200 ordinary-block family; "
            "all hub pair patterns remain free.",
        }
    )
    for output in [HERE / "manifest.json", RAW / "manifest.json"]:
        output.write_text(json.dumps(metadata, indent=2) + "\n")
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                k: metadata[k]
                for k in ["variables", "rows", "model_sha256", "heavy_uncovered_triples"]
            }
        )
    )


if __name__ == "__main__":
    main()
