# Document:    Neutral Queue and Recorder Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      20cf75ff1ea416e82036b54f2ae71350a227011bf8568a3e82ba0cb835db38e1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay saved strict outputs and synthetic queue cases without running a search."""

import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location("neutral_control_" + name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

        result = runner.queue_campaign(seed, {"seed", "old"}, execute, persist)
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

    result = runner.queue_campaign(seed, {"seed"}, chain, lambda r, c: r)
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


def recorder_controls(adapter):
    campaign = HERE.parent / "weak-pair-d28-deterministic-descent"
    result = json.loads((campaign / "result.json").read_text())
    initial = json.loads((campaign / "manifest.json").read_text())["initial"]
    cores = json.loads((campaign / "manifest.json").read_text())["core_rows"]
    audit = json.loads((HERE.parent / "weak-pair-d28-relabel-novelty/audit.json").read_text())
    checked = []
    for kind, name in (("one", "tie-2"), ("two", "tie-4")):
        recorder = adapter.Recorder(kind)
        shell = next(s for s in result["rounds"][0]["shells"] if s["shell"] == kind)
        original = set(initial["ids"])
        ids = audit["profiles"][name]["ids"]
        outgoing = sorted(original - set(ids))
        incoming = sorted(set(ids) - original)
        metrics = recorder.inspect_family(ids, cores)["metrics"]
        if kind == "one":
            assert len(outgoing) == len(incoming) == 1
            out, inc = outgoing[0], incoming[0]
            absent = [i for i in range(4368) if i not in original]
            ordinal = sorted(original).index(out) * 4304 + absent.index(inc) + 1
            row = {"outgoing": out, "incoming": inc, "metrics": metrics}
        else:
            assert len(outgoing) == len(incoming) == 2
            ordinal, _ = recorder.exchange_position(original, outgoing, incoming)
            row = {
                "outgoing": outgoing,
                "incoming": incoming,
                "shell_ordinal": ordinal,
                "metrics": metrics,
            }
        row.update({"ids": ids, "neutral_index": 1, "neutral_ordinal": ordinal})
        meta = {
            "neutral_seen": 1,
            "retained": 1,
            "cap": 64,
            "capped": False,
            "complete": True,
            "rank": [12, 28],
        }
        old_prefix = Path(shell["command"][-1])
        stdout = old_prefix.parent.joinpath("stdout.jsonl").read_text()
        with tempfile.TemporaryDirectory(prefix="neutral-recorder-control-") as directory:
            prefix = Path(directory) / "fixture"
            shutil.copyfile(str(old_prefix) + "-ties.json", str(prefix) + "-ties.json")

            def validate(rows, metadata):
                Path(str(prefix) + "-neutral.json").write_text(json.dumps(rows))
                Path(str(prefix) + "-neutral-meta.json").write_text(json.dumps(metadata))
                return recorder.validate(
                    prefix, stdout, 0, "", shell["elapsed_seconds"], initial, cores
                )

            positive = validate([row], meta)
            assert (
                len(positive["neutral_families"]) == 1
                and positive["neutral_families"][0]["ids"] == ids
            )
            defects = []
            bad = copy.deepcopy(row)
            bad["ids"][0] = bad["ids"][1]
            defects.append(([bad], meta))
            bad = copy.deepcopy(row)
            bad["metrics"]["D2max"] += 1
            defects.append(([bad], meta))
            bad = copy.deepcopy(row)
            bad["neutral_ordinal"] += 1
            defects.append(([bad], meta))
            bad = copy.deepcopy(row)
            bad["neutral_index"] = 2
            defects.append(([bad], meta))
            defects.extend(
                [
                    ([row], meta | {"cap": 65}),
                    ([row], meta | {"neutral_seen": True}),
                    ([row], meta | {"retained": 0}),
                    ([None], meta),
                ]
            )
            for rows, metadata in defects:
                try:
                    validate(rows, metadata)
                except (ValueError, AssertionError, TypeError, KeyError):
                    pass
                else:
                    raise AssertionError("damaged neutral control accepted")
            checked.append(
                {
                    "shell": kind,
                    "passed": True,
                    "positive_saved_neutral_family": name,
                    "negative_controls": len(defects),
                    "synthetic_metadata": True,
                }
            )
    return checked


def main():
    runner = load("run")
    base = runner.base_module()
    report = {
        "passed": True,
        "search_launches": 0,
        "solver_launches": 0,
        "native_search_launches": 0,
        "runner_sha256": base.sha(HERE / "run.py"),
        "adapter_sha256": base.sha(HERE / "adapter.py"),
        "source_sha256": base.sha(Path(__file__)),
        "queue_cases": queue_controls(runner),
        "recorder_cases": recorder_controls(load("adapter")),
        "scope": "Synthetic queue control states and synthetic neutral metadata around real, "
        "previously verified families. Recorded strict output is replayed; no new "
        "neighborhood is enumerated and no new witness is discovered.",
    }
    base.dump(HERE / "controls.json", report)
    print(
        json.dumps(
            {
                "passed": True,
                "queue_cases": len(report["queue_cases"]),
                "search_launches": 0,
                "receipt_sha256": base.sha(HERE / "controls.json"),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
