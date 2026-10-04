# Document:    Independent Propagated Restricted CNF Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay every forced value and every residual clause for matching-063 only."""

import copy
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "four-seven-template-cnf-propagated"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(data)
    return result.hexdigest()


def load(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == ".gz"
                      else path.read_bytes())


def equation(row):
    require(not row.enforcement_literal, "enforced original row")
    coefficients = Counter()
    if row.WhichOneof("constraint") == "linear":
        require(len(row.linear.domain) == 2, "noninterval original row")
        for variable, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True):
            require(variable >= 0, "negative linear variable")
            coefficients[variable] += coefficient
        lower, upper = row.linear.domain
    else:
        require(row.WhichOneof("constraint") == "exactly_one", "unknown original row")
        complement_count = 0
        for literal in row.exactly_one.literals:
            if literal < 0:
                coefficients[-literal - 1] -= 1
                complement_count += 1
            else:
                coefficients[literal] += 1
        lower = upper = 1 - complement_count
    return {i: a for i, a in sorted(coefficients.items()) if a}, lower, upper


def replay(equations, trace):
    assigned, origins = {}, {}
    for number, step in enumerate(trace["steps"]):
        require(step["step"] == number and 0 <= step["row"] < len(equations), "step index")
        terms, lower, upper = equations[step["row"]]
        constant = sum(a * assigned[i] for i, a in terms.items() if i in assigned)
        free = {i: a for i, a in terms.items() if i not in assigned}
        smallest = constant + sum(a for a in free.values() if a < 0)
        largest = constant + sum(a for a in free.values() if a > 0)
        require(step["assigned_before"] == len(assigned), "assignment count")
        require([step[k] for k in ["constant", "minimum", "maximum", "lower", "upper"]]
                == [constant, smallest, largest, lower, upper], "reason arithmetic")
        support = sorted({origins[i] for i in terms if i in assigned})
        require(step["support_steps"] == support and all(s < number for s in support),
                "reason dependency DAG")
        require(step["contradiction"] is False and step["conflict_variable"] is None,
                "unexpected contradiction record")
        require(smallest <= upper and largest >= lower, "inconsistent row interval")
        batch = {}
        for i, value, min0, max0, min1, max1 in step["forced"]:
            require(type(i) is int and i in free and i not in batch, "bad forced variable")
            require(type(value) is int and value in (0, 1), "bad forced value")
            a = free[i]
            zero_low = smallest - (a if a < 0 else 0)
            zero_high = largest - (a if a > 0 else 0)
            require([min0, max0, min1, max1] ==
                    [zero_low, zero_high, zero_low + a, zero_high + a], "conditional bounds")
            possible = [max0 >= lower and min0 <= upper, max1 >= lower and min1 <= upper]
            require(possible[value] and not possible[1 - value], "forced value lacks proof")
            batch[i] = value
        require(bool(batch), "empty noncontradictory step")
        assigned.update(batch)
        origins.update({i: number for i in batch})
    require(trace["values"] == [list(p) for p in sorted(assigned.items())], "final assignments")
    require(trace["origins"] == [list(p) for p in sorted(origins.items())], "final reasons")
    require(trace["contradiction_step"] is None, "unexpected contradiction summary")
    return assigned, origins


def residual_model(original, equations, values, origins, substitutions):
    result = cp_model_pb2.CpModelProto()
    result.variables.extend(original.variables)
    references = []
    for i, value in sorted(values.items()):
        row = result.constraints.add().linear
        row.vars.append(i)
        row.coeffs.append(1)
        row.domain.extend([value, value])
        references.append({"kind": "propagated_unit", "variable": i, "reason_step": origins[i]})
    expected_substitutions = []
    for number, (terms, lower, upper) in enumerate(equations):
        known = sum(a * values[i] for i, a in terms.items() if i in values)
        free = [(i, a) for i, a in terms.items() if i not in values]
        minimum = sum(min(a, 0) for _, a in free)
        maximum = sum(max(a, 0) for _, a in free)
        lo, hi = max(lower - known, minimum), min(upper - known, maximum)
        row = result.constraints.add().linear
        if lo > hi:
            row.domain.extend([1, 1])
        else:
            row.vars.extend(i for i, _ in free)
            row.coeffs.extend(a for _, a in free)
            row.domain.extend([lo, hi])
        references.append({"kind": "substituted_original", "source_row": number})
        expected_substitutions.append({"row": number, "constant": known,
                                       "remaining_terms": len(free), "lower": lo, "upper": hi})
    require(expected_substitutions == substitutions, "substitution inventory")
    return result, references


