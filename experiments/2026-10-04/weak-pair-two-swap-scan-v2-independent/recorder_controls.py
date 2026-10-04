# Document:    Independent Two-Swap Recorder Controls
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      9e89a124afc400f85020d6edae106a938f458bc1daeb11ed0f8ae2d034616ed7
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Synthetic accounting fixtures with real witnesses; never executes a scan prefix."""

import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/weak-pair-two-swap-scan-v2-independent-20261004"
TOTAL, OUTERS, INNER = 18668272896, 8676864, 9260056


def control(runner, cores):
    path = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    spec = importlib.util.spec_from_file_location("recorder_independent_oracle", path)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    require = oracle.require
    base = json.loads((RAW / "control-expectations.json").read_text())
    old = oracle.parse(
        HERE.parent / "native-variable-cardinality/seed-2026104702/search-final-admissible64.txt"
    )
    target = base["base_ids"]
    before = oracle.analyze(old, cores)["metrics"] | {"cardinality": 64}
    after = oracle.analyze(target, cores)["metrics"] | {"cardinality": 64}
    outgoing, incoming = [881, 3145], [1142, 3752]
    require(sorted((set(old) - set(outgoing)) | set(incoming)) == target, "known two-swap control")
    pairs = list(itertools.combinations(old, 2))
    absent = [i for i in range(4368) if i not in set(old)]

    def independent_position(out, inc):
        pair_index = pairs.index(tuple(out))
        a, d = (absent.index(i) for i in inc)
        ordinal = pair_index * sum(range(4304)) + sum(4303 - j for j in range(a)) + d - a
        return ordinal, pair_index * 4304 + a + 1

    position_checks = 0
    for pair_index in (0, 1, 62, 63, 999, 2015):
        for a, d in ((0, 1), (0, 4303), (1, 2), (123, 3000), (4302, 4303)):
            out, inc = list(pairs[pair_index]), [absent[a], absent[d]]
            require(
                runner.exchange_position(set(old), out, inc) == independent_position(out, inc),
                "shell ordinal calculation",
            )
            position_checks += 1
    for outer in (0, 1, 2, 4303, 4304, 4305, 123456, OUTERS - 1, OUTERS):
        groups, remainder = divmod(outer, 4304)
        expected = groups * sum(range(4304)) + sum(4303 - i for i in range(remainder))
        require(runner.shell_started(outer) == expected, "outer shell accounting")
    ordinal, outer = independent_position(outgoing, incoming)
    candidate = {
        "outgoing": outgoing,
        "incoming": incoming,
        "shell_ordinal": ordinal,
        "metrics": after,
    }
    prefix = RAW / "synthetic-recorder"

    def make(
        initial,
        started,
        completed,
        evaluated,
        generated,
        pruned,
        reason,
        seconds,
        last=0,
        record=None,
        best=None,
    ):
        bins, shell_bins = [0] * 8, [0] * 8
        bins[5], shell_bins[5] = started, runner.shell_started(started)
        final = {
            "event": "final",
            "complete": completed == OUTERS,
            "reason": reason,
            "total": TOTAL,
            "outer_total": OUTERS,
            "outer_started": started,
            "outer_completed": completed,
            "evaluated": evaluated,
            "pair_floor_pruned": pruned,
            "eligible_generated": generated,
            "pending_eligible": generated - evaluated,
            "accounted": pruned + evaluated,
            "last_evaluated_ordinal": last,
            "legal": evaluated,
            "strictly_improving_neighbors": int(record is not None),
            "strict_improvement_records": int(record is not None),
            "best_ties": int(record is not None),
            "best_rank": best or [initial["metrics"]["holes"], initial["metrics"]["D2max"]],
            "support_bins": bins,
            "support_shell_bins": shell_bins,
            "seconds": seconds,
        }
        limit = started if reason == "control_limit" else None
        events = [
            {
                "event": "start",
                "budget_seconds": 120,
                "total": TOTAL,
                "outer_total": OUTERS,
                "control_limit": limit,
                "baseline": initial["metrics"],
            }
        ]
        if record is not None:
            events.append(
                record
                | {
                    "event": "improvement",
                    "serial": 1,
                    "evaluated": 1,
                    "outer_index": outer,
                    "seconds": 0.1,
                }
            )
        events.append(final)
        return {
            "events": events,
            "initial": initial,
            "ties": [record] if record else [],
            "limit": limit,
            "rc": int(completed != OUTERS),
        }

    def validate(fixture):
        Path(str(prefix) + "-ties.json").write_text(json.dumps(fixture["ties"]) + "\n")
        return runner.validate(
            prefix,
            "\n".join(map(json.dumps, fixture["events"])),
            fixture["rc"],
            "",
            121.0,
            fixture["initial"],
            cores,
            control_limit=fixture["limit"],
        )

    old_initial = {"ids": old, "metrics": before}
    current = {"ids": target, "metrics": base["baseline"]["metrics"] | {"cardinality": 64}}
    positive = make(
        old_initial,
        outer,
        outer,
        1,
        1,
        runner.shell_started(outer) - 1,
        "control_limit",
        0.2,
        ordinal,
        candidate,
        [12, 29],
    )
    passed = validate(positive)
    target_text = "".join(" ".join(map(str, oracle.SUBSETS[5][i])) + "\n" for i in target)
    require(
        passed["best_ties"][0]["sha256"] == hashlib.sha256(target_text.encode()).hexdigest(),
        "positive family digest",
    )
    zero = make(current, 0, 0, 0, 0, 0, "control_limit", 0.01)
    partial = make(current, 1, 0, 1, 2, 4301, "time_limit", 120.0, 1)
    complete = make(current, OUTERS, OUTERS, 1, 1, TOTAL - 1, "complete", 1.0, 1)
    for fixture in (zero, partial, complete):
        result = validate(fixture)
        require(
            result["passed"]
            and not result["best_ties"]
            and result["final"]["best_rank"] == [12, 29],
            "empty improving-tie outcome",
        )
    rejected = []
    for name in (
        "support_one",
        "shell_without_outer",
        "gap_without_pending",
        "pending_over_tail",
        "wrong_partition",
        "false_complete",
        "early_timeout",
        "numeric_complete",
        "floating_counter",
        "wrong_ordinal",
        "wrong_metrics",
        "duplicate_tie",
        "invalid_outgoing",
        "negative_seconds",
    ):
        fixture = copy.deepcopy(
            positive
            if name in {"wrong_ordinal", "wrong_metrics", "duplicate_tie", "invalid_outgoing"}
            else partial
        )
        final = fixture["events"][-1]
        if name == "support_one":
            final["support_bins"][3], final["support_bins"][5] = 1, 0
            final["support_shell_bins"][3], final["support_shell_bins"][5] = 4303, 0
        elif name == "shell_without_outer":
            final["support_shell_bins"][4] = 1
            final["support_shell_bins"][5] -= 1
        elif name == "gap_without_pending":
            final.update(
                pending_eligible=0, eligible_generated=1, pair_floor_pruned=4302, accounted=4303
            )
        elif name == "pending_over_tail":
            final.update(
                outer_started=4303,
                outer_completed=4302,
                pending_eligible=2,
                eligible_generated=3,
                pair_floor_pruned=runner.shell_started(4303) - 3,
                accounted=runner.shell_started(4303) - 2,
            )
            final["support_bins"][5] = 4303
            final["support_shell_bins"][5] = runner.shell_started(4303)
        elif name == "wrong_partition":
            final["accounted"] += 1
        elif name == "false_complete":
            final["reason"] = "complete"
        elif name == "early_timeout":
            final["seconds"] = 119.0
        elif name == "numeric_complete":
            final["complete"] = 0
        elif name == "floating_counter":
            final["evaluated"] = 1.0
        elif name == "wrong_ordinal":
            fixture["events"][1]["shell_ordinal"] -= 1
        elif name == "wrong_metrics":
            fixture["events"][1]["metrics"]["holes"] = 11
        elif name == "duplicate_tie":
            fixture["ties"].append(copy.deepcopy(candidate))
            final.update(
                best_ties=2,
                strictly_improving_neighbors=2,
                legal=2,
                evaluated=2,
                eligible_generated=2,
                pair_floor_pruned=runner.shell_started(outer) - 2,
            )
        elif name == "invalid_outgoing":
            fixture["events"][1]["outgoing"][0] = -1
        else:
            final["seconds"] = -1
        try:
            validate(fixture)
        except (AssertionError, ValueError, KeyError):
            rejected.append(name)
        else:
            raise ValueError(f"malformed recorder fixture accepted: {name}")
    validate(positive)
    return {
        "passed": True,
        "position_controls": position_checks,
        "shell_prefix_controls": 9,
        "positive_swap": {
            "outgoing": outgoing,
            "incoming": incoming,
            "ordinal": ordinal,
            "outer": outer,
            "from": [12, 34],
            "to": [12, 29],
        },
        "empty_tie_states_accepted": ["zero_control", "partial_timeout", "complete"],
        "malformed_fixtures_rejected": rejected,
        "scope": "Synthetic recorder fixtures; no recorded prefix or complete scan was executed.",
    }
