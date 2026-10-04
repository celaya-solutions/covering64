# Document:    Affine Circle Incidence Necessary Relaxation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      56c28b2edb15dd1333f20d1f2306b6bd60894bb26e6c0083e9dd57d2a5ac70f3
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Build a necessary incidence relaxation of the original288-block pool."""

import hashlib
import itertools
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/affine-circle-incidence-relaxation-20261003"
SOURCE = HERE.parent / "affine-extension-independent/pool.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def construct():
    data = json.loads(SOURCE.read_text())
    circles = list(map(tuple, data["circles"]))
    lines = list(map(tuple, data["lines"]))
    assert len(circles) == len(set(circles)) == 48
    assert len(lines) == len(set(lines)) == 20
    assert all(tuple(sorted(set(c))) == c and len(c) == 5 for c in circles)
    assert all(tuple(sorted(set(line))) == line and len(line) == 4 for line in lines)
    assert all(set(c) <= set(range(1, 17)) for c in circles + lines)
    extensions = {
        tuple(sorted((*line, p))) for line in lines for p in range(1, 17) if p not in line
    }
    assert len(extensions) == 240 and not set(circles) & extensions
    pool = sorted(set(circles) | extensions)
    universe = list(itertools.combinations(range(1, 17), 5))
    global_ids = {block: i for i, block in enumerate(universe)}
    local_ids = {block: i for i, block in enumerate(pool)}
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{global_ids[b]}") for b in pool]
    model.add(sum(variables) == 64)
    line_rows = []
    for line in lines:
        support = [i for i, b in enumerate(pool) if set(line) <= set(b)]
        assert len(support) == 12 and all(pool[i] in extensions for i in support)
        model.add(sum(variables[i] for i in support) >= 1)
        line_rows.append(support)
    circle_rows = []
    for circle in circles:
        support = [
            i for i, b in enumerate(pool) if b in extensions and len(set(circle) & set(b)) == 3
        ]
        assert len(support) == 30
        for b in extensions:
            hits = sum(set(t) <= set(b) for t in itertools.combinations(circle, 3))
            assert hits == int(len(set(circle) & set(b)) == 3)
        model.add(10 * variables[local_ids[circle]] + sum(variables[i] for i in support) >= 10)
        circle_rows.append({"circle_local_id": local_ids[circle], "extensions": support})
    assert all(
        sum(i in row["extensions"] for row in circle_rows) == 6
        for i, b in enumerate(pool)
        if b in extensions
    )
    assert len(model.proto.variables) == 288 and len(model.proto.constraints) == 69
    assert not model.validate()
    payload = {
        "circles": circles,
        "lines": lines,
        "pool": [
            {
                "local_id": i,
                "global_id": global_ids[b],
                "block": b,
                "kind": "circle" if b in circles else "extension",
            }
            for i, b in enumerate(pool)
        ],
        "line_rows": line_rows,
        "circle_rows": circle_rows,
    }
    return model, payload


def main():
    assert not RAW.exists(), "preserve frozen model directory"
    model, pool = construct()
    RAW.mkdir(parents=True)
    model_path = RAW / "exact64-incidence-relaxation.pbtxt"
    assert model.export_to_file(str(model_path))
    (RAW / "pool.json").write_text(json.dumps(pool, indent=2) + "\n")
    (RAW / "build.py").write_bytes(Path(__file__).read_bytes())
    (RAW / "source-pool.json").write_bytes(SOURCE.read_bytes())
    manifest = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "builder_sha256": digest(Path(__file__)),
        "source_pool_sha256": digest(SOURCE),
        "pool_sha256": digest(RAW / "pool.json"),
        "model_sha256": digest(model_path),
        "ortools_version": ortools.__version__,
        "variables": 288,
        "constraints": 69,
        "exact_cardinality_rows": 1,
        "line_rows": 20,
        "circle_rows": 48,
        "model": str(model_path.relative_to(ROOT)),
        "scope": "Necessary incidence relaxation of original48-circle plus240-extension pool. "
        "Selected Boolean block variables in global lexicographic order. A retained circle "
        "satisfies its own row; a deleted circle requires at least10 selected extension "
        "incidences. Repeated coverage of the same triple is allowed by these rows.",
        "global_lower_bound_claim": False,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