def main():
    manifest = load(INPUT / "manifest.json")
    require(sha(INPUT / "build.py") == manifest["builder_sha256"], "builder changed")
    old_folder = HERE.parent / "four-seven-template-cnf-independent"
    previous = load(old_folder / "audit.json")
    require(previous["passed"] and sha(old_folder / "check.py") == previous["checker_sha256"],
            "previous circuit audit changed")
    spec = importlib.util.spec_from_file_location("checked_circuit", old_folder / "check.py")
    circuit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(circuit)
    entry = next(e for e in manifest["cases"] if e["case"] == "matching-063")
    original_entry = next(e for e in previous["cases"] if e["case"] == entry["case"])
    require(entry["source_model_sha256"] == original_entry["model_sha256"], "source audit chain")
    paths = {name: ROOT / entry[name] for name in
             ["source_model", "residual_model", "reasons", "cnf", "row_trace"]}
    for key, path in paths.items():
        require(sha(path) == entry[key + "_sha256"], "input hash: " + key)
    original = text_format.Parse(paths["source_model"].read_text(), cp_model_pb2.CpModelProto())
    require(len(original.variables) == 55528 and len(original.constraints) == 4559,
            "original dimensions")
    require(all(list(v.domain) == [0, 1] for v in original.variables), "original domains")
    equations = [equation(row) for row in original.constraints]
    reasons = load(paths["reasons"])
    values, origins = replay(equations, reasons)
    require(len(values) == entry["propagated_variables"] == 15663 and
            len(reasons["steps"]) == entry["propagation_steps"], "propagation dimensions")
    residual, refs = residual_model(original, equations, values, origins, reasons["substitutions"])
    saved = text_format.Parse(paths["residual_model"].read_text(), cp_model_pb2.CpModelProto())
    require(saved == residual and len(residual.constraints) == entry["residual_constraints"],
            "residual protobuf differs")
    traces = load(paths["row_trace"])
    require(len(traces) == len(residual.constraints), "trace count")
    with paths["cnf"].open() as stream:
        require(stream.readline().split() == ["p", "cnf", str(entry["variables"]),
                                              str(entry["clauses"])], "DIMACS header")
        check = circuit.StreamCheck(stream, len(original.variables))
        all_rows = zip(residual.constraints, refs, traces, strict=True)
        for number, (row, ref, trace) in enumerate(all_rows):
            terms, lo, hi, offset, flip = circuit.row_spec(row)
            before_top, before_count = check.top, check.count
            recipe = check.interval(terms, lo, hi)
            expected = {"row": number, **ref, "negative_offset": offset, "complemented": flip,
                        "arity": len(terms), "lower": lo, "upper": hi, "recipe": recipe,
                        "first_clause": before_count + 1,
                        "clause_count": check.count - before_count,
                        "first_auxiliary": before_top + 1,
                        "auxiliary_count": check.top - before_top,
                        "normalized_sha256": hashlib.sha256(json.dumps(
                            [terms, lo, hi], separators=(",", ":")).encode()).hexdigest()}
            require(trace == expected, "residual trace mismatch")
        require(not stream.read().strip(), "extra clauses")
        require(check.top == entry["variables"] and check.count == entry["clauses"],
                "final encoding counts")
    controls = []
    for label, field, value in [("wrong constant", "constant", 999),
                                ("cyclic reason", "support_steps", [0]),
                                ("wrong lower bound", "lower", 999),
                                ("wrong assignment count", "assigned_before", 5)]:
        damaged = copy.deepcopy(reasons)
        damaged["steps"][0][field] = value
        try:
            replay(equations, damaged)
        except ValueError as error:
            controls.append({"control": label, "rejected": str(error)})
        else:
            raise ValueError("damaged reason accepted")
    for label, mutate in [("wrong forced value", lambda d:
                          d["steps"][0]["forced"][0].__setitem__(
                              1, 1 - d["steps"][0]["forced"][0][1])),
                          ("bad conditional bound", lambda d:
                           d["steps"][0]["forced"][0].__setitem__(2, 99)),
                          ("missing final value", lambda d: d["values"].pop()),
                          ("missing final origin", lambda d: d["origins"].pop())]:
        damaged = copy.deepcopy(reasons)
        mutate(damaged)
        try:
            replay(equations, damaged)
        except ValueError as error:
            controls.append({"control": label, "rejected": str(error)})
        else:
            raise ValueError("damaged assignment accepted: " + label)
    report = {"passed": True, "case": entry["case"], "checker_sha256": sha(Path(__file__)),
              "circuit_checker_sha256": sha(old_folder / "check.py"),
              "manifest_sha256": sha(INPUT / "manifest.json"),
              "source_model_sha256": sha(paths["source_model"]),
              "residual_model_sha256": sha(paths["residual_model"]),
              "cnf_sha256": sha(paths["cnf"]), "reasons_sha256": sha(paths["reasons"]),
              "propagation_steps": len(reasons["steps"]), "proved_values": len(values),
              "clauses": check.count, "variables": check.top, "damaged_controls": controls,
              "scope": "Equivalence gate for propagated matching-063 only. "
              "No solve or UNSAT proof."}
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
