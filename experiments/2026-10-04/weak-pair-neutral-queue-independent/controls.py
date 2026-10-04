# Document:    Independent Neutral Queue and Recorder Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      ee2c405af56335a6f4d96074bc03b173ddb0f156172816776e06f711bbc652fd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Abstract transition tests and synthetic metadata over saved real families; no scans."""

import copy
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/neutral-queue-independent-20261004"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rejected(callback, label):
    try:
        callback()
    except (AssertionError, ValueError, TypeError, KeyError, IndexError):
        return label
    raise ValueError("damaged control accepted: " + label)


def state(name, deficit=26, first=0, holes=12):
    return {
        "sha256": name,
        "ids": [first, first + 100],
        "metrics": {"holes": holes, "D2max": deficit},
        "cover_found": holes == 0,
    }


def outcome(strict=(), neutral=(), complete=True, passed=True, covers=()):
    return {
        "best_ties": list(strict),
        "neutral_ties": list(neutral),
        "complete": complete,
        "passed": passed,
        "observed_covers": list(covers),
    }


def queue_controls(runner):
    seed, old = state("seed", first=50), state("old", first=0)
    a, b, c = state("a", first=2), state("b", first=4), state("c", first=1)
    low, low_peer = state("low", deficit=25, first=10), state("low-peer", deficit=25, first=12)
    cover = state("abstract-cover", deficit=0, holes=0)
    cases = [
        ("empty sample", [outcome(), outcome()], ["seed"], "sample_exhausted", "seed"),
        (
            "history and aliases",
            [
                outcome(neutral=[b, a, old]),
                outcome(neutral=[a, seed]),
                outcome(neutral=[b, old, seed]),
                outcome(),
                outcome(),
                outcome(),
            ],
            ["seed", "a", "b"],
            "sample_exhausted",
            "seed",
        ),
        (
            "global queue lex order",
            [
                outcome(neutral=[b, a]),
                outcome(),
                outcome(neutral=[c]),
                outcome(),
                outcome(),
                outcome(),
                outcome(),
                outcome(),
            ],
            ["seed", "a", "c", "b"],
            "sample_exhausted",
            "seed",
        ),
        (
            "strict clears old queue",
            [
                outcome(neutral=[a, b]),
                outcome(),
                outcome(strict=[low_peer]),
                outcome(strict=[low], neutral=[b]),
                outcome(),
                outcome(),
                outcome(),
                outcome(),
            ],
            ["seed", "a", "low", "low-peer"],
            "sample_exhausted",
            "low",
        ),
        (
            "strict outranks neutral",
            [outcome(neutral=[a]), outcome(strict=[low]), outcome(), outcome()],
            ["seed", "low"],
            "sample_exhausted",
            "low",
        ),
        ("first incomplete", [outcome(complete=False)], ["seed"], "incomplete", "seed"),
        (
            "second incomplete no adoption",
            [outcome(strict=[low]), outcome(complete=False)],
            ["seed"],
            "incomplete",
            "seed",
        ),
        ("first failed", [outcome(passed=False)], ["seed"], "incomplete", "seed"),
        ("cover first", [outcome(covers=[cover])], ["seed"], "cover_observed", "seed"),
        (
            "cover second",
            [outcome(strict=[low]), outcome(covers=[cover])],
            ["seed"],
            "cover_observed",
            "seed",
        ),
        (
            "cover incomplete",
            [outcome(complete=False, covers=[cover])],
            ["seed"],
            "incomplete",
            "seed",
        ),
    ]
    checked = []
    for name, replies, expected_centers, reason, best in cases:
        calls, rows = [], []

        def execute(number, kind, center):
            calls.append((number, kind, center["sha256"]))
            require(len(calls) <= len(replies), "too many calls: " + name)
            return replies[len(calls) - 1]

        def persist(row, center):
            require(row["center_sha256"] == center["sha256"], "persisted wrong center")
            rows.append(row)
            return row

        result = runner.queue_campaign(seed, {"seed", "old"}, execute, persist)
        actual_centers = [row["center_sha256"] for row in rows]
        require(
            actual_centers == expected_centers and len(actual_centers) == len(set(actual_centers)),
            "wrong center order: " + name,
        )
        require(
            result["stop_reason"] == reason and result["best_family"]["sha256"] == best,
            "wrong stop/best: " + name,
        )
        require(
            result["centers_processed"] == len(rows) and len(calls) == len(replies), "wrong counts"
        )
        require(result["plateau_exhaustion_claim"] is False, "false plateau claim")
        require(set(result["visited_hashes"]) == {"seed", "old", *expected_centers}, "visited set")
        for number, row in enumerate(rows, 1):
            call_group = [call for call in calls if call[0] == number]
            require(
                [call[1] for call in call_group] == ["one", "two"][: len(call_group)], "shell order"
            )
            require({call[2] for call in call_group} == {row["center_sha256"]}, "same center")
            require(
                row["local_strict_closed"]
                is (
                    row["complete"]
                    and not row["strict_improvement"]
                    and row["stop_reason"] != "cover_observed"
                ),
                "local scope",
            )
        checked.append(
            {
                "name": name,
                "center_order": actual_centers,
                "shell_calls": len(calls),
                "stop_reason": reason,
            }
        )
    for mode in ("neutral", "strict"):
        calls, rows = [], []

        def chain(number, kind, center):
            calls.append((number, kind, center["sha256"]))
            target = state(
                f"chain-{number}", deficit=26 - number if mode == "strict" else 26, first=number
            )
            return outcome(strict=[target]) if mode == "strict" else outcome(neutral=[target])

        result = runner.queue_campaign(
            seed, {"seed"}, chain, lambda row, _: rows.append(row) or row
        )
        require(
            len(rows) == 16
            and len(calls) == 32
            and result["centers_processed"] == 16
            and result["stop_reason"] == "center_budget",
            "center cap",
        )
        require(
            len({call[2] for call in calls}) == 16 and result["unscanned_next"] is not None,
            "unscanned next lost",
        )
        checked.append({"name": mode + "16-center cap", "centers": 16, "shell_calls": 32})
    failures = []
    for name, replies in (
        ("nonstrict strict list", [outcome(strict=[a]), outcome()]),
        ("worse neutral entry", [outcome(neutral=[state("worse", deficit=27)]), outcome()]),
        ("strict entry already historical", [outcome(strict=[low]), outcome()]),
    ):
        calls = []

        def execute(*_):
            calls.append(1)
            return replies[len(calls) - 1]

        history = {"seed", "low"} if "historical" in name else {"seed"}
        failures.append(
            rejected(
                lambda: runner.queue_campaign(seed, history, execute, lambda row, _: row), name
            )
        )
    return {
        "abstract_states_only": True,
        "transition_cases": checked,
        "invalid_transitions": failures,
    }


