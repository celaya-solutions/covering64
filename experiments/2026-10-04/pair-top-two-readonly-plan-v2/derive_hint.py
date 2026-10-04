# Document:    Complete Top-Two Hint Derivation Helper
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      61ea1522a9e7de5bb022ac3a9fa66ec963757692936c95698e63405eedeb2e1f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Derive a semantic complete vector, with no model construction or optimizer."""

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DAY = ROOT / "experiments/2026-10-04"
POINTS = tuple(range(1, 17))
SETS = {size: tuple(itertools.combinations(POINTS, size)) for size in (2, 3, 4, 5)}
FROZEN = {
    "compact-pair-two-counts/manifest.json":
        "82372b924493eed1e3a24c48e580d0b15796cc1d2c50bbe71b400bee23910aad",
    "fourth-core-independent/audit.json":
        "d57afcefda39021a131529bafda5a9ba8e22188ab671ee610bae058dbe5ffefb",
    "pair-two-necessary-cuts-independent/audit.json":
        "db490b9d3cd3500eb2c85d36f803a73667ceed00e5251932608e7d1150e7099b",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse(text):
    rows = [line.split() for line in text.splitlines() if line.strip()]
    require(len(rows) == 64, "exactly 64 nonempty block rows required")
    blocks = []
    for row in rows:
        require(len(row) == 5, "each block must have exactly five labels")
        require(all(token.isascii() and token.isdecimal() for token in row), "integer labels")
        block = tuple(sorted(map(int, row)))
        require(len(set(block)) == 5 and min(block) >= 1 and max(block) <= 16, "bad block")
        blocks.append(block)
    require(len(set(blocks)) == 64, "duplicate blocks")
    return sorted(blocks)


def load_sources():
    sources = {}
    for relative, digest in FROZEN.items():
        path = DAY / relative
        require(sha(path) == digest, f"frozen source hash mismatch: {relative}")
        sources[relative] = json.loads(path.read_text())
    manifest = sources["compact-pair-two-counts/manifest.json"]
    fourth = sources["fourth-core-independent/audit.json"]
    proof = sources["pair-two-necessary-cuts-independent/audit.json"]
    require(fourth["passed"] and proof["passed"], "unpassed proof source")
    require(fourth["recommended_upper_bound"] == 55, "fourth cap bound changed")
    cores = manifest["core_rows"] + [fourth["core_global_ids"]]
    require(len(cores) == 4, "four cores required")
    require(len({tuple(sorted(core)) for core in cores}) == 4, "duplicate core")
    for core in cores:
        require(len(core) == len(set(core)) == 60, "core must have 60 distinct blocks")
        require(all(type(i) is int and 0 <= i < 4368 for i in core), "invalid core ID")
    return cores


def global_profile(counts):
    weighted = {point: [] for point in POINTS}
    for triple in SETS[3]:
        if counts[triple] >= 6:
            mask = sum(1 << (point - 1) for point in triple)
            entry = (mask, 5 + int(counts[triple] >= 7), triple)
            for point in triple:
                weighted[point].append(entry)

    @lru_cache(maxsize=None)
    def visit(mask):
        if not mask:
            return 0, ()
        low = mask & -mask
        point = low.bit_length()
        best = visit(mask ^ low)
        for triple_mask, weight, triple in weighted[point]:
            if mask & triple_mask == triple_mask:
                value, witness = visit(mask ^ triple_mask)
                option = value + weight, (triple,) + witness
                if option[0] > best[0]:
                    best = option
        return best

    value, witness = visit((1 << 16) - 1)
    return {"maximum": value, "positive_weight_disjoint_triples": witness, "bound": 26}


def dual_verify(blocks, holes):
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    source = ROOT / "scripts/check_cover.py"
    spec = importlib.util.spec_from_file_location("standalone_hint_verifier", source)
    require(spec is not None and spec.loader is not None, "standalone verifier unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    package = verify_cover(blocks, 16, 5, 3)
    standalone = module.verify_cover(blocks, 16, 5, 3, expected_blocks=64)
    require(package["blocks"] == standalone["blocks"] == 64, "verifier cardinality")
    require(len(package["uncovered"]) == standalone["uncovered_count"] == holes, "hole count")
    require(sorted(map(tuple, package["uncovered"])) == sorted(map(tuple, standalone["uncovered"])),
            "uncovered list disagreement")
    require(package["valid"] == standalone["valid"] == (holes == 0), "cover-status mismatch")
    require(package["canonical_sha256"] == standalone["canonical_sha256"], "canonical hash")
    return {
        "package": package,
        "standalone": standalone,
        "package_source_sha256": sha(verify_cover.__code__.co_filename),
        "standalone_source_sha256": sha(source),
    }


def derive(path):
    blocks = parse(path.read_text())
    cores = load_sources()
    block_ids = {block: index for index, block in enumerate(SETS[5])}
    chosen = {block_ids[block] for block in blocks}
    x = [int(index in chosen) for index in range(4368)]
    counts = {
        size: Counter(subset for block in blocks for subset in itertools.combinations(block, size))
        for size in (2, 3, 4)
    }
    hole_values = [int(counts[3][triple] == 0) for triple in SETS[3]]
    holes = sum(hole_values)
    verification = dual_verify(blocks, holes)
    failures, rows = [], 0

    def row(ok, name):
        nonlocal rows
        rows += 1
        if not ok:
            failures.append(name)

    row(sum(x) == 64, "exactly_64")
    support = {size: {subset: [] for subset in SETS[size]} for size in (2, 3)}
    for index, block in enumerate(SETS[5]):
        for size in (2, 3):
            for subset in itertools.combinations(block, size):
                support[size][subset].append(index)
    for size in (2, 3):
        for subset in SETS[size]:
            expected_support = 364 if size == 2 else 78
            require(len(support[size][subset]) == expected_support, "incomplete count support")
            row(counts[size][subset] == sum(x[i] for i in support[size][subset]),
                f"count_{size}_{subset}")
    for triple, hole in zip(SETS[3], hole_values, strict=True):
        row(not hole or counts[3][triple] == 0, f"hole_zero_{triple}")
        row(hole or counts[3][triple] >= 1, f"hole_positive_{triple}")
    z_values, y_values, per_pair = [], [], []
    d2max = d2sum = d3 = d4 = 0
    for pair in SETS[2]:
        positions = [(a, counts[3][tuple(sorted((*pair, a)))]) for a in POINTS if a not in pair]
        require(len(positions) == 14, "fourteen distinct positions required")
        r = counts[2][pair]
        require(sum(t for _, t in positions) == 3 * r, "incidence identity failed")
        ordered = sorted(positions, key=lambda item: (-item[1], item[0]))
        z = ordered[1][1]
        ys = [max(0, t - z) for _, t in positions]
        z_values.append(z)
        y_values.extend(ys)
        for (a, t), y in zip(positions, ys, strict=True):
            row(y >= t - z, f"hinge_{pair}_{a}")
            d3 += max(0, 13 - 3 * r + t)
        row(2 * z + sum(ys) <= 3 * r - 12, f"top_two_{pair}")
        maximum = max(0, 12 - 3 * r + ordered[0][1] + ordered[1][1])
        deficits = []
        for (a, ta), (b, tb) in itertools.combinations(positions, 2):
            deficits.append(max(0, 12 - 3 * r + ta + tb))
            d4 += max(0, 12 - 3 * r + 2 * counts[4][tuple(sorted((*pair, a, b)))])
        require(len(deficits) == 91 and max(deficits) == maximum, "top-two mismatch")
        require(2 * z + sum(ys) == ordered[0][1] + ordered[1][1], "extension mismatch")
        d2max += maximum
        d2sum += sum(deficits)
        per_pair.append({"pair": pair, "positions": positions, "z": z, "y": ys,
                         "D2max": maximum, "D2sum": sum(deficits)})
    overlaps = [sum(x[i] for i in core) for core in cores]
    for index, overlap in enumerate(overlaps):
        row(overlap <= 55, f"core_cap_{index + 1}")
    require(rows == 3605, "proposed model row count mismatch")
    profile = global_profile(counts[3])
    domains = all(5 <= counts[2][pair] <= 64 for pair in SETS[2])
    domains &= all(0 <= counts[3][triple] <= 64 for triple in SETS[3])
    domains &= all(0 <= value <= 64 for value in z_values + y_values)
    diagnostic = {
        "holes": holes, "D2max": d2max, "D2sum": d2sum, "D3": d3, "D4": d4,
        "minimum_pair_count": min(counts[2][pair] for pair in SETS[2]),
        "core_overlaps": overlaps, "global_profile": profile,
        "rows_checked": rows, "row_failures": failures, "domains_pass": domains,
        "objective": 65 * holes + overlaps[0], "covering_witness": holes == 0,
        "qualified": not failures and domains and d2max == d3 == d4 == 0
        and profile["maximum"] <= 26,
    }
    if not diagnostic["qualified"]:
        return diagnostic, None
    values = x + [counts[2][pair] for pair in SETS[2]]
    values += [counts[3][triple] for triple in SETS[3]] + hole_values + z_values + y_values
    require(len(values) == 7408 and all(type(v) is int for v in values), "complete vector")
    payload = {
        "status": "semantic complete vector; not bound to a constructed model",
        "model_constructed": False, "optimizer_calls": 0,
        "source_sha256": sha(__file__), "candidate_path": str(path.resolve()),
        "candidate_sha256": sha(path), "frozen_sources": FROZEN,
        "diagnostics": diagnostic, "verification": verification,
        "proposed_variable_order": {
            "blocks": [0, 4367], "pairs": [4368, 4487], "triples": [4488, 5047],
            "holes": [5048, 5607], "z": [5608, 5727], "y": [5728, 7407],
            "convention": "lexicographic subsets; y by pair then ascending outside point",
        },
        "values": values, "per_pair": per_pair,
        "quadruple_counts": [counts[4][quad] for quad in SETS[4]],
        "core_block_ids": cores,
    }
    return diagnostic, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error("output already exists; never overwrite a receipt")
    try:
        diagnostic, payload = derive(args.candidate)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"qualified": False, "error": str(error), "hint_written": False}))
        return 2
    if payload is not None and args.output is not None:
        with args.output.open("x") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
    diagnostic["hint_written"] = payload is not None and args.output is not None
    print(json.dumps(diagnostic, sort_keys=True))
    return 0 if payload is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
