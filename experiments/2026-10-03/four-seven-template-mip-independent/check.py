# Document:    Independent Matching Template Mixed Integer Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      70b82bf5cb71117b92c0c4b41b8700e55f72b66cbca5b078fce485186c747e3c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Read the frozen MPModelProto directly; never import the builder or call Solve."""

import gzip
import hashlib
import itertools as it
import json
import math
from pathlib import Path

from ortools.linear_solver import linear_solver_pb2, pywraplp

from covering64.core import Universe

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-mip-v1.0.0"
MATRIX_HASH = "ee2072837ae28bcce599c60975995a5c88b3fc3eb635352abc089b3eb6d78bab"
MODEL_HASH = "ca38951e994b1b2f0f0d6b42a3bfa60124366b010f10dd1d0ec2528fce82214b"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(model, matrix):
    require(len(model.variable) == matrix["width"] == 55528, "variable count")
    require(len(model.constraint) == len(matrix["rows"]) == 4550, "row count")
    require(
        not model.general_constraint and not model.HasField("quadratic_objective"),
        "unexpected general or quadratic constraint",
    )
    require(not model.maximize and model.objective_offset == 0, "changed objective")
    for index, variable in enumerate(model.variable):
        require(variable.name == f"x{index}", "column index/name changed")
        require(variable.lower_bound == 0 and variable.upper_bound == 1, "changed domain")
        require(variable.is_integer == (index < 4768), "changed integrality")
        require(variable.objective_coefficient == 0, "nonzero objective coefficient")
    for index, (row, reference) in enumerate(zip(model.constraint, matrix["rows"], strict=True)):
        ids, coefficients, lower, upper = reference
        require(row.name == f"row_{index}", "row index/name changed")
        require(
            len(row.var_index) == len(row.coefficient) == len(ids) == len(coefficients),
            "row width changed",
        )
        require(len(set(row.var_index)) == len(row.var_index), "duplicate row variable")
        require(
            sorted(zip(row.var_index, row.coefficient, strict=True))
            == sorted(zip(ids, coefficients, strict=True)),
            "row coefficients changed",
        )
        require(row.lower_bound == (-math.inf if lower is None else lower), "lower bound changed")
        require(row.upper_bound == (math.inf if upper is None else upper), "upper bound changed")
        require(not row.is_lazy, "lazy row changed")


def template_signatures(matrix):
    blocks = list(it.combinations(range(1, 17), 5))
    require(len(blocks) == 4368, "wrong block universe")
    require(list(Universe.build().blocks) == blocks, "candidate extractor block order changed")
    records = []
    for group, transport in enumerate(matrix["transports"]):
        start, stop = transport["lambda_start"], transport["lambda_stop_exclusive"]
        require(stop - start == 12690, "wrong selector group width")
        entries = [e for e in matrix["extension_rows"] if e["group"] == group]
        simplex = [e for e in entries if e["kind"] == "template_simplex"]
        marginals = [e for e in entries if e["kind"] == "heavy_block_marginal"]
        require(len(simplex) == 1 and len(marginals) == 69, "wrong group row inventory")
        require(
            matrix["rows"][simplex[0]["row"]]
            == [list(range(start, stop)), [1] * (stop - start), 1, 1],
            "wrong simplex",
        )
        signatures = [0] * (stop - start)
        require(len({e["block_index"] for e in marginals}) == 69, "duplicate heavy marginal")
        for bit, entry in enumerate(marginals):
            ids, coefficients, lower, upper = matrix["rows"][entry["row"]]
            require(lower == upper == 0, "wrong marginal equation")
            require(
                ids[0] == entry["block_index"] and coefficients[0] == 1,
                "wrong marginal block column",
            )
            expected = tuple(sorted(transport["anchor_triple"] + entry["outside_edge"]))
            require(blocks[ids[0]] == expected, "heavy block lexicographic identity changed")
            require(
                all(
                    start <= col < stop and value == -1
                    for col, value in zip(ids[1:], coefficients[1:], strict=True)
                ),
                "wrong selector coefficients",
            )
            for column in ids[1:]:
                signatures[column - start] |= 1 << bit
        require(len(set(signatures)) == 12690, "templates not distinguished by all marginals")
        records.append(
            {
                "group": group,
                "templates": len(signatures),
                "coordinates": 69,
                "unique_binary_signatures": len(set(signatures)),
            }
        )
    return records


