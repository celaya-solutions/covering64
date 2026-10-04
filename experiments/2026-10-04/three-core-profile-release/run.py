# Document:    Three-Core Three-Profile Release Pilots
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      0b185073a68c9c80f5b7048fa4cb57ac24c1ad62037caa79cafbe40c394fef92
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
RAW = ROOT / "experiments/scratch/three-core-profile-release-20261004"
SEED = 2026104103
CAP_AUDIT_PATH = DAY / "core-cap-independent/audit.json"
RELEASE = DAY / "six-hole-strong-core-release"
THIRD_CORE_AUDIT_PATH = DAY / "third-core-independent/audit.json"
STRONG_POSTCHECK_PATH = DAY / "six-hole-strong-core-release-independent/postcheck.json"
NEW_PARTITION = [[1, 2, 3], [5, 6, 7], [8, 12, 16], [9, 10, 11], [13, 14, 15]]
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


def core_rows():
    third = json.loads(THIRD_CORE_AUDIT_PATH.read_text())
    assert third["passed"] and third["recommended_upper_bound"] == 55
    return basis.core_rows() + [third["core_global_ids"]]


def partitions():
    return basis.partitions() + [NEW_PARTITION]


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
    for core in core_rows():
        model.add(sum(variables[i] for i in core) <= 55)
    indicators = []
    for partition_index, partition in enumerate(partitions()):
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
    model.minimize(65 * sum(holes) + sum(variables[i] for i in core_rows()[0]))
    chosen = set(hint)
    for i, variable in enumerate(variables):
        model.add_hint(variable, int(i in chosen))
    missing = set(basis.profile(hint)["holes"])
    for i, hole in enumerate(holes):
        model.add_hint(hole, int(i in missing))
    for indicator, triple_id, threshold in indicators:
        model.add_hint(indicator, int(len(chosen.intersection(SUPPORT[triple_id])) >= threshold))
    assert len(model.proto.variables) == 4958 and len(model.proto.constraints) == 1188
    assert not model.validate()
    return model, variables, holes


def select_hints(pools):
    postcheck = json.loads(STRONG_POSTCHECK_PATH.read_text())
    assert postcheck["passed"] and postcheck["producer_optimizer_calls"] == 2
    assert postcheck["result_sha256"] == sha(RELEASE / "result.json")
    assert postcheck["manifest_sha256"] == sha(RELEASE / "manifest.json")
    records, bound = [], {}
    cores, partition_rows = core_rows(), partitions()
    for case in postcheck["cases"]:
        for item in case["saved"] + [case["final"]]:
            relative, digest = item["path"], item["sha256"]
            path = ROOT / relative
            assert relative not in bound and sha(path) == digest
            bound[relative] = digest
            ids = basis.read_seed(path)
            assert ids == item["ids"] and len(ids) == len(set(ids)) == 64
            holes = len(basis.profile(ids)["holes"])
            assert holes == item["holes"]
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
                    "origin": "strong_core_independent_postcheck",
                    "holes": holes,
                    "ids": ids,
                    "core_overlaps": overlaps,
                    "partition_counts": counts,
                    "all_core_caps_pass": core_ok,
                    "all_profile_cuts_pass": profile_ok,
                    "eligible": core_ok and profile_ok,
                    "pool_membership": {
                        name: set(ids) <= set(pool) for name, pool in pools.items()
                    },
                    "missing_pool_ids": {
                        name: sorted(set(ids) - set(pool)) for name, pool in pools.items()
                    },
                }
            )
    assert len(records) == 15
    selected = {}
    for name in pools:
        legal = sorted(
            (row for row in records if row["eligible"] and row["pool_membership"][name]),
            key=lambda row: (row["holes"], row["core_overlaps"][0], row["path"]),
        )
        selected[name] = legal[0]
    assert selected["adaptive-952"]["holes"] == 13
    assert selected["adaptive-952"]["core_overlaps"] == [1, 7, 51]
    assert selected["full-4368"]["holes"] == 10
    assert selected["full-4368"]["core_overlaps"] == [1, 8, 55]
    return selected, records, bound


