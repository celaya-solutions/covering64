# Document:    Independent Two-Point-Star V2 Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      d6ac16462646c12fd7abbb154f0705af09a1d08416a3b097cb9bc5cf13cb264d
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read saved CP outcomes and verify every recorded assignment and witness; no solving."""

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "two-point-star-repair-v2"
AUDIT = HERE.parent / "two-point-star-repair-v2-independent"
RAW = ROOT / "experiments/scratch/two-point-star-repair-v2-20261004"
MANIFEST = "39e895e1bc69b5bc7295460f1151cd951c4c06c1e5691a1a90482b26d0807f74"
GATE = "4856537e48cef8623b46a0abe6cd005e9f67deec67d3c02b0ddb9945208ed552"
BASE_SHA = "f8d2525acd5dcb7db6e60bbff70b60612b12a0a6500bd25ac0841b4de18c955d"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    require(not (HERE / "postcheck.json").exists(), "preserve postcheck")
    require(
        sha(PRODUCER / "manifest.json") == MANIFEST and sha(AUDIT / "gate.json") == GATE,
        "manifest/gate changed",
    )
    manifest, gate, result = (
        read(PRODUCER / "manifest.json"),
        read(AUDIT / "gate.json"),
        read(PRODUCER / "result.json"),
    )
    require(
        gate["passed"] is True and gate["decision"] == "GO" and gate["manifest_sha256"] == MANIFEST,
        "gate decision",
    )
    require(
        sha(PRODUCER / "run.py") == manifest["source_sha256"] == gate["producer_source_sha256"],
        "source changed",
    )
    require(sha(AUDIT / "check.py") == gate["source_sha256"], "gate source changed")
    require(
        result["manifest_sha256"] == MANIFEST
        and result["gate_sha256"] == GATE
        and result["relaunch"] is False
        and result["scope"] == manifest["scope"],
        "runtime bindings",
    )
    require(
        (manifest["seconds"], manifest["workers"], manifest["watchdog"], manifest["grace"])
        == (60, 4, 80, 5),
        "budget changed",
    )
    for entry in manifest["entries"]:
        require(sha(ROOT / entry["model"]) == entry["model_sha256"], "model changed")
    for relative, digest in result["raw_files"].items():
        require(sha(ROOT / relative) == digest, "raw file changed: " + relative)
    oracle_path = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    oracle = load("star_runtime_independent_oracle", oracle_path)
    standalone = load("star_runtime_standalone", ROOT / "scripts/check_cover.py")
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    base_path = HERE.parent / "weak-pair-d28-deterministic-descent/center-02.txt"
    require(sha(base_path) == BASE_SHA == manifest["base_sha256"], "center changed")
    base_ids = set(oracle.parse(base_path))
    cores = read(HERE.parent / "weak-pair-two-swap-scan-v2/manifest.json")["core_rows"]
    base = oracle.analyze(sorted(base_ids), cores)
    require(base["metrics"]["holes"] == 12 and base["metrics"]["D2max"] == 26, "base metrics")
    families, assignment_rows, run_checks = {}, [], []
    runs = result["runs"]
    require(type(runs) is list and 1 <= len(runs) <= 2, "run count")
    stopped = False
    for number, row in enumerate(runs, 1):
        require(
            not stopped and row == read(PRODUCER / f"run-{number}-result.json"), "run order/receipt"
        )
        entry = manifest["entries"][number - 1]
        require(
            row["number"] == entry["number"] == number and row["pivot"] == entry["pivot"], "pivot"
        )
        directory = RAW / f"run-{number}"
        command = row["command"]
        require(
            len(command) == 4
            and Path(command[0]).resolve() == Path(sys.executable).resolve()
            and command[1:] == [str((PRODUCER / "run.py").resolve()), "--child", str(number)],
            "child command",
        )
        require(
            type(row["watchdog_fired"]) is bool and type(row["returncode"]) is int, "exit flags"
        )
        require(
            type(row["elapsed_seconds"]) in (int, float)
            and math.isfinite(row["elapsed_seconds"])
            and row["elapsed_seconds"] >= 0,
            "wall time",
        )
        parameter_path = directory / "parameters.pbtxt"
        require(parameter_path.exists(), "solver parameter receipt missing")
        parameters = sat_parameters_pb2.SatParameters()
        text_format.Parse(parameter_path.read_text(), parameters)
        expected_parameters = sat_parameters_pb2.SatParameters(
            max_time_in_seconds=60,
            num_search_workers=4,
            random_seed=entry["seed"],
            log_search_progress=True,
        )
        require(
            parameters == expected_parameters and entry["seed"] == 2026105300 + number,
            "actual solver parameters",
        )
        require(
            (directory / "stdout.log").exists() and (directory / "stderr.log").exists(),
            "missing raw logs",
        )
        expected_vectors = sorted(directory.glob("callback-*.json"))
        callback_count = len(expected_vectors)
        require(
            [p.name for p in expected_vectors]
            == [f"callback-{i:03d}.json" for i in range(1, callback_count + 1)],
            "callback sequence",
        )
        if (directory / "final-vector.json").exists():
            expected_vectors.append(directory / "final-vector.json")
        require(
            [saved["vector"] for saved in row["saved"]]
            == [str(p.relative_to(ROOT)) for p in expected_vectors],
            "unreported vector",
        )
        pivot = set(entry["pivot"])
        for saved, vector_path in zip(row["saved"], expected_vectors, strict=True):
            values = read(vector_path)["values"]
            require(
                type(values) is list
                and len(values) == 4928
                and all(type(value) is int and value in (0, 1) for value in values),
                "Boolean vector",
            )
            ids = [i for i, value in enumerate(values[:4368]) if value]
            require(len(ids) == 64, "exact64 assignment")
            require(
                all(
                    values[i] == int(i in base_ids)
                    for i, block in enumerate(oracle.SUBSETS[5])
                    if set(block).isdisjoint(pivot)
                ),
                "outside-star membership",
            )
            require(
                sum(not set(oracle.SUBSETS[5][i]).isdisjoint(pivot) for i in ids) == 35,
                "free selected count",
            )
            blocks = [oracle.SUBSETS[5][i] for i in ids]
            witness_text = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
            digest = hashlib.sha256(witness_text.encode()).hexdigest()
            require(
                saved["sha256"] == digest and sha(ROOT / saved["witness"]) == digest, "witness hash"
            )
            if digest not in families:
                direct = oracle.analyze(ids, cores)
                require(direct["metrics"]["minimum_pair_count"] >= 5, "pair floor")
                package = verify_cover(blocks, 16, 5, 3)
                separate = standalone.verify_cover(blocks, 16, 5, 3, expected_blocks=64)
                holes = [
                    list(oracle.SUBSETS[3][i])
                    for i, count in enumerate(direct["counts"][3])
                    if count == 0
                ]
                require(
                    sorted(map(list, package["uncovered"])) == holes == separate["uncovered"],
                    "dual holes",
                )
                require(
                    package["canonical_sha256"] == separate["canonical_sha256"] == digest,
                    "dual hash",
                )
                require(package["valid"] == separate["valid"] == (not holes), "dual verdict")
                path = HERE / ("family-" + digest[:16] + ".txt")
                if path.exists():
                    require(sha(path) == digest, "independent witness collision")
                else:
                    path.write_text(witness_text)
                families[digest] = {
                    "ids": ids,
                    "sha256": digest,
                    "path": str(path.relative_to(ROOT)),
                    "metrics": direct["metrics"] | {"cardinality": 64},
                    "named_weak_core_legal": direct["legal"],
                    "holes": holes,
                    "hole_values": [int(count == 0) for count in direct["counts"][3]],
                    "package": package,
                    "standalone": separate,
                    "removed_from_D26": sorted(base_ids - set(ids)),
                    "added_to_D26": sorted(set(ids) - base_ids),
                }
            checked = families[digest]
            require(
                checked["ids"] == ids and values[4368:] == checked["hole_values"],
                "exact holes/vector alias",
            )
            require(
                saved["holes"] == sum(values[4368:]) == checked["metrics"]["holes"] <= 12,
                "objective witness",
            )
            require(len(saved["verifiers"]) == 2, "dual CLI receipts")
            for verifier in saved["verifiers"]:
                require(
                    verifier["canonical_sha256"] == digest
                    and verifier["blocks"] == 64
                    and verifier["uncovered"] == checked["holes"]
                    and verifier["valid"] is (not checked["holes"]),
                    "saved CLI result",
                )
            assignment_rows.append(
                {
                    "run": number,
                    "pivot": entry["pivot"],
                    "vector_path": saved["vector"],
                    "vector_sha256": sha(vector_path),
                    "family_sha256": digest,
                    "holes": saved["holes"],
                    "metrics": checked["metrics"],
                }
            )
        require(row["cover_found"] is any(s["holes"] == 0 for s in row["saved"]), "run cover label")
        outcome = row["outcome"]
        if outcome is not None:
            require(
                outcome == read(directory / "outcome.json")
                and outcome["callbacks"] == callback_count,
                "outcome/callback receipt",
            )
            response = cp_model_pb2.CpSolverResponse()
            text_format.Parse((directory / "response.pbtxt").read_text(), response)
            require(
                cp_model_pb2.CpSolverStatus.Name(response.status) == outcome["status"], "status"
            )
            require(
                response.objective_value == outcome["objective"]
                and response.best_objective_bound == outcome["bound"]
                and response.wall_time == outcome["wall_seconds"],
                "response metrics",
            )
            require(
                all(
                    type(outcome[key]) in (int, float) and math.isfinite(outcome[key])
                    for key in ("wall_seconds", "objective", "bound")
                ),
                "outcome numeric fields",
            )
            feasible = outcome["status"] in ("FEASIBLE", "OPTIMAL")
            require((directory / "final-vector.json").exists() is feasible, "final solution/status")
            if feasible:
                require(
                    list(response.solution) == read(directory / "final-vector.json")["values"],
                    "response solution mismatch",
                )
                require(outcome["objective"] == row["saved"][-1]["holes"], "solver objective")
                require(outcome["bound"] <= outcome["objective"], "objective bound")
                if outcome["status"] == "OPTIMAL":
                    require(outcome["bound"] == outcome["objective"], "optimal bound")
        else:
            require(not (directory / "outcome.json").exists(), "missing outcome label")
        stopped = (
            row["cover_found"] or row["watchdog_fired"] or row["returncode"] != 0 or outcome is None
        )
        if number < len(runs):
            require(not stopped, "continued past stop condition")
        run_checks.append(
            {
                "number": number,
                "pivot": entry["pivot"],
                "returncode": row["returncode"],
                "watchdog_fired": row["watchdog_fired"],
                "outcome": outcome,
                "callbacks": callback_count,
                "saved_assignments": len(expected_vectors),
                "best_recorded_holes": min((s["holes"] for s in row["saved"]), default=None),
                "cover_found": row["cover_found"],
                "elapsed_seconds": row["elapsed_seconds"],
            }
        )
    require(len(runs) == 2 or stopped, "omitted second run without stop")
    require(
        {p.name for p in RAW.glob("run-*") if p.is_dir()}
        == {f"run-{number}" for number in range(1, len(runs) + 1)},
        "unreported run directory",
    )
    require(
        result["cover_found"] is any(row["cover_found"] for row in runs), "campaign cover verdict"
    )
    if result["cover_found"]:
        cover_hash = sha(PRODUCER / "cover.txt")
        require(cover_hash in families and not families[cover_hash]["holes"], "saved cover")
    receipt = {
        "passed": True,
        "source_sha256": sha(__file__),
        "manifest_sha256": MANIFEST,
        "pre_run_gate_sha256": GATE,
        "producer_result_sha256": sha(PRODUCER / "result.json"),
        "source_revision": manifest["source_revision"],
        "ortools_version": manifest["ortools_version"],
        "base_sha256": BASE_SHA,
        "runs": run_checks,
        "assignments": assignment_rows,
        "checked_distinct_families": len(families),
        "families": list(families.values()),
        "cover_found": result["cover_found"],
        "runtime_raw_bindings": result["raw_files"],
        "solver_launches": 0,
        "search_relaunches": 0,
        "scope": (
            "Both fixed star neighborhoods only. All saved assignments, exact holes, pair floors, "
            "and dual verifier receipts independently checked. Weak/core metrics are diagnostics, "
            "not extra modeled rows. Solver bounds/status are recorded local reports, "
            "not independently "
            "checked global theorems. No new solve was run."
        ),
    }
    (HERE / "postcheck.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "runs": len(runs),
                "assignments": len(assignment_rows),
                "families": len(families),
                "best_holes_by_run": [r["best_recorded_holes"] for r in run_checks],
                "cover_found": result["cover_found"],
            }
        )
    )


if __name__ == "__main__":
    main()
