# Document:    Independent Expanded Affine Catalog and Sample Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      992b62771cd120761c9c5b74f6c7711d39e110b8613795c722f6007cc6338a3a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Invert every catalog transport and replay saved sample certificates only."""

import copy
import gzip
import hashlib
import importlib.util
import json
import struct
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
CAT = BASE / "affine-expanded-catalog"
BENCH = BASE / "affine-expanded-benchmark"
OLD = BASE / "circulant-chosen-link-catalog"
UNION = BASE / "affine-extension-semilinear-completeness"
ENGINE = BASE / "circulant-chosen-link-support-runtime-independent/check.py"


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def pin(path, expected):
    require(sha(path) == expected, f"pin: {path.name}")


def verify_family(ids, inverse, quads, allowed):
    require(len(ids) == len(set(ids)) == 20, "distinct twenty IDs")
    require(tuple(sorted(ids)) == ids and all(0 <= i < 1365 for i in ids), "ID domain/order")
    canonical = tuple(sorted(quads[tuple(sorted(inverse[x] for x in BLOCKS[i][1:]))] for i in ids))
    require(canonical in allowed, "inverse family in complete canonical union")
    return canonical


BLOCKS = tuple(combinations(range(1, 17), 5))


def main():
    started = time.monotonic()
    pin(CAT / "summary.json", "e85200dbdf2a392d192973904bc638e4e55184cdc70e1f8cbe3c7643c19ecd6a")
    pin(BENCH / "manifest.json", "6f828f40aef64b2e1c0e8f8e95341354b8e9d6787f8d193d4e185fb56debee06")
    pin(
        BENCH / "benchmark.json", "9ecae116eb215ec6901f1aa1d091385740f2319f0983a16f41a24b5a15353dc4"
    )
    catalog, manifest, receipt = [
        load(p) for p in (CAT / "summary.json", BENCH / "manifest.json", BENCH / "benchmark.json")
    ]
    for path, value in catalog["input_hashes"].items():
        pin(ROOT / path, value)
    for path, value in catalog["output_hashes"].items():
        pin(CAT / path, value)
    for path, value in manifest["input_hashes"].items():
        pin(ROOT / path, value)
    for path, value in receipt["raw_files"].items():
        pin(ROOT / path, value)
    pin(CAT / "build.py", catalog["source_sha256"])
    pin(BENCH / "run.py", manifest["source_sha256"])
    pin(
        CAT / "benchmark-plan.json",
        "c3e39b227aab62900b5530b565c43850c5def512a024a4a38a6f55d349aecdac",
    )
    summary = load(UNION / "summary.json")
    unions = {
        key: set(map(tuple, rows))
        for key, rows in json.loads(
            gzip.decompress((ROOT / summary["raw_union"]).read_bytes())
        ).items()
    }
    payload = gzip.decompress((ROOT / catalog["catalog_path"]).read_bytes())
    require(len(payload) == 7879680, "packed length")
    require(
        hashlib.sha256(payload).hexdigest() == catalog["catalog_uncompressed_sha256"], "payload pin"
    )
    families = list(struct.iter_unpack("<20H", payload))
    require(len(families) == len(set(families)) == 196992, "global distinct families")
    fibers = load(CAT / "link-fibers.json")
    old_fibers = load(OLD / "link-fibers.json")
    old = load(OLD / "partial-catalog.json")
    old_ids = load(CAT / "old-to-new-ids.json")
    require(len(old_ids) == len(set(old_ids)) == 5536, "old bijection count")
    for index, row in enumerate(old):
        require(families[old_ids[index]] == tuple(row["global_block_ids"]), "old exact family")
    quad_rank = {quad: index for index, quad in enumerate(combinations(range(1, 16), 4))}
    profiles = load(OLD / "profiles.json")
    plan, boundary, old_pairs, census, inverses = [], 0, 0, Counter(), []
    for fid, fiber in enumerate(fibers):
        original = old_fibers[fid]
        for key in ("class", "canonical_to_actual", "actual_excess_edges", "profile_ids"):
            require(fiber[key] == original[key], "unchanged independently checked fiber")
        require(fiber["excess_link_id"] == fid, "fiber identity")
        start, end = fiber["partial_id_range_half_open"]
        require((start, end) == (5184 * fid, 5184 * (fid + 1)), "family boundaries")
        rows = families[start:end]
        require(rows == sorted(rows), "family lexicographic order")
        inverse = {actual: index + 1 for index, actual in enumerate(fiber["canonical_to_actual"])}
        require(set(inverse) == set(range(2, 17)), "transport bijection")
        inverses.append(inverse)
        allowed = unions[fiber["class"]]
        recovered = {verify_family(row, inverse, quad_rank, allowed) for row in rows}
        require(recovered == allowed and len(recovered) == 5184, "complete inverse image union")
        excess_edges = set(map(tuple, fiber["actual_excess_edges"]))
        for pid in fiber["profile_ids"]:
            require(
                {tuple(x for x in t if x != 1) for t in profiles[pid]["excess_triples"] if 1 in t}
                == excess_edges,
                "profile link compatibility",
            )
        count = len(fiber["profile_ids"])
        require(
            fiber["pair_ordinal_range_half_open"] == [boundary, boundary + 5184 * count],
            "pair boundaries",
        )
        expect_old = sorted(old_ids[i] for i in range(*original["partial_id_range_half_open"]))
        require(fiber["old_partial_ids_in_expanded_catalog"] == expect_old, "exact old subset")
        new_ids = sorted(set(range(start, end)) - set(expect_old))
        require(len(new_ids) == fiber["new_only_partial_count"], "new family count")
        old_pairs += len(expect_old) * count
        samples = 27 if fid < 12 else 26
        for sample in range(samples):
            index = (2 * sample + 1) * len(new_ids) * count // (2 * samples)
            partial_offset, profile_offset = divmod(index, count)
            partial = new_ids[partial_offset]
            plan.append(
                {
                    "sample_index": len(plan),
                    "excess_link_id": fid,
                    "pair_ordinal": boundary + (partial - start) * count + profile_offset,
                    "partial_id": partial,
                    "profile_id": fiber["profile_ids"][profile_offset],
                }
            )
        boundary += 5184 * count
        census[fiber["class"]] += len(rows)
    require(boundary == 6739200 and old_pairs == 195296, "old and total pair counts")
    require(boundary - old_pairs == 6543904, "new pair count")
    require(plan == load(CAT / "benchmark-plan.json"), "complete stratified new-only plan")
    # Use the prior independent certificate checker, never either producer.
    spec = importlib.util.spec_from_file_location("independent_support", ENGINE)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    rank = {block: i for i, block in enumerate(BLOCKS)}
    carriers = []
    for triple in engine.TRIPLES:
        extra = sorted(set(range(2, 17)) - set(triple))
        ids = sorted(rank[tuple(sorted((*triple, *pair)))] for pair in combinations(extra, 2))
        require(len(ids) == len(set(ids)) == 66, "inverse complete row carriers")
        carriers.append(engine.ids_mask(ids))
    partial_rows = {
        item["partial_id"]: {
            engine.RANK[t]
            for i in families[item["partial_id"]]
            for t in combinations(BLOCKS[i][1:], 3)
        }
        for item in plan
    }
    require(all(len(rows) == 80 for rows in partial_rows.values()), "sample outside rows")
    profile_rows = [
        {engine.RANK[tuple(t)] for t in p["excess_triples"] if 1 not in t} for p in profiles
    ]
    pairs = {item["pair_ordinal"]: (item["partial_id"], item["profile_id"]) for item in plan}
    data = carriers, partial_rows, profile_rows, pairs
    records = [
        json.loads(line)
        for line in gzip.open(
            ROOT / next(p for p in receipt["raw_files"] if p.endswith("/cases.jsonl.gz")), "rt"
        )
    ]
    require(len(records) == 1000, "complete sample stream")
    outcomes, survivors = Counter(), []
    for record, item in zip(records, plan, strict=True):
        require(all(record[k] == v for k, v in item.items()), "sample identity")
        outcome = engine.check_record(record, item["pair_ordinal"], data)
        outcomes[outcome] += 1
        if outcome == "survives_single_pass":
            survivors.append(record)
    saved = [
        json.loads(line)
        for line in gzip.open(
            ROOT / next(p for p in receipt["raw_files"] if p.endswith("/survivors.jsonl.gz")), "rt"
        )
    ]
    require(
        saved == survivors and dict(outcomes) == receipt["outcomes"], "exact survivor stream/counts"
    )
    controls = []

    def reject(name, callback):
        try:
            callback()
        except (ValueError, KeyError, IndexError):
            controls.append(name)
        else:
            raise AssertionError(f"accepted damaged {name}")

    first = families[0]
    reject(
        "duplicate_family_block",
        lambda: verify_family(
            (first[0], *first[:-1]), inverses[0], quad_rank, unions[fibers[0]["class"]]
        ),
    )
    reject(
        "point_avoiding_block",
        lambda: verify_family(
            (*first[:-1], 1365), inverses[0], quad_rank, unions[fibers[0]["class"]]
        ),
    )
    for name, field, value in (
        ("wrong_partial", "partial_id", -1),
        ("wrong_profile", "profile_id", -1),
        ("wrong_domain", "initial_domain_count", 3002),
        ("wrong_eligible_hash", "eligible_mask_sha256", "0" * 64),
    ):
        damaged = copy.deepcopy(records[0])
        damaged[field] = value
        reject(
            name,
            lambda damaged=damaged: engine.check_record(damaged, damaged["pair_ordinal"], data),
        )
    for outcome in ("insufficient_support", "forced_conflict"):
        damaged = copy.deepcopy(next(row for row in records if row["outcome"] == outcome))
        damaged["demand"] += 1
        reject(
            f"wrong_{outcome}_demand",
            lambda damaged=damaged: engine.check_record(damaged, damaged["pair_ordinal"], data),
        )
    damaged = copy.deepcopy(survivors[0])
    damaged["immediately_forced_blocks"] += 1
    reject(
        "wrong_survivor_forces", lambda: engine.check_record(damaged, damaged["pair_ordinal"], data)
    )
    result = {
        "passed": True,
        "families": len(families),
        "canonical_families_per_class": 5184,
        "fibers": 38,
        "old_families": len(old_ids),
        "old_pairs": old_pairs,
        "new_pairs": boundary - old_pairs,
        "full_pairs": boundary,
        "family_census": dict(census),
        "checked_sample_cases": len(records),
        "outcomes": dict(outcomes),
        "damage_controls_rejected": controls,
        "catalog_summary_sha256": sha(CAT / "summary.json"),
        "sample_receipt_sha256": sha(BENCH / "benchmark.json"),
        "checker_sha256": sha(Path(__file__)),
        "independent_engine_sha256": sha(ENGINE),
        "producer_imports": 0,
        "producer_runs": 0,
        "optimizer_calls": 0,
        "elapsed_seconds": time.monotonic() - started,
        "scope": "Four-core origin-deletion affine recipe only; sample is not a full screen.",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
