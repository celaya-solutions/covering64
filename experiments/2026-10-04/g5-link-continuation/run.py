# Document:    Registry-Filtered Fixed-g5 Descent Continuation
# Version:     v1.0.1
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      7b0b8c6819d075ae60b15fc738fa0975114cf2aca77bd0e01c902add1e3e47b2
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Continue the checked fixed-g5 descent with a separately gated budget."""

import argparse
import importlib.util
import itertools as it
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from ortools import __version__ as ortools_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DAY = HERE.parent
RAW = ROOT / "experiments/scratch/g5-link-continuation-20261004"
PREVIOUS = DAY / "g5-link-descent"
PREVIOUS_RAW = ROOT / "experiments/scratch/g5-link-descent-20261004"
BASE = DAY / "matching-g5-lp/soft-raw-17"
BASE_RAW = ROOT / "experiments/scratch/matching-g5-lp-20261004/soft-raw-17"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sweep = load(DAY / "lp-guided-full-sweep/sweep.py", "g5_sweep")
generator = sweep.generator
registry_module = load(HERE / "registry.py", "g5_registry")
sha = generator.sha
data_hash = generator.data_hash


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n")


def basis():
    blocks, ordinary, heavy, _, broad = sweep.basis()
    rows = list(broad)
    pairs = list(it.combinations(range(1, 17), 2))
    changes = []
    for pair, excess in zip(it.combinations((4, 8, 12, 16), 2), registry_module.GRAPH, strict=True):
        index = 577 + pairs.index(pair)
        ids, hids, lower, upper = rows[index]
        assert (lower, upper) == (5, 7)
        rows[index] = (ids, hids, 5 + excess, 5 + excess)
        changes.append(
            {"row": index, "pair": pair, "before": [lower, upper], "after": [5 + excess] * 2}
        )
    assert [i for i, (a, b) in enumerate(zip(broad, rows, strict=True)) if a != b] == [
        r["row"] for r in changes
    ]
    manifest = json.loads((BASE / "manifest.json").read_text())
    fixed = [tuple(block) for block in manifest["heavy_blocks"]]
    assert json.loads(json.dumps(generator.shifted_rows(rows, heavy, fixed))) == json.loads(
        (BASE_RAW / "rows.json").read_text()
    )
    assert [blocks.index(block) for block in ordinary] == manifest["ordinary_global_ids"]
    previous_result = json.loads((PREVIOUS / "result.json").read_text())
    fixed = [blocks[i] for i in previous_result["best_heavy_global_ids"]]
    return blocks, ordinary, heavy, fixed, rows, changes


def profile_key(heavy_sha, shifted_sha, family_sha):
    return data_hash(
        {"family_sha256": family_sha, "heavy_sha256": heavy_sha, "shifted_rows_sha256": shifted_sha}
    )


def neighbors(fixed, heavy, blocks, rows, cuts, registry, family_sha):
    ranked, counts = generator.ranked_neighbors(fixed, heavy, blocks, rows, cuts)
    for neighbor in ranked:
        candidate = [blocks[i] for i in neighbor["heavy_global_ids"]]
        receipt = registry.classify(candidate)
        neighbor["registry"] = receipt
        neighbor["accepted"] = receipt["accepted"]
        neighbor["rejection_reasons"] = [
            {
                "anchor_group_zero_based": link["anchor_group_zero_based"],
                "representative": link["representative"],
                "proof_sources": link["proof_sources"],
            }
            for link in receipt["links"]
            if link["excluded"]
        ]
        neighbor["cache_key"] = profile_key(
            neighbor["heavy_sha256"], neighbor["shifted_rows_sha256"], family_sha
        )
    return ranked, counts


def prepare():
    assert not (HERE / "manifest.json").exists()
    blocks, ordinary, heavy, fixed, rows, changes = basis()
    previous_manifest = json.loads((PREVIOUS / "manifest.json").read_text())
    previous_result = json.loads((PREVIOUS / "result.json").read_text())
    postcheck_path = DAY / "g5-link-descent-independent/postcheck.json"
    postcheck = json.loads(postcheck_path.read_text())
    assert postcheck["passed"] and postcheck["result_sha256"] == sha(PREVIOUS / "result.json")
    registry = registry_module.Registry()
    classified = registry.classify(fixed)
    assert classified["accepted"]
    family_sha = data_hash(
        {
            "rows": rows,
            "ordinary_global_ids": [blocks.index(block) for block in ordinary],
            "graph_index": 5,
        }
    )
    assert family_sha == previous_manifest["family_sha256"] == previous_result["family_sha256"]
    cuts = json.loads(generator.BUNDLE.read_text())["cuts"]
    assert len(cuts) == 14
    ranked, counts = neighbors(fixed, heavy, blocks, rows, cuts, registry, family_sha)
    final_cache_path = PREVIOUS_RAW / "final-cache.json"
    assert sha(final_cache_path) == previous_result["raw_sha256"]["final-cache.json"]
    previous_cache = json.loads(final_cache_path.read_text())
    assert len(previous_cache) == 255
    baseline_key = previous_result["trajectory"][-1]["cache_key"]
    baseline = previous_cache[baseline_key]
    assert baseline["heavy_global_ids"] == previous_result["best_heavy_global_ids"]
    assert baseline["objective"] == previous_result["best_objective"] == 11.500690015970484
    initial_cache = []
    for key, record in sorted(previous_cache.items()):
        assert record["status"] == "OPTIMAL" and record["family_sha256"] == family_sha
        candidate = [blocks[i] for i in record["heavy_global_ids"]]
        assert record["heavy_sha256"] == data_hash(candidate)
        shifted_sha = data_hash(generator.shifted_rows(rows, heavy, candidate))
        assert record["shifted_rows_sha256"] == shifted_sha
        assert (
            key
            == record["cache_key"]
            == profile_key(record["heavy_sha256"], shifted_sha, family_sha)
        )
        assert registry.classify(candidate)["accepted"]
        for label in ("vector", "dual"):
            assert sha(ROOT / record[f"{label}_path"]) == record[f"{label}_sha256"]
        initial_cache.append(record)
    preflight = {
        "optimization_calls": 0,
        "source_sha256": sha(__file__),
        "family_sha256": family_sha,
        "six_row_changes": changes,
        "baseline_registry": classified,
        "enumeration_counts": counts,
        "generated": len(ranked),
        "accepted": sum(n["accepted"] for n in ranked),
        "rejected": sum(not n["accepted"] for n in ranked),
        "neighbors": ranked,
    }
    dump(HERE / "preflight.json", preflight)
    inputs = previous_manifest["input_files"].copy()
    paths = [Path(__file__), HERE / "registry.py", postcheck_path, final_cache_path]
    paths += [
        PREVIOUS / name
        for name in ("run.py", "registry.py", "manifest.json", "preflight.json", "result.json")
    ]
    paths += [
        ROOT / record[f"{label}_path"] for record in initial_cache for label in ("vector", "dual")
    ]
    inputs.update({str(path.relative_to(ROOT)): sha(path) for path in paths})
    for path, digest in inputs.items():
        assert sha(ROOT / path) == digest
    manifest = {
        "source_sha256": sha(__file__),
        "registry_source_sha256": sha(HERE / "registry.py"),
        "preflight_sha256": sha(HERE / "preflight.json"),
        "input_files": inputs,
        "graph_index": 5,
        "hub_excesses": registry_module.GRAPH,
        "hub_pair_targets": [5 + x for x in registry_module.GRAPH],
        "family_sha256": family_sha,
        "baseline": baseline,
        "initial_cache": initial_cache,
        "baseline_elastic_objective": baseline["objective"],
        "ordinary_global_ids": [blocks.index(block) for block in ordinary],
        "six_row_changes": changes,
        "initial_generated": len(ranked),
        "initial_accepted": preflight["accepted"],
        "initial_rejected": preflight["rejected"],
        "optimization_calls": 0,
        "budgets": {
            "rounds": 10,
            "fresh_lps": 1000,
            "solver_seconds": 150,
            "wall_seconds": 200,
            "each_lp_seconds": 1,
            "workers": 1,
            "seed": 2026104,
        },
        "cache_scope": (
            "Only the 255 checked fixed-g5 LPs in the prior final cache; "
            "exact family, heavy and shifted-row hashes."
        ),
        "ranking": (
            "Original 14 broad exact cuts rank structural neighbors; "
            "no cut prunes an accepted neighbor."
        ),
        "scope": (
            "Fixed-g5 registry-filtered two-edge-switch neighborhoods only; "
            "no global lower-bound claim."
        ),
    }
    dump(HERE / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "preflight_sha256": sha(HERE / "preflight.json"),
                "baseline": baseline["objective"],
                "generated": len(ranked),
                "accepted": preflight["accepted"],
                "rejected": preflight["rejected"],
                "initial_cache": len(initial_cache),
            }
        )
    )


def run(gate_path):
    manifest = json.loads((HERE / "manifest.json").read_text())
    gate = json.loads(gate_path.read_text())
    assert gate["passed"] and gate["manifest_sha256"] == sha(HERE / "manifest.json")
    assert gate["source_sha256"] == manifest["source_sha256"] == sha(__file__)
    assert manifest["preflight_sha256"] == sha(HERE / "preflight.json")
    for relative, digest in manifest["input_files"].items():
        assert sha(ROOT / relative) == digest
    assert not RAW.exists() and not (HERE / "result.json").exists()
    RAW.mkdir()
    for source in (
        Path(__file__),
        HERE / "registry.py",
        HERE / "manifest.json",
        HERE / "preflight.json",
        gate_path,
    ):
        (RAW / source.name).write_bytes(source.read_bytes())
    wall_started = time.monotonic()
    blocks, ordinary, heavy, fixed, rows, _ = basis()
    registry = registry_module.Registry()
    cuts = json.loads(generator.BUNDLE.read_text())["cuts"]
    exact = load(generator.LP_CORE, "g5_exact")
    baseline = manifest["baseline"]
    assert len(manifest["initial_cache"]) == 255
    cache = {record["cache_key"]: record for record in manifest["initial_cache"]}
    assert len(cache) == 255 and baseline["cache_key"] in cache
    best_objective = baseline["objective"]
    fresh = cached = 0
    solver_seconds = 0.0
    rounds, records, trajectory = [], [], [baseline]
    stop_reason = "round_limit"
    exact_primal = None
    exact_record = None
    start = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "gate_sha256": sha(gate_path),
        "ortools_version": ortools_version,
        "budgets": manifest["budgets"],
        "graph_index": 5,
        "family_sha256": manifest["family_sha256"],
    }
    dump(RAW / "start.json", start)
    for round_number in range(1, 11):
        if time.monotonic() - wall_started >= 193:
            stop_reason = "wall_budget_before_neighborhood"
            break
        folder = RAW / f"round-{round_number}"
        folder.mkdir()
        ranked, counts = neighbors(
            fixed, heavy, blocks, rows, cuts, registry, manifest["family_sha256"]
        )
        if round_number == 1:
            assert data_hash(ranked) == data_hash(
                json.loads((HERE / "preflight.json").read_text())["neighbors"]
            )
        accepted = [n for n in ranked if n["accepted"]]
        ranking = {
            "round": round_number,
            "incumbent_heavy_global_ids": [blocks.index(b) for b in fixed],
            "incumbent_objective": best_objective,
            "enumeration_counts": counts,
            "neighbors": ranked,
            "accepted": len(accepted),
            "rejected": len(ranked) - len(accepted),
        }
        dump(folder / "ranking.json", ranking)
        evaluated = []
        for neighbor in accepted:
            assert neighbor["registry"]["accepted"] and len(neighbor["registry"]["links"]) == 4
            key = neighbor["cache_key"]
            if key in cache:
                record = cache[key].copy()
                record["cached_origin_record_sha256"] = data_hash(cache[key])
                assert (
                    record["status"] == "OPTIMAL"
                    and record["shifted_rows_sha256"] == neighbor["shifted_rows_sha256"]
                )
                assert record["family_sha256"] == manifest["family_sha256"]
                assert record["heavy_global_ids"] == neighbor["heavy_global_ids"]
                assert sha(ROOT / record["vector_path"]) == record["vector_sha256"]
                assert sha(ROOT / record["dual_path"]) == record["dual_sha256"]
                record["cached"] = True
                cached += 1
            else:
                if (
                    fresh >= 1000
                    or solver_seconds >= 148.9
                    or time.monotonic() - wall_started >= 196
                ):
                    stop_reason = "fresh_solver_or_wall_budget"
                    break
                candidate = [blocks[i] for i in neighbor["heavy_global_ids"]]
                shifted = generator.shifted_rows(rows, heavy, candidate)
                assert data_hash(shifted) == neighbor["shifted_rows_sha256"]
                record, values, dual = sweep.solve(shifted)
                fresh += 1
                solver_seconds += record["seconds"]
                record.update(
                    cached=False, source_round=round_number, family_sha256=manifest["family_sha256"]
                )
                if values is not None:
                    vector_path = folder / f"rank-{neighbor['rank']:03d}-values.json"
                    dual_path = folder / f"rank-{neighbor['rank']:03d}-dual.json"
                    dump(vector_path, values)
                    dump(dual_path, dual)
                    record.update(
                        vector_path=str(vector_path.relative_to(ROOT)),
                        vector_sha256=sha(vector_path),
                        dual_path=str(dual_path.relative_to(ROOT)),
                        dual_sha256=sha(dual_path),
                    )
                    if record["recomputed_l1_residual"] <= 1e-7:
                        for limit in (100, 10000, 1000000, 1000000000):
                            exact_primal = exact.exact_primal(shifted, values, limit)
                            if exact_primal is not None:
                                exact_primal.update(
                                    graph_index=5,
                                    heavy_global_ids=neighbor["heavy_global_ids"],
                                    ordinary_global_ids=manifest["ordinary_global_ids"],
                                    shifted_rows_sha256=neighbor["shifted_rows_sha256"],
                                )
                                dump(
                                    folder / f"rank-{neighbor['rank']:03d}-exact-primal.json",
                                    exact_primal,
                                )
                                break
            record.update(
                round=round_number,
                rank=neighbor["rank"],
                heavy_sha256=neighbor["heavy_sha256"],
                heavy_global_ids=neighbor["heavy_global_ids"],
                shifted_rows_sha256=neighbor["shifted_rows_sha256"],
                cache_key=key,
                registry_accepted=True,
                registry_receipt_sha256=data_hash(neighbor["registry"]),
                ranking_path=str((folder / "ranking.json").relative_to(ROOT)),
                ranking_sha256=sha(folder / "ranking.json"),
            )
            if record["status"] == "OPTIMAL":
                numerator, denominator = neighbor["maximum_cut_lower_bound"]
                assert record["objective"] + 1e-5 >= numerator / denominator
                cache[key] = record.copy()
            evaluated.append(record)
            records.append(record)
            dump(folder / "evaluations.json", evaluated)
            if exact_primal is not None:
                exact_record = record.copy()
                stop_reason = "checked_exact_fractional_feasibility"
                break
        complete = len(evaluated) == len(accepted)
        all_optimal = complete and all(record["status"] == "OPTIMAL" for record in evaluated)
        eligible = [
            record
            for record in evaluated
            if record["status"] == "OPTIMAL" and record["objective"] < best_objective - 1e-7
        ]
        selected = (
            min(eligible, key=lambda record: (record["objective"], record["heavy_global_ids"]))
            if eligible
            else None
        )
        if exact_record is not None:
            selected = exact_record
        summary = {
            "round": round_number,
            "generated": len(ranked),
            "accepted": len(accepted),
            "rejected": len(ranked) - len(accepted),
            "evaluated": len(evaluated),
            "complete": complete,
            "all_optimal": all_optimal,
            "incumbent_objective": best_objective,
            "minimum_evaluated_objective": min(
                (r["objective"] for r in evaluated if "objective" in r), default=None
            ),
            "selected": selected if all_optimal or exact_primal is not None else None,
            "ranking_path": str((folder / "ranking.json").relative_to(ROOT)),
            "ranking_sha256": sha(folder / "ranking.json"),
            "evaluations_sha256": sha(folder / "evaluations.json") if evaluated else None,
        }
        rounds.append(summary)
        dump(RAW / "rounds.json", rounds)
        print(
            json.dumps({key: value for key, value in summary.items() if key != "selected"}),
            flush=True,
        )
        if exact_primal is not None:
            assert selected is not None
            best_objective = selected["objective"]
            fixed = [blocks[i] for i in selected["heavy_global_ids"]]
            trajectory.append(selected)
            break
        if not complete:
            break
        if not all_optimal:
            stop_reason = "inconclusive_nonoptimal_neighbor"
            break
        if selected is None:
            stop_reason = "complete_accepted_neighborhood_no_improvement"
            break
        best_objective = selected["objective"]
        fixed = [blocks[i] for i in selected["heavy_global_ids"]]
        trajectory.append(selected)
        if exact_primal is not None:
            stop_reason = "checked_exact_fractional_feasibility"
            break
    wall_seconds = time.monotonic() - wall_started
    assert fresh <= 1000 and solver_seconds <= 150 and wall_seconds <= 200
    result = {
        **start,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "initial_objective": baseline["objective"],
        "best_objective": best_objective,
        "best_heavy_global_ids": [blocks.index(b) for b in fixed],
        "rounds": rounds,
        "trajectory": trajectory,
        "records": records,
        "fresh_evaluations": fresh,
        "cached_evaluations": cached,
        "solver_seconds": solver_seconds,
        "wall_seconds": wall_seconds,
        "stop_reason": stop_reason,
        "exact_fractional_feasibility": exact_primal is not None,
        "covering_witness": False,
        "global_lower_bound_claim": False,
    }
    dump(RAW / "final-cache.json", cache)
    result["raw_sha256"] = {
        str(path.relative_to(RAW)): sha(path) for path in sorted(RAW.rglob("*")) if path.is_file()
    }
    dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in ("rounds", "trajectory", "records", "raw_sha256")
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--gate", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare()
    else:
        assert args.gate is not None
        run(args.gate)
