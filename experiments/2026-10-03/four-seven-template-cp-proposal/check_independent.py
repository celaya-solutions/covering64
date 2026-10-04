# Document:    Independent Boolean Template CP Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      37ce1030732c27fd1ba2d52f32f92551552228eaba51266665b0c621ba77b2d0
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Recount exact CP rows, domains and preserved protobuf fields without solving."""

import copy
import gzip
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/four-seven-template-hull-refresh-106-20261003"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def inspect(proto, base, matrix, case):
    require(len(proto.variables) == matrix["width"], "variable count")
    require(len(proto.constraints) == 4550, "constraint count")
    require(all(list(v.domain) == [0, 1] for v in proto.variables), "nonboolean variable")
    require([v.name for v in proto.variables[:4368]] == [f"block_{i}" for i in range(4368)],
            "block variable ordering")
    expected_names = [f"template_{case}_g{g}_{i}" for g in range(4)
                      for i in range((matrix["width"] - 4768) // 4)]
    require([v.name for v in proto.variables[4768:]] == expected_names, "template ordering")
    stripped = copy.deepcopy(proto)
    del stripped.variables[4768:]
    del stripped.constraints[4270:]
    require(stripped == base, "original protobuf fields changed")
    onehot = {4270, 4340, 4410, 4480}
    for index, (constraint, row) in enumerate(zip(proto.constraints, matrix["rows"], strict=True)):
        require(not constraint.enforcement_literal, "conditional constraint")
        columns, coefficients, lower, upper = row
        if index in onehot:
            require(constraint.WhichOneof("constraint") == "exactly_one", "one-hot row type")
            require(list(constraint.exactly_one.literals) == columns and
                    coefficients == [1] * len(columns) and lower == upper == 1,
                    "one-hot row differs from audited simplex")
        else:
            require(constraint.WhichOneof("constraint") == "linear", "linear row type")
            require(list(constraint.linear.vars) == columns and
                    list(constraint.linear.coeffs) == coefficients, "linear coefficients")
            expected = [-(1 << 63) if lower is None else lower,
                        (1 << 63) - 1 if upper is None else upper]
            require(list(constraint.linear.domain) == expected, "linear bounds")
    return {"case": case, "passed": True, "variables": len(proto.variables),
            "rows": len(proto.constraints), "original_fields_preserved": True,
            "original_rows": 4270, "exactly_one_rows": 4, "marginal_rows": 276}


def main():
    manifest = load(HERE / "manifest.json")
    require(sha(HERE / "build.py") == manifest["builder_sha256"], "builder source changed")
    audit_path = HERE.parent / "four-seven-template-hull-refresh/independent-audit.json"
    audit = load(audit_path)
    require(audit["passed"], "catalog and hull audit missing")
    require(audit["manifest_sha256"] == manifest["refresh_manifest_sha256"], "hull changed")
    reports, controls = [], []
    for record in manifest["cases"]:
        case = record["case"]
        path, base_path = ROOT / record["model"], ROOT / record["source_base"]
        require(sha(path) == record["model_sha256"] and
                sha(base_path) == record["source_base_sha256"], "protobuf hash")
        matrix_path = RAW / case / "extended-rows.json.gz"
        verified = next(r for r in audit["cases"] if r["case"] == case)
        require(sha(matrix_path) == record["matrix_sha256"] == verified["matrix_sha256"],
                "matrix disconnected from independent hull audit")
        matrix = load(matrix_path)
        proto = text_format.Parse(path.read_text(), cp_model_pb2.CpModelProto())
        base = text_format.Parse(base_path.read_text(), cp_model_pb2.CpModelProto())
        report = inspect(proto, base, matrix, case)
        report.update(model_sha256=sha(path), matrix_sha256=sha(matrix_path),
                      base_model_sha256=sha(base_path))
        reports.append(report)
        mutations = [
            ("lost row", lambda p: p.constraints.__delitem__(-1)),
            ("lost variable", lambda p: p.variables.__delitem__(-1)),
            ("nonboolean selector", lambda p: p.variables[-1].domain.__setitem__(1, 2)),
            ("wrong block name", lambda p: setattr(p.variables[0], "name", "damaged")),
            ("wrong template name", lambda p: setattr(p.variables[-1], "name", "damaged")),
            ("missing onehot literal", lambda p: p.constraints[4270].exactly_one.literals.pop()),
            ("negated onehot literal", lambda p:
             p.constraints[4270].exactly_one.literals.__setitem__(0, -4769)),
            ("wrong marginal sign", lambda p: p.constraints[4271].linear.coeffs.__setitem__(0, -1)),
            ("changed objective", lambda p: setattr(p.objective, "offset", 1)),
            ("conditional marginal", lambda p: p.constraints[4271].enforcement_literal.append(0)),
        ]
        for name, mutate in mutations:
            damaged = copy.deepcopy(proto)
            mutate(damaged)
            try:
                inspect(damaged, base, matrix, case)
            except ValueError:
                controls.append({"case": case, "mutation": name, "rejected": True})
            else:
                raise ValueError("damaged control accepted: " + name)
    report = {"passed": True, "checker_sha256": sha(Path(__file__)),
              "manifest_sha256": sha(HERE / "manifest.json"),
              "hull_audit_sha256": sha(audit_path), "cases": reports,
              "damaged_controls": controls, "solver_calls": 0,
              "scope": "Exact integer extension of the independently checked surviving hull. "
                       "Unique selected templates reproduce precisely the heavy block incidences; "
                       "the original block model is preserved. No solve or infeasibility claim."}
    (HERE / "independent-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": reports, "damaged_controls": len(controls)}))


if __name__ == "__main__":
    main()
