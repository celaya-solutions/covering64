# Document:    Frozen Fully Cut Integer Pilot Preservation Audit
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      1403af1dbad135130b4baae880cfbeb7f3bada3f88232f76710f16ccd016c33c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit frozen pilot preservation without importing builders or solving models."""

import argparse
import gzip
import hashlib
import json
from itertools import combinations
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(directory, original):
    blocks = list(combinations(range(1, 17), 5))
    results = json.loads(gzip.decompress((directory / "input-results.json.gz").read_bytes()))
    expected_seeds = {"matching-029": 2026103301, "matching-113": 2026103302,
                      "cycle-069": 2026103303, "cycle-046": 2026103304}
    outputs = []
    for case in ("cycle", "matching"):
        model_path = directory / f"{case}-base.pbtxt"
        base = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
        original_model = text_format.Parse((original / f"{case}-base.pbtxt").read_text(),
                                           cp_model_pb2.CpModelProto())
        original_count = len(original_model.constraints)
        require(original_count == 4270 and len(original_model.variables) == 4768,
                "unexpected original lifted base")
        new_rows = list(base.constraints[original_count:])
        require(len(new_rows) == (8120 if case == "cycle" else 8144), "wrong added cut count")
        require(all(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
                    and all(0 <= index < 4368 for index in row.linear.vars) for row in new_rows),
                "new cuts must be unconditional linear rows on block variables only")
        stripped = cp_model_pb2.CpModelProto()
        stripped.CopyFrom(base)
        del stripped.constraints[original_count:]
        require(stripped == original_model, "fully cut base changed an original proto field")
        require(not base.HasField("objective") and not base.HasField("floating_point_objective")
                and not base.HasField("solution_hint"), "unexpected objective or hint")
        for rep_id, seed in expected_seeds.items():
            if not rep_id.startswith(case + "-"):
                continue
            path = directory / rep_id
            metadata = json.loads((path / "metadata.json").read_text())
            candidates = [row for row in results if row["id"] == rep_id]
            require(len(candidates) == 1, "missing or duplicated selected representative")
            entry = candidates[0]
            require(entry["case"] == case and not entry["proves_infeasible"], "bad case selection")
            fixed = metadata["fixed_ids"]
            require(fixed == entry["fixed_ids"] and len(set(fixed)) == len(fixed) == 7,
                    "fixes differ from frozen first-link representative")
            require(all(type(index) is int and 0 <= index < 4368 and
                        blocks[index][:3] == (1, 2, 3) for index in fixed), "bad fixed index")
            model = text_format.Parse((path / "model.pbtxt").read_text(),
                                       cp_model_pb2.CpModelProto())
            start = len(base.constraints)
            require(len(model.variables) == 4768 and len(model.constraints) == start + 7,
                    "wrong pilot dimensions")
            for index, row in zip(fixed, model.constraints[start:], strict=True):
                require(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal,
                        "bad fixing-row type")
                require(list(row.linear.vars) == [index] and list(row.linear.coeffs) == [1]
                        and list(row.linear.domain) == [1, 1], "bad fixing-row coefficient")
            del model.constraints[start:]
            require(model == base, "pilot changed a prior cut-base proto field")
            parameters = text_format.Parse((path / "parameters.txt").read_text(),
                                            sat_parameters_pb2.SatParameters())
            require(parameters.max_time_in_seconds == 300 and parameters.num_search_workers == 2
                    and parameters.random_seed == seed, "wrong solver budget or seed")
            require(parameters.log_search_progress and not parameters.log_to_stdout,
                    "solver log not configured")
            for filename, expected in metadata["sources"].items():
                require(digest(directory / filename) == expected, "frozen source/input drift")
            for file_path, key in ((path / "model.pbtxt", "model_sha256"),
                                    (model_path, "base_sha256"),
                                    (path / "parameters.txt", "parameters_sha256")):
                require(digest(file_path) == metadata[key], "raw model/parameter hash mismatch")
            outputs.append({"id": rep_id, "passed": True, "new_fixing_rows": 7,
                            "base_original_proto_preserved": True,
                            "pilot_base_proto_preserved": True,
                            "new_cuts_only_on_block_variables": True, "seconds": 300,
                            "workers": 2, "seed": seed, "model_sha256": metadata["model_sha256"]})
    return {"cases": outputs, "checker_sha256": digest(Path(__file__)),
            "scope": "Raw encoding preservation and preparation checks, not independent cut "
                     "validity or an integer infeasibility proof."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("original", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.directory, args.original)
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded)
    print(encoded, end="")


if __name__ == "__main__":
    main()
