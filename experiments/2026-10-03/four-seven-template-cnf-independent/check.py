# Document:    Independent Restricted CNF Translation Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check every DIMACS clause against the original Boolean model and threshold lemma."""

import gzip
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from pysat.solvers import Glucose4

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "four-seven-template-cnf"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(data)
    return result.hexdigest()


def row_spec(row):
    """Obtain a sum of signed Boolean literals directly from its integer equation."""
    require(not row.enforcement_literal, "conditional constraint")
    if row.WhichOneof("constraint") == "exactly_one":
        terms = [v + 1 if v >= 0 else v for v in row.exactly_one.literals]
        bounds = [1, 1]
        negative_constant = 0
    else:
        require(row.WhichOneof("constraint") == "linear", "unknown constraint")
        require(len(row.linear.domain) == 2, "noninterval domain")
        require(len(row.linear.vars) == len(row.linear.coeffs), "coefficient count")
        terms, negative_constant = [], 0
        for var, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True):
            require(var >= 0, "negative linear column")
            terms += [var + 1 if coefficient > 0 else -var - 1] * abs(coefficient)
            negative_constant += min(0, coefficient)
        bounds = [int(v) - negative_constant for v in row.linear.domain]
    lo, hi = max(0, bounds[0]), min(len(terms), bounds[1])
    flipped = False
    if lo <= hi:
        forward = max(lo, hi + 1 if hi < len(terms) else 0)
        reverse = max(len(terms) - hi, len(terms) - lo + 1 if lo > 0 else 0)
        if reverse < forward:
            terms = [-v for v in terms]
            lo, hi, flipped = len(terms) - hi, len(terms) - lo, True
    return terms, lo, hi, negative_constant, flipped


class StreamCheck:
    def __init__(self, stream, original_variables):
        self.stream = stream
        self.top = original_variables
        self.count = 0

    def fresh(self):
        self.top += 1
        return self.top

    def clause(self, terms):
        if True in [v for v in terms if type(v) is bool]:
            return
        expected = [v for v in terms if type(v) is int]
        line = self.stream.readline()
        require(bool(line), "missing clause")
        actual = [int(v) for v in line.split()]
        require(actual and actual[-1] == 0 and 0 not in actual[:-1], "invalid clause")
        require(sorted(actual[:-1]) == sorted(expected), "clause does not match row circuit")
        require(all(1 <= abs(v) <= self.top for v in actual[:-1]), "future or bad variable")
        self.count += 1

    @staticmethod
    def inverse(v):
        return not v if type(v) is bool else -v

    def interval(self, terms, lo, hi):
        n = len(terms)
        if lo > hi:
            self.clause([])
            return "contradiction"
        if (lo, hi) == (0, n):
            return "tautology"
        if hi == 0 or lo == n:
            for term in terms:
                self.clause([-term if hi == 0 else term])
            return "all_false" if hi == 0 else "all_true"
        if hi == 1:
            counters = []
            for position in range(n - 1):
                counters.append(self.fresh())
                self.clause([-terms[position], counters[-1]])
                if position:
                    self.clause([-counters[-2], counters[-1]])
                    self.clause([-terms[position], -counters[-2]])
            self.clause([-terms[-1], -counters[-1]])
            if lo:
                self.clause(terms)
            return "sinz_atmost_one"
        if lo == 1 and hi == n:
            self.clause(terms)
            return "atleast_one"
        needed = max(lo, hi + 1 if hi < n else 0)
        # Thresholds T(i,j) mean at least j true inputs in the first i positions.
        # The four clauses are the two implications of T = A or (input and B).
        levels = {0: True}
        for position, literal in enumerate(terms, 1):
            next_levels = {0: True}
            for threshold in range(1, min(position, needed) + 1):
                same = levels.get(threshold, False)
                one_less = levels.get(threshold - 1, False)
                variable = self.fresh()
                self.clause([self.inverse(same), variable])
                self.clause([-literal, self.inverse(one_less), variable])
                self.clause([-variable, same, literal])
                self.clause([-variable, same, one_less])
                next_levels[threshold] = variable
            levels = next_levels
        if lo:
            self.clause([levels[lo]])
        if hi < n:
            self.clause([self.inverse(levels[hi + 1])])
        return "equivalent_threshold_recurrence"


def semantic_checks(builder):
    rows = []
    # Direct weighted sums are the oracle, including signed/repeated literals.
    for coefficients in itertools.product(range(-2, 3), repeat=2):
        for lo in range(-4, 5):
            for hi in range(lo, 5):
                row = cp_model_pb2.ConstraintProto()
                row.linear.vars.extend([0, 1])
                row.linear.coeffs.extend(coefficients)
                row.linear.domain.extend([lo, hi])
                rows.append((row, coefficients, (lo, hi)))
    for literals in itertools.product([0, 1, -1, -2], repeat=3):
        row = cp_model_pb2.ConstraintProto()
        row.exactly_one.literals.extend(literals)
        rows.append((row, None, None))
    assignments = 0
    recipes = set()
    for row, coefficients, bounds in rows:
        output = io.StringIO()
        encoder = builder.Encoder(output, 2)
        terms, lo, hi, _, _ = builder.normalize(row)
        recipes.add(encoder.interval(terms, lo, hi))
        clauses = [[int(v) for v in line.split()[:-1]] for line in output.getvalue().splitlines()]
        # Two-way recurrence gate correctness is checked below on all 16 truth assignments.
        with Glucose4(bootstrap_with=clauses) as solver:
            for values in itertools.product((0, 1), repeat=2):
                if coefficients is not None:
                    value = sum(a * x for a, x in zip(coefficients, values, strict=True))
                    expected = bounds[0] <= value <= bounds[1]
                else:
                    expected = sum(values[v] if v >= 0 else 1 - values[-v - 1]
                                   for v in row.exactly_one.literals) == 1
                assumption = [i + 1 if x else -i - 1 for i, x in enumerate(values)]
                require(solver.solve(assumptions=assumption) == expected,
                        "signed-row semantic mismatch")
                assignments += 1
    for a, b, x, q in itertools.product((False, True), repeat=4):
        clauses = [(not a or q), (not x or not b or q),
                   (not q or a or x), (not q or a or b)]
        require(all(clauses) == (q == (a or (x and b))), "gate truth table")
    require(len(recipes) == 7, "unexercised encoding recipe")
    controls = []
    for text in ["-1 0\n", "1 2 0\n", "1 0\n1 0\n", "0\n", "1 0 0\n", ""]:
        rejected = False
        try:
            stream = io.StringIO(text)
            check = StreamCheck(stream, 1)
            check.clause([1])
            require(not stream.read().strip(), "extra clauses")
        except ValueError:
            rejected = True
        require(rejected, "damaged clause accepted")
        controls.append({"damaged_dimacs": text, "rejected": True})
    return {"rows": len(rows), "assignment_checks": assignments,
            "gate_truth_assignments": 16, "recipes": sorted(recipes),
            "damaged_controls": controls}


