# Document:    Independent Partial Candidate Normalization Audit
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount all mapped incidences and audit all relaxed rows without a solver."""

import argparse
import copy
import hashlib
import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]
import check_hint as hint_audit  # noqa: E402
import check_relaxed_hint as relaxed_audit  # noqa: E402
import first_family_search as builder  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", type=Path, default=HERE / "normalized-h5.json")
    args = parser.parse_args()
    record = json.loads(args.record.read_text())
    hole_count = len(record["package"]["uncovered"])
    original = [tuple(map(int, line.split()))
                for line in Path(record["source"]).read_text().splitlines()]
    normalized = [tuple(map(int, line.split()))
                  for line in args.record.with_suffix(".txt").read_text().splitlines()]
    mapping = {int(k): v for k, v in record["point_map"].items()}

    def check_map(point_map):
        if sorted(point_map) != list(range(1, 17)):
            raise ValueError("mapping input labels are not complete")
        if sorted(point_map.values()) != list(range(1, 17)):
            raise ValueError("mapping is not a permutation")
        transformed = sorted(tuple(sorted(point_map[p] for p in b)) for b in original)
        if transformed != sorted(normalized) or len(set(normalized)) != 64:
            raise ValueError("mapped block list differs or contains duplicates")
        for size in (1, 2, 3):
            before = Counter(t for b in original for t in combinations(b, size))
            after = Counter(t for b in normalized for t in combinations(b, size))
            for t in combinations(range(1, 17), size):
                if before[t] != after[tuple(sorted(point_map[p] for p in t))]:
                    raise ValueError("mapped incidence differs")

    check_map(mapping)
    damaged = dict(mapping)
    damaged[1], damaged[2] = damaged[2], damaged[1]
    try:
        check_map(damaged)
    except ValueError:
        damaged_map_rejected = True
    else:
        raise ValueError("damaged point map accepted")
    family = [tuple(p for p in b if p != 1) for b in normalized
              if set(b) & {1, 2, 3} == {1}]
    _, model, _, _ = builder.build_model(
        family, hole_count, require_outside_pair_bound=False, require_opposite_spoke=False,
    )
    values = hint_audit.values_for(normalized, model.proto)
    for i, value in enumerate(values):
        model.add_hint(model.get_int_var_from_proto_index(i), value)
    output = ROOT / "experiments/scratch" / f"{args.record.stem}-audit-20261003"
    output.mkdir(parents=True, exist_ok=True)
    model_path = output / "model.pbtxt"
    model.export_to_file(str(model_path))
    proto = relaxed_audit.audit.load_model(model_path)
    rows = relaxed_audit.verify_relaxed(proto, family, hole_count)
    hint_audit.verify_hint(proto, values)
    damaged = copy.deepcopy(proto)
    damaged.solution_hint.values[0] = 1 - damaged.solution_hint.values[0]
    try:
        hint_audit.verify_hint(damaged, values)
    except ValueError:
        damaged_hint_rejected = True
    else:
        raise ValueError("damaged hint accepted")
    result = {
        "status": "VERIFIED_POINT_MAP_ALL_INCIDENCES_RELAXED_ROWS_AND_HINT",
        "representative": record["representative"], "point_map": mapping,
        "mapped_incidence_counts_checked": 16 + 120 + 560,
        "rows": rows, "hint_values_checked": len(values), "holes": sum(values[4368:4928]),
        "canonical_sha256": record["package"]["canonical_sha256"],
        "damaged_map_rejected": damaged_map_rejected,
        "damaged_hint_rejected": damaged_hint_rejected,
        "model_path": str(model_path.relative_to(ROOT)),
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                    [Path(__file__), HERE / "normalize_partial.py", HERE / "check_hint.py",
                     HERE / "check_relaxed_hint.py", HERE / "check.py",
                     ROOT / "scripts/first_family_search.py"]},
        "scope": "One partial candidate and explicit relaxed model; no cover or theorem claim.",
    }
    args.record.with_name(f"{args.record.stem}-audit.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["status", "representative", "holes",
                                           "canonical_sha256", "point_map"]}))


if __name__ == "__main__":
    main()
