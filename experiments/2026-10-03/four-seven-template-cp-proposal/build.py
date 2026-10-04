# Document:    Complete Boolean Heavy-Link Template CP Prototype
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Append one-hot selectors and exact marginals to frozen original CP bases; no solve."""

import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path

from google.protobuf import text_format
from ortools import __version__ as ortools_version
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REFRESH = HERE.parent / "four-seven-template-hull-refresh"
MATRICES = ROOT / "experiments/scratch/four-seven-template-hull-refresh-106-20261003"
BASES = ROOT / "experiments/scratch/four-seven-link-lp-full"
MANIFEST_SHA = "84183ee44ed2916ffd18d64b5f113774e4eda47bad5e82c6c79b1b3a64db5bdf"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(proto):
    result = []
    for constraint in proto.constraints:
        require(constraint.WhichOneof("constraint") == "linear", "nonlinear base row")
        require(not constraint.enforcement_literal, "reified base row")
        require(len(constraint.linear.domain) == 2, "noninterval row domain")
        lower, upper = constraint.linear.domain
        result.append(
            [
                list(constraint.linear.vars),
                list(constraint.linear.coeffs),
                None if lower == -(1 << 63) else lower,
                None if upper == (1 << 63) - 1 else upper,
            ]
        )
    return result


def build(case, meta, destination):
    folder = MATRICES / case
    paths = {
        "matrix": folder / "extended-rows.json.gz",
        "catalog": folder / "base-catalog.json.gz",
        "group_catalogs": folder / "group-catalogs.json.gz",
    }
    for name, path in paths.items():
        require(sha(path) == meta[name + "_sha256"], "refreshed input changed")
    matrix = json.loads(gzip.decompress(paths["matrix"].read_bytes()))
    base_path = BASES / (case + "-base.pbtxt")
    base = cp_model_pb2.CpModelProto()
    text_format.Parse(base_path.read_text(), base)
    require(len(base.variables) == matrix["base_width"] == 4768, "base variable count")
    require(len(base.constraints) == matrix["base_rows"] == 4270, "base constraint count")
    require(rows(base) == matrix["rows"][:4270], "base does not match audited rows")
    require(all(list(v.domain) == [0, 1] for v in base.variables), "non-Boolean base")
    require(
        [v.name for v in base.variables[:4368]] == [f"block_{i}" for i in range(4368)],
        "changed lexicographic block variable names",
    )
    proto = cp_model_pb2.CpModelProto()
    proto.CopyFrom(base)
    for transport in matrix["transports"]:
        group = transport["group_index"]
        for index in range(transport["template_count"]):
            proto.variables.add(name=f"template_{case}_g{group}_{index}", domain=[0, 1])
    simplex = []
    marginals = []
    for descriptor in matrix["extension_rows"]:
        number = descriptor["row"]
        ids, coefficients, lower, upper = matrix["rows"][number]
        require(number == len(proto.constraints), "extension rows reordered")
        row = proto.constraints.add()
        if descriptor["kind"] == "template_simplex":
            require(lower == upper == 1 and coefficients == [1] * len(ids), "invalid simplex")
            row.exactly_one.literals.extend(ids)
            simplex.append(number)
        else:
            require(descriptor["kind"] == "heavy_block_marginal", "unexpected extension")
            require(lower == upper == 0, "nonexact marginal")
            row.linear.vars.extend(ids)
            row.linear.coeffs.extend(coefficients)
            row.linear.domain.extend([lower, upper])
            marginals.append(number)
    require(len(proto.variables) == meta["total_variables"], "extended variable count")
    require(len(proto.constraints) == 4550, "extended constraint count")
    require(len(simplex) == 4 and len(marginals) == 276, "extension inventory")
    # Delete only the appended fields and verify every other original proto field verbatim.
    stripped = cp_model_pb2.CpModelProto()
    stripped.CopyFrom(proto)
    del stripped.variables[4768:]
    del stripped.constraints[4270:]
    require(stripped == base, "original proto fields changed")
    model = cp_model.CpModel()
    model.proto.parse_text_format(text_format.MessageToString(proto))
    require(not model.validate(), "invalid CP model")
    target = destination / (case + "-boolean-templates.pbtxt")
    target.write_text(text_format.MessageToString(proto))
    return {
        "case": case,
        "model": str(target.relative_to(ROOT)),
        "model_sha256": sha(target),
        "source_base": str(base_path.relative_to(ROOT)),
        "source_base_sha256": sha(base_path),
        "matrix_sha256": sha(paths["matrix"]),
        "catalog_sha256": sha(paths["catalog"]),
        "group_catalogs_sha256": sha(paths["group_catalogs"]),
        "base_variables": 4768,
        "block_variables": 4368,
        "base_constraints": 4270,
        "boolean_selectors": len(proto.variables) - 4768,
        "total_variables": len(proto.variables),
        "total_constraints": 4550,
        "exactly_one_rows": simplex,
        "marginal_rows": len(marginals),
        "base_proto_preserved": True,
        "cp_model_valid": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.exists(), "new output directory required")
    require(sha(REFRESH / "manifest.json") == MANIFEST_SHA, "refresh manifest changed")
    manifest = json.loads((REFRESH / "manifest.json").read_text())
    output.mkdir(parents=True)
    (output / "build.py").write_bytes(Path(__file__).read_bytes())
    result = {
        "version": "v1.0.0",
        "builder_sha256": sha(Path(__file__)),
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "ortools_version": ortools_version,
        "refresh_manifest_sha256": MANIFEST_SHA,
        "cases": [build(m["case"], m, output) for m in manifest["cases"]],
        "scope": "Exact integer extension of the audited complete surviving-template hull "
        "for normalized regular four-sevenfold covers. No solves; no exclusions.",
    }
    (output / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
