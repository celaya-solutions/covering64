# Document:    Independent Native Variable Cardinality Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      f5f24745ae69f1e7fa0b40bc93b0d7700285fa9a8e3d246bf054939f2db67d99
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
PRODUCER = HERE.parent / "native-variable-cardinality"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(1, 17), 3))
RANK = {block: index for index, block in enumerate(BLOCKS)}
GATE_SHA = "300677f074664d001cba3c63cb156e13e2648020cfa28908560b5f761ad3c6ff"
MANIFEST_SHA = "f79075467ba41b46e53491c032044a23fe9766c680309055c1ff5d0697ec354b"


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
        require(run["validation_passed"], "producer validation failure")
        require(run["returncode"] in (0, 1, 2) and not run["watchdog"]["fired"], "exit/watchdog")
        elapsed = run["elapsed_seconds"]
        require(0 <= elapsed <= 140.5, "wall budget outside watchdog and grace")
        start = datetime.fromisoformat(run["started_utc"]).timestamp()
        if previous_end is not None:
            require(start >= previous_end - 0.1, "overlapping run times")
        previous_end = start + elapsed
        command = run["command"]
        require(
            command
            == [
                str(ROOT / manifest["binary_path"]),
                str(ROOT / manifest["start_path"]),
                str(seed),
                "120",
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
        require(events[0] == {"event": "start", "seed": seed, "budget": 120}, "start event")
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
            require(terminal["seconds"] >= 120, "early unexplained finish")
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
            terminal["max_cardinality"] == 65 and 0 < terminal["min_cardinality"] <= 64,
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
        ids = {RANK[block] for block in parse((ROOT / manifest["start_path"]).read_text())}
        require(
            [trace["step"] for trace in traces] == list(range(min(32, terminal["iterations"]))),
            "trace steps missing",
        )
        for trace in traces:
            action = trace["action"]
            for removed in trace["removed"]:
                if removed >= 0:
                    require(removed in ids, "trace removes absent block")
                    ids.remove(removed)
            if action in ("add_only", "swap"):
                require(trace["incoming"] not in ids, "trace adds duplicate block")
                ids.add(trace["incoming"])
            require(
                metrics(sorted(ids), cores) == trace["metrics"], "trace subset recount mismatch"
            )
        summaries.append(
            {
                "seed": seed,
                "returncode": run["returncode"],
                "success": success,
                "elapsed_seconds": elapsed,
                "record_count": len(records),
                "trace_moves_recounted": len(traces),
                "final_rows": final_rows,
                "terminal": terminal,
            }
        )
    require(
        len(runs) == 2 or runs[-1]["success"] or runs[-1]["returncode"] != 1,
        "campaign result is not terminal",
    )
    original = parse((ROOT / manifest["start_path"]).read_text())
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
        "damaged_full_cover_rejected_by_both": True,
        "first_cover_stop_policy_checked": True,
        "two_seed_sequential_policy_checked": True,
        "scope": "Every saved/final family and first32 traces recounted; no new search",
        "limitations": "No <=64 cover saved; failed bounded searches prove no lower bound.",
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
