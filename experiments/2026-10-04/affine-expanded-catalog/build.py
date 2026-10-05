# Document:    Expanded Four-Class Affine Point-One Catalog
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      546a638857b971c8039ffa6b36d039c1def014f7eea86ec1a4a4cd06a4e54d38
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Materialize the checked affine recipe; no solver or support screening."""

import gzip
import json
import struct
import subprocess
import time
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
OLD = BASE / "circulant-chosen-link-catalog"
AFFINE = BASE / "affine-extension-semilinear-completeness"
RAW = ROOT / "experiments/scratch/affine-expanded-catalog-v1.0.0"
QUADS = tuple(combinations(range(1, 16), 4))
BLOCKS = tuple(combinations(range(1, 17), 5))
RANK = {block: i for i, block in enumerate(BLOCKS)}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def dump(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main():
    started = time.monotonic()
    require(not (HERE / "summary.json").exists() and not RAW.exists(), "fresh preparation")
    complete = load(AFFINE / "summary.json")
    union_path = ROOT / complete["raw_union"]
    require(sha(union_path) == complete["raw_union_sha256"], "canonical union pin")
    require(
        sha(AFFINE / "summary.json")
        == "15a674ea26f0d435f9776ce22ccf458cefe369288922c1f433fff93a45ed6da2",
        "completeness receipt pin",
    )
    unions = json.loads(gzip.decompress(union_path.read_bytes()))
    classes = load(BASE / "clebsch-point-link-construction/classes.json")
    old_fibers = load(OLD / "link-fibers.json")
    old_catalog = load(OLD / "partial-catalog.json")
    require(len(old_fibers) == 38 and len(old_catalog) == 5536, "old catalog sizes")
    for name, families in unions.items():
        target = set(map(tuple, classes[name]["canonical_excess_edges"]))
        require(len(families) == len({tuple(row) for row in families}) == 5184, "class union")
        for ids in families:
            require(len(ids) == len(set(ids)) == 20 and ids == sorted(ids), "quad IDs")
            blocks = [QUADS[i] for i in ids]
            pairs = Counter(edge for block in blocks for edge in combinations(block, 2))
            require(
                len(pairs) == 105 and all(n == 1 + (edge in target) for edge, n in pairs.items()),
                "canonical pairs",
            )
            triples = [triple for block in blocks for triple in combinations(block, 3)]
            require(len(triples) == len(set(triples)) == 80, "canonical distinct triples")
    old_to_new = [None] * len(old_catalog)
    fibers, boundaries, families, plan = [], [0], [], []
    by_class = Counter()
    for fiber in old_fibers:
        fiber_id = fiber["excess_link_id"]
        require(fiber_id == len(fibers), "ordered fiber IDs")
        require(fiber["profile_ids"] == sorted(set(fiber["profile_ids"])), "profile order")
        mapping = fiber["canonical_to_actual"]
        require(sorted(mapping) == list(range(2, 17)), "bijection to actual labels")
        actual_edges = {
            tuple(sorted(mapping[v - 1] for v in edge))
            for edge in classes[fiber["class"]]["canonical_excess_edges"]
        }
        require(actual_edges == set(map(tuple, fiber["actual_excess_edges"])), "E transport")
        mapped_quads = [RANK[(1, *sorted(mapping[v - 1] for v in quad))] for quad in QUADS]
        transported = sorted(
            tuple(sorted(mapped_quads[i] for i in row)) for row in unions[fiber["class"]]
        )
        require(len(transported) == len(set(transported)) == 5184, "distinct fiber families")
        start = len(families)
        families.extend(transported)
        lookup = {ids: start + i for i, ids in enumerate(transported)}
        old_start, old_end = fiber["partial_id_range_half_open"]
        old_ids = []
        for old_id in range(old_start, old_end):
            old = old_catalog[old_id]
            require(
                old["partial_id"] == old_id and old["excess_link_id"] == fiber_id,
                "old IDs and fiber",
            )
            new_id = lookup[tuple(old["global_block_ids"])]
            old_to_new[old_id] = new_id
            old_ids.append(new_id)
        new_ids = sorted(set(range(start, len(families))) - set(old_ids))
        count = len(fiber["profile_ids"])
        item = dict(fiber)
        item.update(
            {
                "partial_id_range_half_open": [start, len(families)],
                "old_partial_ids_in_expanded_catalog": sorted(old_ids),
                "new_only_partial_count": len(new_ids),
                "pair_ordinal_range_half_open": [boundaries[-1], boundaries[-1] + 5184 * count],
            }
        )
        # Twenty-six samples per fiber; the first twelve fibers receive one extra.
        sample_count = 26 + (fiber_id < 12)
        for k in range(sample_count):
            local_new = ((2 * k + 1) * len(new_ids) * count) // (2 * sample_count)
            partial_offset, profile_offset = divmod(local_new, count)
            partial_id = new_ids[partial_offset]
            ordinal = boundaries[-1] + (partial_id - start) * count + profile_offset
            plan.append(
                {
                    "sample_index": len(plan),
                    "excess_link_id": fiber_id,
                    "pair_ordinal": ordinal,
                    "partial_id": partial_id,
                    "profile_id": fiber["profile_ids"][profile_offset],
                }
            )
        boundaries.append(item["pair_ordinal_range_half_open"][1])
        fibers.append(item)
        by_class[fiber["class"]] += 5184
    require(len(families) == len(set(families)) == 196992, "global family count and uniqueness")
    require(
        all(type(i) is int for i in old_to_new) and len(set(old_to_new)) == 5536,
        "every old family has one distinct new ID",
    )
    require(
        sorted(p for fiber in fibers for p in fiber["profile_ids"]) == list(range(1300)),
        "profile partition",
    )
    old_pairs = sum(
        len(f["old_partial_ids_in_expanded_catalog"]) * len(f["profile_ids"]) for f in fibers
    )
    require(boundaries[-1] == 6739200 and old_pairs == 195296, "pair totals")
    require(len(plan) == len({r["pair_ordinal"] for r in plan}) == 1000, "unique benchmark pairs")
    require(not set(row["partial_id"] for row in plan).intersection(old_to_new), "new-only plan")
    payload = b"".join(struct.pack("<20H", *row) for row in families)
    require(len(payload) == 196992 * 40, "packed catalog size")
    require(
        [struct.unpack_from("<20H", payload, i * 40) for i in range(len(families))] == families,
        "packed catalog round trip",
    )
    RAW.mkdir(parents=True)
    catalog_path = RAW / "catalog-20xu16le.bin.gz"
    catalog_path.write_bytes(gzip.compress(payload, compresslevel=6, mtime=0))
    dump("link-fibers.json", fibers)
    dump("old-to-new-ids.json", old_to_new)
    dump("benchmark-plan.json", plan)
    summary = {
        "scope": complete["scope"],
        "families": len(families),
        "fibers": len(fibers),
        "profiles": 1300,
        "implicit_pairs": boundaries[-1],
        "old_families_preserved": 5536,
        "old_pairs_to_skip": old_pairs,
        "new_families": 191456,
        "new_pairs": 6543904,
        "family_counts_by_class": dict(by_class),
        "catalog_path": str(catalog_path.relative_to(ROOT)),
        "catalog_schema": "gzip payload: 196992 fixed records of 20 little-endian uint16 IDs",
        "global_block_order": "zero-based lexicographic combinations of 1..16 choose 5",
        "record_order": "excess_link_id, then lexicographic tuple of sorted global block IDs",
        "pair_order": "fiber, then partial ID, then ascending profile ID within fiber",
        "pair_boundaries": boundaries,
        "old_to_new_schema": "list indexed by original partial ID; value is expanded partial ID",
        "benchmark_plan": "1000 new-only pairs, midpoint strata across each of 38 fibers",
        "benchmark_strata_counts": {str(i): 26 + (i < 12) for i in range(38)},
        "catalog_compressed_sha256": sha(catalog_path),
        "catalog_uncompressed_sha256": sha256(payload).hexdigest(),
        "catalog_compressed_bytes": catalog_path.stat().st_size,
        "catalog_uncompressed_bytes": len(payload),
        "input_hashes": {
            str(p.relative_to(ROOT)): sha(p)
            for p in (
                AFFINE / "summary.json",
                union_path,
                BASE / "clebsch-point-link-construction/classes.json",
                OLD / "link-fibers.json",
                OLD / "partial-catalog.json",
                OLD / "profiles.json",
            )
        },
        "output_hashes": {
            name: sha(HERE / name)
            for name in ("link-fibers.json", "old-to-new-ids.json", "benchmark-plan.json")
        },
        "source_sha256": sha(__file__),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "elapsed_seconds": time.monotonic() - started,
        "optimizer_calls": 0,
        "screen_calls": 0,
    }
    dump("summary.json", summary)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
