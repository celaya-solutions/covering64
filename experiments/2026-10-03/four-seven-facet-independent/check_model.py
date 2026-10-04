# Document:    Independent Signed Facet Model Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Compare all new signed rows with the independently checked proof and preserve the base."""

import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FROZEN = ROOT / "experiments/scratch/four-seven-facet-independent-models"
PROOF_SHA = "7f79089fd414539551863b367b161ee1b8a5dffbaf1e5bd9013ee6ac33cc3e51"
HELPER_SHA = "9a0230ab2e21d56372f303016290753b55ef80b7f6af2b3113ff7b9f77a6be54"
BASE_SHA = {
    ("cycle", False): "5cbaba3a581ab485a1ebd5adc3a328ff53c963a414fadc773bb9687abead02d9",
    ("matching", False): "5f85a1cd9caa86742892e44c0632df0c99c0409bc3e69d0905e4924a08116b84",
    ("cycle", True): "3066ff69537e054cb3c8c12365f4c4f38694a11e8073cf3964d9372265a10c22",
    ("matching", True): "92dc44923c0a68711fc300a5445e35345982af02510f7af54e70466c82beaadd",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(base, model, expected):
    offset = len(base.constraints)
    require(len(model.variables) == 4768 and len(base.variables) == 4768, "wrong variable count")
    require(len(model.constraints) == offset + len(expected), "wrong constraint count")
    for index, row in enumerate(expected):
        actual = model.constraints[offset + index]
        require(actual.WhichOneof("constraint") == "linear" and not actual.enforcement_literal,
                "incorrect row type")
        require(actual.name == row["name"], "wrong row name/order")
        require(list(actual.linear.vars) == row["ids"]
                and list(actual.linear.coeffs) == row["coefficients"]
                and list(actual.linear.domain) == [-(1 << 63), row["bound"]],
                "signed row differs from independently checked proof")
    stripped = cp_model_pb2.CpModelProto()
    stripped.CopyFrom(model)
    del stripped.constraints[offset:]
    require(stripped == base, "prior proto field changed")


def damaged_controls(base, model, expected):
    offset = len(base.constraints)
    changes = {
        "sign": lambda m: m.constraints[offset].linear.coeffs.__setitem__(
            0, -m.constraints[offset].linear.coeffs[0]),
        "column": lambda m: m.constraints[offset].linear.vars.__setitem__(0, 4368),
        "bound": lambda m: m.constraints[offset].linear.domain.__setitem__(1, 999),
        "enforcement": lambda m: m.constraints[offset].enforcement_literal.append(0),
        "missing_row": lambda m: m.constraints.pop(),
        "extra_row": lambda m: m.constraints.add().CopyFrom(m.constraints[offset]),
        "prior_name": lambda m: setattr(m.variables[0], "name", "damaged"),
        "prior_row": lambda m: m.constraints[0].linear.domain.__setitem__(1, 1),
        "hint": lambda m: (m.solution_hint.vars.append(0), m.solution_hint.values.append(1)),
        "objective": lambda m: (m.objective.vars.append(0), m.objective.coeffs.append(1)),
    }
    results = {}
    for name, mutate in changes.items():
        damaged = cp_model_pb2.CpModelProto()
        damaged.CopyFrom(model)
        mutate(damaged)
        try:
            compare(base, damaged, expected)
        except ValueError:
            results[name] = "rejected"
        else:
            raise ValueError(f"damaged model accepted: {name}")
    return results


def main():
    proof_path = HERE.parent / "four-seven-link-orbits/safe-feature-facets.json"
    require(sha(proof_path) == PROOF_SHA, "proof changed")
    audit = json.loads((HERE / "proof-audit.json").read_text())
    require(audit["passed"] is True and audit["proof_sha256"] == PROOF_SHA,
            "independent proof audit missing")
    proof = json.loads(proof_path.read_text())
    metadata = json.loads((FROZEN / "metadata.json").read_text())
    require(metadata["sources"]["four_seven_facet_cuts.py"] == HELPER_SHA, "wrong helper")
    for name, expected_sha in metadata["sources"].items():
        require(sha(FROZEN / name) == expected_sha, "source snapshot changed")
    expected = {}
    for case_data in proof["cases"]:
        case = case_data["case"]
        rows = []
        selected = [f for f in case_data["all_facets"] if f["excludes_certified_orbits"]
                    and not f["already_in_five_rules"]]
        for index, facet in enumerate(selected):
            for target in facet["target_groups"]:
                terms = sorted(target["coefficients"], key=lambda t: t["variable_index"])
                rows.append({"name": f"four_seven_facet_{case}_{index:02d}"
                                     f"_group_{target['group_index']}",
                             "ids": [t["variable_index"] for t in terms],
                             "coefficients": [t["coefficient"] for t in terms],
                             "bound": facet["upper_bound"]})
        require(len(rows) == (16 if case == "cycle" else 36), "wrong new-family row count")
        expected[case] = rows
    require({(m["case"], m["first_features"]) for m in metadata["models"]} == set(BASE_SHA)
            and len(metadata["models"]) == 4, "missing model variant")
    results = []
    for entry in metadata["models"]:
        case, old = entry["case"], entry["first_features"]
        base_path, model_path = FROZEN / entry["base"], FROZEN / entry["facets"]
        require(sha(base_path) == BASE_SHA[(case, old)] == entry["base_sha256"], "wrong base")
        require(sha(model_path) == entry["facets_sha256"], "feature model hash mismatch")
        base = text_format.Parse(base_path.read_text(), cp_model_pb2.CpModelProto())
        model = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
        compare(base, model, expected[case])
        controls = damaged_controls(base, model, expected[case])
        results.append({"case": case, "first_features": old, "passed": True,
                        "base_rows": len(base.constraints), "rows": len(model.constraints),
                        "new_rows": len(expected[case]), "new_variables": 0,
                        "all_prior_proto_fields_preserved": True, "damaged_controls": controls,
                        "model_sha256": sha(model_path), "base_sha256": sha(base_path)})
    result = {"passed": True, "proof_sha256": PROOF_SHA, "helper_sha256": HELPER_SHA,
              "checker_sha256": sha(Path(__file__)), "models": results,
              "scope": "Only signed feature suffix and prior proto preservation; "
              "the separate exact proof audit establishes integer-branch necessity."}
    (HERE / "model-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "models": len(results),
                      "signed_rows_checked": sum(r["new_rows"] for r in results)}))


if __name__ == "__main__":
    main()
