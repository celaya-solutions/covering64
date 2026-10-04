# Document:    Independent Six Case Hub Split Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Independently reconstruct the split rows and enumerate necessary hub counts."""

import copy
import hashlib
import json
import shutil
import sys
from itertools import combinations, product
from pathlib import Path
from types import SimpleNamespace

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

from covering64.core import Universe

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FROZEN = ROOT / "experiments/scratch/four-seven-blossom-cp-v1.1.0"
OUTPUT = ROOT / "experiments/scratch/four-seven-hub-split-independent"
HELPER_SHA = "6a3bc55e12b50ddb06e1905c07335b88d9437c71cd19aec1bd9bf8e89e7c7ee6"
HUBS = (4, 8, 12, 16)
BLOCKS = tuple(combinations(range(1, 17), 5))
HUB_TRIPLES = tuple(combinations(HUBS, 3))
FOUR_IDS = [i for i, block in enumerate(BLOCKS) if set(HUBS).issubset(block)]
TRIPLE_TERMS = [(i, sum(set(triple).issubset(block) for triple in HUB_TRIPLES))
                for i, block in enumerate(BLOCKS)
                if any(set(triple).issubset(block) for triple in HUB_TRIPLES)]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw_model(serialized):
    return text_format.Parse(serialized, cp_model_pb2.CpModelProto())


def load(serialized):
    model = cp_model.CpModel()
    require(model.proto.parse_text_format(serialized), "model parse failed")
    return model, [model.get_bool_var_from_proto_index(i) for i in range(4368)]


def check_model(base, actual, m4, z):
    offset = len(base.constraints)
    require(len(actual.constraints) == offset + 2, "wrong new row count")
    expected = (((i, 1) for i in FOUR_IDS), iter(TRIPLE_TERMS))
    names = ("four_seven_hub_split_four_hub_blocks",
             "four_seven_hub_split_hub_triple_incidences")
    for row, terms, name, target in zip(actual.constraints[offset:], expected, names, (m4, 4 + z)):
        terms = list(terms)
        require(row.WhichOneof("constraint") == "linear", "nonlinear count row")
        require(not row.enforcement_literal, "conditional count row")
        require(row.name == name, "wrong count row name")
        require(list(zip(row.linear.vars, row.linear.coeffs)) == terms, "wrong count terms")
        require(list(row.linear.domain) == [target, target], "wrong count equality")
    original = copy.deepcopy(actual)
    del original.constraints[offset:]
    require(original == base, "prior proto fields changed")


def count_proof(case):
    elevated = {(4, 8), (12, 16)}
    if case == "cycle":
        elevated |= {(8, 12), (4, 16)}
    five_pairs = [pair for pair in combinations(HUBS, 2) if pair not in elevated]
    charges = [sum(set(pair).issubset(triple) for pair in five_pairs) for triple in HUB_TRIPLES]
    require(charges == ([1] * 4 if case == "cycle" else [2] * 4), "wrong excess charges")
    patterns = []
    possible_cases = set()
    for doubled in product((0, 1), repeat=4):
        if any(sum(flag for flag, triple in zip(doubled, HUB_TRIPLES)
                   if set(pair).issubset(triple)) > 1 for pair in five_pairs):
            continue
        z = sum(doubled)
        require(z <= 2, "pair excess permits too many doubled triples")
        patterns.append(list(doubled))
        for m4 in range(7):
            m3 = 4 + z - 4 * m4
            if m3 >= 0:
                require(m4 <= 1, "hub incidences permit two four-hub blocks")
                possible_cases.add((m4, z))
    require(possible_cases == set(product((0, 1), range(3))), "incomplete six-case partition")
    return {"case": case, "multiplicity_five_hub_pairs": five_pairs,
            "charge_per_doubled_triple": charges, "necessary_doubling_patterns": patterns,
            "complete_cases": sorted(possible_cases),
            "argument": "Each fivefold pair has exactly one excess triple incidence. "
                        "Every hub triple uses at least one such pair, so its multiplicity "
                        "is 1 or 2. Enumerated doubled subsets obey every pair excess. "
                        "Counting hub triples gives m3+4*m4=4+z; all cases are disjoint.",
            "scope": "Necessary partition of integer normalized regular four-sevenfold covers; "
                     "enumerated patterns and cases do not assert existence of covers."}


