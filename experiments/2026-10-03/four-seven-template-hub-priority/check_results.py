# Document:    Combined Template-and-Hub Screen Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      e3ff4de9eae821317773fdb8cc56c1738a95063e88370186d158817ef0711195
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read back combined models, transitions, hashes and saved numerical primals."""

import argparse
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
NUMERIC_CHECKER_SHA256 = "2105a615be69d030442a0dbecc471f7e8354e75c86c53e901d181aca2488a2ed"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run = args.run
    checker_path = HERE.parent / "four-seven-template-link-screen/check_results.py"
    require(digest(checker_path) == NUMERIC_CHECKER_SHA256, "frozen numerical checker")
    spec = importlib.util.spec_from_file_location("numeric_readback", checker_path)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    metadata = load(run / "metadata.json")
    preflight = load(run / "preflight.json")
    require(
        preflight["valid"]
        and metadata["runner_sha256"] == preflight["runner_sha256"] == digest(run / "run.py"),
        "frozen preflight/runner",
    )
    require(digest(run / "preflight.json") == metadata["preflight_sha256"], "preflight hash")
    require(digest(run / "priority-plan.json") == metadata["plan_sha256"], "priority hash")
    plan = load(run / "priority-plan.json")
    results = load(run / "results.json.gz")
    require(len(results) == len(plan["priority"]) == 23, "complete priority coverage")
    require([r["id"] for r in results] == [r["id"] for r in plan["priority"]], "priority order")
    blocks = list(combinations(range(1, 17), 5))
    block_ids = {b: i for i, b in enumerate(blocks)}
    selection = load(HERE.parent / "four-seven-blossom-screen/remaining-representatives.json")
    edges = {r["id"]: r["edges"] for case in selection["cases"] for r in case["representatives"]}
    models, records = {}, []
    for result in results:
        case, (m4, z) = result["case"], result["hub_case"]
        key = f"{case}-m4-{m4}-z-{z}"
        directory = run / key
        info = metadata["models"][key]
        matrix_path = directory / "combined-base-rows.json.gz"
        if key not in models:
            require(digest(matrix_path) == info["combined_matrix_sha256"], "combined matrix hash")
            model = load(matrix_path)
            original_path = (
                REPO
                / "experiments/scratch/four-seven-template-hull-20261003"
                / case
                / "extended-rows.json.gz"
            )
            require(digest(original_path) == info["original_matrix_sha256"], "original matrix hash")
            original = load(original_path)
            require(
                model["width"] == original["width"] and len(model["rows"]) == 4552,
                "combined dimensions",
            )
            require(model["rows"][:4550] == original["rows"], "unchanged original hull rows")
            counts = [sum(p in (4, 8, 12, 16) for p in b) for b in blocks]
            four = [i for i, n in enumerate(counts) if n == 4]
            many = [i for i, n in enumerate(counts) if n >= 3]
            expected = [
                [four, [1] * len(four), m4, m4],
                [many, [1 if counts[i] == 3 else 4 for i in many], 4 + z, 4 + z],
            ]
            require(model["rows"][4550:] == expected, "two exact hub equalities")
            models[key] = model
        model = models[key]
        fixed = sorted(block_ids[tuple(sorted((1, 2, 3, *e)))] for e in edges[result["id"]])
        require(result["fixed_ids"] == fixed and len(set(fixed)) == 7, "first-link IDs")
        target = directory / result["id"]
        require(load(target / "result.json") == result, "individual result")
        fixed_record = load(target / "fixed-rows.json")
        require(fixed_record["rows"] == [[[i], [1], 1, 1] for i in fixed], "fixed equalities")
        require(fixed_record["combined_matrix_sha256"] == digest(matrix_path), "fixed matrix link")
        for field, active in (("fixed_state_audit", True), ("reset_audit", False)):
            state = result[field]
            require(state["prefix_sha256"] == info["feasibility_prefix_sha256"], "prefix identity")
            require(state["hub_case"] == [m4, z] and state["phase_one"] is False, "state layout")
            require(state["active_fixed_ids"] == (fixed if active else None), "active IDs")
            expected = [
                dict(
                    row_index=4552 + j,
                    coefficients=[[i, 1.0]] if active else [],
                    lower=1 if active else 0,
                    upper=1 if active else 0,
                )
                for j, i in enumerate(fixed)
            ]
            require(state["fixed_rows"] == expected, "fixed/reset row state")
        require(
            result["feasibility_lp"]["model_audit"] == result["fixed_state_audit"],
            "solve model state",
        )
        require(
            digest(target / "feasibility-solver.log") == result["feasibility_lp"]["log_sha256"],
            "solver log hash",
        )
        require(result["feasibility_lp"]["allocated_seconds"] <= 15, "initial solver budget")
        if "phase_one_lp" in result:
            remaining = max(0, 15 - result["feasibility_lp"]["solve_seconds"])
            require(
                0 < result["phase_one_lp"]["allocated_seconds"] <= remaining + 0.000001,
                "remaining phase-one solver budget",
            )
        require(result["independently_excluded"] is False, "no premature exclusion flag")
        record = dict(
            id=result["id"],
            hub_case=[m4, z],
            status=result["feasibility_lp"]["status_name"],
            certificate_pending_replay=result["certificate_pending_replay"],
            solve_seconds=result["solve_seconds_total"],
        )
        if "sparse_primal_sha256" in result:
            path = target / "sparse-primal.json.gz"
            require(digest(path) == result["sparse_primal_sha256"], "primal hash")
            primal = load(path)
            require(
                primal["combined_matrix_sha256"] == digest(matrix_path), "primal model identity"
            )
            numerical = checker.check_primal(primal, model, fixed)
            require(
                numerical["fractional_block_count"]
                == result["primal_metrics"]["fractional_block_count"],
                "reported fractionality",
            )
            require(
                numerical["near_integral"] == result["integral_blocks"]["near_integral"],
                "reported candidate flag",
            )
            record["numerical_primal"] = numerical
        records.append(record)
    report = dict(
        valid=True,
        complete=True,
        records=records,
        status_counts=dict(Counter(r["status"] for r in records)),
        checker_sha256=digest(Path(__file__)),
        numeric_checker_sha256=NUMERIC_CHECKER_SHA256,
        results_sha256=digest(run / "results.json.gz"),
        scope="Complete model/record readback and numerical primal replay using exact "
        "stored-binary arithmetic. No certificate replay or exact feasible claim.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}))


if __name__ == "__main__":
    main()
