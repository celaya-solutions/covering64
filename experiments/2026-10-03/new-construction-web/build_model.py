# Document:    Exact64 Model over Two Steiner Quadruple Extension Pools
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      864beeac8f2b0ee1c7e0ddd6d5c01bf2f232939b134e70ac48b01aa580298beb
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Export only the gated union-pool exact64 feasibility model; do not solve."""

import hashlib
import itertools
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/new-construction-web-20261003"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    model_path = RAW / "exact64-sqs-union.pbtxt"
    assert not model_path.exists(), "preserve frozen model"
    audit_path = HERE / "construction-audit.json"
    audit = json.loads(audit_path.read_text())
    pool_path = RAW / "union-pool.json"
    pool_hash = next(row["sha256"] for row in audit["pools"] if row["name"] == "union")
    assert audit["passed"] and pool_hash == digest(pool_path)
    assert audit["source_sha256"] == digest(HERE / "check_sqs_lift.py")
    saved = json.loads(pool_path.read_text())
    rows = saved["pool"]
    universe = list(itertools.combinations(range(1, 17), 5))
    global_ids = [row["global_id"] for row in rows]
    pool = [tuple(row["block"]) for row in rows]
    assert len(rows) == len(set(pool)) == 1744
    assert global_ids == sorted(set(global_ids))
    assert all(
        row["local_id"] == i and universe[row["global_id"]] == pool[i] for i, row in enumerate(rows)
    )
    triples = list(itertools.combinations(range(1, 17), 3))
    supports = [
        [i for i, block in enumerate(pool) if set(triple) <= set(block)] for triple in triples
    ]
    assert [list(t) for t in triples] == saved["triples"] and supports == saved["supports"]
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{global_id}") for global_id in global_ids]
    model.add(sum(variables) == 64)
    for support in supports:
        model.add(sum(variables[i] for i in support) >= 1)
    assert len(model.proto.variables) == 1744 and len(model.proto.constraints) == 561
    assert not model.validate()
    assert model.export_to_file(str(model_path))
    (RAW / "build_model.py").write_bytes(Path(__file__).read_bytes())
    manifest = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "builder_sha256": digest(Path(__file__)),
        "construction_checker_sha256": audit["source_sha256"],
        "construction_audit_sha256": digest(audit_path),
        "pool_sha256": pool_hash,
        "model_sha256": digest(model_path),
        "ortools_version": ortools.__version__,
        "pool_path": str(pool_path.relative_to(ROOT)),
        "model_path": str(model_path.relative_to(ROOT)),
        "variables": 1744,
        "rows": 561,
        "cardinality": 64,
        "coverage_rows": 560,
        "global_block_ids_in_variable_order": global_ids,
        "triple_support_histogram": dict(sorted(Counter(map(len, supports)).items())),
        "extra_incidence_constraints": False,
        "symmetry_constraints": False,
        "fixed_blocks": False,
        "one_extension_per_quadruple_constraint": False,
        "objective": None,
        "proposed_pilot": {"seed": 2026104001, "seconds": 180, "workers": 1, "status": "not_run"},
        "solver_calls": 0,
        "scope": "Exact64 feasibility restricted to the1744 five-block extensions of two specified "
        "nonisomorphic SQS16 seeds. No implication for unrestricted C(16,5,3) from failure.",
        "global_lower_bound_claim": False,
    }
    (HERE / "model-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in manifest.items()
                if key != "global_block_ids_in_variable_order"
            }
        )
    )


if __name__ == "__main__":
    main()
