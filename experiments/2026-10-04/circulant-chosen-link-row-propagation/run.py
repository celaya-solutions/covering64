# Document:    Bounded Row Propagation for Surviving Chosen Circulant Links
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      13513bb172b118aadf5500836ebddde9e1c20ad4621f5a4672f79f869d3fd98b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Prepare and benchmark exact forcing traces; no full pass or optimizer."""

from __future__ import annotations

import gzip
import importlib.util
import io
import json
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ONE_PASS = HERE.parent / "circulant-chosen-link-support-screen"
FULL = HERE.parent / "circulant-chosen-link-support-full"
CATALOG = HERE.parent / "circulant-chosen-link-catalog"
RAW = ROOT / "experiments/scratch/circulant-chosen-link-row-propagation-v1.0.0"
FULL_RESULT_SHA = "aabd7d06c2a2b297b69086676e12a68ccfd6a532dcf5ea3aeca53d42fde958e3"
SURVIVORS_SHA = "8914b935b63ccea864ab51f5d0837efcb0eed093b4bbdfc577ecdb2fc0ac2a0c"
ARITHMETIC_SHA = "5007aa2b9b38d980ecb4283aeb23c0873d770ee1e9036d3af0bab1045887428d"
COUNT = 10228
BENCHMARK_COUNT = 1000
SECONDS = 10.0


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def dump(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def load_inputs():
    require(sha(FULL / "result.json") == FULL_RESULT_SHA, "frozen terminal full-pass result")
    result = json.loads((FULL / "result.json").read_text())
    require(result["complete"] and result["completed_cases"] == 195296, "complete first pass")
    require(result["outcomes"]["survives_single_pass"] == COUNT, "survivor census")
    survivor_path = ROOT / result["survivor_records"]
    require(
        sha(survivor_path) == result["survivor_records_sha256"] == SURVIVORS_SHA,
        "survivor file pin",
    )
    with gzip.open(survivor_path, "rt") as handle:
        survivors = [json.loads(line) for line in handle]
    require(len(survivors) == COUNT, "complete survivor list")
    ordinals = [row["pair_ordinal"] for row in survivors]
    require(ordinals == sorted(set(ordinals)), "ordered distinct survivor ordinals")
    require(sha(ONE_PASS / "run.py") == ARITHMETIC_SHA, "frozen domain loader source")
    arithmetic = module(ONE_PASS / "run.py", "frozen_domain_loader")
    data = arithmetic.load_frozen()
    for row in survivors:
        require(
            arithmetic.locate(data, row["pair_ordinal"]) == (row["partial_id"], row["profile_id"]),
            "every survivor identity",
        )
    return arithmetic, data, survivors, survivor_path


def prepare():
    require(not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh preparation")
    _, data, survivors, survivor_path = load_inputs()
    sample = [(index * COUNT) // BENCHMARK_COUNT for index in range(BENCHMARK_COUNT)]
    require(len(set(sample)) == BENCHMARK_COUNT, "fixed sample")
    dependencies = {
        str((FULL / "result.json").relative_to(ROOT)): FULL_RESULT_SHA,
        str(survivor_path.relative_to(ROOT)): SURVIVORS_SHA,
        str((ONE_PASS / "run.py").relative_to(ROOT)): ARITHMETIC_SHA,
        str((ONE_PASS / "manifest.json").relative_to(ROOT)): sha(ONE_PASS / "manifest.json"),
        str((CATALOG / "files.json").relative_to(ROOT)): sha(CATALOG / "files.json"),
        **data["manifest"]["inputs"],
    }
    for path in (
        ROOT / "src/covering64/core.py",
        ROOT / "scripts/check_cover.py",
        HERE / "README.md",
    ):
        dependencies[str(path.relative_to(ROOT))] = sha(path)
    dump(
        HERE / "manifest.json",
        {
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_sha256": sha(__file__),
            "dependencies": dependencies,
            "input_survivor_count": COUNT,
            "benchmark_count": BENCHMARK_COUNT,
            "benchmark_survivor_indices": sample,
            "benchmark_pair_ordinals": [survivors[index]["pair_ordinal"] for index in sample],
            "wall_budget_seconds": SECONDS,
            "stop_starting_cases_at_seconds": SECONDS - 0.25,
            "initial_variables_per_case": 3003,
            "exact_rows_per_case": 456,
            "row_order": "455 lexicographic triples on2..16, then exact cardinality44",
            "operation": (
                "Repeated exact row-bound forcing to contradiction or a complete fixed point."
            ),
            "full_pass_authorized": False,
            "optimizer_calls": 0,
            "failed_literal_probing": False,
            "scope": (
                "Only the frozen10228 single-pass survivors "
                "of the chosen four-witness image catalog."
            ),
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "propagation_launched": False,
            }
        )
    )


def pins():
    manifest = json.loads((HERE / "manifest.json").read_text())
    require(sha(__file__) == manifest["source_sha256"], "frozen propagation source")
    for path, expected in manifest["dependencies"].items():
        require(sha(ROOT / path) == expected, "frozen propagation dependency")
    require(
        manifest["input_survivor_count"] == COUNT
        and manifest["benchmark_count"] == BENCHMARK_COUNT,
        "fixed counts",
    )
    return manifest


def propagate(arithmetic, data, record, deadline):
    profile = data["profile_masks"][record["profile_id"]]
    covered = data["partial_masks"][record["partial_id"]]
    demands = [1 + ((profile >> row) & 1) - ((covered >> row) & 1) for row in range(455)] + [44]
    require(min(demands) >= 0 and sum(demands[:455]) == 440, "exact residual demands")
    masks = [*data["row_masks"], arithmetic.ALL]
    selected = removed = 0
    steps = []
    passes = 0
    row_visits = 0
    final = None
    outcome = None
    while outcome is None:
        passes += 1
        changed = False
        for row, (mask, demand) in enumerate(zip(masks, demands)):
            if time.monotonic() >= deadline:
                outcome = "incomplete_wall_budget"
                final = {"pass": passes, "next_row": row}
                break
            row_visits += 1
            present = mask & selected
            free = mask & ~(selected | removed)
            count = present.bit_count()
            available = free.bit_count()
            if count > demand or count + available < demand:
                outcome = "contradiction"
                final = {
                    "row": row,
                    "demand": demand,
                    "selected_count": count,
                    "free_count": available,
                    "selected_global_ids": arithmetic.global_ids(present),
                    "free_global_ids": arithmetic.global_ids(free),
                }
                break
            if free and count == demand:
                steps.append({"row": row, "value": 0, "global_ids": arithmetic.global_ids(free)})
                removed |= free
                changed = True
            elif free and count + available == demand:
                steps.append({"row": row, "value": 1, "global_ids": arithmetic.global_ids(free)})
                selected |= free
                changed = True
            require(not selected & removed, "consistent row assignments")
        if outcome is None and not changed:
            if selected.bit_count() == 44:
                require(
                    all(
                        (mask & selected).bit_count() == demand
                        for mask, demand in zip(masks, demands)
                    ),
                    "complete exact solution",
                )
                outcome = "complete_cover_candidate"
            else:
                outcome = "survives_row_propagation"
    return {
        **record,
        "outcome": outcome,
        "initial_domain_count": 3003,
        "exact_row_count": 456,
        "passes": passes,
        "row_visits": row_visits,
        "trace": steps,
        "final_evidence": final,
        "selected_global_ids": arithmetic.global_ids(selected),
        "selected_count": selected.bit_count(),
        "removed_count": removed.bit_count(),
        "selected_mask_sha256": sha256(selected.to_bytes(376, "little")).hexdigest(),
        "removed_mask_sha256": sha256(removed.to_bytes(376, "little")).hexdigest(),
    }


def verify_cover_candidate(arithmetic, record, destination):
    catalog = json.loads((CATALOG / "partial-catalog.json").read_text())
    fixed = catalog[record["partial_id"]]["global_block_ids"]
    all_ids = sorted([*fixed, *record["selected_global_ids"]])
    require(len(all_ids) == len(set(all_ids)) == 64, "complete candidate cardinality")
    blocks = [arithmetic.BLOCKS[index] for index in all_ids]
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    standalone = module(ROOT / "scripts/check_cover.py", "full_cover_checker")
    package = verify_cover(blocks)
    independent = standalone.verify_cover(blocks, expected_blocks=64)
    require(package["valid"] and independent["valid"], "both full cover verifiers")
    require(package["canonical_sha256"] == independent["canonical_sha256"], "full cover hashes")
    destination.mkdir()
    witness = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
    (destination / "witness.txt").write_text(witness)
    dump(destination / "package-verifier.json", package)
    dump(destination / "standalone-verifier.json", independent)
    return {
        "witness": str((destination / "witness.txt").relative_to(ROOT)),
        "sha256": sha(destination / "witness.txt"),
    }


def benchmark():
    started = time.monotonic()
    manifest = pins()
    require(
        not (HERE / "benchmark.json").exists() and not RAW.exists(), "one fresh bounded benchmark"
    )
    arithmetic, data, survivors, _ = load_inputs()
    RAW.mkdir(parents=True)
    output_path = RAW / "benchmark-traces.jsonl.gz"
    sample = manifest["benchmark_survivor_indices"]
    outcomes = Counter()
    completed = []
    interrupted = None
    total_steps = row_visits = 0
    candidates = []
    loop_started = time.monotonic()
    with (
        output_path.open("xb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed,
        io.TextIOWrapper(compressed) as output,
    ):
        for position, survivor_index in enumerate(sample):
            if time.monotonic() - started >= SECONDS - 0.25:
                break
            record = propagate(
                arithmetic, data, survivors[survivor_index], started + SECONDS - 0.25
            )
            record["survivor_index"] = survivor_index
            record["benchmark_position"] = position
            if record["outcome"] == "complete_cover_candidate":
                record["verified_cover"] = verify_cover_candidate(
                    arithmetic, record, RAW / f"cover-{record['pair_ordinal']}"
                )
                candidates.append(record["verified_cover"])
            output.write(json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n")
            total_steps += len(record["trace"])
            row_visits += record["row_visits"]
            if record["outcome"] == "incomplete_wall_budget":
                interrupted = {
                    "benchmark_position": position,
                    "survivor_index": survivor_index,
                    "pair_ordinal": record["pair_ordinal"],
                    "trace_prefix_saved": True,
                }
                break
            completed.append(record["pair_ordinal"])
            outcomes[record["outcome"]] += 1
    elapsed = time.monotonic() - started
    loop_elapsed = time.monotonic() - loop_started
    result = {
        "manifest_sha256": sha(HERE / "manifest.json"),
        "source_sha256": sha(__file__),
        "complete_benchmark": len(completed) == BENCHMARK_COUNT,
        "requested_cases": BENCHMARK_COUNT,
        "completed_cases": len(completed),
        "completed_pair_ordinals": completed,
        "next_benchmark_position": len(completed),
        "interrupted_case": interrupted,
        "outcomes": dict(outcomes),
        "total_forcing_steps": total_steps,
        "row_visits": row_visits,
        "elapsed_seconds_including_load_and_output": elapsed,
        "case_loop_seconds_including_output": loop_elapsed,
        "wall_budget_seconds": SECONDS,
        "wall_budget_respected": elapsed <= SECONDS,
        "estimated_full_10228_case_seconds": COUNT * loop_elapsed / len(completed)
        if completed
        else None,
        "estimate_is_not_a_guarantee": True,
        "trace_file": str(output_path.relative_to(ROOT)),
        "trace_file_sha256": sha(output_path),
        "verified_full_cover_candidates": candidates,
        "full_iterative_pass_launched": False,
        "optimizer_calls": 0,
        "scope": manifest["scope"],
    }
    dump(HERE / "benchmark.json", result)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "completed_cases",
                    "outcomes",
                    "total_forcing_steps",
                    "elapsed_seconds_including_load_and_output",
                    "estimated_full_10228_case_seconds",
                    "full_iterative_pass_launched",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["benchmark"]:
        benchmark()
    else:
        raise SystemExit("Usage: run.py prepare|benchmark; no full-pass entrypoint")
