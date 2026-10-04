# Document:    Fixed Circle Deletion Extension Completion Builder
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import argparse
import hashlib
import itertools
import json
from pathlib import Path

from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
POOL = HERE.parent / "affine-extension-independent/pool.json"


def construct(removed, target=64):
    if (type(target) is not int or not 1 <= target <= 288
            or any(type(i) is not int or not 0 <= i < 48 for i in removed)
            or sorted(set(removed)) != removed):
        raise ValueError("invalid target or circle IDs")
    data = json.loads(POOL.read_text())
    circles = list(map(tuple, data["circles"]))
    lines = list(map(tuple, data["lines"]))
    retained = [circle for i, circle in enumerate(circles) if i not in removed]
    extensions = sorted({tuple(sorted((*line, point))) for line in lines
                         for point in range(1, 17) if point not in line})
    global_ids = {b: i for i, b in enumerate(itertools.combinations(range(1, 17), 5))}
    assert len(extensions) == 240 and len(retained) == 48 - len(removed)
    covered = {t for block in retained for t in itertools.combinations(block, 3)}
    missing = [t for t in itertools.combinations(range(1, 17), 3) if t not in covered]
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{global_ids[b]}") for b in extensions]
    model.add(sum(variables) == target - len(retained))
    # Keep one coverage row per uncovered triple; redundant identical line
    # rows are intentionally retained so the model is transparent to audit.
    for triple in missing:
        ids = [i for i, block in enumerate(extensions) if set(triple) <= set(block)]
        assert len(ids) in (3, 12)
        model.add(sum(variables[i] for i in ids) >= 1)
    assert len(missing) == 80 + 10 * len(removed)
    return model, {"removed_circle_ids_zero_based": removed, "target": target,
                   "extension_count": target - len(retained), "extensions": extensions,
                   "retained_circles": retained, "missing_triples": missing,
                   "scope": "Only this fixed retained-circle family in the 288-block pool"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("removed", help="comma-separated zero-based circle IDs, or none")
    parser.add_argument("output", type=Path)
    parser.add_argument("--target", type=int, default=64)
    args = parser.parse_args()
    removed = [] if args.removed == "none" else [int(x) for x in args.removed.split(",")]
    model, metadata = construct(removed, args.target)
    args.output.mkdir(parents=True, exist_ok=False)
    model_path = args.output / "model.pbtxt"
    assert model.export_to_file(str(model_path))
    metadata.update({"model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                     "pool_sha256": hashlib.sha256(POOL.read_bytes()).hexdigest(),
                     "builder_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    (args.output / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({k: v for k, v in metadata.items()
                      if k not in ("extensions", "retained_circles", "missing_triples")}))


if __name__ == "__main__":
    main()
