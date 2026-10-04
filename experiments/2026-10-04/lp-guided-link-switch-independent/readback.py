# Document:    Independent Readback of the Bounded LP-Guided Switch Pilot
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e5466b26a07954385e923f69bc95e9b8cdb04bac5798234053da59badbc55e00
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import importlib.util
import itertools as it
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = HERE.parent / "lp-guided-link-switch"
RAW = ROOT / "experiments/scratch/lp-guided-link-switch-20261004"
ORACLE = ROOT / "experiments/2026-10-03/lookahead-cut-independent/check.py"
INF = 2**63 - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main():
    result = json.loads((RUN / "result.json").read_text())
    proposal = json.loads((RUN / "proposal.json").read_text())
    gate = json.loads((HERE / "audit.json").read_text())
    assert gate["passed"] and result["gate_sha256"] == sha(HERE / "audit.json")
    assert result["runner_sha256"] == sha(RAW / "run.py")
    assert result["proposal_sha256"] == sha(RUN / "proposal.json")
    for path, expected in result["raw_sha256"].items():
        assert sha(RAW / path) == expected
    assert sha(ORACLE) == "41532f815971ea48f3ed42a9ea4bce5c7c4054e139f5bbe13ade4ba108da7b76"
    spec = importlib.util.spec_from_file_location("independent_basis", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    manifest = json.loads(
        (ROOT / "experiments/2026-10-03/lookahead-heavy-strengthened/manifest.json").read_text()
    )
    oracle.MODEL = ROOT / manifest["model"]
    oracle.WITNESS = (
        ROOT
        / "experiments/2026-10-03/four-seven-template-native-lookahead/performance-cycle-best.txt"
    )
    blocks, ordinary, heavy, original, symbolic = oracle.rebuild()
    heavy_index = {b: i for i, b in enumerate(heavy)}
    anchors = [frozenset(range(a, a + 3)) for a in (1, 5, 9, 13)]
    bundle_path = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
    bundle = json.loads(bundle_path.read_text())
    assert sha(bundle_path) == gate["bundle_sha256"]
    cuts = bundle["cuts"]

    def verify_family(family):
        assert len(family) == len(set(family)) == 28 and set(family) <= set(heavy)
        for anchor in anchors:
            local = [b for b in family if anchor <= set(b)]
            outside = Counter(p for b in local for p in set(b) - anchor)
            assert len(local) == 7 and outside == {
                p: 2 if p == max(anchor) + 1 else 1 for p in range(1, 17) if p not in anchor
            }
        counts = Counter(t for b in family for t in it.combinations(b, 3))
        assert all(n <= 2 or frozenset(t) in anchors for t, n in counts.items())

    def rows_for(family):
        ids = {heavy_index[b] for b in family}
        return [
            (
                os,
                [1] * len(os),
                lo - len(ids & set(hs)),
                hi if hi == INF else hi - len(ids & set(hs)),
            )
            for os, hs, lo, hi in symbolic
        ]

    previous = tuple(sorted(original))
    previous_objective = proposal["baseline_elastic_objective"]
    candidates_checked = vectors_checked = 0
    solver_seconds = 0.0
    best_vector = None
    for report in result["rounds"]:
        path = RAW / f"round-{report['round']}" / "ranking.json"
        ranking = json.loads(path.read_text())
        assert sha(path) == report["ranking_sha256"]
        assert tuple(map(tuple, ranking["current_heavy"])) == previous
        assert ranking["current_objective"] == previous_objective
        sort_keys = []
        for record in ranking["neighbors"]:
            family = tuple(blocks[i] for i in record["heavy_global_ids"])
            verify_family(family)
            rows = rows_for(family)
            ids = [heavy_index[b] for b in family]
            gaps = [max(0, c["rhs"] - sum(c["coefficients"][i] for i in ids)) for c in cuts]
            assert record["heavy_local_ids"] == ids
            assert record["heavy_sha256"] == digest(family)
            assert record["shifted_rows_sha256"] == digest(rows)
            assert record["cut_violation_numerators"] == gaps
            assert record["maximum_cut_lower_bound"] == [max(gaps), 1000]
            sort_keys.append((max(gaps), record["heavy_global_ids"]))
            candidates_checked += 1
        assert sort_keys == sorted(sort_keys)
        assert ranking["selected_ranks"] == list(range(20))
        best, best_objective = previous, previous_objective
        for record in report["results"]:
            neighbor = ranking["neighbors"][record["rank"]]
            assert record["rank"] in ranking["selected_ranks"]
            assert record["heavy_sha256"] == neighbor["heavy_sha256"]
            family = tuple(blocks[i] for i in neighbor["heavy_global_ids"])
            if "vector_path" in record:
                vector_path = ROOT / record["vector_path"]
                assert sha(vector_path) == record["vector_sha256"]
                values = json.loads(vector_path.read_text())
                assert len(values) == 1200 and all(-1e-7 <= v <= 1 + 1e-7 for v in values)
                residual = 0.0
                for os, _, lower, upper in rows_for(family):
                    value = sum(values[i] for i in os)
                    residual += max(0.0, lower - value)
                    if upper != INF:
                        residual += max(0.0, value - upper)
                assert abs(residual - record["recomputed_l1_residual"]) < 1e-7
                assert residual <= record["objective"] + 1e-5
                vectors_checked += 1
                if [blocks.index(b) for b in family] == result["best_heavy_global_ids"]:
                    best_vector = values
            if not record.get("cached"):
                solver_seconds += record["seconds"]
            if record["status"] == "OPTIMAL" and record["objective"] < best_objective - 1e-7:
                best, best_objective = family, record["objective"]
        assert report["objective_after"] == best_objective
        assert report["best_heavy_global_ids"] == [blocks.index(b) for b in best]
        previous, previous_objective = best, best_objective
    assert previous_objective == result["final_objective"]
    assert abs(solver_seconds - result["solver_seconds"]) < 1e-8
    assert vectors_checked == result["lp_evaluations"] == 60 and solver_seconds <= 30
    assert best_vector is not None
    exact_x = [Fraction(v).limit_denominator(10**9) for v in best_vector]
    exact_x = [min(Fraction(1), max(Fraction(0), v)) for v in exact_x]
    exact_residual = Fraction(0)
    for os, _, lower, upper in rows_for(previous):
        value = sum((exact_x[i] for i in os), Fraction(0))
        exact_residual += max(Fraction(0), lower - value)
        if upper != INF:
            exact_residual += max(Fraction(0), value - upper)
    assert abs(float(exact_residual) - result["final_objective"]) < 1e-6
    # Assemble a regular 64-block binding state from the selected heavy tuple
    # and original ordinary blocks. This is not an optimized near-cover.
    original_seed = [
        tuple(map(int, line.split())) for line in oracle.WITNESS.read_text().splitlines()
    ]
    binding_family = sorted([b for b in original_seed if b in ordinary] + list(previous))
    assert len(binding_family) == len(set(binding_family)) == 64
    (HERE / "selected-binding-seed.txt").write_text(
        "".join(" ".join(map(str, b)) + "\n" for b in binding_family)
    )
    audit = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "result_sha256": sha(RUN / "result.json"),
        "proposal_sha256": sha(RUN / "proposal.json"),
        "round_rankings_replayed": len(result["rounds"]),
        "ranked_candidates_reconstructed": candidates_checked,
        "numerical_vectors_replayed": vectors_checked,
        "solver_seconds_verified": solver_seconds,
        "final_objective": result["final_objective"],
        "final_heavy_global_ids": result["best_heavy_global_ids"],
        "final_shifted_rows_sha256": digest(rows_for(previous)),
        "exact_elastic_residual_upper_bound": [
            exact_residual.numerator,
            exact_residual.denominator,
        ],
        "exact_elastic_residual_float": float(exact_residual),
        "selected_binding_seed_sha256": sha(HERE / "selected-binding-seed.txt"),
        "optimization_calls": 0,
        "scope": (
            "Numerical-point and ranking replay. Positive elastic residual is not "
            "an infeasibility proof or an original-LP feasible witness."
        ),
    }
    (HERE / "readback.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit), flush=True)


if __name__ == "__main__":
    main()
