# Document:    Independent Replay of Affine LP Farkas Certificates
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      1d813f31b0b0165b6abe9ec2fe040dabf6999d65cb33a1d83577d3d95c1400da
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Replay every saved bounded-LP exclusion with integers only.

No producer import, LP solver or NumPy is used. For each saved case this
rebuilds the residual system from the frozen catalogs, recomputes the kept
five-subsets avoiding point one, and checks

    sum_r b_r Y_r - sum_j max(0, sum_{r in column j} Y_r) > 0.

For x in [0,1]^n with Ax = b the left side is at most zero, so a positive value
excludes that one fixed link/profile completion. The case list must equal the
two pinned survivor streams exactly, once each.
"""

import gzip
import json
import struct
import sys
from bisect import bisect_right
from collections import Counter
from hashlib import sha256
from itertools import combinations
from multiprocessing import get_context
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
RAW = ROOT / "experiments/scratch/affine-lp-farkas-v1.0.0"
OLD = BASE / "circulant-chosen-link-catalog"
EXPANDED = BASE / "affine-expanded-catalog"
SURVIVORS = {
    "original": (
        "experiments/scratch/circulant-chosen-link-row-propagation-full-v1.0.0/survivors.jsonl.gz",
        "60e42a6855fc897130c80d8db8189cd9639e0981555386e5938ed02a5eda90ed",
    ),
    "expanded": (
        "experiments/scratch/affine-expanded-full-support-v1.0.0/survivors.jsonl.gz",
        "340a1bbf418a1a72a1cb4dced4a27b25e43b38add9614180a7d31bcb4af7ec04",
    ),
}
LEX = {t: i for i, t in enumerate(combinations(range(2, 17), 3))}
CARD = len(LEX)
QUINTS = [q for q in combinations(range(2, 17), 5)]
QUINT_ROWS = [[LEX[t] for t in combinations(q, 3)] for q in QUINTS]
POINT_ONE = list(combinations(range(1, 17), 5))[:1365]
STATE = {}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def fiber_ordinal(fibers, partial_id, profile_id, total):
    starts, offsets, offset = [], [], 0
    for fiber in fibers:
        start, stop = fiber["partial_id_range_half_open"]
        starts.append(start)
        offsets.append(offset)
        offset += (stop - start) * len(fiber["profile_ids"])
    require(offset == total, "complete fiber order")
    index = bisect_right(starts, partial_id) - 1
    fiber = fibers[index]
    start, stop = fiber["partial_id_range_half_open"]
    require(start <= partial_id < stop and profile_id in fiber["profile_ids"], "fiber member")
    width = len(fiber["profile_ids"])
    return offsets[index] + (partial_id - start) * width + fiber["profile_ids"].index(profile_id)


def setup():
    summary = json.loads((EXPANDED / "summary.json").read_text())
    require(
        digest(EXPANDED / "summary.json")
        == "e85200dbdf2a392d192973904bc638e4e55184cdc70e1f8cbe3c7643c19ecd6a",
        "expanded summary pin",
    )
    packed = gzip.decompress((ROOT / summary["catalog_path"]).read_bytes())
    require(sha256(packed).hexdigest() == summary["catalog_uncompressed_sha256"], "packed")
    STATE["packed"] = packed
    STATE["old"] = json.loads((OLD / "partial-catalog.json").read_text())
    STATE["profiles"] = json.loads((OLD / "profiles.json").read_text())
    STATE["fibers"] = {
        "original": json.loads((OLD / "link-fibers.json").read_text()),
        "expanded": json.loads((EXPANDED / "link-fibers.json").read_text()),
    }


def blocks_for(catalog, partial_id):
    if catalog == "original":
        entry = STATE["old"][partial_id]
        require(entry["partial_id"] == partial_id, "original partial index")
        ids = entry["global_block_ids"]
    else:
        ids = struct.unpack_from("<20H", STATE["packed"], 40 * partial_id)
    require(len(set(ids)) == 20 and all(0 <= i < 1365 for i in ids), "point-one partial")
    return [POINT_ONE[i] for i in ids]


def replay(record):
    catalog = record["catalog"]
    total = 195296 if catalog == "original" else 6739200
    require(
        fiber_ordinal(STATE["fibers"][catalog], record["partial_id"], record["profile_id"], total)
        == record["pair_ordinal"],
        "pair ordinal binding",
    )
    excess = {tuple(t) for t in STATE["profiles"][record["profile_id"]]["excess_triples"]}
    hits = Counter()
    for block in blocks_for(catalog, record["partial_id"]):
        for t in combinations(block, 3):
            hits[t] += 1
    for t in combinations(range(1, 17), 3):
        if t[0] == 1:
            require(hits[t] == 1 + (t in excess), "point-one multiplicity")
    demand = [0] * CARD
    for t, row in LEX.items():
        demand[row] = 1 + (t in excess) - hits[t]
        require(demand[row] >= 0, "nonnegative residual demand")
    require(sum(demand) == 440, "total residual demand")
    if record["outcome"] != "lp_farkas_exclusion":
        return record["outcome"], 0
    y = dict(record["certificate"]["y"])
    require(all(type(k) is int and type(v) is int for k, v in y.items()), "integer certificate")
    require(all(0 <= k <= CARD for k in y), "row range")
    value = 44 * y.get(CARD, 0) + sum(demand[r] * v for r, v in y.items() if r < CARD)
    kept = 0
    for rows in QUINT_ROWS:
        if any(demand[r] == 0 for r in rows):
            continue
        kept += 1
        s = y.get(CARD, 0) + sum(y.get(r, 0) for r in rows)
        if s > 0:
            value -= s
    require(kept == record["eligible"], "kept column count")
    require(value > 0 and value == record["certificate"]["margin"], "positive exact margin")
    return record["outcome"], kept


def replay_chunk(lines):
    tally = Counter()
    for line in lines:
        outcome, _ = replay(json.loads(line))
        tally[outcome] += 1
    return tally


def chunks(handle, size=2000):
    batch = []
    for line in handle:
        batch.append(line)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def damage_controls():
    setup()
    with gzip.open(RAW / "certificates.jsonl.gz", "rt") as handle:
        sample = json.loads(next(handle))
    rejected = []

    def expect_reject(label, mutate):
        record = json.loads(json.dumps(sample))
        mutate(record)
        try:
            replay(record)
        except (AssertionError, KeyError, ValueError, IndexError):
            rejected.append(label)
            return
        raise AssertionError(f"damaged control accepted: {label}")

    def bump_row(record):
        row, value = record["certificate"]["y"][0]
        record["certificate"]["y"][0] = [row, value + 1]

    expect_reject("one multiplier changed", bump_row)
    expect_reject(
        "margin overstated",
        lambda r: r["certificate"].update(margin=r["certificate"]["margin"] + 1),
    )
    expect_reject("zero certificate", lambda r: r["certificate"].update(y=[], margin=0))
    expect_reject("wrong profile", lambda r: r.update(profile_id=(r["profile_id"] + 1) % 1300))
    expect_reject("wrong partial", lambda r: r.update(partial_id=r["partial_id"] + 1))
    expect_reject(
        "float multiplier",
        lambda r: r["certificate"]["y"].__setitem__(0, [r["certificate"]["y"][0][0], 0.5]),
    )
    expect_reject("kept count changed", lambda r: r.update(eligible=r["eligible"] + 1))
    return rejected


def main():
    result = json.loads((RAW / "result.json").read_text())
    require(digest(RAW / "certificates.jsonl.gz") == result["certificates_sha256"], "stream pin")
    expected = Counter()
    for catalog, (path, pin) in SURVIVORS.items():
        require(digest(ROOT / path) == pin, f"{catalog} survivor stream pin")
        with gzip.open(ROOT / path, "rt") as handle:
            for line in handle:
                row = json.loads(line)
                expected[(catalog, row["pair_ordinal"], row["partial_id"], row["profile_id"])] += 1
    require(set(expected.values()) == {1}, "distinct input cases")
    seen = Counter()
    with gzip.open(RAW / "certificates.jsonl.gz", "rt") as handle:
        for line in handle:
            r = json.loads(line)
            seen[(r["catalog"], r["pair_ordinal"], r["partial_id"], r["profile_id"])] += 1
    require(seen == expected, "certificate stream covers every input case exactly once")
    totals = Counter()
    with (
        get_context("spawn").Pool(8, initializer=setup) as pool,
        gzip.open(RAW / "certificates.jsonl.gz", "rt") as handle,
    ):
        for tally in pool.imap_unordered(replay_chunk, chunks(handle)):
            totals.update(tally)
    controls = damage_controls()
    review = {
        "cases": sum(expected.values()),
        "checker_sha256": digest(__file__),
        "certificates_sha256": result["certificates_sha256"],
        "damaged_controls_rejected": controls,
        "outcomes": dict(totals),
        "passed": True,
        "scope": (
            "Bounded-LP exclusions of fixed point-one link/profile completions in the "
            "circulant {+-1,+-3,8} excess branch only; not a global lower bound."
        ),
        "solver_imports": 0,
    }
    (HERE / "review.json").write_text(json.dumps(review, indent=1, sort_keys=True) + "\n")
    print(json.dumps(review))


if __name__ == "__main__":
    sys.exit(main())
