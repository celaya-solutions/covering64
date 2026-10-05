# Document:    Independent Replay of the Full New-Only Affine Support Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      37ff00091703bab597f53849d92662a255d64861f67a750d341b79d97168eb47
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay all 6,543,904 committed support-screen records without producer code.

The per-record arithmetic is the frozen independent `check_record` used for the
original 195,296 pairs, which builds row carriers by the inverse construction.
This wrapper supplies the expanded partials from the pinned packed catalog,
an independently enumerated new-only case order, and the committed-prefix pins
from the run's authoritative cursor. It never imports the screen producer.
"""

import gzip
import importlib.util
import json
import struct
import sys
from bisect import bisect_right
from collections import Counter
from hashlib import sha256
from itertools import combinations, islice
from multiprocessing import get_context
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
CHECKER = BASE / "circulant-chosen-link-support-runtime-independent/check.py"
CHECKER_SHA = "34454b7922b3165000622ab7a810d316f2a511e1f0181e23a450b35209afbc95"
EXPANDED = BASE / "affine-expanded-catalog"
RAW = ROOT / "experiments/scratch/affine-expanded-full-support-v1.0.0"
RESULT = BASE / "affine-expanded-full-support-v1.0.1/result.json"
RESULT_SHA = "704c1aa8459ef6b23042cbd38bcc718ab1418ae2285b8940dac067ab51cfd288"
NEW_TOTAL = 6543904
FULL_TOTAL = 6739200
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(2, 17), 3))
RANK = {t: i for i, t in enumerate(TRIPLES)}
STATE = {}


def require(test, message):
    if not test:
        raise ValueError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load_checker():
    spec = importlib.util.spec_from_file_location("frozen_support_checker", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Partials:
    """Outside rows met by each packed twenty-block family, built on demand."""

    def __init__(self, packed):
        self.packed = packed
        self.cache = {}

    def __getitem__(self, partial_id):
        if partial_id not in self.cache:
            if len(self.cache) > 64:
                self.cache.clear()
            ids = struct.unpack_from("<20H", self.packed, 40 * partial_id)
            require(all(BLOCKS[i][0] == 1 for i in ids), "fixed point-one blocks")
            counts = Counter(t for i in ids for t in combinations(BLOCKS[i], 3) if 1 not in t)
            require(len(counts) == 80 and set(counts.values()) == {1}, "outside multiplicity")
            self.cache[partial_id] = frozenset(RANK[t] for t in counts)
        return self.cache[partial_id]


class Pairs:
    """Full-domain ordinal to (partial, profile), from the expanded fibers."""

    def __init__(self, fibers):
        self.fibers = fibers
        self.starts, offset = [], 0
        for fiber in fibers:
            start, stop = fiber["partial_id_range_half_open"]
            self.starts.append(offset)
            offset += (stop - start) * len(fiber["profile_ids"])
        require(offset == FULL_TOTAL, "full pair domain")

    def __getitem__(self, ordinal):
        index = bisect_right(self.starts, ordinal) - 1
        fiber = self.fibers[index]
        local = ordinal - self.starts[index]
        width = len(fiber["profile_ids"])
        partial = fiber["partial_id_range_half_open"][0] + local // width
        return partial, fiber["profile_ids"][local % width]


def expected_ordinals(fibers, old_ids):
    """New-only order: fiber, partial, profile, skipping every mapped old partial."""
    old = set(old_ids)
    offset = 0
    for fiber in fibers:
        start, stop = fiber["partial_id_range_half_open"]
        width = len(fiber["profile_ids"])
        for partial in range(start, stop):
            if partial not in old:
                for k in range(width):
                    yield offset + (partial - start) * width + k
        offset += (stop - start) * width


def setup():
    checker = load_checker()
    row_carriers, _, profile_rows, _ = checker.prepare_data()
    summary = json.loads((EXPANDED / "summary.json").read_text())
    packed = gzip.decompress((ROOT / summary["catalog_path"]).read_bytes())
    require(sha256(packed).hexdigest() == summary["catalog_uncompressed_sha256"], "packed catalog")
    fibers = json.loads((EXPANDED / "link-fibers.json").read_text())
    STATE["check"] = checker.check_record
    STATE["data"] = (row_carriers, Partials(packed), profile_rows, Pairs(fibers))


def check_chunk(chunk):
    tally = Counter()
    for line, ordinal in chunk:
        record = json.loads(line)
        require(type(record["new_pair_index"]) is int, "new index")
        tally[STATE["check"](record, ordinal, STATE["data"])] += 1
    return tally


def chunks(lines, ordinals, size=4000):
    batch = []
    for line, ordinal in zip(lines, ordinals, strict=True):
        batch.append((line, ordinal))
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def main():
    require(digest(CHECKER) == CHECKER_SHA, "frozen independent per-record checker")
    require(digest(RESULT) == RESULT_SHA, "screen receipt pin")
    result = json.loads(RESULT.read_text())
    cursor = result["committed_cursor"]
    require(result["status"] == "complete" and cursor["committed_cases"] == NEW_TOTAL, "complete")
    for name, path in (("cases", "cases.jsonl.gz"), ("survivors", "survivors.jsonl.gz")):
        data = (RAW / path).read_bytes()
        require(len(data) == cursor["files"][name]["bytes"], f"{name} committed length")
        require(sha256(data).hexdigest() == cursor["files"][name]["sha256"], f"{name} prefix hash")
    summary = json.loads((EXPANDED / "summary.json").read_text())
    fibers = json.loads((EXPANDED / "link-fibers.json").read_text())
    old_ids = json.loads((EXPANDED / "old-to-new-ids.json").read_text())
    require(len(set(old_ids)) == 5536, "old partial map")
    require(summary["catalog_uncompressed_bytes"] == 196992 * 40, "catalog size")
    totals, survivor_lines = Counter(), []
    with gzip.open(RAW / "cases.jsonl.gz", "rt") as handle:

        def lines():
            for line in handle:
                if '"survives_single_pass"' in line:
                    survivor_lines.append(json.loads(line))
                yield line

        with get_context("spawn").Pool(8, initializer=setup) as pool:
            work = chunks(lines(), expected_ordinals(fibers, old_ids))
            while group := list(islice(work, 64)):
                for tally in pool.map(check_chunk, group):
                    totals.update(tally)
    require(sum(totals.values()) == NEW_TOTAL, "every committed case replayed")
    require(dict(totals) == cursor["outcomes"], "outcome census")
    with gzip.open(RAW / "survivors.jsonl.gz", "rt") as handle:
        survivors = [json.loads(line) for line in handle]
    require(survivors == survivor_lines, "survivor stream equals survivors in the case stream")
    review = {
        "cases": NEW_TOTAL,
        "checker_sha256": digest(__file__),
        "frozen_record_checker_sha256": CHECKER_SHA,
        "cursor_prefix_hashes": {k: v["sha256"] for k, v in cursor["files"].items()},
        "outcomes": dict(totals),
        "passed": True,
        "producer_imports": 0,
        "scope": "Support-screen exclusions and survivors of the new-only affine pairs only.",
        "survivors_matched": len(survivors),
    }
    (HERE / "review.json").write_text(json.dumps(review, indent=1, sort_keys=True) + "\n")
    print(json.dumps(review))


if __name__ == "__main__":
    sys.exit(main())
