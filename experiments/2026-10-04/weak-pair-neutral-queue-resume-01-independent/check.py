# Document:    Independent Neutral Queue Resume Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2e478de5b6504798220a6b59ed6a9dd804d13befe95f08d35f5f2e09b7796042
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check carried frontier, exclusions, unchanged kernels, and the new bounded wrapper."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-neutral-queue-resume-01"
PREVIOUS = HERE.parent / "weak-pair-neutral-queue"
PREVIOUS_AUDIT = HERE.parent / "weak-pair-neutral-queue-runtime-independent"
MANIFEST = "aeaa247b3c1f5ba967e968412f59d261659c760e766fd5787637e953ff39b4ba"
PRIOR_MANIFEST = "5a1082e2f28194ee4c90ee0d16bf0d5b22502164e082e757a35842547eae2a82"
PRIOR_RESULT = "086524c3b7f8db6e11ab6b3e321c379facc36b3f51fb163740e7cc7fdac9d048"
PRIOR_POSTCHECK = "fd044b1f88955403181b2d6ac739526c2d27ded14b0cff66f36a59d40a1cdde3"
PRIOR_FRONTIER = "523ab6b38b23748885d19023d41b0dde5cdbd52b06b920aec6c1418f706ffe06"


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


def controls(runner):
    def state(name, first=0, deficit=25, holes=11):
        return {
            "sha256": name,
            "ids": [first, first + 100],
            "metrics": {"holes": holes, "D2max": deficit},
            "cover_found": holes == 0,
        }

    def outcome(strict=(), neutral=(), complete=True, covers=()):
        return {
            "passed": True,
            "complete": complete,
            "best_ties": list(strict),
            "neutral_ties": list(neutral),
            "observed_covers": list(covers),
        }

    seed, a, b, c = state("seed"), state("a", 5), state("b", 10), state("c", 2)
    better, peer, cover = state("better", 3, 24), state("peer", 9, 24), state("cover", 1, 0, 0)
    cases = [
        (
            "carry pending frontier",
            [outcome()] * 6,
            [seed, b, a],
            ["seed", "a", "b"],
            "sample_exhausted",
            "seed",
        ),
        (
            "new neutral before saved pending",
            [outcome(neutral=[c, b]), outcome()] + [outcome()] * 6,
            [seed, b, a],
            ["seed", "c", "a", "b"],
            "sample_exhausted",
            "seed",
        ),
        (
            "strict best replaces saved frontier",
            [outcome(strict=[peer]), outcome(strict=[better])] + [outcome()] * 4,
            [seed, a, b],
            ["seed", "better", "peer"],
            "sample_exhausted",
            "better",
        ),
        (
            "second incomplete keeps carried frontier",
            [outcome(strict=[better]), outcome(complete=False)],
            [seed, a, b],
            ["seed"],
            "incomplete",
            "seed",
        ),
        (
            "early cover preserves scope",
            [outcome(covers=[cover])],
            [seed, a, b],
            ["seed"],
            "cover_observed",
            "seed",
        ),
    ]
    results = []
    for name, replies, frontier, expected, reason, best in cases:
        calls, rows = [], []

        def execute(number, kind, center):
            calls.append((number, kind, center["sha256"]))
            require(len(calls) <= len(replies), "too many shell calls")
            return replies[len(calls) - 1]

        result = runner.queue_campaign(
            seed, {"historical"}, execute, lambda row, _: rows.append(row) or row, frontier
        )
        require([row["center_sha256"] for row in rows] == expected, name + " center order")
        require(
            result["stop_reason"] == reason and result["best_family"]["sha256"] == best,
            name + " stop/best",
        )
        require(
            len(calls) == len(replies) and result["plateau_exhaustion_claim"] is False,
            name + " limits",
        )
        for number, row in enumerate(rows, 1):
            group = [call for call in calls if call[0] == number]
            require(
                [call[1] for call in group] == ["one", "two"][: len(group)]
                and {call[2] for call in group} == {row["center_sha256"]},
                name + " same-center shells",
            )
        if reason in ("incomplete", "cover_observed"):
            require(
                [s["sha256"] for s in result["unscanned_frontier"]] == ["a", "b"],
                "lost carried frontier",
            )
            require(
                result["unscanned_next"] is None and result["queued_unscanned"] == 2,
                "frontier counts",
            )
        else:
            require(result["unscanned_frontier"] == [], "unexplored saved frontier")
        results.append({"name": name, "centers": expected, "shell_calls": len(calls)})
    static = state("static-pending", 1000)
    calls = []

    def chain(number, kind, center):
        calls.append((number, kind, center["sha256"]))
        return outcome(neutral=[state(f"next-{number}", number)])

    result = runner.queue_campaign(seed, {"historical"}, chain, lambda row, _: row, [seed, static])
    require(
        len(calls) == 64
        and result["centers_processed"] == 32
        and result["stop_reason"] == "center_budget",
        "fresh32/64 cap",
    )
    require(len({call[2] for call in calls}) == 32, "repeated resume center")
    require(
        [s["sha256"] for s in result["unscanned_frontier"]] == ["next-32", "static-pending"]
        and result["unscanned_next"]["sha256"] == "next-32"
        and result["queued_unscanned"] == 1,
        "popped next and old pending preserved",
    )
    results.append(
        {"name": "32-center cap carries popped next and pending", "centers": 32, "shell_calls": 64}
    )
    rejections = []
    for name, initial, historical, frontier in (
        ("empty frontier", seed, set(), []),
        ("initial missing", seed, set(), [a]),
        ("duplicate frontier", seed, set(), [seed, seed]),
        ("historical initial", seed, {"seed"}, [seed]),
        ("historical pending", seed, {"a"}, [seed, a]),
        ("mixed rank", seed, set(), [seed, better]),
        ("nonleast initial", a, set(), [seed, a]),
    ):
        launched = []
        try:
            runner.queue_campaign(
                initial,
                historical,
                lambda *args: launched.append(args),
                lambda row, _: row,
                frontier,
            )
        except ValueError:
            require(not launched, "invalid frontier launched shell")
            rejections.append(name)
        else:
            raise ValueError("accepted invalid frontier: " + name)
    return {
        "abstract_states_only": True,
        "transition_cases": results,
        "rejected_before_launch": rejections,
    }


