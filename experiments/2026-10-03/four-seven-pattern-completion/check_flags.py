# Document:    Raw Fixed Double Pattern Flag Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check all400 appended flag-fixing rows from frozen protobuf and raw triples."""

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(directory):
    model_path = directory / "model.pbtxt"
    model = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
    metadata = json.loads((directory / "metadata.json").read_text())
    raw_pattern = (directory / "pattern.txt").read_text()
    pattern = [tuple(map(int, row.split())) for row in raw_pattern.splitlines() if row.strip()]
    require(len(pattern) == 44 and len(set(pattern)) == 44, "need44 distinct triples")
    anchors = ({1, 2, 3}, {5, 6, 7}, {9, 10, 11}, {13, 14, 15})
    triples = list(combinations(range(1, 17), 3))
    eligible = [i for i, t in enumerate(triples)
                if all(len(set(t) & a) <= 1 for a in anchors)]
    require(set(pattern).issubset({triples[i] for i in eligible}), "ineligible pattern")
    require(len(model.variables) == 4768 and len(model.constraints) == 4670, "wrong sizes")
    require(all(list(v.domain) == [0, 1] for v in model.variables), "wrong domain")
    require(all(c.WhichOneof("constraint") == "linear" and not c.enforcement_literal
                for c in model.constraints), "unexpected constraint type")
    require([v.name for v in model.variables[:4368]]
            == [f"block_{i}" for i in range(4368)], "wrong block order")
    require([v.name for v in model.variables[4368:]]
            == [f"double_triple_{i}" for i in eligible], "wrong flag order")
    for offset, tid in enumerate(eligible):
        row = model.constraints[4270 + offset].linear
        target = int(triples[tid] in pattern)
        require(list(row.vars) == [4368 + offset] and list(row.coeffs) == [1]
                and list(row.domain) == [target, target], "incorrect fixing row")
    require(hashlib.sha256(model_path.read_bytes()).hexdigest() == metadata["model_sha256"],
            "model hash mismatch")
    require(hashlib.sha256(raw_pattern.encode()).hexdigest() == metadata["pattern_sha256"],
            "pattern hash mismatch")
    for filename, digest in metadata["sources"].items():
        require(hashlib.sha256((directory / filename).read_bytes()).hexdigest() == digest,
                "source snapshot hash mismatch")
    return {"passed": True, "fixed_rows_checked": 400, "selected_flags": 44,
            "variables": 4768, "rows": 4670,
            "model_sha256": metadata["model_sha256"],
            "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope": "Raw audit of the400 fixing rows and variable order. "
            "This does not independently re-audit the4270 earlier rows or prove infeasibility."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(args.directory)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
