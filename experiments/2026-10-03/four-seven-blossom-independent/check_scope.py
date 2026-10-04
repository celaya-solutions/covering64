# Document:    Independent Blossom Helper Scope Rejection Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Confirm invalid branch scopes are rejected before any model mutation."""

import hashlib
import json
import sys
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

from covering64.core import Universe

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
HELPER_SHA = "91e9166a89e5fa610cf970f16c17e829f809388c3f18a6070c7198a396438818"
FROZEN = ROOT / "experiments/scratch/four-seven-blossom-cuts-v1.0.0"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    helper_path = ROOT / "scripts/four_seven_blossom_cuts.py"
    require(hashlib.sha256(helper_path.read_bytes()).hexdigest() == HELPER_SHA,
            "helper differs from audited snapshot")
    sys.path.insert(0, str(ROOT / "scripts"))
    from four_seven_blossom_cuts import add_blossom_cuts

    universe = Universe.build()
    reports = []
    for case in ("cycle", "matching"):
        text = (FROZEN / f"{case}-base.pbtxt").read_text()

        def load(serialized=text):
            model = cp_model.CpModel()
            require(model.proto.parse_text_format(serialized), "base parse failed")
            return model, [model.get_bool_var_from_proto_index(i) for i in range(4368)]

        for control in ("wrong_case", "unknown_case", "nonboolean_block", "reversed_variables",
                        "missing_coverage", "missing_regular_degree", "missing_forbidden_block",
                        "duplicate_application"):
            model, xs = load()
            requested_case = case
            if control == "wrong_case":
                requested_case = "matching" if case == "cycle" else "cycle"
            elif control == "unknown_case":
                requested_case = "other"
            elif control == "nonboolean_block":
                model.proto.variables[0].domain[1] = 2
            elif control == "reversed_variables":
                xs = list(reversed(xs))
            elif control.startswith("missing_"):
                if control == "missing_coverage":
                    domain, length = (1, (1 << 63) - 1), None
                elif control == "missing_regular_degree":
                    domain, length = (20, 20), None
                else:
                    domain, length = (0, 0), 1
                matches = [i for i, row in enumerate(model.proto.constraints)
                           if row.has_linear() and not row.enforcement_literal
                           and tuple(row.linear.domain) == domain
                           and (length is None or len(row.linear.vars) == length)]
                require(matches, "control row absent")
                raw = text_format.Parse(str(model.proto), cp_model_pb2.CpModelProto())
                del raw.constraints[matches[0]]
                model, xs = load(text_format.MessageToString(raw))
            elif control == "duplicate_application":
                add_blossom_cuts(universe, model, xs, case)
            before = str(model.proto)
            try:
                add_blossom_cuts(universe, model, xs, requested_case)
            except ValueError as error:
                require(str(model.proto) == before, "rejected scope mutated the model")
                reports.append({"case": case, "control": control, "rejected": True,
                                "model_unchanged": True, "reason": str(error)})
            else:
                raise ValueError(f"invalid scope accepted: {case}/{control}")
    result = {"passed": True, "controls": reports, "helper_sha256": HELPER_SHA,
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "Rejection behavior of the frozen helper, not a new mathematical proof."}
    (HERE / "scope-controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "controls_rejected_without_mutation": len(reports)}))


if __name__ == "__main__":
    main()