def check_damage(base, actual, m4, z):
    controls = []
    offset = len(base.constraints)
    for control in ("drop_row", "extra_row", "first_coefficient", "second_coefficient",
                    "first_bound", "second_bound", "conditional_row", "prior_row",
                    "prior_variable", "objective"):
        damaged = copy.deepcopy(actual)
        if control == "drop_row":
            del damaged.constraints[offset]
        elif control == "extra_row":
            damaged.constraints.add().CopyFrom(damaged.constraints[offset])
        elif control == "first_coefficient":
            damaged.constraints[offset].linear.coeffs[0] = 2
        elif control == "second_coefficient":
            damaged.constraints[offset + 1].linear.coeffs[0] += 1
        elif control == "first_bound":
            damaged.constraints[offset].linear.domain[1] += 1
        elif control == "second_bound":
            damaged.constraints[offset + 1].linear.domain[0] -= 1
        elif control == "conditional_row":
            damaged.constraints[offset].enforcement_literal.append(0)
        elif control == "prior_row":
            damaged.constraints[0].linear.domain[0] += 1
        elif control == "prior_variable":
            damaged.variables[0].domain[1] = 2
        else:
            damaged.objective.offset += 1
        try:
            check_model(base, damaged, m4, z)
        except ValueError:
            controls.append(control)
        else:
            raise ValueError(f"damaged model accepted: {control}")
    return controls


def scope_controls(universe, serialized, case, add_split):
    reports = []
    invalid_cases = ((-1, 0), (2, 0), (0, -1), (0, 3), (True, 0), (0, False),
                     (0.0, 0), (0, 1.0), ("0", 0), (0, None))
    controls = [(f"invalid_counts_{i}", pair) for i, pair in enumerate(invalid_cases)]
    controls += [(name, (0, 0)) for name in (
        "wrong_case", "unknown_case", "wrong_universe", "nonboolean_block",
        "reversed_variables", "reversed_blocks", "missing_coverage", "missing_regular_degree",
        "missing_forbidden_block", "missing_cardinality", "missing_pair", "missing_sevenfold",
        "duplicate_application")]
    for control, pair in controls:
        model, xs = load(serialized)
        requested_case, requested_universe = case, universe
        if control == "wrong_case":
            requested_case = "matching" if case == "cycle" else "cycle"
        elif control == "unknown_case":
            requested_case = "other"
        elif control == "wrong_universe":
            requested_universe = SimpleNamespace(v=15, k=5, t=3)
        elif control == "nonboolean_block":
            model.proto.variables[0].domain[1] = 2
        elif control == "reversed_variables":
            xs.reverse()
        elif control == "reversed_blocks":
            requested_universe = SimpleNamespace(v=16, k=5, t=3,
                                                blocks=tuple(reversed(universe.blocks)),
                                                containing=universe.containing)
        elif control.startswith("missing_"):
            domains = {"missing_coverage": (1, (1 << 63) - 1),
                       "missing_regular_degree": (20, 20),
                       "missing_forbidden_block": (0, 0), "missing_cardinality": (64, 64),
                       "missing_pair": (5, 5), "missing_sevenfold": (7, 7)}
            raw = raw_model(str(model.proto))
            matches = [i for i, row in enumerate(raw.constraints)
                       if row.WhichOneof("constraint") == "linear"
                       and not row.enforcement_literal
                       and tuple(row.linear.domain) == domains[control]
                       and (control != "missing_forbidden_block" or len(row.linear.vars) == 1)]
            require(matches, "scope control row absent")
            required = copy.deepcopy(raw.constraints[matches[0]].linear)
            duplicate_ids = [i for i, row in enumerate(raw.constraints)
                             if row.WhichOneof("constraint") == "linear"
                             and not row.enforcement_literal and row.linear == required]
            for index in reversed(duplicate_ids):
                del raw.constraints[index]
            model, xs = load(text_format.MessageToString(raw))
        elif control == "duplicate_application":
            add_split(universe, model, xs, case, 0, 0)
        before = str(model.proto)
        try:
            add_split(requested_universe, model, xs, requested_case, *pair)
        except ValueError as error:
            require(str(model.proto) == before, "invalid scope mutated model")
            reports.append({"case": case, "control": control, "reason": str(error),
                            "rejected_without_mutation": True})
        else:
            raise ValueError(f"invalid scope accepted: {case}/{control}")
    return reports