def recorder_controls(adapter, oracle):
    require(not RAW.exists(), "preserve raw controls")
    RAW.mkdir(parents=True)
    descent = HERE.parent / "weak-pair-d28-deterministic-descent"
    manifest, result = (
        json.loads((descent / "manifest.json").read_text()),
        json.loads((descent / "result.json").read_text()),
    )
    profile = json.loads((HERE.parent / "weak-pair-d28-relabel-novelty/audit.json").read_text())
    original, cores = set(manifest["initial"]["ids"]), manifest["core_rows"]
    checked = []
    for kind, family_name in (("one", "tie-2"), ("two", "tie-4")):
        recorder = adapter.Recorder(kind)
        ids = profile["profiles"][family_name]["ids"]
        direct = oracle.analyze(ids, cores)
        require(
            direct["legal"]
            and (direct["metrics"]["holes"], direct["metrics"]["D2max"]) == (12, 28),
            "positive neutral fixture",
        )
        outgoing, incoming = sorted(original - set(ids)), sorted(set(ids) - original)
        absent, selected = [i for i in range(4368) if i not in original], sorted(original)
        if kind == "one":
            require(len(outgoing) == len(incoming) == 1, "one fixture distance")
            out, inc = outgoing[0], incoming[0]
            ordinal = selected.index(out) * 4304 + absent.index(inc) + 1
            native = {"outgoing": out, "incoming": inc}
        else:
            require(len(outgoing) == len(incoming) == 2, "two fixture distance")
            pair_index = list(itertools.combinations(selected, 2)).index(tuple(outgoing))
            ai, di = (absent.index(i) for i in incoming)
            ordinal = pair_index * 9260056 + sum(4303 - index for index in range(ai)) + di - ai
            native = {"outgoing": outgoing, "incoming": incoming, "shell_ordinal": ordinal}
        native |= {
            "ids": ids,
            "metrics": direct["metrics"] | {"cardinality": 64},
            "neutral_index": 1,
            "neutral_ordinal": ordinal,
        }
        metadata = {
            "neutral_seen": 1,
            "retained": 1,
            "cap": 64,
            "capped": False,
            "complete": True,
            "rank": [12, 28],
        }
        shell = next(row for row in result["rounds"][0]["shells"] if row["shell"] == kind)
        source_prefix = Path(shell["command"][-1])
        stdout = source_prefix.parent.joinpath("stdout.jsonl").read_text()
        prefix = RAW / kind
        Path(str(prefix) + "-ties.json").write_bytes(
            Path(str(source_prefix) + "-ties.json").read_bytes()
        )
        count = 0

        def validate(rows, meta):
            nonlocal count
            count += 1
            Path(str(prefix) + "-neutral.json").write_text(json.dumps(rows) + "\n")
            Path(str(prefix) + "-neutral-meta.json").write_text(json.dumps(meta) + "\n")
            return recorder.validate(
                prefix, stdout, 0, "", shell["elapsed_seconds"], manifest["initial"], cores
            )

        positive = validate([native], metadata)
        require(
            positive["neutral_families"][0]["ids"] == ids
            and positive["neutral_families"][0]["metrics"] == native["metrics"],
            "positive adapter output",
        )
        failures = []
        meta_defects = {
            "wrong cap": metadata | {"cap": 63},
            "boolean cap": metadata | {"cap": True},
            "float seen": metadata | {"neutral_seen": 1.0},
            "retained mismatch": metadata | {"retained": 0},
            "incomplete flag": metadata | {"complete": False},
            "wrong capped flag": metadata | {"capped": True},
            "wrong rank": metadata | {"rank": [12, 29]},
            "Boolean rank": metadata | {"rank": [True, 28]},
            "legal count overflow": metadata | {"neutral_seen": 100000000000, "capped": True},
            "extra field": metadata | {"extra": 1},
            "missing field": {k: v for k, v in metadata.items() if k != "cap"},
        }
        for name, meta in meta_defects.items():
            failures.append(rejected(lambda m=meta: validate([native], m), name))
        row_defects = {"non-object": None}
        for name in (
            "duplicate IDs",
            "reversed IDs",
            "float IDs",
            "wrong metrics",
            "Boolean metric",
            "wrong ordinal",
            "Boolean ordinal",
            "wrong index",
            "Boolean index",
            "bad outgoing",
        ):
            row = copy.deepcopy(native)
            if name == "duplicate IDs":
                row["ids"][0] = row["ids"][1]
            elif name == "reversed IDs":
                row["ids"].reverse()
            elif name == "float IDs":
                row["ids"][0] = float(row["ids"][0])
            elif name == "wrong metrics":
                row["metrics"]["D2max"] = 29
            elif name == "Boolean metric":
                row["metrics"]["D3"] = False
            elif name == "wrong ordinal":
                row["neutral_ordinal"] += 1
            elif name == "Boolean ordinal":
                row["neutral_ordinal"] = True
            elif name == "wrong index":
                row["neutral_index"] = 2
            elif name == "Boolean index":
                row["neutral_index"] = True
            elif kind == "one":
                row["outgoing"] = True
            else:
                row["outgoing"][0] = True
            row_defects[name] = row
        for name, damaged in row_defects.items():
            failures.append(rejected(lambda r=damaged: validate([r], metadata), name))
        duplicate = copy.deepcopy(native)
        duplicate["neutral_index"] = 2
        failures.append(
            rejected(
                lambda: validate(
                    [native, duplicate], metadata | {"neutral_seen": 2, "retained": 2}
                ),
                "duplicate canonical family",
            )
        )
        final = validate([native], metadata)
        checked.append(
            {
                "kind": kind,
                "fixture": family_name,
                "canonical_sha256": final["neutral_families"][0]["sha256"],
                "independent_metrics": direct["metrics"],
                "independent_ordinal": ordinal,
                "rejected_controls": failures,
                "calls": count,
                "synthetic_metadata": True,
            }
        )
    return {"shell_controls": checked, "optimizer_launches": 0}
