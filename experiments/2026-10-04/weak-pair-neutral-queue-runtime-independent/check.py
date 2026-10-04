# Document:    Independent Neutral Queue Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      92e80b246e6e8cd3a614681c0b165c857a1490d095d65bf8197db77a3be1412b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Audit recorded shell data and queue decisions; reconstruct families without a new scan."""

import hashlib
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-neutral-queue"
AUDIT = HERE.parent / "weak-pair-neutral-queue-independent"
RAW = ROOT / "experiments/scratch/weak-pair-neutral-queue-run-20261004"
MANIFEST = "5a1082e2f28194ee4c90ee0d16bf0d5b22502164e082e757a35842547eae2a82"
GATE = "e808301cec82a6ea805dba9ab2aa58debb56233b7cf9eac9615f485f448f8e90"
RUNNER = "fdc7a9e89f4ce039112a3474d0a656dd246679a6355d6eebae826fbe3b65f085"
COUNTER_SHA = "7af64c5dce047dec1bb6df71d4e23a64f702e8d2b629ebf05b6ef3a59b348435"


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


def rank(state):
    return state["metrics"]["holes"], state["metrics"]["D2max"]


def normal(value):
    return json.loads(json.dumps(value))


def main():
    require(not (HERE / "postcheck.json").exists(), "preserve runtime receipt")
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
        "gate binding",
    )
    require(
        result["manifest_sha256"] == MANIFEST
        and result["gate_sha256"] == GATE
        and result["runner_sha256"] == gate["runner_sha256"] == RUNNER
        and sha(PRODUCER / "run.py") == RUNNER,
        "run binding",
    )
    for group in ("input_files", "sources", "raw_files", "files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, "producer binding changed: " + relative)
    for name, digest in gate["independent_sources"].items():
        require(sha(AUDIT / name) == digest, "gate source changed")
    require(
        sha(ROOT / gate["native_receipt_path"]) == gate["native_receipt_sha256"],
        "native review changed",
    )
    require(
        sha(AUDIT / "controls.json") == gate["wrapper_controls_sha256"], "wrapper controls changed"
    )
    require(
        result["relaunch"] is False
        and result["budget_transfer"] is False
        and result["plateau_exhaustion_claim"] is False,
        "scope/relaunch flags",
    )
    require(
        result["scope"] == manifest["scope"] and manifest["budget"] == gate["budget"],
        "scope/budget",
    )
    require(sha(ROOT / result["raw_index_path"]) == result["raw_index_sha256"], "raw index changed")
    raw_index = read(ROOT / result["raw_index_path"])
    for relative, digest in raw_index.items():
        require(sha(ROOT / relative) == digest, "runtime raw changed: " + relative)
    require(
        read(RAW / "start.json")
        == {
            "gate_sha256": GATE,
            "manifest_sha256": MANIFEST,
            "runner_sha256": RUNNER,
            "initial_sha256": manifest["initial"]["sha256"],
            **{
                f"{kind}_binary_sha256": spec["binary_sha256"]
                for kind, spec in manifest["shells"].items()
            },
        },
        "launch receipt",
    )
    counter_path = HERE.parent / "weak-pair-d28-deterministic-descent-runtime-independent/check.py"
    require(sha(counter_path) == COUNTER_SHA, "independent counter helper changed")
    counts = load("neutral_runtime_counter_checks", counter_path)
    oracle_path = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    oracle = load("neutral_runtime_direct_oracle", oracle_path)
    separate = load("neutral_runtime_standalone", ROOT / "scripts/check_cover.py")
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    families = {}
    family_references = 0

    def verify(state):
        nonlocal family_references
        family_references += 1
        ids = state["ids"]
        require(
            type(ids) is list
            and len(ids) == 64
            and ids == sorted(set(ids))
            and all(type(i) is int and 0 <= i < 4368 for i in ids),
            "candidate IDs",
        )
        blocks = [oracle.SUBSETS[5][i] for i in ids]
        text = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
        digest = hashlib.sha256(text.encode()).hexdigest()
        require(state["sha256"] == state["canonical_sha256"] == digest, "candidate canonical hash")
        if digest not in families:
            direct = oracle.analyze(ids, manifest["core_rows"])
            require(direct["legal"], "candidate weak/core legality")
            package = normal(verify_cover(blocks, 16, 5, 3))
            standalone = normal(separate.verify_cover(blocks, 16, 5, 3, expected_blocks=64))
            holes = [
                list(oracle.SUBSETS[3][i])
                for i, value in enumerate(direct["counts"][3])
                if value == 0
            ]
            require(package["uncovered"] == standalone["uncovered"] == holes, "dual hole mismatch")
            require(
                package["canonical_sha256"] == standalone["canonical_sha256"] == digest, "dual hash"
            )
            require(package["valid"] == standalone["valid"] == (not holes), "dual verdict")
            witness = HERE / ("family-" + digest[:16] + ".txt")
            if witness.exists():
                require(sha(witness) == digest, "witness collision")
            else:
                witness.write_text(text)
            families[digest] = {
                "ids": ids,
                "sha256": digest,
                "path": str(witness.relative_to(ROOT)),
                "metrics": direct["metrics"] | {"cardinality": 64},
                "cover_found": not holes,
                "package": package,
                "standalone": standalone,
            }
        checked = families[digest]
        require(
            checked["ids"] == ids and checked["metrics"] == state["metrics"],
            "candidate metric alias",
        )
        require(
            state["cover_found"] is checked["cover_found"]
            and state["package_valid"] is checked["cover_found"]
            and state["standalone_valid"] is checked["cover_found"],
            "candidate cover label",
        )
        dual = {"package": checked["package"], "standalone": checked["standalone"]}
        if "verification" in state:
            require(state["verification"] == dual, "candidate dual receipt")
        if "witness_path" in state:
            require(
                sha(ROOT / state["witness_path"]) == digest
                and sha(ROOT / state["receipt_path"]) == state["receipt_sha256"],
                "saved candidate file",
            )
            receipt = read(ROOT / state["receipt_path"])
            require(
                receipt["verification"] == dual
                and receipt["ids"] == ids
                and receipt["metrics"] == state["metrics"]
                and receipt["sha256"] == digest,
                "saved candidate receipt",
            )
        return checked

    shell_checks = []

    def inspect_shell(outcome, center, number, kind):
        require(
            outcome["round"] == number
            and outcome["shell"] == kind
            and outcome["center_sha256"] == center["sha256"]
            and outcome["center_metrics"] == center["metrics"],
            "shell center/order",
        )
        directory = RAW / f"round-{number:02d}-{kind}"
        prefix = directory / "scan"
        spec = manifest["shells"][kind]
        require(sha(directory / "center.txt") == center["sha256"], "shell center witness")
        require(
            outcome["command"]
            == [str(ROOT / spec["binary_path"]), str(directory / "center.txt"), "120", str(prefix)],
            "shell command",
        )
        require(
            outcome["binary_sha256"] == spec["binary_sha256"]
            and outcome["recorder_sha256"] == spec["recorder_sha256"],
            "shell code binding",
        )
        shell_path = directory / "shell-result.json"
        require(
            outcome["shell_result_path"] == str(shell_path.relative_to(ROOT))
            and outcome["shell_result_sha256"] == sha(shell_path),
            "shell receipt hash",
        )
        require(
            read(shell_path)
            == {
                k: v
                for k, v in outcome.items()
                if k
                not in (
                    "shell_result_path",
                    "shell_result_sha256",
                    "neutral_ties",
                    "neutral_metadata",
                )
            },
            "base/extended shell receipt",
        )
        require(
            outcome["relaunch"] is False and outcome["budget_transfer"] is False, "shell restart"
        )
        watchdog = outcome["watchdog"]
        require(
            watchdog["deadline_seconds"] == 135
            and watchdog["grace_seconds"] == 5
            and watchdog["relaunch"] is False,
            "watchdog limits",
        )
        require(
            all(type(watchdog[key]) is bool for key in ("fired", "terminate_sent", "kill_sent"))
            and watchdog["fired"] == watchdog["terminate_sent"]
            and (not watchdog["kill_sent"] or watchdog["fired"]),
            "watchdog actions",
        )
        require(
            type(outcome["elapsed_seconds"]) in (int, float)
            and math.isfinite(outcome["elapsed_seconds"])
            and outcome["elapsed_seconds"] >= 0,
            "wall time",
        )
        for relative, digest in outcome["raw_files"].items():
            require(sha(ROOT / relative) == digest, "shell raw changed")
        saved = {state["sha256"]: state for state in outcome["saved_candidates"]}
        require(len(saved) == len(outcome["saved_candidates"]), "duplicate canonical candidate")
        for state in saved.values():
            verify(state)
        require(
            outcome["observed_covers"]
            == [state for state in saved.values() if state["cover_found"]],
            "observed cover set",
        )
        if not outcome["passed"]:
            require(
                outcome["complete"] is False
                and outcome["final"] is None
                and outcome["neutral_ties"] == []
                and outcome["neutral_metadata"] is None,
                "invalid shell conclusion",
            )
            return
        require(
            not watchdog["fired"]
            and outcome["elapsed_seconds"] <= 140.5
            and not (directory / "stderr.txt").read_text(),
            "completed shell budget/stderr",
        )
        require(
            outcome["validation_error"] is None and outcome["rejected_candidate_records"] == [],
            "validated shell rejected candidate",
        )
        events = [
            json.loads(line) for line in (directory / "stdout.jsonl").read_text().splitlines()
        ]
        require(len(events) >= 2 and all(type(event) is dict for event in events), "event objects")
        start = {
            "event": "start",
            "budget_seconds": 120,
            "total": 275456 if kind == "one" else counts.TOTAL,
            "control_limit": None,
            "baseline": center["metrics"],
        }
        if kind == "two":
            start["outer_total"] = counts.OUTERS
        require(events[0] == start and events[-1] == outcome["final"], "native start/final")
        final, records = events[-1], events[1:-1]
        counts.check_counts(kind, final, outcome)
        require(all(row.get("event") == "improvement" for row in records), "unknown event")
        require(
            [row["serial"] for row in records] == list(range(1, len(records) + 1))
            and len(records) == final["strict_improvement_records"],
            "record serials",
        )
        ties = read(Path(str(prefix) + "-ties.json"))
        neutral = read(Path(str(prefix) + "-neutral.json"))
        metadata = read(Path(str(prefix) + "-neutral-meta.json"))
        require(metadata == outcome["neutral_metadata"], "neutral metadata receipt")
        require(
            set(metadata) == {"neutral_seen", "retained", "cap", "capped", "complete", "rank"},
            "neutral fields",
        )
        require(
            all(
                type(metadata[key]) is int and metadata[key] >= 0
                for key in ("neutral_seen", "retained", "cap")
            )
            and metadata["cap"] == 64
            and metadata["retained"] == len(neutral) == min(64, metadata["neutral_seen"]),
            "neutral count/cap",
        )
        require(
            type(metadata["complete"]) is bool
            and metadata["complete"] == final["complete"]
            and type(metadata["capped"]) is bool
            and metadata["capped"] == (metadata["neutral_seen"] > 64),
            "neutral completeness/capping",
        )
        require(
            metadata["rank"] == list(rank(center))
            and metadata["neutral_seen"] + final["strictly_improving_neighbors"] <= final["legal"],
            "neutral rank/count bounds",
        )
        original, selected = set(center["ids"]), center["ids"]
        absent = [i for i in range(4368) if i not in original]
        pairs = list(itertools.combinations(selected, 2))
        exchange_by_hash = {}

        def exchange(row):
            outgoing, incoming = row["outgoing"], row["incoming"]
            if kind == "one":
                require(type(outgoing) is int and type(incoming) is int, "one IDs")
                outgoing, incoming = [outgoing], [incoming]
            size = 1 if kind == "one" else 2
            require(
                type(outgoing) is list
                and type(incoming) is list
                and len(outgoing) == len(incoming) == size
                and all(type(i) is int and 0 <= i < 4368 for i in outgoing + incoming)
                and outgoing == sorted(set(outgoing))
                and incoming == sorted(set(incoming)),
                "exchange IDs",
            )
            require(
                set(outgoing) <= original and not set(incoming) & original, "exchange membership"
            )
            ids = sorted((original - set(outgoing)) | set(incoming))
            text = "".join(" ".join(map(str, oracle.SUBSETS[5][i])) + "\n" for i in ids)
            digest = hashlib.sha256(text.encode()).hexdigest()
            require(
                digest in saved
                and saved[digest]["ids"] == ids
                and saved[digest]["metrics"] == row["metrics"],
                "unsaved/wrong exchange",
            )
            key = tuple(outgoing + incoming)
            require(
                digest not in exchange_by_hash or exchange_by_hash[digest][0] == key,
                "exchange alias",
            )
            if kind == "one":
                ordinal = selected.index(outgoing[0]) * 4304 + absent.index(incoming[0]) + 1
                outer = None
                require(ordinal <= final["evaluated"], "one ordinal prefix")
            else:
                pair_index = pairs.index(tuple(outgoing))
                ai, di = (absent.index(i) for i in incoming)
                ordinal = pair_index * counts.INNER + sum(4303 - j for j in range(ai)) + di - ai
                outer = pair_index * 4304 + ai + 1
                require(
                    row["shell_ordinal"] == ordinal
                    and ordinal <= final["last_evaluated_ordinal"]
                    and outer <= final["outer_started"],
                    "two ordinal prefix",
                )
            exchange_by_hash[digest] = (key, ordinal)
            return saved[digest], ordinal, outer, key

        previous_rank, previous_eval, previous_ordinal, previous_time = rank(center), 0, 0, 0.0
        for row in records:
            state, ordinal, outer, _ = exchange(row)
            require(
                rank(state) < previous_rank
                and type(row["evaluated"]) is int
                and previous_eval < row["evaluated"] <= final["evaluated"]
                and ordinal > previous_ordinal,
                "strict record order",
            )
            require(
                type(row["seconds"]) in (int, float)
                and math.isfinite(row["seconds"])
                and previous_time <= row["seconds"] <= final["seconds"],
                "record time",
            )
            require(
                row["evaluated"] == ordinal if kind == "one" else row["outer_index"] == outer,
                "record position",
            )
            previous_rank, previous_eval, previous_ordinal, previous_time = (
                rank(state),
                row["evaluated"],
                ordinal,
                row["seconds"],
            )
        require(
            final["best_rank"] == list(previous_rank)
            and len(ties) == final["best_ties"]
            and bool(ties) == (previous_rank < rank(center)),
            "best strict rank/ties",
        )
        strict_states, strict_keys = [], []
        for row in ties:
            state, _, _, key = exchange(row)
            require(rank(state) == previous_rank < rank(center), "strict tie rank")
            strict_states.append(state)
            strict_keys.append(key)
        require(
            strict_keys == sorted(set(strict_keys)) and outcome["best_ties"] == strict_states,
            "strict tie list",
        )
        neutral_states, traversal = [], []
        for row in neutral:
            state, ordinal, _, _ = exchange(row)
            require(
                row["ids"] == state["ids"]
                and rank(state) == rank(center)
                and type(row["neutral_ordinal"]) is int
                and row["neutral_ordinal"] == ordinal
                and type(row["neutral_index"]) is int,
                "neutral family/rank/position",
            )
            neutral_states.append(state)
            traversal.append((row["neutral_index"], ordinal))
        require(
            [tuple(state["ids"]) for state in neutral_states]
            == sorted({tuple(state["ids"]) for state in neutral_states}),
            "neutral family order/aliases",
        )
        traversal.sort()
        require(
            [i for i, _ in traversal] == list(range(1, len(neutral) + 1))
            and all(a[1] < b[1] for a, b in zip(traversal, traversal[1:])),
            "neutral traversal",
        )
        require(outcome["neutral_ties"] == neutral_states, "neutral saved ties")
        require(set(exchange_by_hash) == set(saved), "unaccounted candidate")
        audit = read(directory / "candidate-audit.json")
        require(
            audit["passed"] is True
            and audit["final"] == final
            and audit["strict_improvements"] == records
            and audit["neutral_metadata"] == metadata,
            "candidate audit/log",
        )
        require(
            [s["sha256"] for s in audit["best_ties"]] == [s["sha256"] for s in strict_states]
            and [s["sha256"] for s in audit["neutral_families"]]
            == [s["sha256"] for s in neutral_states],
            "candidate audit sets",
        )
        require(
            len(audit["audited_families"]) == len(saved)
            and {s["sha256"] for s in audit["audited_families"]} == set(saved),
            "audit all candidates",
        )
        shell_checks.append(
            {
                "center_number": number,
                "shell": kind,
                "center_sha256": center["sha256"],
                "complete": final["complete"],
                "final": final,
                "neutral_metadata": metadata,
                "saved_candidates": len(saved),
                "elapsed_seconds": outcome["elapsed_seconds"],
            }
        )

    current = best = manifest["initial"]
    verify(current)
    visited = set(manifest["historical_visited_hashes"])
    queue, covers, decisions = {}, [], []
    summaries = result["centers"]
    require(
        len(summaries) == result["centers_processed"] and 1 <= len(summaries) <= 16, "center count"
    )
    calls, stop, next_center = 0, None, None
    for number, summary in enumerate(summaries, 1):
        require(stop is None, "continued after stop")
        require(number == 1 or current["sha256"] not in visited, "repeated historical center")
        require(rank(current) == rank(best), "uphill queue center")
        visited.add(current["sha256"])
        queue.pop(current["sha256"], None)
        require(
            summary == read(PRODUCER / f"center-{number:02d}-summary.json"),
            "center summary changed",
        )
        require(
            sha(ROOT / summary["full_result_path"]) == summary["full_result_sha256"],
            "full center hash",
        )
        row = read(ROOT / summary["full_result_path"])
        require(
            row["center_number"] == number
            and row["center_sha256"] == current["sha256"]
            and row["center_metrics"] == current["metrics"],
            "processed center",
        )
        require(sha(ROOT / summary["witness_path"]) == current["sha256"], "center saved witness")
        outcomes = row["shells"]
        require(1 <= len(outcomes) <= 2, "shell count at center")
        for index, outcome in enumerate(outcomes):
            kind = ("one", "two")[index]
            inspect_shell(outcome, current, number, kind)
            calls += 1
            covers.extend(outcome["observed_covers"])
            if not outcome["passed"] or not outcome["complete"]:
                stop = "incomplete"
            elif outcome["observed_covers"]:
                stop = "cover_observed"
            if stop:
                require(index == len(outcomes) - 1, "shell continued after stop")
        complete = len(outcomes) == 2 and all(o["passed"] and o["complete"] for o in outcomes)
        strict, next_center = False, None
        if stop is None:
            require(complete, "missing complete second shell")
            candidates = [s for outcome in outcomes for s in outcome["best_ties"]]
            if candidates:
                strict = True
                best_rank = min(map(rank, candidates))
                tied = [s for s in candidates if rank(s) == best_rank]
                best = min(tied, key=lambda s: tuple(s["ids"]))
                require(
                    rank(best) < rank(current) and best["sha256"] not in visited, "strict choice"
                )
                queue = {s["sha256"]: s for s in tied if s["sha256"] not in visited}
                next_center = best
                queue.pop(best["sha256"], None)
            else:
                for outcome in outcomes:
                    for state in outcome["neutral_ties"]:
                        require(rank(state) == rank(best), "neutral rank in queue")
                        if state["sha256"] not in visited:
                            queue[state["sha256"]] = state
                if queue:
                    next_center = min(queue.values(), key=lambda s: tuple(s["ids"]))
                    queue.pop(next_center["sha256"])
                else:
                    stop = "sample_exhausted"
        if stop is None and number == 16:
            stop = "center_budget"
        require(
            row["complete"] is complete
            and row["strict_improvement"] is strict
            and row["best_sha256"] == best["sha256"]
            and row["best_rank"] == list(rank(best))
            and row["next_center"] == next_center
            and row["queue_remaining"] == len(queue)
            and row["stop_reason"] == stop
            and row["cover_found"] is bool(covers),
            "queue decision",
        )
        require(
            row["local_strict_closed"] is (complete and not strict and stop != "cover_observed"),
            "local closure",
        )
        for key, value in row.items():
            if key not in ("shells", "next_center"):
                require(summary[key] == value, "summary field")
        require(
            summary["next_center_sha256"] == (next_center["sha256"] if next_center else None),
            "summary next",
        )
        require(len(summary["shells"]) == len(outcomes), "summary shell count")
        for compact, outcome in zip(summary["shells"], outcomes, strict=True):
            require(
                compact
                == {
                    "shell": outcome["shell"],
                    "passed": outcome["passed"],
                    "complete": outcome["complete"],
                    "shell_result_path": outcome["shell_result_path"],
                    "shell_result_sha256": outcome["shell_result_sha256"],
                    "strict_ties": len(outcome["best_ties"]),
                    "neutral_metadata": outcome["neutral_metadata"],
                },
                "summary shell",
            )
        decisions.append({k: v for k, v in summary.items() if k != "shells"})
        require((stop is not None) == (number == len(summaries)), "terminal center count")
        if stop is None:
            current = next_center
    require(
        calls == result["shell_launches"] <= 32
        and result["stop_reason"] == stop
        and result["best_family"] == best
        and result["visited_hashes"] == sorted(visited)
        and result["queued_unscanned"] == len(queue)
        and result["unscanned_next"] == next_center
        and result["observed_covers"] == covers
        and result["cover_found"] is bool(covers),
        "campaign result",
    )
    expected_dirs = {
        f"round-{number:02d}-{kind}"
        for number, summary in enumerate(summaries, 1)
        for kind in (s["shell"] for s in summary["shells"])
    }
    require({p.name for p in RAW.iterdir() if p.is_dir()} == expected_dirs, "extra shell directory")
    frontier = dict(queue)
    if next_center is not None:
        frontier[next_center["sha256"]] = next_center
    require(
        all(
            digest not in visited and rank(state) == rank(best)
            for digest, state in frontier.items()
        ),
        "unscanned frontier invariant",
    )
    if stop in ("center_budget", "sample_exhausted"):
        observed_unvisited = {
            digest
            for digest, state in families.items()
            if rank(state) == rank(best) and digest not in visited
        }
        require(set(frontier) == observed_unvisited, "retained frontier reconstruction")
    ordered_frontier = sorted(frontier.values(), key=lambda state: tuple(state["ids"]))
    frontier_receipt = {
        "producer_result_sha256": sha(PRODUCER / "result.json"),
        "best_rank": list(rank(best)),
        "visited_hashes": sorted(visited),
        "unscanned_next_sha256": next_center["sha256"] if next_center else None,
        "families": [families[state["sha256"]] for state in ordered_frontier],
        "scope": "Reconstructed retained unscanned frontier only; no new search or plateau claim.",
    }
    (HERE / "unscanned-frontier.json").write_text(
        json.dumps(frontier_receipt, indent=2, sort_keys=True) + "\n"
    )
    receipt = {
        "passed": True,
        "source_sha256": sha(__file__),
        "manifest_sha256": MANIFEST,
        "pre_run_gate_sha256": GATE,
        "producer_result_sha256": sha(PRODUCER / "result.json"),
        "source_revision": manifest["source_revision"],
        "counter_helper_sha256": COUNTER_SHA,
        "oracle_sha256": sha(oracle_path),
        "centers_processed": len(summaries),
        "shell_launches": calls,
        "stop_reason": stop,
        "best_rank": list(rank(best)),
        "best_family_sha256": best["sha256"],
        "cover_found": bool(covers),
        "checked_distinct_families": len(families),
        "checked_family_references": family_references,
        "center_decisions": decisions,
        "shells": shell_checks,
        "families": list(families.values()),
        "visited_hashes": sorted(visited),
        "queued_unscanned": len(queue),
        "unscanned_next_sha256": next_center["sha256"] if next_center else None,
        "raw_index_sha256": result["raw_index_sha256"],
        "unscanned_frontier_path": str((HERE / "unscanned-frontier.json").relative_to(ROOT)),
        "unscanned_frontier_sha256": sha(HERE / "unscanned-frontier.json"),
        "unscanned_frontier_count": len(ordered_frontier),
        "optimizer_launches": 0,
        "native_requeries": 0,
        "scope": (
            "All recorded strict and sampled neutral families are reconstructed and dual checked. "
            "Frozen native review plus exact terminal counts supports completed-shell claims. "
            "Unrecorded trials were not re-enumerated, and first64 sampling does not exhaust a "
            "plateau or guarantee globally smallest64. No global theorem or unrestricted claim."
        ),
    }
    (HERE / "postcheck.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "centers": len(summaries),
                "shells": calls,
                "families": len(families),
                "best_rank": list(rank(best)),
                "stop_reason": stop,
                "cover_found": bool(covers),
            }
        )
    )


if __name__ == "__main__":
    main()
