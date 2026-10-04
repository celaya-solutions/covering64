# Document:    Restricted Boolean Template CP to Proof CNF Translation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Stream exact signed-row translations with auditable sequential threshold circuits."""

import gzip
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "four-seven-template-cp-restricted"
OUTPUT = ROOT / "experiments/scratch/four-seven-template-cnf-v1.0.0"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def neg(literal):
    return not literal if isinstance(literal, bool) else -literal


def limit(lower, upper, size):
    return max(lower if lower > 0 else 0, upper + 1 if upper < size else 0)


def normalize(row):
    kind = row.WhichOneof("constraint")
    require(not row.enforcement_literal, "conditional constraint is unsupported")
    if kind == "exactly_one":
        # CP literals encode not(index) as -index-1; DIMACS encodes -(index+1).
        literals = [i + 1 if i >= 0 else i for i in row.exactly_one.literals]
        lower, upper, offset = 1, 1, 0
    else:
        require(kind == "linear" and len(row.linear.domain) == 2, "unsupported row")
        literals = []
        offset = 0
        for index, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True):
            require(index >= 0, "negative linear variable index")
            if coefficient > 0:
                literals.extend([index + 1] * coefficient)
            elif coefficient < 0:
                literals.extend([-(index + 1)] * -coefficient)
                offset += coefficient
        lower, upper = (int(bound) - offset for bound in row.linear.domain)
    n = len(literals)
    lower, upper = max(0, lower), min(n, upper)
    flip = False
    if lower <= upper and limit(n - upper, n - lower, n) < limit(lower, upper, n):
        literals = [-i for i in literals]
        lower, upper = n - upper, n - lower
        flip = True
    return literals, lower, upper, offset, flip


class Encoder:
    def __init__(self, stream, original_variables):
        self.stream = stream
        self.variables = original_variables
        self.clauses = 0

    def variable(self):
        self.variables += 1
        return self.variables

    def emit(self, literals):
        # Constants occur only within threshold gates. Integer repeated literals remain repeated.
        if any(value is True for value in literals):
            return
        clause = [v for v in literals if v is not False]
        require(all(type(v) is int and v != 0 for v in clause), "invalid DIMACS literal")
        self.stream.write(" ".join(map(str, clause)) + (" " if clause else "") + "0\n")
        self.clauses += 1

    def atmost_one(self, literals):
        if len(literals) < 2:
            return
        previous = None
        for literal in literals[:-1]:
            current = self.variable()
            self.emit([-literal, current])
            if previous is not None:
                self.emit([-previous, current])
                self.emit([-literal, -previous])
            previous = current
        self.emit([-literals[-1], -previous])

    def interval(self, literals, lower, upper):
        n = len(literals)
        if lower > upper:
            self.emit([])
            return "contradiction"
        if lower == 0 and upper == n:
            return "tautology"
        if upper == 0:
            for literal in literals:
                self.emit([-literal])
            return "all_false"
        if lower == n:
            for literal in literals:
                self.emit([literal])
            return "all_true"
        if upper == 1:
            self.atmost_one(literals)
            if lower == 1:
                self.emit(literals)
            return "sinz_atmost_one"
        if lower == 1 and upper == n:
            self.emit(literals)
            return "atleast_one"
        maximum = limit(lower, upper, n)
        previous = [True] + [False] * maximum
        for position, literal in enumerate(literals, 1):
            current = [True] + [False] * maximum
            for threshold in range(1, min(position, maximum) + 1):
                # q(i,j) iff q(i-1,j) OR (literal_i AND q(i-1,j-1)).
                a, b = previous[threshold], previous[threshold - 1]
                q = self.variable()
                self.emit([neg(a), q])
                self.emit([-literal, neg(b), q])
                self.emit([-q, a, literal])
                self.emit([-q, a, b])
                current[threshold] = q
            previous = current
        if lower > 0:
            self.emit([previous[lower]])
        if upper < n:
            self.emit([neg(previous[upper + 1])])
        return "equivalent_threshold_recurrence"


