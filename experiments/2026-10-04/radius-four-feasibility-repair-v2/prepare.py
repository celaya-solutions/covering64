# Document:    Radius-Four Feasibility Repair Preparation
# Version:     v2.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      daac02e7d11e6349075d3e2b3a65d75aa3f16ddaf0333ecc46cf64dd421c3477
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze a two-row local feasibility model without calling a solver."""

import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
from pathlib import Path

import ortools
from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/radius-four-feasibility-repair-v2-20261004"
PRIOR = HERE.parent / "soft-pair-hole-priority"
BASE = HERE.parent / "weak-pair-swap-scan-runtime-independent/swap-881-1142.txt"
BASE_SHA = "44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a"
PRIOR_SHA = "d33005daaaa946d57c4fa5bb15f3bcb70eda9d86087dbb149f582ccc0c36f0b9"
PREP_SHA = "98e7f124cfb1f89af8555298bf0fb27d7b5d783e84aa6a27134546188c337cf3"
D29_MANIFEST = HERE.parent / "weak-pair-d29-relabel-screen/manifest.json"
D29_MANIFEST_SHA = "8de73d082aae946e5bc4c4c2a609de6a46f8ebe8916cd0b3f7780f2ad86aab00"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def prior_module():
    path = PRIOR / "prepare.py"
    require(sha(path) == PREP_SHA, "prior preparer changed")
    spec = importlib.util.spec_from_file_location("frozen_soft_preparer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def helper_module():
    return prior_module().helper_module()


def recount(ids, cores, baseline_ids):
    actual = prior_module().recount(ids, cores)
    del actual["metrics"]["canonical_objective"]
    overlap = len(set(ids) & set(baseline_ids))
    actual["metrics"].update(
        {"cardinality": len(ids), "baseline_overlap": overlap, "replacement_distance": 64 - overlap}
    )
    return actual


def check_vector(model, values):
    require(len(values) == len(model.proto.variables), "incomplete vector")
    for index, (var, value) in enumerate(zip(model.proto.variables, values, strict=True)):
        domain = list(var.domain)
        require(
            type(value) is int
            and any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)),
            f"variable domain violation {index}",
        )
    enforced = 0
    for index, constraint in enumerate(model.proto.constraints):
        literals = list(constraint.enforcement_literal)
        require(constraint.has_linear(), f"nonlinear constraint {index}")
        if not all(values[lit] == 1 if lit >= 0 else values[-lit - 1] == 0 for lit in literals):
            continue
        enforced += 1
        linear = constraint.linear
        value = sum(
            coefficient * values[var]
            for var, coefficient in zip(linear.vars, linear.coeffs, strict=True)
        )
        domain = list(linear.domain)
        require(
            any(domain[i] <= value <= domain[i + 1] for i in range(0, len(domain), 2)),
            f"linear row violation {index}",
        )
    return {
        "variables_checked": len(values),
        "rows_checked": len(model.proto.constraints),
        "enforced_rows_checked": enforced,
    }


def proto_hash(proto):
    return hashlib.sha256(proto.SerializeToString(deterministic=True)).hexdigest()


def bound_inputs():
    require(sha(PRIOR / "manifest.json") == PRIOR_SHA, "prior manifest changed")
    require(sha(D29_MANIFEST) == D29_MANIFEST_SHA, "D29 audit manifest changed")
    prior = json.loads((PRIOR / "manifest.json").read_text())
    screen = json.loads(D29_MANIFEST.read_text())
    require(screen["passed"] is True, "D29 screen failed")
    inputs = prior["sources"] | prior["input_files"] | screen["files"]
    inputs[str((PRIOR / "manifest.json").relative_to(ROOT))] = PRIOR_SHA
    inputs[str(D29_MANIFEST.relative_to(ROOT))] = D29_MANIFEST_SHA
    inputs[str(BASE.relative_to(ROOT))] = BASE_SHA
    for kind in ("model", "parameters"):
        inputs[prior[f"{kind}_path"]] = prior[f"{kind}_sha256"]
    for path, digest in inputs.items():
        require(sha(ROOT / path) == digest, f"bound input changed: {path}")
    return prior, inputs


def main():
    require(not RAW.exists() and not (HERE / "manifest.json").exists(), "preparation exists")
    prior, inputs = bound_inputs()
    helper = helper_module()
    cores = helper.load_sources()
    require(cores == prior["core_rows"], "core rows changed")
    blocks = helper.parse(BASE.read_text())
    rank = {block: index for index, block in enumerate(prior_module().SETS[5])}
    ids = sorted(rank[block] for block in blocks)
    require(len(ids) == 64, "baseline cardinality")
    actual = recount(ids, cores, ids)
    require(actual["metrics"]["holes"] == 12, "baseline holes changed")
    require(actual["metrics"]["D2max"] == actual["metrics"]["D2sum"] == 29, "baseline D2")
    verification = helper.dual_verify(blocks, 12)

    original = cp_model_pb2.CpModelProto()
    text_format.Parse((ROOT / prior["model_path"]).read_text(), original)
    require(len(original.variables) == 5728, "base variables")
    require(len(original.constraints) == 14405, "base constraints")
    require(original.HasField("objective"), "base objective missing")
    require(len(original.solution_hint.vars) == 5728, "base hint missing")
    reduced = cp_model_pb2.CpModelProto()
    reduced.CopyFrom(original)
    reduced.ClearField("objective")
    reduced.ClearField("solution_hint")
    model_proto = cp_model_pb2.CpModelProto()
    model_proto.CopyFrom(reduced)
    overlap = model_proto.constraints.add()
    overlap.name = "radius_four_baseline_overlap"
    overlap.linear.vars.extend(ids)
    overlap.linear.coeffs.extend([1] * 64)
    overlap.linear.domain.extend([60, 9223372036854775807])
    holes = model_proto.constraints.add()
    holes.name = "radius_four_holes_at_most_eleven"
    holes.linear.vars.extend(range(5048, 5608))
    holes.linear.coeffs.extend([1] * 560)
    holes.linear.domain.extend([-9223372036854775808, 11])
    prefix = cp_model_pb2.CpModelProto()
    prefix.CopyFrom(model_proto)
    del prefix.constraints[14405:]
    require(prefix == reduced, "unexpected inherited proto change")
    require(not model_proto.HasField("objective"), "objective not cleared")
    require(not model_proto.HasField("solution_hint"), "hint not cleared")
    require(not model_proto.HasField("floating_point_objective"), "floating objective present")
    parameters = sat_parameters_pb2.SatParameters()
    text_format.Parse((ROOT / prior["parameters_path"]).read_text(), parameters)
    old_parameters = sat_parameters_pb2.SatParameters()
    old_parameters.CopyFrom(parameters)
    parameters.random_seed = 2026105201
    check_parameters = sat_parameters_pb2.SatParameters()
    check_parameters.CopyFrom(parameters)
    check_parameters.random_seed = old_parameters.random_seed
    require(check_parameters == old_parameters, "unexpected parameter change")
    require(
        parameters.max_time_in_seconds == 300 and parameters.num_search_workers == 4,
        "budget changed",
    )

    model = cp_model.CpModel()
    require(model.proto.parse_text_format(text_format.MessageToString(model_proto)), "native parse")
    require(not model.validate(), "native model validation failed")
    base_model = cp_model.CpModel()
    require(base_model.proto.parse_text_format(text_format.MessageToString(reduced)), "base parse")
    baseline_check = check_vector(base_model, actual["values"])
    try:
        check_vector(model, actual["values"])
    except ValueError as error:
        require(str(error) == "linear row violation 14406", "unexpected baseline rejection")
        baseline_rejection = str(error)
    else:
        raise ValueError("12-hole baseline incorrectly accepted")

    RAW.mkdir(parents=True)
    (RAW / "model.pbtxt").write_text(text_format.MessageToString(model_proto))
    (RAW / "parameters.pbtxt").write_text(text_format.MessageToString(parameters))
    dump(RAW / "baseline-vector.json", {"values": actual["values"], "is_solution_hint": False})
    dump(HERE / "baseline-verification.json", verification)
    dump(
        HERE / "baseline-profile.json",
        {
            "candidate_sha256": BASE_SHA,
            "actual_metrics": actual["metrics"],
            "pair_details": actual["pair_details"],
            "global_profile": helper.global_profile(actual["triple_counts"]),
            "base_vector_check": baseline_check,
            "new_model_rejection": baseline_rejection,
            "is_solution_hint": False,
        },
    )
    sources = {
        str(path.relative_to(ROOT)): sha(path)
        for path in (HERE / "prepare.py", HERE / "execute.py", HERE / "runner_controls.py")
    }
    archive = RAW / "frozen-sources"
    for path, digest in (sources | inputs).items():
        if path.endswith(".py"):
            destination = archive / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, destination)
            require(sha(destination) == digest, "source archive mismatch")
    semantics = {
        "optimizer_calls": 1,
        "objective": None,
        "hint_entries": 0,
        "cp_sat_seconds": 300,
        "workers": 4,
        "seed": 2026105201,
        "watchdog_seconds": 330,
        "termination_grace_seconds": 5,
        "conditional_route": "Root launches only after two-swap terminal with no <=11 candidate.",
        "stop_policy": "CP-SAT feasibility may finish on the first <=11-hole partial. Callback "
        "explicitly stops only on a dual-verified actual cover. No relaunch or "
        "budget transfer, even if a partial is found early.",
        "records": "Save every callback and final full vector, witness, fresh metrics including "
        "D3/D4, exact row checks, and both verifier receipts; no objective score.",
        "scope": "Radius <=4 around the frozen D29 representative, inherited soft rows and four "
        "named core caps, <=11 holes. No explicit hard quadruple rows. Partial success "
        "is not a cover; timeout/UNKNOWN is inconclusive; no global inference.",
    }
    dump(HERE / "runner-semantics.json", semantics)
    preparation = {
        "passed": True,
        "optimizer_calls": 0,
        "model_validate": "",
        "all_inherited_fields_equal_after_objective_and_hint_clear": True,
        "unchanged_prefix_proto_sha256": proto_hash(reduced),
        "new_model_proto_sha256": proto_hash(model_proto),
        "added_constraint_indices": [14405, 14406],
        "baseline_not_feasible_for_new_model": True,
        "baseline_rejection": baseline_rejection,
        "parameter_delta": {"random_seed": [old_parameters.random_seed, 2026105201]},
    }
    dump(HERE / "preparation.json", preparation)
    files = {
        str(path.relative_to(ROOT)): sha(path) for path in sorted(HERE.iterdir()) if path.is_file()
    }
    raw_files = {
        str(path.relative_to(ROOT)): sha(path) for path in sorted(RAW.rglob("*")) if path.is_file()
    }
    manifest = {
        "document": "Radius-Four Feasibility Repair Manifest",
        "version": "v2.0.0",
        "date": "2026-10-04",
        "status": "PREPARED_NOT_RUN",
        "optimizer_calls": 0,
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "ortools_version": ortools.__version__,
        "python_version": platform.python_version(),
        "candidate_path": str(BASE.relative_to(ROOT)),
        "candidate_sha256": BASE_SHA,
        "baseline_ids": ids,
        "core_rows": cores,
        "variables": 5728,
        "constraints": 14407,
        "variable_order": "All 4368 lexicographic block variables unchanged; pairs 4368..4487; "
        "triples 4488..5047; holes 5048..5607; soft deficits 5608..5727.",
        "objective": "none",
        "full_hint_entries": 0,
        "budget_seconds": 300,
        "workers": 4,
        "seed": 2026105201,
        "watchdog_seconds": 330,
        "termination_grace_seconds": 5,
        "model_delta": "Clear objective and all hints; append overlap >=60 and holes <=11 only.",
        "parameter_delta": preparation["parameter_delta"],
        "unchanged_prefix_proto_sha256": proto_hash(reduced),
        "prior_manifest_sha256": PRIOR_SHA,
        "d29_screen_manifest_sha256": D29_MANIFEST_SHA,
        "model_path": str((RAW / "model.pbtxt").relative_to(ROOT)),
        "model_sha256": sha(RAW / "model.pbtxt"),
        "parameters_path": str((RAW / "parameters.pbtxt").relative_to(ROOT)),
        "parameters_sha256": sha(RAW / "parameters.pbtxt"),
        "sources": sources,
        "input_files": inputs,
        "files": files,
        "raw_files": raw_files,
        "scope": semantics["scope"],
        "stop_policy": semantics["stop_policy"],
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "prepared": True,
                "optimizer_calls": 0,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "model_sha256": manifest["model_sha256"],
                "parameters_sha256": manifest["parameters_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
