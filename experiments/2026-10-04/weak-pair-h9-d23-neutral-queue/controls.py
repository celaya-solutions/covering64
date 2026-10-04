# Document:    H9 D23 Neutral Queue Deterministic Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f7cc8c53b2f42972eca786cd81acfe792c074519a481a7a90f1b70068113bd49
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Test queue policy with synthetic outcomes; no production or native launches."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("resume_queue_controls", HERE / "run.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def state(tag, deficit=26, first=0, holes=12):
    return {
        "sha256": tag,
        "ids": list(range(first, first + 64)),
        "metrics": {"holes": holes, "D2max": deficit},
        "cover_found": holes == 0,
    }


def outcome(strict=(), neutral=(), complete=True, passed=True, covers=()):
    return {
        "passed": passed,
        "complete": complete,
        "best_ties": list(strict),
        "neutral_ties": list(neutral),
        "observed_covers": list(covers),
    }


def queue_controls(runner):
    seed = state("seed")
    a = state("a", first=1)
    b = state("b", first=2)
    old = state("old", first=0)
    low = state("low", 25, first=3)
    sibling = state("sibling", 25, first=4)
    cover = state("cover", 0, first=5, holes=0)
    cases = [
        ("empty-sample", [outcome(), outcome()], "sample_exhausted", 1, "seed"),
        (
            "dedup-prior-and-sampled-centers",
            [
                outcome(neutral=[b, old, a]),
                outcome(neutral=[a]),
                outcome(neutral=[seed, b]),
                outcome(),
                outcome(),
                outcome(),
            ],
            "sample_exhausted",
            3,
            "seed",
        ),
        (
            "strict-first-and-clear-worse-frontier",
            [
                outcome(neutral=[a, b]),
                outcome(),
                outcome(strict=[sibling, low]),
                outcome(neutral=[b]),
                outcome(),
                outcome(),
                outcome(),
                outcome(),
            ],
            "sample_exhausted",
            4,
            "low",
        ),
        ("incomplete-first", [outcome(complete=False)], "incomplete", 1, "seed"),
        (
            "incomplete-second-no-adoption",
            [outcome(strict=[low]), outcome(complete=False)],
            "incomplete",
            1,
            "seed",
        ),
        ("cover-early", [outcome(strict=[cover], covers=[cover])], "cover_observed", 1, "seed"),
        ("incomplete-cover", [outcome(complete=False, covers=[cover])], "incomplete", 1, "seed"),
    ]
    results = []
    for name, replies, reason, count, best in cases:
        calls, rows = [], []

        def execute(n, k, c):
            calls.append((n, k, c["sha256"]))
            return replies[len(calls) - 1]

        def persist(row, current):
            rows.append(row)
            return row

        result = runner.queue_campaign(seed, {"old"}, execute, persist, [seed])
        assert result["stop_reason"] == reason and result["centers_processed"] == count
        assert result["best_family"]["sha256"] == best and not result["plateau_exhaustion_claim"]
        visited = [r["center_sha256"] for r in rows]
        assert len(visited) == len(set(visited)) and "old" not in visited
        assert all(len({c[2] for c in calls if c[0] == i}) == 1 for i in range(1, count + 1))
        if name == "strict-first-and-clear-worse-frontier":
            assert visited == ["seed", "a", "low", "sibling"]
        if name == "dedup-prior-and-sampled-centers":
            assert visited == ["seed", "a", "b"]
        results.append({"case": name, "passed": True, "centers": count, "shell_calls": len(calls)})
    calls = []

    def chain(n, k, c):
        calls.append((n, k, c["sha256"]))
        return outcome(neutral=[state(f"next-{n}", first=n + 1)])

    result = runner.queue_campaign(seed, set(), chain, lambda r, c: r, [seed])
    assert (
        len(calls) == 32
        and result["centers_processed"] == 16
        and result["stop_reason"] == "center_budget"
    )
    assert len({c[2] for c in calls}) == 16
    results.append(
        {
            "case": "sixteen-center-thirty-two-shell-cap",
            "passed": True,
            "centers": 16,
            "shell_calls": 32,
        }
    )
    return results


def resume_controls():
    seed, a, b = state("seed"), state("a", first=1), state("b", first=2)
    low = state("low", deficit=25, first=3)
    cases = []
    for name, frontier, strict, expected in (
        ("carry-all-saved-frontier", [seed, a, b], False, ["seed", "a", "b"]),
        ("clear-saved-worse-frontier-on-descent", [seed, a, b], True, ["seed", "low"]),
    ):
        rows, calls = [], []

        def execute(n, k, c):
            calls.append((n, k, c["sha256"]))
            return outcome(strict=[low] if strict and n == 1 and k == "two" else [])

        result = RUNNER.queue_campaign(
            seed, {"old"}, execute, lambda r, c: rows.append(r) or r, frontier
        )
        assert [r["center_sha256"] for r in rows] == expected
        assert result["unscanned_frontier"] == []
        assert result["unscanned_next"] is None and result["queued_unscanned"] == 0
        assert result["stop_reason"] == "sample_exhausted"
        cases.append({"case": name, "passed": True, "shell_calls": len(calls)})

    calls = []

    def chain(n, k, c):
        calls.append((n, k, c["sha256"]))
        return outcome(neutral=[state(f"next-{n}", first=n + 1)])

    result = RUNNER.queue_campaign(seed, {"old"}, chain, lambda r, c: r, [seed])
    assert len(calls) == 32 and result["centers_processed"] == 16
    assert result["unscanned_frontier"] == [result["unscanned_next"]]
    assert result["unscanned_frontier"][0]["sha256"] not in result["visited_hashes"]
    cases.append({"case": "explicit-popped-next-preserved", "passed": True})

    damages = (
        ("empty-frontier", seed, set(), []),
        ("missing-initial", seed, set(), [a]),
        ("duplicate-frontier", seed, set(), [seed, seed]),
        ("visited-initial-no-exception", seed, {"seed"}, [seed]),
        ("visited-pending", seed, {"a"}, [seed, a]),
        ("mixed-rank", seed, set(), [seed, low]),
        ("initial-not-lexicographically-first", a, set(), [a, seed]),
    )
    for name, initial, historical, frontier in damages:
        launched = []
        try:
            RUNNER.queue_campaign(
                initial, historical, lambda *args: launched.append(args), lambda r, c: r, frontier
            )
        except ValueError:
            assert launched == []
        else:
            raise AssertionError(name)
        cases.append({"case": name, "passed": True, "rejected_before_launch": True})
    return cases


if __name__ == "__main__":
    results = queue_controls(RUNNER) + resume_controls()

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    receipt = {
        "passed": True,
        "cases": results,
        "runner_sha256": sha(HERE / "run.py"),
        "controls_sha256": sha(Path(__file__)),
        "native_search_launches": 0,
        "scope": "Synthetic queue and resume policy only; frozen native kernels unchanged",
    }
    (HERE / "controls.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": True, "cases": len(results), "native_search_launches": 0}))