def main():
    helper = ROOT / "scripts/four_seven_hub_split.py"
    require(sha(helper) == HELPER_SHA, "helper source changed")
    require(not (HERE / "audit.json").exists(), "refusing to replace completed audit")
    sys.path.insert(0, str(ROOT / "scripts"))
    from four_seven_hub_split import add_hub_count_split

    OUTPUT.mkdir(parents=True, exist_ok=True)
    source_hashes = {}
    for path in (helper, ROOT / "scripts/four_seven_double_cuts.py"):
        shutil.copyfile(path, OUTPUT / path.name)
        source_hashes[path.name] = sha(path)
    universe = Universe.build()
    reports, controls, proofs = [], [], []
    prepared_audit = json.loads((HERE.parent / "four-seven-blossom-independent" /
                                "prepared-cp-v1.1-audit.json").read_text())
    require(prepared_audit["passed"], "full-cut base audit missing")
    for case in ("cycle", "matching"):
        base_path = FROZEN / f"{case}-base.pbtxt"
        audited_base_hashes = {
            "cycle": "06c3e44716d86d34c4df397413c35ab81eed3dd7af21a2956fbe5fe84f26af4d",
            "matching": "f73f9a40b5d9f566aceed15311c42b2103cfd290c6faf09cd62fd39e682b955f",
        }
        require(sha(base_path) == audited_base_hashes[case], "previously audited base changed")
        serialized = base_path.read_text()
        base = raw_model(serialized)
        shutil.copyfile(base_path, OUTPUT / f"{case}-base.pbtxt")
        proofs.append(count_proof(case))
        for m4, z in product((0, 1), range(3)):
            model, xs = load(serialized)
            metadata = add_hub_count_split(universe, model, xs, case, m4, z)
            output_path = OUTPUT / f"{case}-m4-{m4}-z-{z}.pbtxt"
            output_path.write_text(str(model.proto))
            actual = raw_model(output_path.read_text())
            check_model(base, actual, m4, z)
            require(metadata["new_rows"] == 2 and metadata["new_variables"] == 0,
                    "wrong reported size")
            require(metadata["four_hub_block_ids"] == FOUR_IDS
                    and metadata["hub_triple_terms"] == TRIPLE_TERMS, "wrong metadata terms")
            partition = [list(p) for p in product((0, 1), range(3))]
            require(metadata["complete_case_partition"] == partition,
                    "wrong reported partition")
            rejected = check_damage(base, actual, m4, z)
            reports.append({"case": case, "m4": m4, "z": z, "passed": True,
                            "base_sha256": sha(base_path), "model_sha256": sha(output_path),
                            "rows_before": len(base.constraints), "rows_added": 2,
                            "variables": len(base.variables), "all_prior_fields_preserved": True,
                            "damaged_controls_rejected": rejected})
        controls.extend(scope_controls(universe, serialized, case, add_hub_count_split))
    result = {"passed": True, "helper_sha256": HELPER_SHA,
              "models": reports, "scope_controls": controls,
              "proof_enumerations": proofs, "source_sha256": source_hashes,
              "checker_sha256": sha(Path(__file__)), "four_hub_block_terms": len(FOUR_IDS),
              "hub_triple_terms": len(TRIPLE_TERMS),
              "scope": "Six-case necessary partition and encoding audit only; no solve performed."}
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "models": len(reports),
                      "damaged_models_rejected": 10 * len(reports),
                      "invalid_scopes_rejected_without_mutation": len(controls)}))


if __name__ == "__main__":
    main()
