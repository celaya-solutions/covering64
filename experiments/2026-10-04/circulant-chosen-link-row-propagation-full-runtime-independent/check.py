# Document:    Independent Full Row Propagation Runtime Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      2caaebc32e05cc047a3086f383cec78fc3bb41aa5ec5b1370b9e710e222050b9
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Stream saved committed traces through a pinned independent set-based checker."""

import argparse
import copy
import gzip
import importlib.util
import io
import json
import sys
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
PRODUCER = BASE / "circulant-chosen-link-row-propagation-full"
GATE = BASE / "circulant-chosen-link-row-propagation-full-independent"
ENGINE = BASE / "circulant-row-propagation-independent/check.py"
RAW = ROOT / "experiments/scratch/circulant-chosen-link-row-propagation-full-v1.0.0"
CAT = BASE / "circulant-chosen-link-catalog"
PINS = {
    "runner": (
        PRODUCER / "run.py",
        "f2f92fee793b23803ee4dc71bd536f345d0e1d3a154735cf889b607b55184173",
    ),
    "manifest": (
        PRODUCER / "manifest.json",
        "b7110cbdd8db86b27d1c302267bc843f50aa0b40ae240b8862ebe4f2b5679ec2",
    ),
    "gate": (
        GATE / "gate.json",
        "a233e41f4162ebc52cb578f538916f718b7da12c9942e66bef778d083a543145",
    ),
    "gate_review": (
        GATE / "review.json",
        "a06710917ac8c6afd02093c6b1e1e382cfd9119ab78df255ee202c81f5315735",
    ),
    "engine": (ENGINE, "198653227c4a1ef70f85d56f8f1e5a2c26efc68f6cf925a1dad7bb3837822d11"),
    "benchmark_audit": (
        BASE / "circulant-row-propagation-independent/benchmark-audit.json",
        "dcd303e56b7474a6155ac644603c3b3baa55adb0b2936ba624848d826510360a",
    ),
}
SURVIVOR_FIELDS = (
    "survivor_index",
    "pair_ordinal",
    "partial_id",
    "profile_id",
    "selected_count",
    "removed_count",
    "selected_mask_sha256",
    "removed_mask_sha256",
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    hasher = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    require(len(payload.encode()) < 1_000_000, "small receipt")
    path.write_text(payload)


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def committed_records(path, offset):
    require(type(offset) is int and 0 <= offset <= path.stat().st_size, "strict committed offset")
    with path.open("rb") as raw:
        compressed = raw.read(offset)
    if not compressed:
        return
    with gzip.GzipFile(fileobj=io.BytesIO(compressed), mode="rb") as stream:
        for line in stream:
            require(line.endswith(b"\n"), "complete committed JSON line")
            yield json.loads(line)


def identity(record, index, survivors, pair_order):
    require(
        type(record["survivor_index"]) is int and record["survivor_index"] == index,
        "ordered committed input index",
    )
    original = survivors[index]
    for key, value in original.items():
        require(record.get(key) == value, "complete input record binding: " + key)
    for key in ("pair_ordinal", "partial_id", "profile_id"):
        require(type(record[key]) is int, "strict identity integer")
    ordinal = record["pair_ordinal"]
    require(0 <= ordinal < len(pair_order), "pair ordinal bounds")
    require(
        (record["partial_id"], record["profile_id"]) == pair_order[ordinal], "catalog pair binding"
    )


def visit_counts(record):
    """Recover pass boundaries from increasing row order and saved force steps."""
    passed, previous = 1, -1
    for step in record["trace"]:
        row = step["row"]
        if row <= previous:
            passed += 1
        previous = row
    outcome = record["outcome"]
    if outcome in ("survives_row_propagation", "complete_cover_candidate"):
        if record["trace"]:
            passed += 1
        visits = passed * 456
    elif outcome == "contradiction":
        row = record["final_evidence"]["row"]
        if row <= previous:
            passed += 1
        visits = (passed - 1) * 456 + row + 1
    elif outcome == "incomplete_wall_budget":
        row = record["final_evidence"]["next_row"]
        require(type(row) is int and 0 <= row < 456, "interrupted next row")
        if row <= previous:
            passed += 1
        visits = (passed - 1) * 456 + row
        require(record["final_evidence"]["pass"] == passed, "interrupted pass")
    else:
        raise AssertionError("unknown trace outcome")
    require(type(record["passes"]) is int and record["passes"] == passed, "saved pass count")
    require(
        type(record["row_visits"]) is int and record["row_visits"] == visits, "saved row visits"
    )


def special_trace(record, context, engine):
    """Replay valid deductions for an interrupted trace or complete candidate."""
    rows, profiles, partials = context
    excess, fixed = profiles[record["profile_id"]], partials[record["partial_id"]]
    demands = [1 + (triple in excess) - fixed[triple] for triple in engine.TRIPLES] + [44]
    require(min(demands) >= 0 and sum(demands[:-1]) == 440, "special trace demands")
    require(
        record["initial_domain_count"] == 3003 and record["exact_row_count"] == 456,
        "special trace dimensions",
    )
    selected, removed = set(), set()
    for step in record["trace"]:
        row, value, ids = step["row"], step["value"], step["global_ids"]
        require(type(row) is int and 0 <= row < 456, "strict row")
        require(type(value) is int and value in (0, 1), "strict forced value")
        require(all(type(v) is int for v in ids) and ids == sorted(set(ids)), "strict forced IDs")
        free = rows[row] - selected - removed
        present = len(rows[row] & selected)
        require(free and ids == sorted(free), "complete forced free set")
        require(present <= demands[row] <= present + len(free), "noncontradictory forcing row")
        require(
            (present == demands[row]) if value == 0 else (present + len(free) == demands[row]),
            "exact force bound",
        )
        (removed if value == 0 else selected).update(free)
        require(not selected & removed and selected | removed <= engine.DOMAIN, "consistent domain")
    require(record["selected_global_ids"] == sorted(selected), "selected vector")
    require(
        record["selected_count"] == len(selected) and record["removed_count"] == len(removed),
        "special state counts",
    )
    require(record["selected_mask_sha256"] == engine.bitmap_hash(selected), "selected state hash")
    require(record["removed_mask_sha256"] == engine.bitmap_hash(removed), "removed state hash")
    if record["outcome"] == "complete_cover_candidate":
        require(
            record["final_evidence"] is None and len(selected) == 44, "complete candidate count"
        )
        require(
            all(len(row & selected) == demand for row, demand in zip(rows, demands)),
            "complete candidate exact equations",
        )
    else:
        require(record["outcome"] == "incomplete_wall_budget", "special outcome")
    return selected


def candidate_check(record, selected, engine):
    partials = read(CAT / "partial-catalog.json")
    ids = sorted([*partials[record["partial_id"]]["global_block_ids"], *selected])
    require(len(ids) == len(set(ids)) == 64, "candidate distinct 64 blocks")
    blocks = [engine.BLOCKS[index] for index in ids]
    canonical = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
    declaration = record["verified_cover"]
    path = ROOT / declaration["witness"]
    require(
        path == RAW / f"cover-{record['pair_ordinal']}" / "witness.txt", "candidate output location"
    )
    require(
        path.read_text() == canonical and digest(path) == declaration["sha256"], "candidate witness"
    )
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    standalone = module(ROOT / "scripts/check_cover.py", "runtime_standalone")
    package = verify_cover(blocks)
    independent = standalone.verify_cover(blocks, expected_blocks=64)
    require(package["valid"] and independent["valid"], "both full-cover verifiers")
    require(package["canonical_sha256"] == independent["canonical_sha256"], "dual candidate hash")
    for filename, receipt in (
        ("package-verifier.json", package),
        ("standalone-verifier.json", independent),
    ):
        require(
            read(path.parent / filename) == json.loads(json.dumps(receipt)),
            "saved candidate receipt",
        )
    return {"pair_ordinal": record["pair_ordinal"], "canonical_sha256": package["canonical_sha256"]}


def damage_controls(samples, context, engine, survivors, pair_order):
    rejected = []
    for name in (
        "flipped_value",
        "omitted_literal",
        "wrong_row",
        "bool_value",
        "final_demand",
        "removed_hash",
        "survivor_omitted_step",
        "wrong_input_index",
        "wrong_profile",
        "wrong_passes",
        "wrong_row_visits",
    ):
        key = "survives_row_propagation" if name == "survivor_omitted_step" else "contradiction"
        if key not in samples:
            continue
        damaged = copy.deepcopy(samples[key])
        if name == "flipped_value":
            damaged["trace"][0]["value"] ^= 1
        elif name == "omitted_literal":
            damaged["trace"][0]["global_ids"].pop()
        elif name == "wrong_row":
            damaged["trace"][0]["row"] = 455
        elif name == "bool_value":
            damaged["trace"][0]["value"] = False
        elif name == "final_demand":
            damaged["final_evidence"]["demand"] += 1
        elif name == "removed_hash":
            damaged["removed_mask_sha256"] = "0" * 64
        elif name == "survivor_omitted_step":
            damaged["trace"].pop()
        elif name == "wrong_input_index":
            damaged["survivor_index"] += 1
        elif name == "wrong_profile":
            damaged["profile_id"] += 1
        elif name == "wrong_passes":
            damaged["passes"] += 1
        else:
            damaged["row_visits"] += 1
        try:
            identity(damaged, samples[key]["survivor_index"], survivors, pair_order)
            engine.check(damaged, context)
            visit_counts(damaged)
        except (AssertionError, KeyError, IndexError):
            rejected.append(name)
        else:
            raise AssertionError("accepted damaged record: " + name)
    return rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-sha256", required=True)
    parser.add_argument("--execution-sha256", required=True)
    args = parser.parse_args()
    for path, expected in PINS.values():
        require(digest(path) == expected, "frozen independent pin: " + str(path))
    require(digest(PRODUCER / "result.json") == args.result_sha256, "terminal result pin")
    require(digest(PRODUCER / "execution.json") == args.execution_sha256, "supervisor result pin")
    manifest, result, execution = [
        read(PRODUCER / name) for name in ("manifest.json", "result.json", "execution.json")
    ]
    for path, expected in manifest["dependencies"].items():
        require(digest(ROOT / path) == expected, "manifest dependency: " + path)
    launch = read(PRODUCER / "launch.json")
    root_launch = read(PRODUCER / "root-review-launch.json")
    require(launch["manifest_sha256"] == PINS["manifest"][1], "worker launch binding")
    require(root_launch["manifest_sha256"] == PINS["manifest"][1], "root launch manifest")
    require(root_launch["runner_sha256"] == PINS["runner"][1], "root launch runner")
    require(root_launch["gate_sha256"] == PINS["gate"][1], "root launch gate")
    require(
        root_launch["maximum_launches"] == 1 and root_launch["dependency_pins_checked"] == 22,
        "root launch scope",
    )
    cursor = read(RAW / "cursor.json")
    count = cursor["next_survivor_index"]
    require(type(count) is int and 0 <= count <= 10228, "bounded completed prefix")
    require(cursor["completed_prefix"] == [0, count], "cursor half-open prefix")
    require(execution["cursor"] == cursor, "supervisor cursor binding")
    require(
        execution["cursor_file_sha256"] == digest(RAW / "cursor.json"), "supervisor cursor hash"
    )
    require(execution["result_present"] is True, "terminal result present")
    require(execution["result_sha256"] == args.result_sha256, "supervisor terminal hash")
    require(execution["manifest_sha256"] == PINS["manifest"][1], "supervisor manifest")
    require(execution["retry_or_automatic_resume"] is False, "no retry or resume")
    require(
        execution["watchdog_seconds"] == 50 and execution["grace_seconds"] == 5, "watchdog budgets"
    )
    require(type(execution["returncode"]) is int, "child return code")
    for label in ("stdout", "stderr"):
        require(execution[label + "_sha256"] == digest(RAW / (label + ".log")), "process log hash")
    require(all(result[k] == value for k, value in cursor.items()), "worker cursor binding")
    require(result["manifest_sha256"] == PINS["manifest"][1], "terminal manifest")
    require(result["source_sha256"] == PINS["runner"][1], "terminal runner")
    require(
        result["propagator_source_sha256"] == manifest["benchmark_source_sha256"],
        "terminal propagator",
    )
    require(result["complete"] == (count == 10228), "complete only for all inputs")
    require(
        result["requested_cases"] == 10228 and result["completed_cases"] == count, "terminal counts"
    )
    require(
        result["stop_reason"] == ("complete" if count == 10228 else "cooperative_wall_budget"),
        "terminal stop reason",
    )
    require(
        result["wall_budget_seconds"] == 45 and result["full_iterative_passes"] == 1,
        "single cooperative pass",
    )
    require(
        result["optimizer_calls"] == 0 and result["scope"] == manifest["scope"], "terminal scope"
    )
    elapsed = result["elapsed_seconds_including_load_output_and_hashes"]
    require(
        elapsed >= 0 and result["wall_budget_respected"] == (elapsed <= 45), "honest worker budget"
    )
    raw_paths = {}
    for path_field, hash_field, expected in (
        ("proof_records", "proof_records_sha256", RAW / "traces.jsonl.gz"),
        ("survivor_records_path", "survivor_records_sha256", RAW / "survivors.jsonl.gz"),
        ("cursor_file", "cursor_file_sha256", RAW / "cursor.json"),
    ):
        require(ROOT / result[path_field] == expected, "saved output path")
        require(digest(expected) == result[hash_field], "saved raw output hash")
        raw_paths[str(expected.relative_to(ROOT))] = digest(expected)
    previous = read(BASE / "circulant-chosen-link-support-full/result.json")
    input_path = ROOT / previous["survivor_records"]
    require(digest(input_path) == previous["survivor_records_sha256"], "all input survivors hash")
    with gzip.open(input_path, "rt") as stream:
        survivors = [json.loads(line) for line in stream]
    require(len(survivors) == 10228, "input survivor count")
    ordinals = [row["pair_ordinal"] for row in survivors]
    require(ordinals == sorted(set(ordinals)), "ascending distinct input ordinals")
    fibers = read(CAT / "link-fibers.json")
    pair_order = [
        (p, q)
        for fiber in fibers
        for p in range(*fiber["partial_id_range_half_open"])
        for q in fiber["profile_ids"]
    ]
    require(len(pair_order) == 195296, "full catalog pair order")
    for original in survivors:
        require(
            pair_order[original["pair_ordinal"]]
            == (original["partial_id"], original["profile_id"]),
            "all input identities bound",
        )
    engine = module(ENGINE, "pinned_independent_row_checker")
    context = engine.context()
    outcomes, steps, visits, records = Counter(), 0, 0, 0
    residuals, candidates, samples, interrupted = [], [], {}, None
    identity_hash = sha256()
    for index, record in enumerate(
        committed_records(RAW / "traces.jsonl.gz", cursor["trace_committed_bytes"])
    ):
        require(index < len(survivors), "no extra trace input")
        identity(record, index, survivors, pair_order)
        outcome = record["outcome"]
        if outcome in ("contradiction", "survives_row_propagation"):
            engine.check(record, context)
        else:
            selected = special_trace(record, context, engine)
            if outcome == "complete_cover_candidate":
                candidates.append(candidate_check(record, selected, engine))
        visit_counts(record)
        if outcome == "incomplete_wall_budget":
            require(index == count and interrupted is None, "one final interrupted input")
            interrupted = {
                "survivor_index": index,
                "pair_ordinal": record["pair_ordinal"],
                "trace_prefix_saved": True,
                "next_row": record["final_evidence"]["next_row"],
                "pass": record["final_evidence"]["pass"],
            }
        else:
            require(index < count, "completed record within cursor")
            outcomes[outcome] += 1
        if outcome == "survives_row_propagation":
            residuals.append({key: record[key] for key in SURVIVOR_FIELDS})
        if outcome not in samples and outcome in ("contradiction", "survives_row_propagation"):
            samples[outcome] = record
        steps += len(record["trace"])
        visits += record["row_visits"]
        records += 1
        identity_hash.update(
            json.dumps(
                [
                    index,
                    record["pair_ordinal"],
                    record["partial_id"],
                    record["profile_id"],
                    outcome,
                ],
                separators=(",", ":"),
            ).encode()
            + b"\n"
        )
    require(
        records == cursor["trace_records"] == count + (interrupted is not None), "trace accounting"
    )
    require(interrupted == cursor["interrupted_case"], "interrupted cursor accounting")
    require(
        dict(outcomes) == cursor["outcomes"] and sum(outcomes.values()) == count,
        "outcome accounting",
    )
    require(
        steps == cursor["total_forcing_steps"] and visits == cursor["row_visits"], "trace counters"
    )
    saved_residuals = list(
        committed_records(RAW / "survivors.jsonl.gz", cursor["survivor_committed_bytes"])
    )
    require(
        saved_residuals == residuals and len(residuals) == cursor["survivor_records"],
        "exact residual records",
    )
    require(len(candidates) == len(cursor["verified_full_cover_candidates"]), "candidate census")
    if execution["returncode"] == 0 and not execution["watchdog_fired"]:
        require((RAW / "stderr.log").read_bytes() == b"", "clean normal worker stderr")
        stdout = json.loads((RAW / "stdout.log").read_text())
        require(
            stdout == {key: result[key] for key in ("complete", "completed_cases", "outcomes")},
            "normal stdout terminal summary",
        )
    damage = damage_controls(samples, context, engine, survivors, pair_order)
    for path in (
        RAW / "stdout.log",
        RAW / "stderr.log",
        PRODUCER / "launch.json",
        PRODUCER / "root-review-launch.json",
    ):
        raw_paths[str(path.relative_to(ROOT))] = digest(path)
    save(HERE / "raw-files.json", raw_paths)
    receipt = {
        "passed": True,
        "checker_sha256": digest(Path(__file__)),
        "independent_engine_sha256": PINS["engine"][1],
        "gate_sha256": PINS["gate"][1],
        "manifest_sha256": PINS["manifest"][1],
        "runner_sha256": PINS["runner"][1],
        "result_sha256": args.result_sha256,
        "execution_sha256": args.execution_sha256,
        "dependency_pins_checked": len(manifest["dependencies"]),
        "complete": result["complete"],
        "completed_cases": count,
        "trace_records": records,
        "outcomes": dict(outcomes),
        "force_steps_replayed": steps,
        "row_visits_checked": visits,
        "input_cases_bound": len(survivors),
        "catalog_pair_order_size": len(pair_order),
        "ordered_trace_identities_sha256": identity_hash.hexdigest(),
        "interrupted_case": interrupted,
        "verified_candidates": candidates,
        "committed_trace_bytes": cursor["trace_committed_bytes"],
        "committed_survivor_bytes": cursor["survivor_committed_bytes"],
        "uncertified_trace_tail_bytes": (RAW / "traces.jsonl.gz").stat().st_size
        - cursor["trace_committed_bytes"],
        "uncertified_survivor_tail_bytes": (RAW / "survivors.jsonl.gz").stat().st_size
        - cursor["survivor_committed_bytes"],
        "worker_elapsed_seconds": elapsed,
        "cooperative_budget_respected": result["wall_budget_respected"],
        "supervisor_elapsed_seconds": execution["elapsed_seconds"],
        "watchdog_fired": execution["watchdog_fired"],
        "kill_required": execution["kill_required"],
        "returncode": execution["returncode"],
        "damage_controls_rejected": damage,
        "raw_files_sha256": digest(HERE / "raw-files.json"),
        "producer_imports": 0,
        "producer_reruns": 0,
        "optimizer_calls": 0,
        "scope": "Saved committed prefixes for the chosen four-witness image catalog only. "
        "Contradictions exclude those exact profile/partial cases; "
        "fixed points do not prove feasibility.",
    }
    save(HERE / "review.json", receipt)
    print(
        json.dumps(
            {
                "passed": True,
                "complete": result["complete"],
                "completed_cases": count,
                "outcomes": dict(outcomes),
                "force_steps": steps,
                "review_sha256": digest(HERE / "review.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
