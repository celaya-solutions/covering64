# Document:    Checked-Reason Boolean Propagation Before CNF Translation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare smaller equivalent CNFs, preserving every original-variable propagation reason."""

import gzip
import hashlib
import importlib.util
import json
import shutil
from collections import defaultdict
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CP = HERE.parent / "four-seven-template-cp-restricted"
PREVIOUS = HERE.parent / "four-seven-template-cnf"
OUTPUT = ROOT / "experiments/scratch/four-seven-template-cnf-propagated-v1.0.0"
ENCODER_SHA = "4fc5f86cf00426c1abae09a76c8c1f641560f9d8e9232be29a0d8369329af26c"
SPEC = importlib.util.spec_from_file_location("audited_threshold_encoder", PREVIOUS / "build.py")
ENC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENC)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def save_gzip(path, data):
    path.write_bytes(gzip.compress(json.dumps(data, separators=(",", ":")).encode(), mtime=0))


def equation(row):
    require(not row.enforcement_literal, "conditional source row")
    coefficients = defaultdict(int)
    kind = row.WhichOneof("constraint")
    if kind == "linear":
        require(len(row.linear.domain) == 2, "noninterval source row")
        for variable, coefficient in zip(row.linear.vars, row.linear.coeffs, strict=True):
            require(variable >= 0, "negative linear index")
            coefficients[variable] += coefficient
        lower, upper = row.linear.domain
    else:
        require(kind == "exactly_one", "unsupported source row")
        negative = 0
        for literal in row.exactly_one.literals:
            if literal >= 0:
                coefficients[literal] += 1
            else:
                coefficients[-literal - 1] -= 1
                negative += 1
        lower = upper = 1 - negative
    return [(i, a) for i, a in sorted(coefficients.items()) if a], lower, upper


def propagate(equations):
    values, origins, steps = {}, {}, []
    contradiction = None

    def visit(number):
        nonlocal contradiction
        terms, lower, upper = equations[number]
        constant = sum(a * values[i] for i, a in terms if i in values)
        unknown = [(i, a) for i, a in terms if i not in values]
        minimum = constant + sum(min(0, a) for _, a in unknown)
        maximum = constant + sum(max(0, a) for _, a in unknown)
        support = sorted({origins[i] for i, _ in terms if i in values})
        forced = []
        conflict_variable = None
        impossible = minimum > upper or maximum < lower
        if not impossible:
            for i, a in unknown:
                min0, max0 = minimum - min(0, a), maximum - max(0, a)
                min1, max1 = min0 + a, max0 + a
                feasible0 = min0 <= upper and max0 >= lower
                feasible1 = min1 <= upper and max1 >= lower
                if not feasible0 and not feasible1:
                    impossible, conflict_variable = True, i
                    break
                if feasible0 != feasible1:
                    forced.append([i, int(feasible1), min0, max0, min1, max1])
        if not forced and not impossible:
            return False
        step = {
            "step": len(steps),
            "row": number,
            "support_steps": support,
            "assigned_before": len(values),
            "constant": constant,
            "minimum": minimum,
            "maximum": maximum,
            "lower": lower,
            "upper": upper,
            "forced": [] if impossible else forced,
            "contradiction": impossible,
            "conflict_variable": conflict_variable,
        }
        steps.append(step)
        if impossible:
            contradiction = step["step"]
            return False
        for i, value, *_ in forced:
            require(i not in values, "duplicate propagated variable")
            values[i], origins[i] = value, step["step"]
        return True

    # Collect original one-variable constraints before propagating longer rows.
    for number, (terms, _, _) in enumerate(equations):
        if len(terms) == 1:
            visit(number)
            if contradiction is not None:
                return values, origins, steps, contradiction
    while True:
        changed = False
        for number in range(len(equations)):
            changed = visit(number) or changed
            if contradiction is not None:
                return values, origins, steps, contradiction
        if not changed:
            return values, origins, steps, contradiction