def damaged_controls(model, matrix):
    def missing_variable(m):
        del m.variable[-1]

    def missing_row(m):
        del m.constraint[-1]

    def duplicate_coefficient(m):
        m.constraint[0].var_index.append(m.constraint[0].var_index[0])
        m.constraint[0].coefficient.append(1)

    modifications = [
        ("missing_variable", missing_variable),
        ("missing_row", missing_row),
        ("column_name", lambda m: setattr(m.variable[0], "name", "x1")),
        ("block_continuous", lambda m: setattr(m.variable[0], "is_integer", False)),
        ("auxiliary_continuous", lambda m: setattr(m.variable[4767], "is_integer", False)),
        ("selector_integer", lambda m: setattr(m.variable[4768], "is_integer", True)),
        ("lower_domain", lambda m: setattr(m.variable[0], "lower_bound", -1)),
        ("upper_domain", lambda m: setattr(m.variable[-1], "upper_bound", 2)),
        ("nan_domain", lambda m: setattr(m.variable[-1], "upper_bound", math.nan)),
        ("objective", lambda m: setattr(m.variable[0], "objective_coefficient", 1)),
        ("maximize", lambda m: setattr(m, "maximize", True)),
        ("offset", lambda m: setattr(m, "objective_offset", 1)),
        ("row_name", lambda m: setattr(m.constraint[0], "name", "wrong")),
        ("row_coefficient", lambda m: m.constraint[0].coefficient.__setitem__(0, 2)),
        ("row_column", lambda m: m.constraint[0].var_index.__setitem__(0, 13)),
        ("row_lower", lambda m: setattr(m.constraint[0], "lower_bound", -1)),
        ("row_upper", lambda m: setattr(m.constraint[0], "upper_bound", 1)),
        ("lazy_row", lambda m: setattr(m.constraint[0], "is_lazy", True)),
        ("duplicate_coefficient", duplicate_coefficient),
    ]
    records = []
    for name, mutate in modifications:
        damaged = linear_solver_pb2.MPModelProto()
        damaged.CopyFrom(model)
        mutate(damaged)
        try:
            check(damaged, matrix)
        except ValueError as error:
            records.append({"control": name, "rejected": str(error)})
        else:
            raise ValueError(f"damaged control accepted: {name}")
    return records


def main():
    require(sha(RAW / "model.pb.gz") == MODEL_HASH, "frozen model hash")
    require(sha(RAW / "matrix.json.gz") == MATRIX_HASH, "frozen matrix hash")
    matrix = json.loads(gzip.decompress((RAW / "matrix.json.gz").read_bytes()))
    model = linear_solver_pb2.MPModelProto()
    model.ParseFromString(gzip.decompress((RAW / "model.pb.gz").read_bytes()))
    check(model, matrix)
    signatures = template_signatures(matrix)
    controls = damaged_controls(model, matrix)
    solver = pywraplp.Solver.CreateSolver("SCIP")
    require(solver is not None, "SCIP unavailable")
    require(solver.LoadModelFromProtoKeepNames(model) == "", "SCIP refused model")
    reconstructed = linear_solver_pb2.MPModelProto()
    solver.ExportModelToProto(reconstructed)
    require(reconstructed == model, "SCIP load/export changed model")
    require(solver.SetNumThreads(1), "SCIP single-thread setting rejected")
    report = {
        "passed": True,
        "model_sha256": MODEL_HASH,
        "matrix_sha256": MATRIX_HASH,
        "checker_sha256": sha(Path(__file__)),
        "variables": 55528,
        "rows": 4550,
        "boolean_variables": 4768,
        "continuous_selectors": 50760,
        "lexicographic_block_columns": 4368,
        "template_signatures": signatures,
        "damaged_controls": controls,
        "scip_unsolved_load_export_equal": True,
        "single_thread_accepted": True,
        "solver": solver.SolverVersion(),
        "solve_called": False,
        "scope": "Exact MIP export audit against separately audited whole matching matrix.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["passed", "model_sha256", "matrix_sha256"]}))


if __name__ == "__main__":
    main()
