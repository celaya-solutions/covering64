# Document:    Independent Native Partial-Start Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      aba39b8178d6e234fc75e08b5b74f6b0317bf9f75b01077f17f3fc81102739bd
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read-only validation of every saved state and terminal campaign policy."""

import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "native-variable-partial-start"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
RANK = {block: index for index, block in enumerate(BLOCKS)}
GATE_SHA = "ea66aee6e55730dc8b0716e0472badc64cabed1b58468d25ba23293d9d8158d5"
MANIFEST_SHA = "d66e4f2dfe7604b06dcd9d94ac49efc0c82b748b03977195e4a3924f6b2daaa5"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse(text):
    rows = [tuple(map(int, line.split())) for line in text.splitlines() if line.strip()]
    require(
        all(
            len(row) == len(set(row)) == 5
            and 1 <= min(row) <= max(row) <= 16
            and tuple(sorted(row)) == row
            for row in rows
        ),
        "malformed block",
    )
    require(len(rows) == len(set(rows)), "duplicate family")
    require(rows == sorted(rows), "nonlexicographic family")
    return rows


def metrics(ids, cores):
    require(len(ids) == len(set(ids)), "duplicate IDs")
    counts = Counter(triple for index in ids for triple in itertools.combinations(BLOCKS[index], 3))
    return {
        "cardinality": len(ids),
        "holes": 560 - len(counts),
        "core_overlaps": [len(set(ids).intersection(core)) for core in cores],
    }


def validate_trace_shape(trace):
    for name, upper in (("target", 560), ("draw", 100), ("incoming", 4368)):
        value = trace[name]
        require(type(value) is int and 0 <= value < upper, f"invalid trace {name}")
    require(type(trace["step"]) is int and trace["step"] >= 0, "invalid trace step")
    removed = trace["removed"]
    require(
        type(removed) is list
        and len(removed) == 2
        and all(type(value) is int and -1 <= value < 4368 for value in removed),
        "invalid removed IDs",
    )
    action = trace["action"]
    require(action in {"add_only", "swap", "double_drop"}, "unexpected live action")
    require(
        (action == "add_only" and removed == [-1, -1])
        or (action == "swap" and removed[0] >= 0 and removed[1] == -1)
        or (action == "double_drop" and min(removed) >= 0 and removed[0] != removed[1]),
        "wrong removal arity or sentinels",
    )
    require(
        all(type(trace[key]) is bool for key in ("fallback", "novelty", "weights_updated")),
        "nonboolean trace flag",
    )
    require(not (trace["fallback"] and trace["novelty"]), "conflicting incoming flags")


def trace_shape_controls():
    base = {
        "step": 0,
        "target": 46,
        "draw": 76,
        "action": "double_drop",
        "incoming": 19,
        "removed": [4224, 1650],
        "fallback": True,
        "novelty": False,
        "weights_updated": False,
    }
    validate_trace_shape(base)
    patches = [
        {"target": -1},
        {"target": 560},
        {"target": True},
        {"draw": -1},
        {"draw": 100},
        {"draw": False},
        {"incoming": -1},
        {"incoming": 4368},
        {"incoming": True},
        {"step": True},
        {"step": -1},
        {"removed": [1]},
        {"removed": [1, 2, 3]},
        {"removed": [True, 2]},
        {"removed": [-2, 2]},
        {"removed": [4368, 2]},
        {"removed": [1, 1]},
        {"removed": [1, -1]},
        {"action": "swap"},
        {"action": "add_only"},
        {"fallback": 1},
        {"novelty": 0},
        {"weights_updated": 0},
        {"novelty": True},
    ]
    for patch in patches:
        try:
            validate_trace_shape(base | patch)
        except ValueError:
            pass
        else:
            raise ValueError("malformed trace control accepted")
    return len(patches)


def main():
    output = HERE / "postcheck.json"
    require(not output.exists(), "postcheck exists")
    require(sha(HERE / "gate.json") == GATE_SHA, "pre-run gate changed")
    require(sha(PRODUCER / "manifest.json") == MANIFEST_SHA, "producer manifest changed")
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    result_path = PRODUCER / "result.json"
    result = json.loads(result_path.read_text())
    require(
        result["manifest_sha256"] == MANIFEST_SHA and result["gate_sha256"] == GATE_SHA,
        "runtime binding mismatch",
    )
    require(result["budget"] == manifest["budget"], "budget changed")
    trace_controls_rejected = trace_shape_controls()
    for group in ("source_files", "input_files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, f"frozen artifact changed: {relative}")
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    spec = importlib.util.spec_from_file_location(
        "standalone_postcheck", ROOT / "scripts/check_cover.py"
    )
    standalone = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(standalone)
    cores = manifest["core_rows"]
    checked = []

    def check(path, expected):
        blocks = parse(path.read_text())
        ids = [RANK[block] for block in blocks]
        actual = metrics(ids, cores)
        require(actual == expected, f"saved metrics mismatch: {path.name}")
        package = verify_cover(blocks, 16, 5, 3)
        separate = standalone.verify_cover(blocks, 16, 5, 3, expected_blocks=len(blocks))
        holes = [
            triple for triple in TRIPLES if not any(set(triple) <= set(block) for block in blocks)
        ]
        require(
            sorted(map(tuple, package["uncovered"]))
            == holes
            == sorted(map(tuple, separate["uncovered"])),
            "dual verifier hole mismatch",
        )
        require(package["valid"] == separate["valid"] == (not holes), "dual verdict mismatch")
        require(package["canonical_sha256"] == separate["canonical_sha256"], "canonical mismatch")
        row = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha(path),
            "metrics": actual,
            "exact64_four_caps_pass": len(blocks) == 64 and max(actual["core_overlaps"]) <= 55,
            "package": package,
            "standalone": separate,
        }
        checked.append(row)
        return row

    seeds = manifest["budget"]["seeds"]
    runs = result["runs"]
    require(
        0 < len(runs) <= 2 and [run["seed"] for run in runs] == seeds[: len(runs)], "seed policy"
    )
    require(result["skipped_seeds"] == seeds[len(runs) :], "skipped seed accounting")
    summaries, previous_end = [], None
    for run_index, run in enumerate(runs):
        seed = run["seed"]
        initial = next(row for row in manifest["initial_partials"] if row["seed"] == seed)
        require(run["validation_passed"], "producer validation failure")
        require(run["returncode"] in (0, 1, 2) and not run["watchdog"]["fired"], "exit/watchdog")
        elapsed = run["elapsed_seconds"]
        require(0 <= elapsed <= 320.5, "wall budget outside watchdog and grace")
        start = datetime.fromisoformat(run["started_utc"]).timestamp()
        if previous_end is not None:
            require(start >= previous_end - 0.1, "overlapping run times")
        previous_end = start + elapsed
        command = run["command"]
        require(
            command
            == [
                str(ROOT / manifest["binary_path"]),
                str(ROOT / manifest["incumbent_path"]),
                str(ROOT / initial["path"]),
                str(seed),
                "300",
                str(PRODUCER / f"seed-{seed}/search"),
            ],
            "command changed",
        )
        for stream in ("stdout", "stderr"):
            require(sha(ROOT / run[stream]["path"]) == run[stream]["sha256"], "log hash mismatch")
        require(not (ROOT / run["stderr"]["path"]).read_text(), "native stderr not empty")
        events = [
            json.loads(line) for line in (ROOT / run["stdout"]["path"]).read_text().splitlines()
        ]
        require(
            events[0]
            == {
                "event": "start",
                "seed": seed,
                "budget": 300,
                "mode": "search",
                "control_step_limit": None,
            },
            "start event",
        )
        require(
            all(
                event["event"]
                in {"start", "record", "trace", "finished", "cover_found", "interrupted"}
                for event in events
            ),
            "unknown log event",
        )
        terminal = events[-1]
        require(terminal == run["final"], "terminal log differs from result")
        records = [event for event in events if event["event"] == "record"]
        traces = [event for event in events if event["event"] == "trace"]
        directory = PRODUCER / f"seed-{seed}"
        require(
            [row["serial"] for row in records] == list(range(1, len(records) + 1)), "serial gap"
        )
        seen = {"complete": [], "raw64": [], "admissible64": []}
        expected_paths = set()
        prior_seconds, prior_mutations = 0.0, 0
        success_records = []
        for record in records:
            role = record["role"]
            require(role in seen, "unknown record role")
            path = directory / f"search-record-{record['serial']}-{role}.txt"
            expected_paths.add(path)
            row = check(path, record["metrics"])
            row.update(
                {
                    "seed": seed,
                    "role": role,
                    "step": record["step"],
                    "mutations": record["mutations"],
                }
            )
            actual = row["metrics"]
            require(
                record["seconds"] >= prior_seconds and record["mutations"] >= prior_mutations,
                "record order regression",
            )
            prior_seconds, prior_mutations = record["seconds"], record["mutations"]
            if role == "complete":
                require(actual["holes"] == 0, "false complete record")
                require(
                    not seen[role]
                    or actual["cardinality"] < seen[role][-1]["metrics"]["cardinality"],
                    "nonimproving complete record",
                )
                if actual["cardinality"] <= 64:
                    success_records.append(record)
            else:
                require(actual["cardinality"] == 64, "64 label at wrong cardinality")
                require(
                    not seen[role] or actual["holes"] < seen[role][-1]["metrics"]["holes"],
                    "nonimproving64 record",
                )
                if role == "admissible64":
                    require(row["exact64_four_caps_pass"], "false admissible64 label")
            seen[role].append(row)
        require(seen["complete"][0]["metrics"]["cardinality"] == 65, "initial complete baseline")
        require(
            [row["role"] for row in records[:3]] == ["complete", "raw64", "admissible64"],
            "initial roles",
        )
        require(
            all(row["step"] == row["mutations"] == 0 for row in records[:3]),
            "initial mutation counters",
        )
        require(
            records[0]["metrics"] == manifest["initial_complete"]["metrics"],
            "complete initial metrics",
        )
        require(
            records[1]["metrics"] == records[2]["metrics"] == initial["metrics"],
            "partial initial metrics",
        )
        require(
            seen["complete"][0]["sha256"] == manifest["initial_complete"]["sha256"],
            "initial incumbent bytes",
        )
        require(
            seen["raw64"][0]["sha256"] == seen["admissible64"][0]["sha256"] == initial["sha256"],
            "initial partial bytes",
        )
        final_rows = {}
        for role in ("current", "complete", "raw64", "admissible64"):
            path = directory / f"search-final-{role}.txt"
            if terminal[role] is None:
                require(
                    role != "current" and not seen[role] and not path.exists(),
                    "false absent record",
                )
                final_rows[role] = None
                continue
            expected_paths.add(path)
            row = check(path, terminal[role])
            row.update({"seed": seed, "role": "final_" + role})
            final_rows[role] = row
            if role != "current":
                require(row["sha256"] == seen[role][-1]["sha256"], "final best not last record")
        require(set(directory.glob("*.txt")) == expected_paths, "unaccounted saved family")
        success = terminal["current"]["holes"] == 0 and terminal["current"]["cardinality"] <= 64
        require(success == run["success"] == (run["returncode"] == 0), "success/exit mismatch")
        expected_terminal = (
            "cover_found" if success else "finished" if run["returncode"] == 1 else "interrupted"
        )
        require(terminal["event"] == expected_terminal, "terminal classification")
        require(0 <= terminal["seconds"] <= elapsed + 1, "native elapsed mismatch")
        if not success and run["returncode"] == 1:
            require(terminal["seconds"] >= 300, "early unexplained finish")
        counts = terminal["action_counts"]
        require(
            len(counts) == 6 and all(type(value) is int and value >= 0 for value in counts),
            "actions",
        )
        require(sum(counts) == terminal["iterations"], "iteration total")
        expected_mutations = counts[1] + counts[2] + counts[3] + 2 * counts[4] + 2 * counts[5]
        require(
            expected_mutations - int(success) <= terminal["mutations"] <= expected_mutations,
            "mutation total",
        )
        require(
            counts[3] - int(success) <= terminal["weight_updates"] <= counts[3], "weight updates"
        )
        require(
            terminal["fallbacks"] + terminal["novelties"] <= sum(counts[3:]), "selection totals"
        )
        require(
            terminal["max_cardinality"] == 64 and 62 <= terminal["min_cardinality"] <= 64,
            "cardinality range",
        )
        if success:
            require(
                success_records and run_index == len(runs) - 1, "campaign continued after success"
            )
            first = success_records[0]
            require(
                terminal["mutations"] == first["mutations"]
                and terminal["iterations"] == first["step"] + 1,
                "mutation after first cover",
            )
        else:
            require(not success_records, "successful record ignored")
        if run_index + 1 < len(runs):
            require(not success and run["returncode"] == 1, "unjustified next seed")
        # Recount the first32 explicit move traces without using producer state or score methods.
        ids = {RANK[block] for block in parse((ROOT / initial["path"]).read_text())}
        require(
            [trace["step"] for trace in traces] == list(range(min(32, terminal["iterations"]))),
            "trace steps missing",
        )
        trace_sizes = [64]
        trace_mutations, trace_weight_updates = 0, 0
        trace_weights = {triple: 1 for triple in TRIPLES}
        for trace in traces:
            validate_trace_shape(trace)
            action = trace["action"]
            before = metrics(sorted(ids), cores)
            require(before["holes"] > 0, "trace after a cover")
            require(action in {"add_only", "swap", "double_drop"}, "unexpected live action")
            require((action == "add_only") == (len(ids) < 64), "cardinality move policy")
            target = TRIPLES[trace["target"]]
            require(not any(set(target) <= set(BLOCKS[i]) for i in ids), "covered target")
            if trace["step"] < 4:
                require(trace["fallback"], "fresh age fallback omitted")
            if trace["fallback"]:
                first = next(i for i, block in enumerate(BLOCKS) if set(target) <= set(block))
                require(trace["incoming"] == first, "fallback not first lex carrier")
            for removed in trace["removed"]:
                if removed >= 0:
                    require(removed in ids, "trace removes absent block")
                    ids.remove(removed)
                    trace_mutations += 1
                    trace_sizes.append(len(ids))
            if action in ("add_only", "swap"):
                require(trace["incoming"] not in ids, "trace adds duplicate block")
                ids.add(trace["incoming"])
                trace_mutations += 1
                trace_sizes.append(len(ids))
            actual = metrics(sorted(ids), cores)
            require(actual == trace["metrics"], "trace subset recount mismatch")
            reached = actual["holes"] == 0 and actual["cardinality"] <= 64
            require(
                trace["weights_updated"] == (action == "add_only" and not reached),
                "trace weight policy",
            )
            if trace["weights_updated"]:
                counts = Counter(t for i in ids for t in itertools.combinations(BLOCKS[i], 3))
                for triple in TRIPLES:
                    if counts[triple] == 0:
                        trace_weights[triple] += 1
                trace_weight_updates += 1
        require(terminal["min_cardinality"] <= min(trace_sizes), "reported minimum above replay")
        require(terminal["max_cardinality"] == max(trace_sizes) == 64, "reported maximum differs")
        require(terminal["mutations"] >= trace_mutations, "terminal mutations below replay")
        require(
            terminal["weight_updates"] >= trace_weight_updates,
            "terminal weight updates below replay",
        )
        require(
            terminal["max_weight"] >= max(trace_weights.values()), "terminal weights below replay"
        )
        if terminal["iterations"] <= 32:
            require(terminal["min_cardinality"] == min(trace_sizes), "complete replay minimum")
            require(terminal["mutations"] == trace_mutations, "complete replay mutations")
            require(terminal["weight_updates"] == trace_weight_updates, "complete replay updates")
            require(
                terminal["max_weight"] == max(trace_weights.values()), "complete replay weights"
            )
        summaries.append(
            {
                "seed": seed,
                "returncode": run["returncode"],
                "success": success,
                "elapsed_seconds": elapsed,
                "record_count": len(records),
                "trace_moves_recounted": len(traces),
                "initial_zero_mutation_records_checked": True,
                "initial_partial_sha256": initial["sha256"],
                "trace_live_minimum": min(trace_sizes),
                "trace_live_maximum": max(trace_sizes),
                "final_rows": final_rows,
                "terminal": terminal,
            }
        )
    require(
        len(runs) == 2 or runs[-1]["success"] or runs[-1]["returncode"] != 1,
        "campaign result is not terminal",
    )
    original = parse((ROOT / manifest["incumbent_path"]).read_text())
    invalid = {
        "duplicate": original[:-1] + [original[0]],
        "bad_label": [(0, 2, 3, 4, 6)] + original[1:],
    }
    rejected = []
    for name, blocks in invalid.items():
        try:
            parse("\n".join(" ".join(map(str, block)) for block in blocks))
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError("damaged runtime control accepted")
    damaged = [(1, 2, 3, 4, 5)] + original[1:]
    require(
        not verify_cover(damaged, 16, 5, 3)["valid"]
        and not standalone.verify_cover(damaged, 16, 5, 3, 65)["valid"],
        "damaged cover accepted",
    )
    receipt = {
        "passed": True,
        "optimizer_launches": 0,
        "source_sha256": sha(__file__),
        "pre_run_gate_sha256": GATE_SHA,
        "producer_manifest_sha256": MANIFEST_SHA,
        "producer_result_sha256": sha(result_path),
        "runs": summaries,
        "saved_family_count": len(checked),
        "distinct_families": len({row["sha256"] for row in checked}),
        "all_saved_families": checked,
        "malformed_controls_rejected": rejected,
        "malformed_trace_controls_rejected": trace_controls_rejected,
        "damaged_full_cover_rejected_by_both": True,
        "first_cover_stop_policy_checked": True,
        "two_seed_sequential_policy_checked": True,
        "scope": "Every saved/final family and first32 traces recounted; no new search",
        "limitations": "Bounded heuristic outcomes do not establish a global lower bound.",
        "timing_context": (
            "A separate four-worker soft H12 CP run overlapped; "
            "timings are not a controlled performance comparison."
        ),
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    require(sha(HERE / "gate.json") == GATE_SHA, "gate mutated")
    print(
        json.dumps(
            {
                "passed": True,
                "saved_families": len(checked),
                "runs": len(runs),
                "postcheck_sha256": sha(output),
            }
        )
    )


if __name__ == "__main__":
    main()
