# Document:    H9 D23 Sixteen Center Neutral Queue Runner
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      65ea193fadebd9023fb05ddd45d14261f047f075167e8420c23a6dd5e6d594bc
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Explore at most16 unvisited centers from the finally audited native best family."""

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = ROOT / "experiments/scratch/weak-pair-h9-d23-neutral-queue-run-20261004"
BASE = HERE.parent / "weak-pair-d28-deterministic-descent/run.py"
BASE_SHA = "cd36b47116fb4ac44f52481cbe104f2f1df2b6acf972c4f7ab7058a7e6a70d91"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def base_module():
    base = load(BASE, "neutral_base_runner")
    base.require(base.sha(BASE) == BASE_SHA, "frozen bounded wrapper changed")
    base.RUN = RUN
    return base


def rank(state):
    return state["metrics"]["holes"], state["metrics"]["D2max"]


def queue_campaign(initial, historical, execute, persist, frontier):
    visited = set(historical)
    current = best = initial
    queue = {}
    for state in frontier:
        if state["sha256"] in queue or state["sha256"] in visited:
            raise ValueError("duplicate or visited resume frontier state")
        if rank(state) != rank(initial):
            raise ValueError("resume frontier has mixed ranks")
        queue[state["sha256"]] = state
    if not queue or initial != min(queue.values(), key=lambda s: tuple(s["ids"])):
        raise ValueError("initial must be lexicographically first resume frontier state")
    summaries, covers = [], []
    for number in range(1, 17):
        if current["sha256"] in visited:
            raise ValueError("repeated queued center")
        if rank(current) != rank(best):
            raise ValueError("queue attempted uphill center")
        visited.add(current["sha256"])
        queue.pop(current["sha256"], None)
        outcomes = []
        reason = None
        for kind in ("one", "two"):
            outcome = execute(number, kind, current)
            outcomes.append(outcome)
            covers.extend(outcome["observed_covers"])
            if not outcome["passed"] or not outcome["complete"]:
                reason = "incomplete"
                break
            if outcome["observed_covers"]:
                reason = "cover_observed"
                break
        complete = len(outcomes) == 2 and all(o["complete"] and o["passed"] for o in outcomes)
        next_center = None
        strict = False
        if complete and reason is None:
            candidates = [s for o in outcomes for s in o["best_ties"]]
            if any(rank(s) >= rank(current) for s in candidates):
                raise ValueError("nonstrict entry in strict ties")
            if candidates:
                strict = True
                winning_rank = min(map(rank, candidates))
                tied = [s for s in candidates if rank(s) == winning_rank]
                best = min(tied, key=lambda s: tuple(s["ids"]))
                queue = {s["sha256"]: s for s in tied if s["sha256"] not in visited}
                if best["sha256"] in visited:
                    raise ValueError(
                        "strict improvement already visited; history rank invariant failed"
                    )
                next_center = best
                queue.pop(best["sha256"], None)
            else:
                for outcome in outcomes:
                    for state in outcome["neutral_ties"]:
                        if rank(state) != rank(best):
                            raise ValueError("nonneutral queue entry")
                        if state["sha256"] not in visited:
                            queue[state["sha256"]] = state
                if queue:
                    next_center = min(queue.values(), key=lambda s: tuple(s["ids"]))
                    queue.pop(next_center["sha256"])
                else:
                    reason = "sample_exhausted"
        if reason is None and number == 16:
            reason = "center_budget"
        row = {
            "center_number": number,
            "center_sha256": current["sha256"],
            "center_metrics": current["metrics"],
            "shells": outcomes,
            "complete": complete,
            "strict_improvement": strict,
            "best_sha256": best["sha256"],
            "best_rank": list(rank(best)),
            "next_center": next_center,
            "queue_remaining": len(queue),
            "stop_reason": reason,
            "local_strict_closed": complete and not strict and reason != "cover_observed",
            "cover_found": bool(covers),
        }
        summary = persist(row, current)
        summaries.append(summary)
        if reason:
            return {
                "stop_reason": reason,
                "centers_processed": number,
                "centers": summaries,
                "best_family": best,
                "observed_covers": covers,
                "visited_hashes": sorted(visited),
                "queued_unscanned": len(queue),
                "unscanned_next": next_center,
                "unscanned_frontier": sorted(
                    list(queue.values()) + ([] if next_center is None else [next_center]),
                    key=lambda s: tuple(s["ids"]),
                ),
                "cover_found": bool(covers),
                "plateau_exhaustion_claim": False,
            }
        current = next_center
    raise AssertionError("center budget")


def execute_shell(number, kind, center, manifest, recorder, base):
    outcome = base.execute_shell(number, kind, center, manifest, recorder)
    outcome["neutral_ties"] = []
    outcome["neutral_metadata"] = None
    if outcome["passed"]:
        audit_path = RUN / f"round-{number:02d}-{kind}" / "candidate-audit.json"
        audit = json.loads(audit_path.read_text())
        by_hash = {s["sha256"]: s for s in outcome["saved_candidates"]}
        outcome["neutral_ties"] = [by_hash[s["sha256"]] for s in audit["neutral_families"]]
        outcome["neutral_metadata"] = audit["neutral_metadata"]
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--gate-sha256", required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    base = base_module()
    require, sha, dump = base.require, base.sha, base.dump
    require(not RUN.exists() and not (HERE / "result.json").exists(), "queue already launched")
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(args.gate) == args.gate_sha256, "gate hash changed")
    gate = json.loads(args.gate.read_text())
    require(gate.get("passed") is True and gate.get("decision") == "GO", "independent GO required")
    expected = {
        "manifest_sha256": sha(HERE / "manifest.json"),
        "runner_sha256": sha(__file__),
        "initial_sha256": manifest["initial"]["sha256"],
        **{
            f"{kind}_binary_sha256": manifest["shells"][kind]["binary_sha256"]
            for kind in ("one", "two")
        },
    }
    for key, value in expected.items():
        require(gate.get(key) == value, f"gate binding {key}")
    for group in ("input_files", "sources", "files", "raw_files"):
        for path, digest in manifest[group].items():
            require(sha(ROOT / path) == digest, f"changed input {path}")
    require(manifest["budget"]["max_centers"] == 16, "center budget changed")
    require(manifest["budget"]["max_shell_launches"] == 32, "shell budget changed")
    require(manifest["budget"]["seconds_per_shell"] == 120, "shell time changed")
    require(manifest["budget"]["watchdog_seconds"] == 135, "watchdog changed")
    require(manifest["budget"]["termination_grace_seconds"] == 5, "grace changed")
    adapter = load(HERE.parent / "weak-pair-neutral-queue/adapter.py", "neutral_adapter")
    recorders = {kind: adapter.Recorder(kind) for kind in ("one", "two")}
    initial = base.verify_family(
        manifest["initial"]["ids"], recorders["one"], manifest["core_rows"]
    )
    require(initial == manifest["initial"], "initial verification changed")
    frontier = json.loads((ROOT / manifest["resume_frontier_path"]).read_text())["frontier"]
    require(len(frontier) == manifest["resume_frontier_count"], "frontier count changed")
    for state in frontier:
        checked = base.verify_family(state["ids"], recorders["one"], manifest["core_rows"])
        require(checked == state, "frontier family verification changed")
    RUN.mkdir(parents=True)
    dump(RUN / "start.json", {"gate_sha256": args.gate_sha256, **expected})

    def persist(row, current):
        row["observed_fifth_core_overlap"] = len(
            set(current["ids"]) & set(manifest["observed_fifth_core"]["ids"])
        )
        witness = HERE / f"center-{row['center_number']:02d}.txt"
        with witness.open("x") as handle:
            handle.write(recorders["one"].family_text(current["ids"]))
        require(sha(witness) == current["sha256"], "center preservation hash")
        full = RUN / f"center-{row['center_number']:02d}-result.json"
        dump(full, row)
        summary = {k: v for k, v in row.items() if k not in ("shells", "next_center")}
        summary.update(
            {
                "witness_path": str(witness.relative_to(ROOT)),
                "full_result_path": str(full.relative_to(ROOT)),
                "full_result_sha256": sha(full),
                "next_center_sha256": None
                if row["next_center"] is None
                else row["next_center"]["sha256"],
                "shells": [
                    {
                        "shell": o["shell"],
                        "passed": o["passed"],
                        "complete": o["complete"],
                        "shell_result_path": o["shell_result_path"],
                        "shell_result_sha256": o["shell_result_sha256"],
                        "strict_ties": len(o["best_ties"]),
                        "neutral_metadata": o["neutral_metadata"],
                    }
                    for o in row["shells"]
                ],
            }
        )
        dump(HERE / f"center-{row['center_number']:02d}-summary.json", summary)
        print(
            json.dumps(
                {
                    "center": row["center_number"],
                    "rank": row["best_rank"],
                    "strict_improvement": row["strict_improvement"],
                    "queue_remaining": row["queue_remaining"],
                    "stop_reason": row["stop_reason"],
                }
            ),
            flush=True,
        )
        return summary

    result = queue_campaign(
        initial,
        manifest["historical_visited_hashes"],
        lambda n, k, c: execute_shell(n, k, c, manifest, recorders[k], base),
        persist,
        frontier,
    )
    raw_index = {str(p.relative_to(ROOT)): sha(p) for p in sorted(RUN.rglob("*")) if p.is_file()}
    dump(RUN / "files.json", raw_index)
    result.update(
        {
            "manifest_sha256": expected["manifest_sha256"],
            "gate_sha256": args.gate_sha256,
            "runner_sha256": sha(__file__),
            "relaunch": False,
            "budget_transfer": False,
            "shell_launches": sum(len(r["shells"]) for r in result["centers"]),
            "raw_index_path": str((RUN / "files.json").relative_to(ROOT)),
            "raw_index_sha256": sha(RUN / "files.json"),
            "scope": manifest["scope"],
            "best_observed_fifth_core_overlap": len(
                set(result["best_family"]["ids"]) & set(manifest["observed_fifth_core"]["ids"])
            ),
        }
    )
    dump(HERE / "result.json", result)
    print(
        json.dumps(
            {
                "stop_reason": result["stop_reason"],
                "cover_found": result["cover_found"],
                "centers_processed": result["centers_processed"],
                "best_rank": list(rank(result["best_family"])),
                "result_sha256": sha(HERE / "result.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