def translate(meta):
    source = ROOT / meta["model"]
    require(sha(source) == meta["model_sha256"], "restricted CP model changed")
    proto = cp_model_pb2.CpModelProto()
    text_format.Parse(source.read_text(), proto)
    require(all(list(v.domain) == [0, 1] for v in proto.variables), "non-Boolean variable")
    require(
        {d.name for d, _ in proto.ListFields()} <= {"variables", "constraints", "name"},
        "unsupported model field",
    )
    require(
        len(proto.variables) == 55528 and len(proto.constraints) == 4559, "restricted dimensions"
    )
    partial = OUTPUT / (meta["case"] + ".clauses")
    traces = []
    with partial.open("w", buffering=1024 * 1024) as stream:
        encoder = Encoder(stream, len(proto.variables))
        for number, row in enumerate(proto.constraints):
            literals, lower, upper, offset, flip = normalize(row)
            before_variables, before_clauses = encoder.variables, encoder.clauses
            recipe = encoder.interval(literals, lower, upper)
            traces.append(
                {
                    "row": number,
                    "kind": row.WhichOneof("constraint"),
                    "source_row_sha256": hashlib.sha256(
                        row.SerializeToString(deterministic=True)
                    ).hexdigest(),
                    "negative_offset": offset,
                    "complemented": flip,
                    "arity": len(literals),
                    "lower": lower,
                    "upper": upper,
                    "recipe": recipe,
                    "normalized_sha256": hashlib.sha256(
                        json.dumps([literals, lower, upper], separators=(",", ":")).encode()
                    ).hexdigest(),
                    "first_clause": before_clauses + 1,
                    "clause_count": encoder.clauses - before_clauses,
                    "first_auxiliary": before_variables + 1,
                    "auxiliary_count": encoder.variables - before_variables,
                }
            )
    target = OUTPUT / (meta["case"] + ".cnf")
    with target.open("wb") as final, partial.open("rb") as body:
        final.write(f"p cnf {encoder.variables} {encoder.clauses}\n".encode())
        shutil.copyfileobj(body, final, 1024 * 1024)
    trace = OUTPUT / (meta["case"] + "-rows.json.gz")
    trace.write_bytes(gzip.compress(json.dumps(traces, separators=(",", ":")).encode(), mtime=0))
    return {
        "case": meta["case"],
        "hub_case": meta["hub_case"],
        "fixed_ids": meta["fixed_ids"],
        "source_model": meta["model"],
        "source_model_sha256": sha(source),
        "cnf": str(target.relative_to(ROOT)),
        "cnf_sha256": sha(target),
        "cnf_bytes": target.stat().st_size,
        "original_variables": len(proto.variables),
        "variables": encoder.variables,
        "clauses": encoder.clauses,
        "source_constraints": len(proto.constraints),
        "row_trace": str(trace.relative_to(ROOT)),
        "row_trace_sha256": sha(trace),
    }


def main():
    require(not OUTPUT.exists(), "new output directory required")
    manifest = json.loads((INPUT / "manifest.json").read_text())
    audit = json.loads((INPUT / "independent-audit.json").read_text())
    require(
        audit["passed"] is True and sha(INPUT / "manifest.json") == audit["manifest_sha256"],
        "restricted model audit chain",
    )
    require(
        sha(INPUT / "check_independent.py") == audit["checker_sha256"], "restricted audit changed"
    )
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "build.py").write_bytes(Path(__file__).read_bytes())
    result = {
        "version": "v1.0.0",
        "builder_sha256": sha(Path(__file__)),
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "restricted_manifest_sha256": sha(INPUT / "manifest.json"),
        "restricted_audit_sha256": sha(INPUT / "independent-audit.json"),
        "cases": [translate(case) for case in manifest["cases"]],
        "scope": "Exact extension of two audited restricted Boolean CP models. "
        "Original variable i maps to DIMACS i+1. No solve or UNSAT proof yet.",
    }
    for path in [HERE / "manifest.json", OUTPUT / "manifest.json"]:
        path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
