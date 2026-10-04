# Document:    Frozen First-Link Integer Model Preservation Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Remove exactly seven fixing rows and compare every remaining proto field."""

import argparse
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check(directory):
    metadata = json.loads((directory / "metadata.json").read_text())
    model_path = directory / "model.pbtxt"
    base_path = directory / "base.pbtxt"
    model = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
    base = text_format.Parse(base_path.read_text(), cp_model_pb2.CpModelProto())
    require(len(model.variables) == 4768 and len(model.constraints) == 4277,
            "unexpected full model dimensions")
    require(len(base.variables) == 4768 and len(base.constraints) == 4270,
            "unexpected base dimensions")
    require(len(metadata["fixed_ids"]) == 7 and len(set(metadata["fixed_ids"])) == 7
            and all(type(i) is int and 0 <= i < 4368 for i in metadata["fixed_ids"]),
            "malformed fixed block IDs")
    for offset, index in enumerate(metadata["fixed_ids"]):
        constraint = model.constraints[4270 + offset]
        require(constraint.WhichOneof("constraint") == "linear"
                and not constraint.enforcement_literal, "incorrect fixing row type")
        row = constraint.linear
        require(list(row.vars) == [index] and list(row.coeffs) == [1]
                and list(row.domain) == [1, 1], "incorrect fixing row")
    del model.constraints[4270:]
    require(model == base, "a prior proto field changed")
    for path, key in ((model_path, "model_sha256"), (base_path, "base_sha256")):
        require(hashlib.sha256(path.read_bytes()).hexdigest() == metadata[key], "hash mismatch")
    return {"id": metadata["id"], "passed": True, "all_prior_proto_fields_preserved": True,
            "new_rows_checked": 7, "model_sha256": metadata["model_sha256"],
            "base_sha256": metadata["base_sha256"],
            "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope": "Encoding preservation only; no integer infeasibility proof."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    encoded = json.dumps(check(args.directory), indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
