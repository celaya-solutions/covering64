# Document:    Independent Relaxed Partial Hint Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Verify only the requested pair and opposite-spoke rows are removed."""

import argparse
import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("hint_audit", HERE / "check_hint.py")
hint_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hint_audit)
audit = hint_audit.audit


def verify_relaxed(model, family, max_missing):
    variables, expected = audit.expected_model(family, max_missing)
    removed = []
    for pair in audit.PAIRS:
        terms = [(i, 1) for i, b in enumerate(audit.BLOCKS) if set(pair) <= set(b)]
        row = audit.linear(terms, 5, audit.LIMIT)
        audit.require(expected[row] == 1, "outside-pair row not unique")
        del expected[row]
        removed.append(row)
    names = {name: i for i, (name, _) in enumerate(variables)}
    opposite = audit.linear([(names[f"local_hole_{a}_(4, 6)"], 1) for a in (2, 3)], 1, audit.LIMIT)
    audit.require(expected[opposite] == 1, "opposite-spoke row not unique")
    del expected[opposite]
    removed.append(opposite)
    audit.require(
        [(v.name, tuple(v.domain)) for v in model.variables] == variables,
        "relaxed mode changed variables",
    )
    actual = Counter(audit.actual_row(row) for row in model.constraints)
    audit.require(actual == expected, "relaxed mode removed or changed unintended rows")
    objective = model.objective
    audit.require(
        dict(zip(objective.vars, objective.coeffs)) == {i: 1 for i in range(4368, 4928)}
        and objective.offset == 0
        and objective.scaling_factor == 1,
        "relaxed objective is not exact hole count",
    )
    return {
        "variables": len(variables),
        "constraints": sum(expected.values()),
        "removed_constraints": len(removed),
        "outside_pair_rows_removed": 78,
        "opposite_spoke_rows_removed": 1,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, default=HERE / "relaxed-hint-result.json")
    args = parser.parse_args()
    metadata = json.loads((args.run / "metadata.json").read_text())
    for name, digest in metadata["sources"].items():
        audit.require(
            hashlib.sha256((args.run / name).read_bytes()).hexdigest() == digest,
            "saved source hash mismatch",
        )
    path = args.run / "model.pbtxt"
    audit.require(
        hashlib.sha256(path.read_bytes()).hexdigest() == metadata["model_sha256"],
        "model hash mismatch",
    )
    model = audit.load_model(path)
    seed = args.run / "initial.txt"
    raw = seed.read_bytes()
    audit.require(hashlib.sha256(raw).hexdigest() == metadata["hint_sha256"], "hint hash mismatch")
    blocks = [tuple(map(int, line.split())) for line in raw.decode().splitlines()]
    family = sorted(tuple(p for p in b if p != 1) for b in blocks if set(b) & {1, 2, 3} == {1})
    missing = metadata["initial"]["standalone"]["uncovered_count"]
    checked = verify_relaxed(model, family, missing)
    values = hint_audit.values_for(blocks, model)
    hint_audit.verify_hint(model, values)
    audit.require(sum(values[4368:4928]) == missing, "relaxed hint objective mismatch")
    controls = []
    for name in ("extra_missing_row", "bad_objective", "bad_hint"):
        damaged = copy.deepcopy(model)
        if name == "extra_missing_row":
            del damaged.constraints[0]
        elif name == "bad_objective":
            damaged.objective.coeffs[0] = 2
        else:
            damaged.solution_hint.values[0] = 1 - damaged.solution_hint.values[0]
        try:
            verify_relaxed(damaged, family, missing)
            hint_audit.verify_hint(damaged, values)
        except ValueError:
            controls.append({"name": name, "rejected": True})
        else:
            raise ValueError(f"relaxed damage accepted: {name}")
    result = {
        "status": "VERIFIED_RELAXED_PARTIAL_ROWS_AND_HINT",
        **checked,
        "hint_variables": len(values),
        "hint_holes": missing,
        "controls": controls,
        "model_sha256": metadata["model_sha256"],
        "candidate_sha256": metadata["hint_sha256"],
        "sources": metadata["sources"],
        "audit_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "row_checker_sha256": hashlib.sha256((HERE / "check.py").read_bytes()).hexdigest(),
        "hint_checker_sha256": hashlib.sha256((HERE / "check_hint.py").read_bytes()).hexdigest(),
        "scope": "Explicit relaxed partial optimization; candidate need not satisfy pair lower "
        "bounds or opposite-spoke omission. No full-cover or global negative claim.",
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "constraints": checked["constraints"],
                "removed": checked["removed_constraints"],
                "holes": missing,
            }
        )
    )


if __name__ == "__main__":
    main()
