# Document:    Independent Deterministic Descent Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      5cbbd7c21254c982fb476a3d55a21cc27b631eb6dae2d3caa37322848c7f1943
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Recount saved families and audit bounded descent decisions without running search."""

import hashlib
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-d28-deterministic-descent"
AUDIT = HERE.parent / "weak-pair-d28-deterministic-descent-independent"
RAW = ROOT / "experiments/scratch/weak-pair-d28-deterministic-descent-run-20261004"
MANIFEST = "c985387e9429ca012c001dc03a105b702c8c231b55d005515e478c267cd5c17c"
GATE = "88a0e128b20bbff8287ee50749cdd8e46bd1267b30191faad3879e19c13f3c05"
RUNNER = "cd36b47116fb4ac44f52481cbe104f2f1df2b6acf972c4f7ab7058a7e6a70d91"
INNER = math.comb(4304, 2)
OUTERS = math.comb(64, 2) * 4304
TOTAL = math.comb(64, 2) * INNER


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


def started_shell(count):
    groups, remainder = divmod(count, 4304)
    return groups * INNER + sum(4303 - index for index in range(remainder))


def check_counts(kind, final, outcome):
    require(type(final["complete"]) is bool and final["event"] == "final", "terminal event")
    names = [
        "total",
        "evaluated",
        "legal",
        "strictly_improving_neighbors",
        "strict_improvement_records",
        "best_ties",
    ]
    if kind == "two":
        names += [
            "outer_total",
            "outer_started",
            "outer_completed",
            "pair_floor_pruned",
            "eligible_generated",
            "pending_eligible",
            "accounted",
            "last_evaluated_ordinal",
        ]
    require(all(type(final[key]) is int and final[key] >= 0 for key in names), "counter type/range")
    require(
        0
        <= final["strict_improvement_records"]
        <= final["strictly_improving_neighbors"]
        <= final["legal"]
        <= final["evaluated"]
        <= final["total"],
        "counter order",
    )
    require(final["best_ties"] <= final["strictly_improving_neighbors"], "tie count")
    require(
        type(final["best_rank"]) is list
        and len(final["best_rank"]) == 2
        and all(type(i) is int and i >= 0 for i in final["best_rank"]),
        "rank type",
    )
    require(type(outcome["returncode"]) is int and outcome["returncode"] in (0, 1), "native exit")
    require(
        final["complete"]
        == (outcome["returncode"] == 0)
        == (final["reason"] == "complete")
        == outcome["complete"],
        "completion verdict",
    )
    require(final["reason"] in ("complete", "time_limit", "interrupted"), "terminal reason")
    require(
        type(final["seconds"]) in (int, float)
        and math.isfinite(final["seconds"])
        and 0 <= final["seconds"] <= outcome["elapsed_seconds"] + 1,
        "native timing",
    )
    if final["reason"] == "time_limit":
        require(final["seconds"] >= 120, "early time limit")
    if kind == "one":
        require(final["total"] == 64 * 4304 == 275456, "one-shell total")
        require(final["complete"] == (final["evaluated"] == 275456), "one-shell completion")
        return
    require(final["total"] == TOTAL and final["outer_total"] == OUTERS, "two-shell totals")
    require(0 <= final["outer_completed"] <= final["outer_started"] <= OUTERS, "outer order")
    require(final["complete"] == (final["outer_completed"] == OUTERS), "outer completion")
    gap = final["outer_started"] - final["outer_completed"]
    started = started_shell(final["outer_started"])
    require(gap in (0, 1) and (gap == 1) == (final["pending_eligible"] > 0), "pending outer gap")
    if gap:
        require(
            final["pending_eligible"] <= 4303 - ((final["outer_started"] - 1) % 4304),
            "unfinished outer tail",
        )
    require(
        final["accounted"] == final["pair_floor_pruned"] + final["evaluated"] <= TOTAL,
        "shell accounted",
    )
    require(
        final["eligible_generated"] == final["evaluated"] + final["pending_eligible"],
        "generated eligible",
    )
    require(final["pair_floor_pruned"] + final["eligible_generated"] == started, "started prefix")
    require(
        0 <= final["last_evaluated_ordinal"] <= started
        and bool(final["last_evaluated_ordinal"]) == bool(final["evaluated"]),
        "last ordinal",
    )
    for key in ("support_bins", "support_shell_bins"):
        require(
            type(final[key]) is list
            and len(final[key]) == 8
            and all(type(i) is int and i >= 0 for i in final[key]),
            "support bins",
        )
    require(final["support_bins"][3] == final["support_shell_bins"][3] == 0, "size-one support")
    require(sum(final["support_bins"]) == final["outer_started"], "outer bins sum")
    require(sum(final["support_shell_bins"]) == started, "shell bins sum")
    require(
        all(
            s <= 4303 * n
            for s, n in zip(final["support_shell_bins"], final["support_bins"], strict=True)
        ),
        "support shell capacity",
    )
    require(sum(final["support_shell_bins"][:2]) <= final["pair_floor_pruned"], "pruned bins")
    if final["complete"]:
        require(
            final["accounted"] == TOTAL and final["pending_eligible"] == 0, "complete accounting"
        )


def main():
    require(not (HERE / "postcheck.json").exists(), "preserve runtime receipt")
    require(sha(PRODUCER / "manifest.json") == MANIFEST, "manifest changed")
    require(sha(PRODUCER / "run.py") == RUNNER and sha(AUDIT / "gate.json") == GATE, "gate/runner")
    manifest, gate, result = (
        read(PRODUCER / "manifest.json"),
        read(AUDIT / "gate.json"),
        read(PRODUCER / "result.json"),
    )
    require(gate["passed"] is True and gate["decision"] == "GO", "gate verdict")
    require(
        result["manifest_sha256"] == gate["manifest_sha256"] == MANIFEST
        and result["gate_sha256"] == GATE
        and result["runner_sha256"] == RUNNER,
        "run bindings",
    )
    for group in ("input_files", "sources", "raw_files", "files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, "manifest artifact changed: " + relative)
    for relative, digest in result["raw_files"].items():
        require(sha(ROOT / relative) == digest, "runtime raw changed: " + relative)
    for name, digest in gate["independent_sources"].items():
        require(sha(AUDIT / name) == digest, "gate source changed")
    for relative, digest in gate["raw_files"].items():
        require(sha(ROOT / relative) == digest, "gate control changed")
    require(manifest["max_rounds"] == 4 and manifest["max_shell_launches"] == 8, "bounds")
    require(
        manifest["budget"]
        == gate["budget"]
        == {
            "seconds_per_shell": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "budget_transfer": False,
            "relaunch": False,
            "seed": None,
        },
        "budget changed",
    )
    start = read(RAW / "start.json")
    require(
        start
        == {
            "gate_path": str((AUDIT / "gate.json").resolve()),
            "gate_sha256": GATE,
            "manifest_sha256": MANIFEST,
            "runner_sha256": RUNNER,
            "initial_sha256": manifest["initial"]["sha256"],
            **{
                f"{kind}_binary_sha256": s["binary_sha256"]
                for kind, s in manifest["shells"].items()
            },
        },
        "launch receipt",
    )
    require(result["relaunch"] is False and result["budget_transfer"] is False, "campaign restart")
    require(result["scope"] == manifest["scope"], "scope changed")
    oracle_path = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    oracle = load("descent_runtime_direct_oracle", oracle_path)
    separate = load("descent_runtime_standalone", ROOT / "scripts/check_cover.py")
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    verified, references = {}, []

    def verify(state, label):
        ids = state["ids"]
        require(
            type(ids) is list
            and len(ids) == 64
            and ids == sorted(set(ids))
            and all(type(i) is int and 0 <= i < 4368 for i in ids),
            "family IDs " + label,
        )
        blocks = [oracle.SUBSETS[5][i] for i in ids]
        witness_text = "".join(" ".join(map(str, b)) + "\n" for b in blocks)
        digest = hashlib.sha256(witness_text.encode()).hexdigest()
        require(state["sha256"] == state["canonical_sha256"] == digest, "canonical hash " + label)
        if digest not in verified:
            direct = oracle.analyze(ids, manifest["core_rows"])
            require(direct["legal"], "named weak/core rows " + label)
            package = verify_cover(blocks, 16, 5, 3)
            standalone = separate.verify_cover(blocks, 16, 5, 3, expected_blocks=64)
            holes = [
                list(oracle.SUBSETS[3][i])
                for i, count in enumerate(direct["counts"][3])
                if count == 0
            ]
            require(
                sorted(map(list, package["uncovered"])) == holes == standalone["uncovered"],
                "hole list " + label,
            )
            require(
                package["canonical_sha256"] == standalone["canonical_sha256"] == digest,
                "dual verifier canonical hash",
            )
            require(package["valid"] == standalone["valid"] == (not holes), "cover verdict")
            path = HERE / ("family-" + digest[:16] + ".txt")
            if path.exists():
                require(sha(path) == digest, "independent witness collision")
            else:
                path.write_text(witness_text)
            verified[digest] = {
                "ids": ids,
                "metrics": direct["metrics"] | {"cardinality": 64},
                "sha256": digest,
                "path": str(path.relative_to(ROOT)),
                "cover_found": not holes,
                "package": normal(package),
                "standalone": normal(standalone),
            }
        checked = verified[digest]
        require(
            checked["ids"] == ids and state["metrics"] == checked["metrics"], "family metric alias"
        )
        require(
            state["cover_found"] is checked["cover_found"]
            and state["package_valid"] is checked["cover_found"]
            and state["standalone_valid"] is checked["cover_found"],
            "state covering labels",
        )
        if "verification" in state:
            require(
                state["verification"]
                == {"package": checked["package"], "standalone": checked["standalone"]},
                "saved dual receipt " + label,
            )
        if "witness_path" in state:
            require(sha(ROOT / state["witness_path"]) == digest, "producer witness changed")
            require(
                sha(ROOT / state["receipt_path"]) == state["receipt_sha256"],
                "candidate receipt changed",
            )
            archived = read(ROOT / state["receipt_path"])
            require(
                {k: state[k] for k in archived if k != "verification"}
                == {k: v for k, v in archived.items() if k != "verification"},
                "archive state",
            )
            require(
                archived["verification"]
                == {"package": checked["package"], "standalone": checked["standalone"]},
                "archive dual verification",
            )
        references.append({"label": label, "sha256": digest})
        return checked

    current = manifest["initial"]
    verify(current, "initial")
    require(sha(PRODUCER / "center-00.txt") == current["sha256"], "saved initial")
    require(read(PRODUCER / "center-00-verification.json") == current, "initial receipt")
    rounds = result["rounds"]
    require(type(rounds) is list and 1 <= len(rounds) <= 4, "round count")
    shell_summaries, expected_covers, total_calls = [], [], 0
    reason, closure = None, False
    for number, row in enumerate(rounds, 1):
        require(row == read(PRODUCER / f"round-{number:02d}.json"), "round receipt disagreement")
        require(
            row["round"] == number
            and row["center_sha256"] == current["sha256"]
            and row["center_metrics"] == current["metrics"],
            "round center",
        )
        outcomes = row["shells"]
        require(1 <= len(outcomes) <= 2, "shell count per round")
        all_ties = []
        for shell_index, outcome in enumerate(outcomes):
            kind = ("one", "two")[shell_index]
            total_calls += 1
            require(outcome["round"] == number and outcome["shell"] == kind, "shell order")
            require(
                outcome["center_sha256"] == current["sha256"]
                and outcome["center_metrics"] == current["metrics"],
                "shell center",
            )
            directory = RAW / f"round-{number:02d}-{kind}"
            prefix = directory / "scan"
            require(sha(directory / "center.txt") == current["sha256"], "shell center file")
            expected_path = directory / "shell-result.json"
            require(
                outcome["shell_result_path"] == str(expected_path.relative_to(ROOT))
                and outcome["shell_result_sha256"] == sha(expected_path),
                "shell receipt hash",
            )
            require(
                read(expected_path)
                == {
                    k: v
                    for k, v in outcome.items()
                    if k not in ("shell_result_path", "shell_result_sha256")
                },
                "shell receipt content",
            )
            spec = manifest["shells"][kind]
            require(
                outcome["binary_sha256"] == spec["binary_sha256"]
                and outcome["recorder_sha256"] == spec["recorder_sha256"],
                "shell implementation",
            )
            require(
                outcome["command"]
                == [
                    str(ROOT / spec["binary_path"]),
                    str(directory / "center.txt"),
                    "120",
                    str(prefix),
                ],
                "shell command",
            )
            require(
                outcome["relaunch"] is False and outcome["budget_transfer"] is False,
                "shell restarted",
            )
            require(
                type(outcome["elapsed_seconds"]) in (int, float)
                and math.isfinite(outcome["elapsed_seconds"])
                and outcome["elapsed_seconds"] >= 0,
                "wall timing",
            )
            watchdog = outcome["watchdog"]
            require(
                watchdog["deadline_seconds"] == 135
                and watchdog["grace_seconds"] == 5
                and watchdog["relaunch"] is False,
                "watchdog limit",
            )
            for flag in ("fired", "terminate_sent", "kill_sent"):
                require(type(watchdog[flag]) is bool, "watchdog flag")
            require(
                watchdog["fired"] == watchdog["terminate_sent"]
                and (not watchdog["kill_sent"] or watchdog["fired"]),
                "watchdog actions",
            )
            for relative, digest in outcome["raw_files"].items():
                require(sha(ROOT / relative) == digest, "shell raw binding")
            candidates = outcome["saved_candidates"]
            saved = {state["sha256"]: state for state in candidates}
            require(len(saved) == len(candidates), "duplicate canonical candidate")
            for state in candidates:
                verify(state, f"round-{number}-{kind}-candidate")
            require(
                outcome["observed_covers"]
                == [state for state in candidates if state["cover_found"]],
                "observed cover list",
            )
            expected_covers.extend(outcome["observed_covers"])
            if outcome["passed"]:
                require(
                    outcome["validation_error"] is None
                    and not outcome["rejected_candidate_records"],
                    "passed shell rejected candidate",
                )
                require(
                    not watchdog["fired"] and outcome["elapsed_seconds"] <= 140.5, "passed budget"
                )
                require(not (directory / "stderr.txt").read_text(), "native stderr")
                events = [
                    json.loads(line)
                    for line in (directory / "stdout.jsonl").read_text().splitlines()
                ]
                require(
                    len(events) >= 2 and all(type(event) is dict for event in events),
                    "event objects",
                )
                expected_start = {
                    "event": "start",
                    "budget_seconds": 120,
                    "total": 275456 if kind == "one" else TOTAL,
                    "control_limit": None,
                    "baseline": current["metrics"],
                }
                if kind == "two":
                    expected_start["outer_total"] = OUTERS
                require(events[0] == expected_start, "native start")
                final, records = events[-1], events[1:-1]
                require(final == outcome["final"], "native final")
                check_counts(kind, final, outcome)
                require(all(r.get("event") == "improvement" for r in records), "unknown event")
                require(
                    [r["serial"] for r in records] == list(range(1, len(records) + 1))
                    and len(records) == final["strict_improvement_records"],
                    "record serials",
                )
                ties = read(Path(str(prefix) + "-ties.json"))
                require(len(ties) == final["best_ties"], "native tie count")
                original, initial_ids = set(current["ids"]), current["ids"]
                absent = [i for i in range(4368) if i not in original]
                pairs = list(itertools.combinations(initial_ids, 2))
                checked_exchange, digest_exchange = {}, {}

                def exchange(native):
                    outgoing, incoming = native["outgoing"], native["incoming"]
                    if kind == "one":
                        require(
                            type(outgoing) is int and type(incoming) is int, "one exchange types"
                        )
                        outgoing, incoming = [outgoing], [incoming]
                    require(
                        type(outgoing) is list
                        and type(incoming) is list
                        and len(outgoing) == len(incoming) == shell_index + 1,
                        "exchange size",
                    )
                    require(
                        outgoing == sorted(set(outgoing))
                        and incoming == sorted(set(incoming))
                        and all(type(i) is int and 0 <= i < 4368 for i in outgoing + incoming),
                        "exchange IDs",
                    )
                    require(
                        set(outgoing) <= original and not set(incoming) & original, "exchange roles"
                    )
                    ids = sorted((original - set(outgoing)) | set(incoming))
                    text = "".join(" ".join(map(str, oracle.SUBSETS[5][i])) + "\n" for i in ids)
                    digest = hashlib.sha256(text.encode()).hexdigest()
                    require(
                        digest in saved
                        and saved[digest]["ids"] == ids
                        and saved[digest]["metrics"] == native["metrics"],
                        "unsaved/damaged native family",
                    )
                    key = tuple(outgoing + incoming)
                    require(
                        digest not in digest_exchange or digest_exchange[digest] == key,
                        "exchange alias",
                    )
                    digest_exchange[digest] = key
                    if kind == "one":
                        ordinal = (
                            initial_ids.index(outgoing[0]) * 4304 + absent.index(incoming[0]) + 1
                        )
                        require(ordinal <= final["evaluated"], "one prefix")
                        outer = None
                    else:
                        pair_index = pairs.index(tuple(outgoing))
                        ai, di = (absent.index(i) for i in incoming)
                        ordinal = pair_index * INNER + sum(4303 - j for j in range(ai)) + di - ai
                        outer = pair_index * 4304 + ai + 1
                        require(
                            native["shell_ordinal"] == ordinal
                            and ordinal <= final["last_evaluated_ordinal"]
                            and outer <= final["outer_started"],
                            "two prefix",
                        )
                    checked_exchange[key] = (digest, ordinal)
                    return saved[digest], ordinal, outer, key

                previous_rank, previous_evaluated, previous_ordinal, previous_time = (
                    rank(current),
                    0,
                    0,
                    0.0,
                )
                for record in records:
                    state, ordinal, outer, _ = exchange(record)
                    require(
                        type(record["evaluated"]) is int
                        and previous_evaluated < record["evaluated"] <= final["evaluated"]
                        and ordinal > previous_ordinal
                        and rank(state) < previous_rank,
                        "record ordering",
                    )
                    require(
                        type(record["seconds"]) in (int, float)
                        and math.isfinite(record["seconds"])
                        and previous_time <= record["seconds"] <= final["seconds"],
                        "record timing",
                    )
                    if kind == "one":
                        require(record["evaluated"] == ordinal, "one record ordinal")
                    else:
                        require(record["outer_index"] == outer, "two record outer")
                    previous_rank, previous_evaluated = rank(state), record["evaluated"]
                    previous_ordinal, previous_time = ordinal, record["seconds"]
                require(list(previous_rank) == final["best_rank"], "best rank")
                tie_states, tie_keys = [], []
                for tie in ties:
                    state, _, _, key = exchange(tie)
                    require(
                        rank(state) == previous_rank < rank(current), "nonbest or nonstrict tie"
                    )
                    tie_states.append(state)
                    tie_keys.append(key)
                require(tie_keys == sorted(set(tie_keys)), "tie identity order")
                require(
                    bool(ties) == (previous_rank < rank(current)), "missing/spurious improving ties"
                )
                require(outcome["best_ties"] == tie_states, "wrapper tie list")
                require(set(digest_exchange) == set(saved), "unaccounted saved candidate")
                audit = read(directory / "candidate-audit.json")
                require(
                    audit["passed"] is True
                    and audit["final"] == final
                    and audit["strict_improvements"] == records,
                    "candidate audit/log",
                )
                require(
                    [state["sha256"] for state in audit["best_ties"]]
                    == [state["sha256"] for state in tie_states],
                    "candidate audit ties",
                )
                audit_rows = {state["sha256"]: state for state in audit["audited_families"]}
                require(set(audit_rows) == set(saved), "candidate audit set")
                require(len(audit_rows) == len(audit["audited_families"]), "audit duplicate family")
                for digest, state in audit_rows.items():
                    outgoing, incoming = state["outgoing"], state["incoming"]
                    key = (outgoing, incoming) if kind == "one" else tuple(outgoing + incoming)
                    position = state["ordinal"] if kind == "one" else state["shell_ordinal"]
                    require(
                        checked_exchange.get(key) == (digest, position), "audit exchange position"
                    )
                    require(
                        state["metrics"] == saved[digest]["metrics"]
                        and state["canonical_sha256"] == digest
                        and state["package_valid"] is saved[digest]["cover_found"]
                        and state["standalone_valid"] is saved[digest]["cover_found"],
                        "candidate audit content",
                    )
                all_ties.extend(tie_states)
            else:
                require(
                    outcome["complete"] is False
                    and outcome["final"] is None
                    and outcome["best_ties"] == []
                    and outcome["validation_error"],
                    "invalid shell label",
                )
            shell_summaries.append(
                {
                    "round": number,
                    "shell": kind,
                    "passed": outcome["passed"],
                    "complete": outcome["complete"],
                    "center_sha256": current["sha256"],
                    "final": outcome["final"],
                    "saved_candidates": len(candidates),
                    "elapsed_seconds": outcome["elapsed_seconds"],
                }
            )
            if not outcome["passed"] or not outcome["complete"] or outcome["observed_covers"]:
                require(shell_index == len(outcomes) - 1, "shell launched after stop")
        if not outcomes[-1]["passed"] or not outcomes[-1]["complete"]:
            expected_reason, winner, complete, closure = "incomplete", None, False, False
        elif len(outcomes) == 1:
            require(bool(outcomes[0]["observed_covers"]), "missing second shell")
            expected_reason, winner, complete, closure = "cover_observed", None, False, False
        else:
            complete = True
            winner = (
                min(all_ties, key=lambda state: (rank(state), tuple(state["ids"])))
                if all_ties
                else None
            )
            closure = winner is None
            expected_reason = (
                "no_strict_improvement"
                if winner is None
                else "cover"
                if winner["cover_found"]
                else "round_limit"
                if number == 4
                else None
            )
        require(
            row["selected"] == winner
            and row["stop_reason"] == expected_reason
            and row["complete"] is complete
            and row["local_closure"] is closure,
            "round choice/stop",
        )
        require(row["cover_found"] is bool(expected_covers), "round cover label")
        if winner is not None:
            require(rank(winner) < rank(current), "nonstrict adoption")
            current = winner
            require(
                sha(PRODUCER / f"center-{number:02d}.txt") == current["sha256"], "adopted witness"
            )
            verify(read(PRODUCER / f"center-{number:02d}-verification.json"), f"adopted-{number}")
        reason = expected_reason
        require(
            (reason is not None) == (number == len(rounds)),
            "campaign stopped/continued incorrectly",
        )
    require(total_calls == result["shell_launches"] <= 8, "total shell budget")
    require(
        result["final_center"] == current
        and result["stop_reason"] == reason
        and result["local_closure"] is closure,
        "final campaign result",
    )
    require(
        result["observed_covers"] == expected_covers
        and result["cover_found"] is bool(expected_covers),
        "campaign cover list",
    )
    expected_dirs = {f"round-{s['round']:02d}-{s['shell']}" for s in shell_summaries}
    require(
        {p.name for p in RAW.iterdir() if p.is_dir()} == expected_dirs, "unreported shell directory"
    )
    receipt = {
        "passed": True,
        "source_sha256": sha(__file__),
        "manifest_sha256": MANIFEST,
        "pre_run_gate_sha256": GATE,
        "producer_result_sha256": sha(PRODUCER / "result.json"),
        "runner_sha256": RUNNER,
        "source_revision": manifest["source_revision"],
        "oracle_sha256": sha(oracle_path),
        "budget": manifest["budget"],
        "rounds": len(rounds),
        "shell_launches": total_calls,
        "shells": shell_summaries,
        "stop_reason": reason,
        "local_closure": closure,
        "cover_found": bool(expected_covers),
        "initial_rank": rank(manifest["initial"]),
        "final_rank": rank(current),
        "final_center_sha256": current["sha256"],
        "checked_distinct_families": len(verified),
        "families": list(verified.values()),
        "family_references": references,
        "runtime_raw_bindings": result["raw_files"],
        "optimizer_launches": 0,
        "enumeration_relaunches": 0,
        "solver_launches": 0,
        "enumeration_evidence": (
            "Previously audited unchanged finite kernels, fixed per-round centers, "
            "safe-pruning proof, exact terminal accounting, normal exit where complete, "
            "and unique exchange identities for recorded families."
        ),
        "limitation": (
            "Unrecorded trial metrics were not individually recomputed; no second enumeration. "
            "Any local-closure claim is limited to strict rank improvements within two exchanges "
            "of the exact final center under named filters. "
            "Plateau paths and general existence remain open."
        ),
    }
    (HERE / "postcheck.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(HERE / "postcheck.json"),
                "rounds": len(rounds),
                "shells": total_calls,
                "stop_reason": reason,
                "final_rank": rank(current),
                "checked_families": len(verified),
            }
        )
    )


if __name__ == "__main__":
    main()
