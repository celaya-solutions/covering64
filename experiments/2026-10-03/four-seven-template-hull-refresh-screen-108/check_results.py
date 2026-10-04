# Document:    108-Exclusion Matching LP Screen Saved Evidence Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      c7cfbe72d5e73fd0c368539abafb49374ab87ebb18081474d3d2237379cedf8f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Verify all 49 records and sparse numerical primals without invoking a solver."""

import argparse
import gzip
import hashlib
import importlib.util
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
NUMERIC_CHECKER_SHA256 = "2105a615be69d030442a0dbecc471f7e8354e75c86c53e901d181aca2488a2ed"
MATRIX_SHA256 = "e9b2289291479c5f1119f432f0131d8fda8130ace2e64c773cf93dd8928ceade"


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
    source = HERE.parent / "four-seven-template-link-screen/check_results.py"
    require(digest(source) == NUMERIC_CHECKER_SHA256, "frozen numerical checker")
    spec = importlib.util.spec_from_file_location("saved_numeric_checker", source)
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    metadata, preflight = load(run / "metadata.json"), load(run / "preflight.json")
    require(
        preflight["valid"]
        and preflight["runner_sha256"] == metadata["source_sha256"] == digest(run / "run.py"),
        "frozen source and preflight",
    )
    require(digest(run / "preflight.json") == metadata["preflight_sha256"], "preflight hash")
    require(digest(run / "extended-rows.json.gz") == MATRIX_SHA256, "audited refreshed matrix")
    matrix = load(run / "extended-rows.json.gz")
    require(matrix["width"] == 52936 and len(matrix["rows"]) == 4550, "matrix dimensions")
    selected = load(run / "selection.json")
    union = load(
        HERE.parent
        / "four-seven-template-hull-refresh-independent"
        / "combined-first-link-exclusions.json"
    )
    expected_ids = [i for i in union["remaining_ids"] if i.startswith("matching-")]
    require(
        [r["id"] for r in selected] == expected_ids and len(selected) == 48, "complete selected IDs"
    )
    results = load(run / "results.json.gz")
    require([r["id"] for r in results] == ["matching-whole", *expected_ids], "complete ordered run")
    block_ids = {b: i for i, b in enumerate(combinations(range(1, 17), 5))}
    fixed_by_id = {
        r["id"]: sorted(block_ids[tuple(sorted((1, 2, 3, *e)))] for e in r["edges"])
        for r in selected
    }
    fixed_by_id["matching-whole"] = []
    for kind, stages in metadata["model_prefixes"].items():
        for stage, checksum in stages.items():
            label = "phase-one" if stage == "phase_one" else stage
            require(
                hashlib.sha256(
                    gzip.decompress((run / f"{kind}-{label}-base.pb.gz").read_bytes())
                ).hexdigest()
                == checksum,
                "serialized model prefix hash",
            )
    records, controls = [], []
    for result in results:
        identifier = result["id"]
        whole = identifier == "matching-whole"
        kind, fixed = ("whole" if whole else "fixed"), fixed_by_id[identifier]
        require(result["fixed_ids"] == fixed and result["whole_branch"] == whole, "fixed selection")
        require(
            result["checked_rows"] == 4550 + len(fixed) and result["checked_columns"] == 52936,
            "result dimensions",
        )
        target = run / identifier
        require(load(target / "result.json") == result, "individual result identity")
        require(
            load(target / "fixed-rows.json")
            == dict(
                id=identifier,
                width=52936,
                base_matrix_sha256=MATRIX_SHA256,
                rows=[[[i], [1], 1, 1] for i in fixed],
            ),
            "fixed matrix rows",
        )
        prefix = metadata["model_prefixes"][kind]["feasibility"]
        if whole:
            state = dict(prefix_sha256=prefix, active_fixed_ids=[], phase_one=False, soft_rows=0)
            require(
                result["fixed_state_audit"]
                == result["reset_audit"]
                == result["feasibility_lp"]["model_audit"]
                == state,
                "whole immutable state",
            )
        else:
            checker.check_states(result, prefix, fixed)
        require(
            digest(target / "feasibility-solver.log") == result["feasibility_lp"]["log_sha256"],
            "feasibility log hash",
        )
        require(0 < result["feasibility_lp"]["allocated_seconds"] <= 15, "feasibility budget")
        if "phase_one_lp" in result:
            phase = result["phase_one_lp"]
            remaining = max(0, 15 - result["feasibility_lp"]["solve_seconds"])
            require(
                0 < phase["allocated_seconds"] <= remaining + 0.000001, "remaining phase I budget"
            )
            require(
                digest(target / "phase-one-solver.log") == phase["log_sha256"], "phase I log hash"
            )
        require(result["independently_excluded"] is False, "no premature exclusion claim")
        record = dict(
            id=identifier,
            status=result["feasibility_lp"]["status_name"],
            whole_branch=whole,
            certificate_pending_replay=result["certificate_pending_replay"],
            solve_seconds=result["solve_seconds_total"],
        )
        if "sparse_primal_sha256" in result:
            path = target / "sparse-primal.json.gz"
            require(digest(path) == result["sparse_primal_sha256"], "primal hash")
            primal = load(path)
            require(primal["base_matrix_sha256"] == MATRIX_SHA256, "primal matrix link")
            numerical = checker.check_primal(primal, matrix, fixed)
            require(
                numerical["fractional_block_count"]
                == result["primal_metrics"]["fractional_block_count"],
                "reported fractionality",
            )
            require(
                numerical["near_integral"] == result["integral_blocks"]["near_integral"],
                "candidate flag",
            )
            record["primal_audit"] = numerical
            if not whole and not controls:
                controls = checker.damaged_controls(primal, matrix, fixed, result, prefix)
        records.append(record)
    report = dict(
        valid=True,
        complete=True,
        checked_records=49,
        records=records,
        status_counts=dict(Counter(r["status"] for r in records)),
        damaged_controls=controls,
        checker_sha256=digest(Path(__file__)),
        numeric_checker_sha256=NUMERIC_CHECKER_SHA256,
        results_sha256=digest(run / "results.json.gz"),
        matrix_sha256=MATRIX_SHA256,
        scope="Complete record/model linkage, reset states and exact arithmetic on saved "
        "binary primals. Numerical residuals are not exact feasible witnesses. "
        "Certificates require separate independent replay.",
    )
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}))


if __name__ == "__main__":
    main()
