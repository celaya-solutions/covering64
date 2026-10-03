# Document:    Strengthened Four Sevenfold LP Witness Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Extend preserved exact witnesses through the integer-derived double-triple lift."""

import hashlib
import importlib.util
import json
import sys
from fractions import Fraction
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

from covering64.core import Universe

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import four_seven_double_cuts as lift  # noqa: E402

SPEC = importlib.util.spec_from_file_location("original_lp_check", HERE / "check.py")
ORIGINAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORIGINAL)


def main():
    universe = Universe.build()
    result = {}
    for case in ("cycle", "matching"):
        source = ORIGINAL.SCRATCH / case / "model.pbtxt"
        model = cp_model.CpModel()
        if not model.proto.parse_text_format(source.read_text()):
            raise ValueError("could not load preserved model")
        xs = [model.get_int_var_from_proto_index(i) for i in range(4368)]
        _, added = lift.add_double_triple_cuts(universe, model, xs, case)
        directory = ORIGINAL.SCRATCH / "strengthened" / case
        directory.mkdir(parents=True, exist_ok=True)
        model_path = directory / "model.pbtxt"
        model.export_to_file(str(model_path))
        proto = cp_model_pb2.CpModelProto()
        text_format.Parse(model_path.read_text(), proto)
        witness_path = HERE / f"{case}-witness.json"
        witness = json.loads(witness_path.read_text())
        values = [Fraction(0)] * 4368
        for index, numerator, denominator in witness["nonzero_weights"]:
            values[index] = Fraction(numerator, denominator)
        auxiliary = lift.fractional_double_values(universe, values)
        extended = values + [auxiliary[v.name] for v in proto.variables[4368:]]
        if not ORIGINAL.check_exact(proto, extended):
            raise ValueError("fractional witness fails the strengthened model")
        numeric, _ = ORIGINAL.solve(proto, list(range(len(proto.variables))), "full", directory)
        damaged = extended[:]
        damaged[4368] += Fraction(1, 1000)
        if ORIGINAL.check_exact(proto, damaged):
            raise ValueError("damaged auxiliary value accepted")
        auxiliary_path = HERE / f"{case}-double-values.json"
        auxiliary_path.write_text(json.dumps({
            "case": case, "values": {name: [value.numerator, value.denominator]
                                      for name, value in auxiliary.items()},
            "sum": str(sum(auxiliary.values(), Fraction(0))),
            "original_witness_sha256": hashlib.sha256(witness_path.read_bytes()).hexdigest(),
            "scope": "Fractional LP witness values, not CP-SAT integer hints.",
        }, indent=2) + "\n")
        record = {
            "application": added, "numeric_lp": numeric,
            "preserved_witness_exactly_extended": True,
            "exact_rows_checked": len(proto.constraints),
            "exact_domains_checked": len(proto.variables),
            "fixed_triples_checked": 156, "double_values_checked": 400,
            "double_value_sum": str(sum(auxiliary.values(), Fraction(0))),
            "damaged_auxiliary_rejected": True,
            "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
            "double_values_sha256": hashlib.sha256(auxiliary_path.read_bytes()).hexdigest(),
        }
        result[case] = record
        print(json.dumps({"case": case, **record}), flush=True)
    source = ROOT / "scripts/four_seven_double_cuts.py"
    (ORIGINAL.SCRATCH / "strengthened/four_seven_double_cuts.py").write_bytes(source.read_bytes())
    result["sources"] = {
        "helper_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "integer_row_checker_sha256": hashlib.sha256((HERE / "check.py").read_bytes()).hexdigest(),
    }
    (HERE / "strengthened-result.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
