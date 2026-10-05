# Document:    Bounded Expanded Affine Catalog Support Benchmark
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      afb7389ee9ab1ab616cf12dea4d4f0dee8dbf0e377e05f1e58f60c3d5911d0c4
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Freeze inputs, then benchmark 1000 new pairs using the unchanged saved screen."""

import gzip
import importlib.util
import io
import json
import struct
import subprocess
import sys
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
CATALOG = BASE / "affine-expanded-catalog"
CORE = BASE / "circulant-chosen-link-support-screen/run.py"
PROFILES = BASE / "circulant-chosen-link-catalog/profiles.json"
RAW = ROOT / "experiments/scratch/affine-expanded-benchmark-v1.0.0"
SECONDS = 10.0
TOTAL = 6739200


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def prepare():
    require(not (HERE / "manifest.json").exists() and not RAW.exists(), "fresh preparation")
    catalog = load(CATALOG / "summary.json")
    plan = load(CATALOG / "benchmark-plan.json")
    original_manifest = CORE.parent / "manifest.json"
    require(sha(CORE) == load(original_manifest)["source_sha256"], "unchanged original screen")
    inputs = {CATALOG / "summary.json", CORE, PROFILES, ROOT / catalog["catalog_path"]}
    inputs.add(original_manifest)
    inputs.update(CATALOG / name for name in catalog["output_hashes"])
    require(len(plan) == 1000 and catalog["implicit_pairs"] == TOTAL, "frozen benchmark domain")
    dump(
        "manifest.json",
        {
            "source_sha256": sha(__file__),
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "input_hashes": {str(p.relative_to(ROOT)): sha(p) for p in sorted(inputs)},
            "core_source": str(CORE.relative_to(ROOT)),
            "core_source_sha256": sha(CORE),
            "core_function": "screen(data, ordinal), with locate and global_ids unchanged",
            "module_constant_overrides": {"TOTAL": {"before": 195296, "after": TOTAL}},
            "other_module_overrides": [],
            "domain_data_fields": [
                "fibers",
                "boundaries",
                "profile_masks",
                "partial_masks",
                "partial_indices",
                "row_masks",
            ],
            "full_pair_order": catalog["pair_order"],
            "pair_count_including_old": TOTAL,
            "new_pair_count": 6543904,
            "old_pair_count_skipped": 195296,
            "benchmark_cases": 1000,
            "benchmark_selection": catalog["benchmark_plan"],
            "selection_contains_old_pairs": False,
            "cooperative_seconds": SECONDS,
            "deadline_scope": (
                "source/input validation, catalog reading, sampled-mask loading, scan"
            ),
            "loading_scope": "read packed catalog; construct partial masks only for sampled IDs",
            "full_catalog_mask_loading_measured": False,
            "residual_rows": 455,
            "sum_selected_blocks": 44,
            "avoiding_point_one_block_domain": 3003,
            "iteration": False,
            "optimizer": False,
            "full_screen_authorized": False,
        },
    )
    print(
        json.dumps(
            {
                "manifest_sha256": sha(HERE / "manifest.json"),
                "source_sha256": sha(__file__),
                "benchmark_cases": 1000,
            },
            sort_keys=True,
        )
    )


def load_sample_data(manifest):
    require(sha(__file__) == manifest["source_sha256"], "runner source pin")
    for relative, expected in manifest["input_hashes"].items():
        require(sha(ROOT / relative) == expected, "frozen input pin")
    spec = importlib.util.spec_from_file_location("frozen_affine_support_core", CORE)
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    require(core.TOTAL == 195296, "original TOTAL")
    core.TOTAL = TOTAL
    catalog = load(CATALOG / "summary.json")
    fibers = load(CATALOG / "link-fibers.json")
    plan = load(CATALOG / "benchmark-plan.json")
    old_ids = set(load(CATALOG / "old-to-new-ids.json"))
    payload = gzip.decompress((ROOT / catalog["catalog_path"]).read_bytes())
    require(sha256(payload).hexdigest() == catalog["catalog_uncompressed_sha256"], "payload pin")
    require(len(payload) == 196992 * 40, "full packed payload size")
    triple_rank = {triple: row for row, triple in enumerate(core.TRIPLES)}
    row_masks = [0] * 455
    require(core.BLOCKS[1365:] == core.AVOIDING and len(core.AVOIDING) == 3003, "full domain")
    for index, block in enumerate(core.AVOIDING):
        for triple in combinations(block, 3):
            row_masks[triple_rank[triple]] |= 1 << index
    require(all(mask.bit_count() == 66 for mask in row_masks), "complete row carriers")
    profile_masks = []
    for profile in load(PROFILES):
        require(profile["profile_id"] == len(profile_masks), "profile index")
        rows = [
            triple_rank[tuple(triple)] for triple in profile["excess_triples"] if 1 not in triple
        ]
        require(len(rows) == len(set(rows)) == 65, "profile outside rows")
        profile_masks.append(sum(1 << row for row in rows))
    partial_masks, partial_indices = {}, {}
    for partial_id in sorted({row["partial_id"] for row in plan}):
        require(partial_id not in old_ids, "no old partial in benchmark")
        ids = struct.unpack_from("<20H", payload, partial_id * 40)
        require(
            len(set(ids)) == 20 and ids == tuple(sorted(ids)) and max(ids) < 1365,
            "sample partial global IDs",
        )
        triples = [triple for i in ids for triple in combinations(core.BLOCKS[i][1:], 3)]
        require(len(triples) == len(set(triples)) == 80, "sample outside triples")
        indices = sorted(triple_rank[triple] for triple in triples)
        partial_indices[partial_id] = indices
        partial_masks[partial_id] = sum(1 << row for row in indices)
    data = {
        "fibers": fibers,
        "boundaries": catalog["pair_boundaries"],
        "row_masks": row_masks,
        "profile_masks": profile_masks,
        "partial_masks": partial_masks,
        "partial_indices": partial_indices,
    }
    require(data["boundaries"][-1] == TOTAL, "full pair ordinal domain")
    for index, row in enumerate(plan):
        require(row["sample_index"] == index, "sample sequence")
        require(
            core.locate(data, row["pair_ordinal"]) == (row["partial_id"], row["profile_id"]),
            "sample preserves full pair IDs",
        )
    return core, data, plan


def benchmark():
    started = time.monotonic()
    require(not (HERE / "benchmark.json").exists() and not RAW.exists(), "fresh benchmark")
    manifest = load(HERE / "manifest.json")
    core, data, plan = load_sample_data(manifest)
    loaded = time.monotonic()
    RAW.mkdir(parents=True)
    outcomes, operations = Counter(), Counter()
    per_fiber = {}
    for fiber in data["fibers"]:
        count = len(fiber["profile_ids"])
        per_fiber[fiber["excess_link_id"]] = {
            "class": fiber["class"],
            "sample_cases": 0,
            "screen_seconds": 0.0,
            "new_pair_population": fiber["new_only_partial_count"] * count,
            "outcomes": Counter(),
            "operations": Counter(),
        }
    processed = 0
    with (
        (RAW / "cases.jsonl.gz").open("wb") as raw_cases,
        (RAW / "survivors.jsonl.gz").open("wb") as raw_survivors,
        gzip.GzipFile(fileobj=raw_cases, mode="wb", mtime=0) as compressed_cases,
        gzip.GzipFile(fileobj=raw_survivors, mode="wb", mtime=0) as compressed_survivors,
        io.TextIOWrapper(compressed_cases) as cases,
        io.TextIOWrapper(compressed_survivors) as survivors,
    ):
        for item in plan:
            if time.monotonic() - started >= SECONDS:
                break
            case_started = time.monotonic()
            result = core.screen(data, item["pair_ordinal"])
            case_seconds = time.monotonic() - case_started
            result.update(
                {"sample_index": item["sample_index"], "excess_link_id": item["excess_link_id"]}
            )
            line = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
            cases.write(line)
            if result["outcome"] == "survives_single_pass":
                survivors.write(line)
            outcomes[result["outcome"]] += 1
            operations.update(result["operation_counts"])
            fiber = per_fiber[item["excess_link_id"]]
            fiber["sample_cases"] += 1
            fiber["screen_seconds"] += case_seconds
            fiber["outcomes"][result["outcome"]] += 1
            fiber["operations"].update(result["operation_counts"])
            processed += 1
    elapsed = time.monotonic() - started
    complete = processed == len(plan)
    result = {
        "status": "complete" if complete else "cooperative_timeout",
        "planned_cases": len(plan),
        "processed_cases": processed,
        "outcomes": dict(outcomes),
        "operation_counts": dict(operations),
        "per_fiber": per_fiber,
        "loading_seconds": loaded - started,
        "screen_function_seconds": sum(row["screen_seconds"] for row in per_fiber.values()),
        "elapsed_seconds": elapsed,
        "cooperative_seconds": SECONDS,
        "loading_scope": manifest["loading_scope"],
        "sample_partial_masks_loaded": len(data["partial_masks"]),
        "full_catalog_mask_loading_measured": False,
        "sample_cursor": {
            "next_sample_index": processed,
            "next_full_pair_ordinal": None if complete else plan[processed]["pair_ordinal"],
        },
        "full_screen_cursor": None,
        "full_screen_started": False,
        "sparse_sample_does_not_cover_an_ordinal_interval": True,
        "source_sha256": sha(__file__),
        "manifest_sha256": sha(HERE / "manifest.json"),
        "raw_files": {str(p.relative_to(ROOT)): sha(p) for p in sorted(RAW.iterdir())},
        "optimizer_calls": 0,
        "cover_search_calls": 0,
    }
    dump("benchmark.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "per_fiber"}, sort_keys=True))


if __name__ == "__main__":
    require(len(sys.argv) == 2 and sys.argv[1] in ("prepare", "benchmark"), "explicit mode")
    (prepare if sys.argv[1] == "prepare" else benchmark)()