def main():
    manifest = json.loads((INPUT / "manifest.json").read_text())
    restricted = HERE.parent / "four-seven-template-cp-restricted"
    require(sha(restricted / "manifest.json") == manifest["restricted_manifest_sha256"],
            "restricted model manifest changed")
    require(sha(restricted / "independent-audit.json") == manifest["restricted_audit_sha256"],
            "restricted model audit changed")
    prior_audit = json.loads((restricted / "independent-audit.json").read_text())
    require(prior_audit["passed"] and prior_audit["manifest_sha256"] ==
            manifest["restricted_manifest_sha256"], "prior encoding gate failed")
    prior = {e["case"]: e for e in json.loads((restricted / "manifest.json").read_text())["cases"]}
    require({e["case"] for e in manifest["cases"]} == set(prior), "case inventory changed")
    source = INPUT / "build.py"
    require(sha(source) == manifest["builder_sha256"], "frozen builder changed")
    spec = importlib.util.spec_from_file_location("frozen_cnf_builder", source)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    semantics = semantic_checks(builder)
    records = []
    for entry in manifest["cases"]:
        require(entry["source_model"] == prior[entry["case"]]["model"] and
                entry["source_model_sha256"] == prior[entry["case"]]["model_sha256"],
                "CNF source is not the audited restricted model")
        cnf, model_path, trace_path = (ROOT / entry[k] for k in
                                       ("cnf", "source_model", "row_trace"))
        for path, key in [(cnf, "cnf_sha256"), (model_path, "source_model_sha256"),
                          (trace_path, "row_trace_sha256")]:
            require(sha(path) == entry[key], "input hash mismatch")
        proto = text_format.Parse(model_path.read_text(), cp_model_pb2.CpModelProto())
        require(len(proto.variables) == 55528, "original variable count")
        require(all(list(v.domain) == [0, 1] for v in proto.variables), "original Boolean domains")
        require({d.name for d, _ in proto.ListFields()} <= {"variables", "constraints", "name"},
                "untranslated model field")
        traces = json.loads(gzip.decompress(trace_path.read_bytes()))
        require(len(traces) == len(proto.constraints) == 4559, "row count")
        with cnf.open() as stream:
            require(stream.readline().split() == ["p", "cnf", str(entry["variables"]),
                                                  str(entry["clauses"])], "DIMACS header")
            check = StreamCheck(stream, len(proto.variables))
            for number, (row, trace) in enumerate(zip(proto.constraints, traces, strict=True)):
                terms, lo, hi, offset, flip = row_spec(row)
                require(all(1 <= abs(v) <= 55528 for v in terms), "source variable boundary")
                before_top, before_count = check.top, check.count
                recipe = check.interval(terms, lo, hi)
                expected = {"row": number, "kind": row.WhichOneof("constraint"),
                            "source_row_sha256": hashlib.sha256(
                                row.SerializeToString(deterministic=True)).hexdigest(),
                            "negative_offset": offset, "complemented": flip,
                            "arity": len(terms), "lower": lo, "upper": hi, "recipe": recipe,
                            "normalized_sha256": hashlib.sha256(json.dumps(
                                [terms, lo, hi], separators=(",", ":")).encode()).hexdigest(),
                            "first_clause": before_count + 1,
                            "clause_count": check.count - before_count,
                            "first_auxiliary": before_top + 1,
                            "auxiliary_count": check.top - before_top}
                require(trace == expected, "row trace mismatch")
            require(not stream.read().strip(), "unexpected trailing clauses")
            require(check.top == entry["variables"] and check.count == entry["clauses"],
                    "final clause or auxiliary count")
        records.append({"case": entry["case"], "cnf_sha256": sha(cnf),
                        "model_sha256": sha(model_path), "variables": check.top,
                        "clauses": check.count, "rows": len(proto.constraints)})
        print(json.dumps(records[-1]), flush=True)
    report = {"passed": True, "manifest_sha256": sha(INPUT / "manifest.json"),
              "checker_sha256": sha(Path(__file__)), "cases": records, "semantics": semantics,
              "scope": "Equivalent CNF encoding of two already restricted CP models only. "
              "No SAT/UNSAT search or proof-check result is established by this audit."}
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "rows": semantics["rows"],
                      "assignment_checks": semantics["assignment_checks"]}), flush=True)


if __name__ == "__main__":
    main()