def build(meta):
    source = ROOT / meta["model"]
    require(ENC.sha(source) == meta["model_sha256"], "source model changed")
    original = cp_model_pb2.CpModelProto()
    text_format.Parse(source.read_text(), original)
    require(all(list(v.domain) == [0, 1] for v in original.variables), "source not Boolean")
    require(
        {d.name for d, _ in original.ListFields()} <= {"variables", "constraints", "name"},
        "unsupported source model fields",
    )
    equations = [equation(row) for row in original.constraints]
    values, origins, steps, contradiction = propagate(equations)
    residual = cp_model_pb2.CpModelProto()
    residual.variables.extend(original.variables)
    refs = []
    for variable, value in sorted(values.items()):
        row = residual.constraints.add().linear
        row.vars.append(variable)
        row.coeffs.append(1)
        row.domain.extend([value, value])
        refs.append(
            {"kind": "propagated_unit", "variable": variable, "reason_step": origins[variable]}
        )
    substitutions = []
    for number, (terms, lower, upper) in enumerate(equations):
        constant = sum(a * values[i] for i, a in terms if i in values)
        unknown = [(i, a) for i, a in terms if i not in values]
        minimum, maximum = sum(min(0, a) for _, a in unknown), sum(max(0, a) for _, a in unknown)
        clipped_lower, clipped_upper = (
            max(lower - constant, minimum),
            min(upper - constant, maximum),
        )
        row = residual.constraints.add().linear
        if clipped_lower > clipped_upper:
            row.domain.extend([1, 1])
        else:
            row.vars.extend(i for i, _ in unknown)
            row.coeffs.extend(a for _, a in unknown)
            row.domain.extend([clipped_lower, clipped_upper])
        refs.append({"kind": "substituted_original", "source_row": number})
        substitutions.append(
            {
                "row": number,
                "constant": constant,
                "remaining_terms": len(unknown),
                "lower": clipped_lower,
                "upper": clipped_upper,
            }
        )
    path = OUTPUT / (meta["case"] + "-residual.pbtxt")
    path.write_text(text_format.MessageToString(residual))
    reasons = OUTPUT / (meta["case"] + "-reasons.json.gz")
    save_gzip(
        reasons,
        {
            "steps": steps,
            "values": sorted(values.items()),
            "origins": sorted(origins.items()),
            "contradiction_step": contradiction,
            "substitutions": substitutions,
        },
    )
    body = OUTPUT / (meta["case"] + ".clauses")
    traces = []
    with body.open("w", buffering=1024 * 1024) as output:
        encoder = ENC.Encoder(output, len(original.variables))
        for number, row in enumerate(residual.constraints):
            literals, lower, upper, offset, flip = ENC.normalize(row)
            start_var, start_clause = encoder.variables, encoder.clauses
            recipe = encoder.interval(literals, lower, upper)
            traces.append(
                {
                    "row": number,
                    **refs[number],
                    "negative_offset": offset,
                    "complemented": flip,
                    "arity": len(literals),
                    "lower": lower,
                    "upper": upper,
                    "recipe": recipe,
                    "first_clause": start_clause + 1,
                    "clause_count": encoder.clauses - start_clause,
                    "first_auxiliary": start_var + 1,
                    "auxiliary_count": encoder.variables - start_var,
                    "normalized_sha256": hashlib.sha256(
                        json.dumps([literals, lower, upper], separators=(",", ":")).encode()
                    ).hexdigest(),
                }
            )
    cnf = OUTPUT / (meta["case"] + ".cnf")
    with cnf.open("wb") as target, body.open("rb") as clauses:
        target.write(f"p cnf {encoder.variables} {encoder.clauses}\n".encode())
        shutil.copyfileobj(clauses, target, 1024 * 1024)
    trace = OUTPUT / (meta["case"] + "-rows.json.gz")
    save_gzip(trace, traces)
    return {
        "case": meta["case"],
        "hub_case": meta["hub_case"],
        "fixed_ids": meta["fixed_ids"],
        "source_model": meta["model"],
        "source_model_sha256": ENC.sha(source),
        "residual_model": str(path.relative_to(ROOT)),
        "residual_model_sha256": ENC.sha(path),
        "reasons": str(reasons.relative_to(ROOT)),
        "reasons_sha256": ENC.sha(reasons),
        "propagated_variables": len(values),
        "propagation_steps": len(steps),
        "propagation_contradiction": contradiction is not None,
        "original_variables": len(original.variables),
        "original_constraints": len(original.constraints),
        "residual_constraints": len(residual.constraints),
        "cnf": str(cnf.relative_to(ROOT)),
        "cnf_sha256": ENC.sha(cnf),
        "cnf_bytes": cnf.stat().st_size,
        "variables": encoder.variables,
        "clauses": encoder.clauses,
        "row_trace": str(trace.relative_to(ROOT)),
        "row_trace_sha256": ENC.sha(trace),
    }


def main():
    require(not OUTPUT.exists(), "new output directory required")
    require(ENC.sha(PREVIOUS / "build.py") == ENCODER_SHA, "audited encoder changed")
    manifest = json.loads((CP / "manifest.json").read_text())
    audit = json.loads((CP / "independent-audit.json").read_text())
    require(
        audit["passed"] is True and ENC.sha(CP / "manifest.json") == audit["manifest_sha256"],
        "restricted CP audit chain",
    )
    OUTPUT.mkdir(parents=True)
    (OUTPUT / "build.py").write_bytes(Path(__file__).read_bytes())
    (OUTPUT / "audited-encoder.py").write_bytes((PREVIOUS / "build.py").read_bytes())
    result = {
        "version": "v1.0.0",
        "builder_sha256": ENC.sha(Path(__file__)),
        "encoder_sha256": ENCODER_SHA,
        "restricted_manifest_sha256": ENC.sha(CP / "manifest.json"),
        "restricted_audit_sha256": ENC.sha(CP / "independent-audit.json"),
        "cases": [build(case) for case in manifest["cases"]],
        "scope": "Preparation only. Each propagated value has an original-row arithmetic reason; "
        "all values remain explicit units. Independent propagation/translation audit required.",
    }
    for target in [HERE / "manifest.json", OUTPUT / "manifest.json"]:
        target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