def main():
    require(not (HERE / "gate.json").exists(), "preserve gate")
    require(sha(PRODUCER / "manifest.json") == MANIFEST, "manifest changed")
    require(
        sha(PREVIOUS / "manifest.json") == PRIOR_MANIFEST
        and sha(PREVIOUS / "result.json") == PRIOR_RESULT,
        "previous campaign changed",
    )
    require(
        sha(PREVIOUS_AUDIT / "postcheck.json") == PRIOR_POSTCHECK
        and sha(PREVIOUS_AUDIT / "unscanned-frontier.json") == PRIOR_FRONTIER,
        "prior audit changed",
    )
    manifest, previous = read(PRODUCER / "manifest.json"), read(PREVIOUS / "manifest.json")
    prior_frontier = read(PREVIOUS_AUDIT / "unscanned-frontier.json")
    require(
        manifest["status"] == "PREPARED_NOT_RUN"
        and manifest["search_launches"] == 0
        and manifest["seed_revisit_exception"] is None,
        "resume state/revisit policy",
    )
    require(
        manifest["prior_manifest_sha256"] == PRIOR_MANIFEST
        and manifest["prior_result_sha256"] == PRIOR_RESULT
        and manifest["prior_runtime_review_sha256"] == PRIOR_POSTCHECK,
        "previous evidence binding",
    )
    for group in ("input_files", "sources", "files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, "bound input changed: " + relative)
    require(
        manifest["budget"]
        == {
            "max_centers": 32,
            "max_shell_launches": 64,
            "seconds_per_shell": 120,
            "watchdog_seconds": 135,
            "termination_grace_seconds": 5,
            "budget_transfer": False,
            "relaunch": False,
            "seed": None,
        },
        "new budget",
    )
    require(
        manifest["historical_visited_hashes"] == prior_frontier["visited_hashes"],
        "completed history lost",
    )
    require(
        manifest["core_rows"] == previous["core_rows"] and previous["neutral_cap_per_shell"] == 64,
        "filters/sampling changed",
    )
    for kind, shell in manifest["shells"].items():
        require(
            shell["binary_sha256"] == previous["shells"][kind]["binary_sha256"]
            and sha(ROOT / shell["binary_path"]) == shell["binary_sha256"],
            "new native binary",
        )
        require(
            shell["recorder_sha256"] == previous["shells"][kind]["recorder_sha256"]
            and sha(ROOT / shell["recorder_path"]) == shell["recorder_sha256"],
            "new adapter",
        )
    frontier = read(ROOT / manifest["resume_frontier_path"])["frontier"]
    require(len(frontier) == manifest["resume_frontier_count"] == 14, "carried frontier count")
    require(
        [s["sha256"] for s in frontier] == [s["sha256"] for s in prior_frontier["families"]],
        "frontier membership/order",
    )
    require(
        manifest["initial"] == min(frontier, key=lambda s: tuple(s["ids"])), "resume initial choice"
    )
    oracle = load("resume_gate_oracle", HERE.parent / "weak-pair-swap-scan-independent/oracle.py")
    runner = load("resume_runner_under_audit", PRODUCER / "run.py")
    base = runner.base_module()
    adapter = runner.load(HERE.parent / "weak-pair-neutral-queue/adapter.py", "resume_gate_adapter")
    recorder = adapter.Recorder("one")
    for state, independent in zip(frontier, prior_frontier["families"], strict=True):
        require(
            state["ids"] == independent["ids"] and state["metrics"] == independent["metrics"],
            "frontier content",
        )
        direct = oracle.analyze(state["ids"], manifest["core_rows"])
        require(
            direct["legal"] and direct["metrics"] | {"cardinality": 64} == state["metrics"],
            "frontier recount",
        )
        require(
            base.verify_family(state["ids"], recorder, manifest["core_rows"]) == state,
            "frontier dual verification",
        )
    require(
        not runner.RUN.exists() and not (PRODUCER / "result.json").exists(),
        "premature resume launch",
    )
    finite = controls(runner)
    gate = {
        "passed": True,
        "decision": "GO",
        "manifest_sha256": MANIFEST,
        "runner_sha256": sha(PRODUCER / "run.py"),
        "initial_sha256": manifest["initial"]["sha256"],
        **{f"{kind}_binary_sha256": s["binary_sha256"] for kind, s in manifest["shells"].items()},
        "budget": manifest["budget"],
        "source_sha256": sha(__file__),
        "prior_result_sha256": PRIOR_RESULT,
        "prior_postcheck_sha256": PRIOR_POSTCHECK,
        "prior_frontier_sha256": PRIOR_FRONTIER,
        "carried_families_dual_rechecked": 14,
        "queue_delta_controls": finite,
        "optimizer_launches": 0,
        "scope": "New separately bounded continuation over unvisited carried frontier. Same native "
        "binaries/adapter, no historical revisit exception,32 centers/64 calls maximum. "
        "No full plateau claim; empty retained sample is not a global theorem.",
    }
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "decision": "GO",
                "passed": True,
                "gate_sha256": sha(HERE / "gate.json"),
                "carried_families": 14,
                "optimizer_launches": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
