# Document:    Direct Numerical Readback of LP-Guided Link Switch Pilot
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      839d1449de65ce6cb862acbe1ba3953aeea4e9851ee71b1cbd9cbdeaf728407f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read every saved LP vector without running a solver or claiming an exact optimum."""

import hashlib
import itertools as it
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/lp-guided-link-switch-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def supports():
    anchors = [set(range(a, a + 3)) for a in (1, 5, 9, 13)]
    rows = [((), 64, 64)]
    rows += [(t, 1, None if set(t) in anchors else 2) for t in it.combinations(range(1, 17), 3)]
    rows += [((p,), 20, 20) for p in range(1, 17)]
    for pair in it.combinations(range(1, 17), 2):
        targets = set()
        for anchor in anchors:
            for point, other in (pair, pair[::-1]):
                if point in anchor:
                    targets.add(7 if other in anchor else 6 if other == max(anchor) + 1 else 5)
        assert len(targets) <= 1
        if targets:
            target = targets.pop()
            rows.append((pair, target, target))
        else:
            rows.append((pair, 5, 7))
    assert len(rows) == 697
    return rows


def residual(values, fixed, rows, ordinary_support):
    assert len(values) == 1200 and all(
        math.isfinite(value) and -1e-7 <= value <= 1 + 1e-7 for value in values
    )
    total = 0.0
    fixed_sets = list(map(set, fixed))
    for (support, lower, upper), ids in zip(rows, ordinary_support, strict=True):
        value = sum(values[index] for index in ids)
        value += sum(set(support) <= block for block in fixed_sets)
        total += max(0.0, lower - value)
        if upper is not None:
            total += max(0.0, value - upper)
    return total


def main():
    result = json.loads((HERE / "result.json").read_text())
    proposal = json.loads((HERE / "proposal.json").read_text())
    assert result["runner_sha256"] == sha(HERE / "run.py") == sha(RAW / "run.py")
    assert result["proposal_sha256"] == sha(HERE / "proposal.json") == sha(RAW / "proposal.json")
    for relative, expected in result["raw_sha256"].items():
        assert sha(RAW / relative) == expected
    blocks = list(it.combinations(range(1, 17), 5))
    ordinary = [blocks[index] for index in proposal["ordinary_global_ids"]]
    rows = supports()
    ordinary_support = [
        [i for i, block in enumerate(ordinary) if set(support) <= set(block)]
        for support, _, _ in rows
    ]
    prior_objective = proposal["baseline_elastic_objective"]
    prior_ids = proposal["initial_heavy_global_ids"]
    records = []
    total_seconds = 0.0
    first_values = first_fixed = None
    for round_result in result["rounds"]:
        folder = RAW / f"round-{round_result['round']}"
        ranking = json.loads((folder / "ranking.json").read_text())
        evaluations = json.loads((folder / "evaluations.json").read_text())
        assert sha(folder / "ranking.json") == round_result["ranking_sha256"]
        assert evaluations == round_result["results"]
        assert [blocks.index(tuple(block)) for block in ranking["current_heavy"]] == prior_ids
        assert ranking["current_objective"] == prior_objective
        assert ranking["selected_ranks"] == list(range(20))
        best_objective, best_ids = prior_objective, prior_ids
        for evaluation in evaluations:
            assert not evaluation.get("cached", False)
            neighbor = ranking["neighbors"][evaluation["rank"]]
            vector_path = ROOT / evaluation["vector_path"]
            assert sha(vector_path) == evaluation["vector_sha256"]
            values = json.loads(vector_path.read_text())
            fixed = [blocks[index] for index in neighbor["heavy_global_ids"]]
            assert len(fixed) == len(set(fixed)) == 28
            observed = residual(values, fixed, rows, ordinary_support)
            assert (
                evaluation["status"] == "OPTIMAL"
                and abs(observed - evaluation["objective"]) <= 1e-5
            )
            assert abs(observed - evaluation["recomputed_l1_residual"]) <= 1e-8
            lower, denominator = neighbor["maximum_cut_lower_bound"]
            assert observed + 1e-5 >= lower / denominator
            if evaluation["objective"] < best_objective - 1e-7:
                best_objective, best_ids = evaluation["objective"], neighbor["heavy_global_ids"]
            total_seconds += evaluation["seconds"]
            records.append(
                {
                    "round": round_result["round"],
                    "rank": evaluation["rank"],
                    "objective": evaluation["objective"],
                    "fresh_l1_residual": observed,
                    "heavy_sha256": neighbor["heavy_sha256"],
                }
            )
            if first_values is None:
                first_values, first_fixed = values, fixed
        assert best_ids == round_result["best_heavy_global_ids"]
        assert best_objective == round_result["objective_after"]
        prior_ids, prior_objective = best_ids, best_objective
    assert prior_ids == result["best_heavy_global_ids"]
    assert prior_objective == result["final_objective"]
    assert len(records) == result["lp_evaluations"] == 60
    assert abs(total_seconds - result["solver_seconds"]) < 1e-9 and total_seconds <= 30
    assert len({record["heavy_sha256"] for record in records}) == 60
    damaged = first_values.copy()
    damaged[0] = 2.0
    try:
        residual(damaged, first_fixed, rows, ordinary_support)
    except AssertionError:
        damaged_vector_rejected = True
    else:
        raise AssertionError("damaged vector accepted")
    report = {
        "passed": True,
        "source_sha256": sha(__file__),
        "result_sha256": sha(HERE / "result.json"),
        "vectors_checked": len(records),
        "status_counts": dict(Counter("OPTIMAL" for _ in records)),
        "solver_seconds": total_seconds,
        "initial_objective": proposal["baseline_elastic_objective"],
        "final_objective": prior_objective,
        "exact_fractional_feasibility": False,
        "damaged_vector_rejected": damaged_vector_rejected,
        "records": records,
        "scope": (
            "Direct floating-point residual readback. "
            "No solver calls and no exact optimality claim."
        ),
    }
    (HERE / "readback.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}))


if __name__ == "__main__":
    main()