def prepare():
    assert not (HERE / "manifest.json").exists() and not RAW.exists()
    previous = json.loads((RELEASE / "manifest.json").read_text())
    cap = json.loads(CAP_AUDIT_PATH.read_text())
    third = json.loads(THIRD_CORE_AUDIT_PATH.read_text())
    postcheck = json.loads(STRONG_POSTCHECK_PATH.read_text())
    assert cap["passed"] and third["passed"] and postcheck["passed"]
    assert cap["optimizer_calls"] == third["optimizer_calls"] == 0
    assert cap["recommended_upper_bound"] == third["recommended_upper_bound"] == 55
    assert previous["core_rows"] == core_rows()[:2]
    assert previous["partitions"] == partitions()[:2]
    assert previous["source_sha256"] == sha(RELEASE / "run.py")
    assert third["sources"][str(STRONG_POSTCHECK_PATH.relative_to(ROOT))] == sha(
        STRONG_POSTCHECK_PATH
    )
    final_scan = postcheck["cases"][1]["final"]["all_five_heavy_scan"]
    assert any(x["triples"] == NEW_PARTITION for x in final_scan["five_heavy_obstructions"])
    pools = {case["name"]: case["pool"] for case in previous["cases"]}
    assert len(pools["adaptive-952"]) == 952
    assert pools["full-4368"] == list(range(4368))
    selected, selection_records, selection_bound = select_hints(pools)
    dump(
        HERE / "hint-selection.json",
        {
            "selected": selected,
            "candidates": selection_records,
            "ordering": ["holes", "original_core_overlap", "path"],
            "scope": (
                "All 15 independently checked strong-core saved/final paths; "
                "pool-specific legal hints."
            ),
            "optimizer_calls": 0,
        },
    )
    RAW.mkdir(parents=True)
    parameters_path = RAW / "frozen-parameters.pbtxt"
    parameters_path.write_text(str(solver_for().parameters))
    cases = []
    for name, pool in pools.items():
        chosen = selected[name]
        hint = chosen["ids"]
        model, _, _ = build_model(pool, hint)
        path = RAW / f"{name}-model.pbtxt"
        path.write_text(str(model.proto))
        cases.append(
            {
                "name": name,
                "pool": pool,
                "pool_size": len(pool),
                "hint": hint,
                "hint_source_path": chosen["path"],
                "hint_sha256": chosen["sha256"],
                "hint_holes": chosen["holes"],
                "hint_core_overlaps": chosen["core_overlaps"],
                "hint_composite_objective": 65 * chosen["holes"] + chosen["core_overlaps"][0],
                "model_path": str(path.relative_to(ROOT)),
                "model_sha256": sha(path),
                "parameters_path": str(parameters_path.relative_to(ROOT)),
                "parameters_sha256": sha(parameters_path),
            }
        )
    paths = [
        Path(__file__),
        RELEASE / "run.py",
        RELEASE / "manifest.json",
        RELEASE / "result.json",
        STRONG_POSTCHECK_PATH,
        STRONG_POSTCHECK_PATH.with_name("postcheck.py"),
        THIRD_CORE_AUDIT_PATH,
        THIRD_CORE_AUDIT_PATH.with_name("check.py"),
        THIRD_CORE_AUDIT_PATH.with_name("manifest.json"),
        HERE / "hint-selection.json",
    ]
    inputs = dict(previous["input_files"])
    inputs.update(third["sources"])
    inputs.update(selection_bound)
    inputs.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    for relative, digest in inputs.items():
        assert sha(ROOT / relative) == digest
    indicators = [
        {
            "partition": partition_index,
            "position": position,
            "threshold": threshold,
            "triple": triple,
            "variable_id": 4928 + 10 * partition_index + 2 * position + (threshold - 6),
        }
        for partition_index, partition in enumerate(partitions())
        for position, triple in enumerate(partition)
        for threshold in [6, 7]
    ]
    manifest = {
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "ortools_version": ortools.__version__,
        "python_version": sys.version,
        "input_files": inputs,
        "proof_files": previous["proof_files"],
        "sources": previous["sources"],
        "seed": SEED,
        "seed_policy": "Identical seed and parameters in both cases; no offset.",
        "hint_policy": (
            "Best eligible checked hint within each unchanged pool. The globally best 10-hole "
            "hint contains three blocks outside the adaptive pool; hints therefore differ."
        ),
        "core_rows": core_rows(),
        "core_upper_bound": 55,
        "strong_core_audit_path": str(CAP_AUDIT_PATH.relative_to(ROOT)),
        "strong_core_audit_sha256": sha(CAP_AUDIT_PATH),
        "strong_core_translations": cap["current_core_translations"],
        "third_core_audit_path": str(THIRD_CORE_AUDIT_PATH.relative_to(ROOT)),
        "third_core_audit_sha256": sha(THIRD_CORE_AUDIT_PATH),
        "third_core_map_images": third["map_images"],
        "hint_selection_path": str((HERE / "hint-selection.json").relative_to(ROOT)),
        "hint_selection_sha256": sha(HERE / "hint-selection.json"),
        "previous_release_manifest_sha256": sha(RELEASE / "manifest.json"),
        "partitions": partitions(),
        "profile_rule": previous["profile_rule"],
        "threshold_indicators": indicators,
        "profile_threshold_truth_table_sha256": previous["profile_threshold_truth_table_sha256"],
        "original_elite_global_ids": previous["original_elite_global_ids"],
        "hole_triple_ids": previous["hole_triple_ids"],
        "hole_triples": previous["hole_triples"],
        "hole_carrier_global_ids": previous["hole_carrier_global_ids"],
        "cases": cases,
        "variables": 4958,
        "rows": 1188,
        "block_variables": 4368,
        "objective": previous["objective"],
        "budget": {"cases": 2, "seconds_per_case": 120, "workers": 4},
        "optimization_calls": 0,
        "scope": (
            "Two bounded construction pilots with different hints, not a controlled pool-size "
            "comparison. Both models "
            "release all 64 slots and retain cardinality, exact hole indicators, three "
            "independently checked core<=55 rows, and three proved five-heavy partition cuts. "
            "The adaptive pool remains 952 blocks; the full pool remains all 4368 blocks. "
            "No new radius or overlap cap. Newly observed obstructions are recorded, not "
            "used for an undeclared extra solve. No global lower-bound theorem follows."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "source_sha256": sha(__file__),
                "manifest_sha256": sha(HERE / "manifest.json"),
                "cases": [
                    {
                        k: case[k]
                        for k in [
                            "name",
                            "pool_size",
                            "hint_holes",
                            "hint_sha256",
                            "model_sha256",
                            "parameters_sha256",
                        ]
                    }
                    for case in cases
                ],
                "optimization_calls": 0,
            }
        )
    )


def save_state(ids, holes, value, path):
    recounted = basis.profile(ids)
    overlap = len(set(ids) & set(core_rows()[0]))
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
        model, variables, holes = build_model(case["pool"], case["hint"])
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
