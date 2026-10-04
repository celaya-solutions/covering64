# Document:    Matched Core-Cap-55 Adaptive Pool and Full-Universe Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2bebf64fa9e13c5c283e80e017298e4ee7076a516b96317483c918a25a69388c
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare or run two frozen models; solving requires an independent gate."""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ortools
from ortools.sat.python import cp_model

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/six-hole-strong-core-release-20261004"
SEED = 2026104102
HINT_PATH = DAY / "heterogeneous-profile-pool/elite/best-02-h14.txt"
CAP_AUDIT_PATH = DAY / "core-cap-independent/audit.json"
RELEASE = DAY / "six-hole-pool-release"
AUDIT_PATH = DAY / "heterogeneous-profile-postcheck/audit.json"
PRIOR = DAY / "heterogeneous-profile-pool"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


basis = load(PRIOR / "run.py", "six_hole_release_basis")
BLOCKS, TRIPLES, SUPPORT = basis.BLOCKS, basis.TRIPLES, basis.SUPPORT
sha, dump = basis.sha, basis.dump


def solver_for():
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120
    solver.parameters.num_search_workers = 4
    solver.parameters.random_seed = SEED
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False
    return solver


def build_model(pool, hint):
    allowed = set(pool)
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f"block_{i}") for i in range(len(BLOCKS))]
    holes = [model.new_bool_var(f"hole_{i}") for i in range(len(TRIPLES))]
    model.add(sum(variables) == 64)
    model.add(
        cp_model.LinearExpr.sum([variables[i] for i in range(len(BLOCKS)) if i not in allowed]) == 0
    )
    for hole, carriers in zip(holes, SUPPORT, strict=True):
        coverage = sum(variables[i] for i in carriers)
        model.add(coverage >= 1).only_enforce_if(hole.Not())
        model.add(coverage == 0).only_enforce_if(hole)
    for core in basis.core_rows():
        model.add(sum(variables[i] for i in core) <= 55)
    indicators = []
    for partition_index, partition in enumerate(basis.partitions()):
        sixes, sevens = [], []
        for position, triple in enumerate(partition):
            triple_id = TRIPLES.index(tuple(triple))
            count = sum(variables[i] for i in SUPPORT[triple_id])
            six = model.new_bool_var(f"partition_{partition_index}_triple_{position}_at_least_6")
            seven = model.new_bool_var(f"partition_{partition_index}_triple_{position}_at_least_7")
            model.add(count >= 6).only_enforce_if(six)
            model.add(count <= 5).only_enforce_if(six.Not())
            model.add(count >= 7).only_enforce_if(seven)
            model.add(count <= 6).only_enforce_if(seven.Not())
            sixes.append(six)
            sevens.append(seven)
            indicators.extend([(six, triple_id, 6), (seven, triple_id, 7)])
        model.add(5 * sum(sixes) + sum(sevens) <= 26)
    model.minimize(65 * sum(holes) + sum(variables[i] for i in basis.core_rows()[0]))
    chosen = set(hint)
    for i, variable in enumerate(variables):
        model.add_hint(variable, int(i in chosen))
    missing = set(basis.profile(hint)["holes"])
    for i, hole in enumerate(holes):
        model.add_hint(hole, int(i in missing))
    for indicator, triple_id, threshold in indicators:
        model.add_hint(indicator, int(len(chosen.intersection(SUPPORT[triple_id])) >= threshold))
    assert len(model.proto.variables) == 4948 and len(model.proto.constraints) == 1166
    assert not model.validate()
    return model, variables, holes


def select_hint():
    inventory_path = DAY / "heterogeneous-seed-inventory/inventory.json"
    inventory = json.loads(inventory_path.read_text())
    profile_audit = json.loads(AUDIT_PATH.read_text())
    release_audit_path = DAY / "six-hole-pool-release-independent/postcheck.json"
    release_audit = json.loads(release_audit_path.read_text())
    release_result = json.loads((RELEASE / "result.json").read_text())
    assert profile_audit["passed"] and release_audit["passed"]
    assert release_audit["result_sha256"] == sha(RELEASE / "result.json")
    candidates = [
        (item["path"], item["sha256"], "original_inventory") for item in inventory["entries"]
    ]
    candidates += [
        (item["path"], item["sha256"], "profile_postcheck")
        for item in profile_audit["checked_states"]
    ]
    for case in release_result["cases"]:
        candidates += [
            (item["path"], item["sha256"], "matched_release_postcheck")
            for item in case["improvements"] + [case["final"]]
            if item is not None
        ]
    records, seen, bound = [], set(), {}
    cores, partition_rows = basis.core_rows(), basis.partitions()
    for relative, digest, origin in candidates:
        if relative in seen:
            continue
        seen.add(relative)
        path = ROOT / relative
        assert sha(path) == digest
        bound[relative] = digest
        ids = basis.read_seed(path)
        holes = len(basis.profile(ids)["holes"])
        overlaps = [len(set(ids) & set(core)) for core in cores]
        counts = [
            [len(set(ids) & set(SUPPORT[TRIPLES.index(tuple(t))])) for t in row]
            for row in partition_rows
        ]
        core_ok = all(value <= 55 for value in overlaps)
        profile_ok = all(
            5 * sum(value >= 6 for value in row) + sum(value >= 7 for value in row) <= 26
            for row in counts
        )
        records.append(
            {
                "path": relative,
                "sha256": digest,
                "origin": origin,
                "holes": holes,
                "core_overlaps": overlaps,
                "partition_counts": counts,
                "both_core_caps_pass": core_ok,
                "both_profile_cuts_pass": profile_ok,
                "eligible": core_ok and profile_ok,
            }
        )
    legal = sorted(
        (row for row in records if row["eligible"]),
        key=lambda row: (row["holes"], row["core_overlaps"][0], row["path"]),
    )
    selected = legal[0]
    assert ROOT / selected["path"] == HINT_PATH
    assert selected["holes"] == 14 and selected["core_overlaps"] == [1, 7]
    return selected, records, bound, [inventory_path, release_audit_path, RELEASE / "result.json"]


def prepare():
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    prior = json.loads((PRIOR / "manifest.json").read_text())
    cap = json.loads(CAP_AUDIT_PATH.read_text())
    assert cap["passed"] and cap["optimizer_calls"] == 0
    assert cap["recommended_upper_bound"] == 55
    assert [row["core_global_ids"] for row in cap["current_core_translations"]] == basis.core_rows()
    assert all(row["recommended_upper_bound"] == 55 for row in cap["current_core_translations"])
    chosen, selection_records, selection_bound, selection_paths = select_hint()
    audit = json.loads(AUDIT_PATH.read_text())
    assert audit["passed"] and audit["producer_manifest_sha256"] == sha(PRIOR / "manifest.json")
    assert audit["producer_result_sha256"] == sha(PRIOR / "result.json")
    states = [item for item in audit["checked_states"] if item["facts"]["holes"] == 6]
    assert len(states) == 4 and all(
        not x["facts"]["all_disjoint_five_heavy_obstructions"] for x in states
    )
    sources, missing = [], set()
    for item in states:
        path = ROOT / item["path"]
        assert sha(path) == item["sha256"]
        ids = basis.read_seed(path)
        recounted = basis.profile(ids)
        assert len(recounted["holes"]) == 6
        missing.update(recounted["holes"])
        sources.append(
            {
                "path": item["path"],
                "sha256": item["sha256"],
                "ids": ids,
                "profile": recounted,
                "is_final_response": item["is_final_response"],
            }
        )
    assert len(missing) == 12
    hint = basis.read_seed(HINT_PATH)
    assert sha(HINT_PATH) == "e942f6018640e2ead11e6e1f4ec9c3d16cf64166ed504f680f2fd04207cd0e2c"
    assert len(basis.profile(hint)["holes"]) == 14
    original_core = basis.core_rows()[0]
    assert len(set(hint) & set(original_core)) == 1
    elite = set(prior["cases"][0]["pool"])
    assert prior["cases"][0]["name"] == "elite" and len(elite) == 277
    carriers = set().union(*(set(SUPPORT[t]) for t in missing))
    assert len(carriers) == 720
    adaptive = sorted(elite | carriers)
    assert len(adaptive) == 952 and set(hint) <= set(adaptive)
    pools = {"adaptive-952": adaptive, "full-4368": list(range(len(BLOCKS)))}
    dump(
        HERE / "hint-selection.json",
        {"selected": chosen, "candidates": selection_records, "optimizer_calls": 0},
    )
    RAW.mkdir(parents=True)
    parameters_path = RAW / "frozen-parameters.pbtxt"
    parameters_path.write_text(str(solver_for().parameters))
    cases = []
    for name, pool in pools.items():
        model, _, _ = build_model(pool, hint)
        path = RAW / f"{name}-model.pbtxt"
        path.write_text(str(model.proto))
        cases.append(
            {
                "name": name,
                "pool": pool,
                "pool_size": len(pool),
                "model_path": str(path.relative_to(ROOT)),
                "model_sha256": sha(path),
                "parameters_path": str(parameters_path.relative_to(ROOT)),
                "parameters_sha256": sha(parameters_path),
            }
        )
    paths = [
        Path(__file__),
        PRIOR / "run.py",
        PRIOR / "manifest.json",
        PRIOR / "result.json",
        DAY / "heterogeneous-profile-pool-independent/gate.json",
        AUDIT_PATH,
        DAY / "heterogeneous-profile-postcheck/check.py",
    ]
    paths += selection_paths + [
        CAP_AUDIT_PATH,
        CAP_AUDIT_PATH.with_name("check.py"),
        CAP_AUDIT_PATH.with_name("replay.json"),
        HERE / "hint-selection.json",
        RELEASE / "manifest.json",
    ]
    inputs = dict(prior["input_files"])
    inputs.update(cap["sources"])
    inputs.update(selection_bound)
    inputs.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    inputs.update({row["path"]: row["sha256"] for row in sources})
    for relative, digest in inputs.items():
        assert sha(ROOT / relative) == digest
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "ortools_version": ortools.__version__,
        "python_version": sys.version,
        "input_files": inputs,
        "proof_files": prior["proof_files"],
        "sources": sources,
        "hint_source_path": str(HINT_PATH.relative_to(ROOT)),
        "hint_sha256": sha(HINT_PATH),
        "hint": hint,
        "hint_holes": 14,
        "hint_original_core_overlap": 1,
        "hint_composite_objective": 911,
        "seed": SEED,
        "seed_policy": "Identical seed and parameters in both cases; no offset.",
        "core_rows": basis.core_rows(),
        "core_upper_bound": 55,
        "strong_core_audit_path": str(CAP_AUDIT_PATH.relative_to(ROOT)),
        "strong_core_audit_sha256": sha(CAP_AUDIT_PATH),
        "strong_core_translations": cap["current_core_translations"],
        "hint_selection_path": str((HERE / "hint-selection.json").relative_to(ROOT)),
        "hint_selection_sha256": sha(HERE / "hint-selection.json"),
        "previous_release_manifest_sha256": sha(RELEASE / "manifest.json"),
        "essential_correction": (
            "The previous59-core-block states violate the already checked maximum55-core "
            "condition for full64-block covers. This new pilot applies that stronger proved "
            "cap to both checked core images and uses a legal14-hole hint."
        ),
        "partitions": basis.partitions(),
        "profile_rule": prior["profile_rule"],
        "threshold_indicators": prior["threshold_indicators"],
        "profile_threshold_truth_table_sha256": prior["threshold_truth_table_sha256"],
        "original_elite_global_ids": sorted(elite),
        "hole_triple_ids": sorted(missing),
        "hole_triples": [TRIPLES[t] for t in sorted(missing)],
        "hole_carrier_global_ids": sorted(carriers),
        "cases": cases,
        "variables": 4948,
        "rows": 1166,
        "block_variables": 4368,
        "objective": {
            "hole_coefficient": 65,
            "original_core_coefficient": 1,
            "original_core_global_ids": original_core,
            "rationale": "Core overlap is between 0 and 60; one fewer hole always wins.",
        },
        "budget": {"cases": 2, "seconds_per_case": 120, "workers": 4},
        "optimization_calls": 0,
        "scope": (
            "Matched bounded construction pilot. Both models release all 64 slots and retain "
            "only cardinality, exact hole indicators, two independently checked core<=55 rows, "
            "and two "
            "proved five-heavy partition cuts. The adaptive case also restricts its block pool. "
            "The full case includes all 4368 blocks. The objective prefers fewer holes first, "
            "then less original-core overlap. No new overlap cap or hidden radius. A newly "
            "observed forbidden partition is recorded at postcheck, not used for an extra solve. "
            "No infeasibility or global lower-bound theorem follows from these bounded calls."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "source_sha256": sha(__file__),
                "manifest_sha256": sha(HERE / "manifest.json"),
                "cases": cases,
                "optimization_calls": 0,
            }
        )
    )


def save_state(ids, holes, value, path):
    recounted = basis.profile(ids)
    overlap = len(set(ids) & set(basis.core_rows()[0]))
    assert len(ids) == len(set(ids)) == 64
    assert holes == recounted["holes"] and value == 65 * len(holes) + overlap
    path.write_text("".join(" ".join(map(str, BLOCKS[i])) + "\n" for i in ids))
    return {
        "composite_objective": value,
        "holes": len(holes),
        "original_core_overlap": overlap,
        "ids": ids,
        "profile": recounted,
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
    }


class SaveBest(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables, holes, directory):
        super().__init__()
        self.variables, self.holes, self.directory = variables, holes, directory
        self.best = 65 * 561 + 60
        self.records = []

    def on_solution_callback(self):
        value = int(round(self.objective_value))
        if value >= self.best:
            return
        ids = [i for i, variable in enumerate(self.variables) if self.value(variable)]
        missing = [i for i, hole in enumerate(self.holes) if self.value(hole)]
        overlap = value - 65 * len(missing)
        path = self.directory / f"best-{len(self.records):02d}-h{len(missing)}-c{overlap}.txt"
        self.records.append(save_state(ids, missing, value, path))
        self.best = value
        if not missing:
            self.stop_search()


def run(gate_path):
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert (
        manifest["source_sha256"] == sha(__file__)
        and manifest["ortools_version"] == ortools.__version__
    )
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    assert not (RAW / "start.json").exists() and not (HERE / "result.json").exists()
    for path in [Path(__file__), HERE / "manifest.json", gate_path]:
        (RAW / path.name).write_bytes(path.read_bytes())
    dump(
        RAW / "start.json",
        {
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "manifest_sha256": sha(HERE / "manifest.json"),
            "gate_sha256": sha(gate_path),
        },
    )
    records = []
    for case in manifest["cases"]:
        directory = HERE / case["name"]
        directory.mkdir()
        model, variables, holes = build_model(case["pool"], manifest["hint"])
        assert hashlib.sha256(str(model.proto).encode()).hexdigest() == case["model_sha256"]
        solver = solver_for()
        assert (
            hashlib.sha256(str(solver.parameters).encode()).hexdigest() == case["parameters_sha256"]
        )
        logs = []
        solver.log_callback = logs.append
        callback = SaveBest(variables, holes, directory)
        before = time.monotonic()
        status = solver.solve(model, callback)
        elapsed = time.monotonic() - before
        paths = {
            "log": RAW / f"{case['name']}-solver.log",
            "response": RAW / f"{case['name']}-response.pbtxt",
            "parameters": RAW / f"{case['name']}-parameters.pbtxt",
        }
        paths["log"].write_text("".join(logs))
        paths["response"].write_text(str(solver.response_proto))
        paths["parameters"].write_text(str(solver.parameters))
        record = {
            "name": case["name"],
            "status": solver.status_name(status),
            "seconds": elapsed,
            "reported_seconds": solver.wall_time,
            "objective_bound": solver.best_objective_bound,
            "best_composite_objective": callback.best if callback.records else None,
            "improvements": callback.records,
            "final": None,
            "raw_files": {
                key: {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}
                for key, path in paths.items()
            },
        }
        if status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
            ids = [i for i, variable in enumerate(variables) if solver.value(variable)]
            missing = [i for i, hole in enumerate(holes) if solver.value(hole)]
            value = int(round(solver.objective_value))
            record["final"] = save_state(ids, missing, value, directory / "final-response.txt")
        records.append(record)
        dump(
            HERE / "result.json",
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "gate_sha256": sha(gate_path),
                "cases": records,
                "optimizer_calls": len(records),
                "global_lower_bound_claim": False,
            },
        )
        print(
            json.dumps(
                {k: record[k] for k in ("name", "status", "seconds", "best_composite_objective")}
            ),
            flush=True,
        )
        if record["final"] is not None and record["final"]["holes"] == 0:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--run", type=Path, metavar="GATE_JSON")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    else:
        run(args.run)
