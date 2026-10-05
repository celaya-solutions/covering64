# Document:    Independent Affine Parity Certificate Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      608cc3d43d4cb2b144c1e93a929c04d27aa9a49dbc8e89e9aff6c8f6a8195502
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check saved parity contradictions directly; solve consistency by column space."""

import copy
import gzip
import json
import struct
from collections import Counter
from hashlib import sha256
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = HERE.parent
PRODUCER = BASE / "affine-mod2-pilot"
OLD = BASE / "circulant-chosen-link-catalog"
EXPANDED = BASE / "affine-expanded-catalog"
AUDIT = BASE / "circulant-chosen-link-row-propagation-full-runtime-independent/review.json"
PINS = {
    "result.json": "aacc0a5cd51bc8315e8b72dd1f14d7376b4241237672fbbceceec6d7e3288c71",
    "manifest.json": "dbf45a715ed80ef0ca0090abdfa06feb9c4fec786290934dee263d9b75602e5f",
    "executed-source.txt": "3e9e6a30089c9c995c049dc9ecce44d684ff049c2fabc790a7f4020b79ccb647",
}
AUDIT_SHA = "aceba1e0c1280be6154950dfe61e5545ff40035cb5307e3749b1ac97c630f92a"
BLOCKS = tuple(combinations(range(1, 17), 5))
TRIPLES = tuple(combinations(range(2, 17), 3))
TRIPLE_ID = {triple: index for index, triple in enumerate(TRIPLES)}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    require(len(data.encode()) < 1_000_000, "small receipt")
    Path(path).write_text(data)


def columns():
    """Independent column construction: ten triple incidences plus cardinality."""
    result = []
    require(len(BLOCKS) == 4368 and len(TRIPLES) == 455, "complete lex universes")
    require(all(1 in block for block in BLOCKS[:1365]), "point-one fixed variables")
    require(all(1 not in block for block in BLOCKS[1365:]), "point-one-free variables")
    for block in BLOCKS[1365:]:
        value = 1 << 455
        for triple in combinations(block, 3):
            value |= 1 << TRIPLE_ID[triple]
        require(value.bit_count() == 11, "ten triple terms and cardinality")
        result.append(value)
    require(len(result) == 3003, "all completion columns")
    require(
        all(sum((col >> row) & 1 for col in result) == 66 for row in range(455)),
        "all triple rows have 66 columns",
    )
    return result


def pair_binding(case, fibers, expanded):
    require(
        all(type(case[k]) is int for k in ("partial_id", "profile_id", "pair_ordinal")),
        "strict case identity",
    )
    offset = 0
    found = None
    for fiber in fibers:
        start, stop = fiber["partial_id_range_half_open"]
        profiles = fiber["profile_ids"]
        require(profiles == sorted(set(profiles)), "ordered distinct fiber profiles")
        width = len(profiles)
        end = offset + (stop - start) * width
        if expanded:
            require(fiber["pair_ordinal_range_half_open"] == [offset, end], "expanded pair ranges")
        if start <= case["partial_id"] < stop:
            require(found is None and case["profile_id"] in profiles, "unique compatible fiber")
            expected = (
                offset + (case["partial_id"] - start) * width + profiles.index(case["profile_id"])
            )
            require(case["pair_ordinal"] == expected, "explicit catalog pair ordinal")
            found = fiber
        offset = end
    require(found is not None, "partial belongs to a fiber")
    require(offset == (6739200 if expanded else 195296), "complete implicit pair order")
    return found


def row_system(ids, profile, all_columns):
    require(len(ids) == 20 and list(ids) == sorted(set(ids)), "twenty distinct sorted partial IDs")
    require(all(type(i) is int and 0 <= i < 1365 for i in ids), "point-one partial IDs")
    blocks = [BLOCKS[index] for index in ids]
    counts = Counter(triple for block in blocks for triple in combinations(block, 3))
    excess = set(map(tuple, profile["excess_triples"]))
    require(len(excess) == 80, "eighty distinct excess triples")
    require(
        all(
            counts[(1, a, b)] == 1 + ((1, a, b) in excess) for a, b in combinations(range(2, 17), 2)
        ),
        "all pinned point-one equations",
    )
    outside = {t: n for t, n in counts.items() if 1 not in t}
    require(len(outside) == 80 and set(outside.values()) == {1}, "partial outside triple caps")
    require(len(counts) == 185 and sum(counts.values()) == 200, "actual partial coverage")
    demands = [1 + (triple in excess) - counts[triple] for triple in TRIPLES] + [44]
    require(min(demands) >= 0 and sum(demands[:-1]) == 440, "exact residual demands")
    zero_mask = sum(1 << row for row, demand in enumerate(demands[:-1]) if demand == 0)
    eligible = [(index, col) for index, col in enumerate(all_columns) if not col & zero_mask]
    rhs = sum((demand % 2) << row for row, demand in enumerate(demands))
    require(all((col & zero_mask) == 0 for _, col in eligible), "safe zero-demand eligibility")
    return demands, eligible, rhs


def certificate(row_ids, eligible, rhs):
    require(isinstance(row_ids, list) and row_ids, "nonempty certificate rows")
    require(
        all(type(row) is int and 0 <= row < 456 for row in row_ids), "strict certificate row IDs"
    )
    require(row_ids == sorted(set(row_ids)), "ordered unique certificate rows")
    selected = sum(1 << row for row in row_ids)
    require(
        all((col & selected).bit_count() % 2 == 0 for _, col in eligible),
        "every eligible column cancels",
    )
    require((rhs & selected).bit_count() % 2 == 1, "odd summed right-hand side")
    return selected


def basis_for_columns(eligible, row_mask=None):
    """Column-space elimination with highest-row pivots, unlike producer row elimination."""
    pivots = {}
    for _, column in eligible:
        column = column if row_mask is None else column & row_mask
        while column:
            pivot = column.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = column
                break
            column ^= pivots[pivot]
    return pivots


def reduce_rhs(rhs, basis):
    while rhs:
        pivot = rhs.bit_length() - 1
        if pivot not in basis:
            return rhs
        rhs ^= basis[pivot]
    return 0


def identity(actual, expected):
    for field in ("catalog", "pair_ordinal", "partial_id", "profile_id"):
        require(
            type(actual[field]) is type(expected[field]) and actual[field] == expected[field],
            "complete ordered input identity: " + field,
        )


def damage_controls(sample_bad, sample_good):
    record, eligible, rhs = sample_bad
    rejected = []

    def reject(label, operation):
        try:
            operation()
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError("damaged certificate accepted: " + label)

    rows = record["xor_rows"]
    reject("empty_rows", lambda: certificate([], eligible, rhs))
    reject("duplicate_row", lambda: certificate(sorted(rows + [rows[0]]), eligible, rhs))
    reject("reversed_rows", lambda: certificate(list(reversed(rows)), eligible, rhs))
    for label, value in (
        ("negative_row", -1),
        ("out_of_range", 456),
        ("bool_row", False),
        ("float_row", 1.0),
        ("string_row", "1"),
    ):
        damaged = [value, *rows[1:]]
        reject(label, lambda damaged=damaged: certificate(damaged, eligible, rhs))
    toggled = sorted(set(rows) ^ {455})
    reject("toggled_cardinality_row", lambda: certificate(toggled, eligible, rhs))
    reject("even_rhs", lambda: certificate(rows, eligible, rhs ^ (1 << rows[0])))
    meaningful = next(
        row for row in rows if ((rhs >> row) & 1) or any((col >> row) & 1 for _, col in eligible)
    )
    reject(
        "omitted_meaningful_row",
        lambda: certificate([r for r in rows if r != meaningful], eligible, rhs),
    )
    for field in ("pair_ordinal", "partial_id", "profile_id"):
        damaged = copy.deepcopy(record)
        damaged[field] += 1
        reject("wrong_" + field, lambda damaged=damaged: identity(damaged, record))
    good, good_eligible, good_rhs = sample_good
    basis = basis_for_columns(good_eligible)
    require(
        reduce_rhs(good_rhs, basis) == 0 and len(basis) == good["rank"],
        "consistent positive control",
    )
    require(len(basis) != good["rank"] + 1, "damaged rank rejected")
    rejected.append("wrong_consistent_rank")
    missing_direction = next(1 << row for row in range(456) if reduce_rhs(1 << row, basis))
    require(reduce_rhs(good_rhs ^ missing_direction, basis) != 0, "damaged consistent RHS rejected")
    rejected.append("wrong_consistent_rhs")
    return rejected


def main():
    for name, expected in PINS.items():
        require(digest(PRODUCER / name) == expected, "exact frozen pilot input")
    require(digest(AUDIT) == AUDIT_SHA, "accepted original survivor audit")
    manifest, result = read(PRODUCER / "manifest.json"), read(PRODUCER / "result.json")
    archive = read(PRODUCER / "source-archive.json")
    require(
        archive["executed_source"] == "executed-source.txt"
        and archive["executed_source_sha256"] == PINS["executed-source.txt"],
        "exact source archive",
    )
    require(archive["formatted_source_executed"] is False, "formatted copy not claimed executed")
    require(
        result["source_sha256"] == manifest["source_sha256"] == PINS["executed-source.txt"],
        "executed source binding",
    )
    require(result["manifest_sha256"] == PINS["manifest.json"], "manifest binding")
    for path, expected in manifest["inputs"].items():
        require(digest(ROOT / path) == expected, "frozen pilot data input")
    require(
        result["complete"] is True and len(result["results"]) == manifest["planned_cases"] == 1121,
        "complete saved outcome stream",
    )
    require(result["optimizer_calls"] == manifest["optimizer_calls"] == 0, "no optimizer")
    require(
        manifest["cooperative_seconds"] == 10 and 0 <= result["elapsed_seconds"] <= 10,
        "saved finite budget",
    )
    summary = read(EXPANDED / "summary.json")
    extra_pins = {}
    for name in ("link-fibers.json",):
        path = EXPANDED / name
        require(digest(path) == summary["output_hashes"][name], "expanded fiber pin")
        extra_pins[str(path.relative_to(ROOT))] = digest(path)
    old_fibers = read(OLD / "link-fibers.json")
    require(
        digest(OLD / "link-fibers.json")
        == summary["input_hashes"][str((OLD / "link-fibers.json").relative_to(ROOT))],
        "original fiber pin",
    )
    extra_pins[str((OLD / "link-fibers.json").relative_to(ROOT))] = digest(OLD / "link-fibers.json")
    expanded_fibers = read(EXPANDED / "link-fibers.json")
    original_stream = (
        ROOT
        / "experiments/scratch/circulant-chosen-link-row-propagation-full-v1.0.0/survivors.jsonl.gz"
    )
    sample_stream = ROOT / "experiments/scratch/affine-expanded-benchmark-v1.0.0/survivors.jsonl.gz"
    expected_cases = []
    for stream_path, kind, expected_count in (
        (original_stream, "original", 1096),
        (sample_stream, "expanded_sample", 25),
    ):
        with gzip.open(stream_path, "rt") as stream:
            inputs = [json.loads(line) for line in stream]
        require(len(inputs) == expected_count, "complete input substream")
        require(
            len({(row["pair_ordinal"], row["partial_id"], row["profile_id"]) for row in inputs})
            == len(inputs),
            "distinct input identities",
        )
        expected_cases.extend(
            {
                "catalog": kind,
                **{key: row[key] for key in ("pair_ordinal", "partial_id", "profile_id")},
            }
            for row in inputs
        )
    old_partials = read(OLD / "partial-catalog.json")
    profiles = read(OLD / "profiles.json")
    catalog_bytes = gzip.decompress((ROOT / summary["catalog_path"]).read_bytes())
    require(
        len(catalog_bytes) == summary["catalog_uncompressed_bytes"] == 196992 * 40,
        "fixed binary catalog size",
    )
    require(
        sha256(catalog_bytes).hexdigest() == summary["catalog_uncompressed_sha256"],
        "uncompressed catalog hash",
    )
    all_columns = columns()
    outcomes, checked, sample_bad, sample_good = Counter(), [], None, None
    for actual, expected in zip(result["results"], expected_cases, strict=True):
        identity(actual, expected)
        expanded = actual["catalog"] == "expanded_sample"
        pair_binding(actual, expanded_fibers if expanded else old_fibers, expanded)
        if expanded:
            require(0 <= actual["partial_id"] < 196992, "expanded partial range")
            ids = list(struct.unpack_from("<20H", catalog_bytes, actual["partial_id"] * 40))
        else:
            partial = old_partials[actual["partial_id"]]
            require(partial["partial_id"] == actual["partial_id"], "original partial index")
            ids = partial["global_block_ids"]
        require(0 <= actual["profile_id"] < 1300, "profile index")
        demands, eligible, rhs = row_system(ids, profiles[actual["profile_id"]], all_columns)
        require(
            type(actual["eligible_count"]) is int and actual["eligible_count"] == len(eligible),
            "eligible column count",
        )
        if actual["outcome"] == "parity_contradiction":
            certificate(actual["xor_rows"], eligible, rhs)
            last_row = max(actual["xor_rows"])
            before = (1 << last_row) - 1
            basis = basis_for_columns(eligible, before)
            require(reduce_rhs(rhs & before, basis) == 0, "earlier row prefix is consistent")
            require(
                type(actual["rank_before_contradiction"]) is int
                and actual["rank_before_contradiction"] == len(basis),
                "rank before first contradiction",
            )
            rank = len(basis)
            if sample_bad is None:
                sample_bad = actual, eligible, rhs
        else:
            require(actual["outcome"] == "parity_consistent", "known parity outcome")
            basis = basis_for_columns(eligible)
            require(reduce_rhs(rhs, basis) == 0, "RHS belongs to eligible column space")
            require(
                type(actual["rank"]) is int and actual["rank"] == len(basis),
                "independent matrix rank",
            )
            rank = len(basis)
            if sample_good is None:
                sample_good = actual, eligible, rhs
        outcomes[(actual["catalog"], actual["outcome"])] += 1
        checked.append(
            {
                **expected,
                "outcome": actual["outcome"],
                "eligible_columns": len(eligible),
                "rank_checked": rank,
                "certificate_row_count": len(actual.get("xor_rows", [])),
            }
        )
    require(
        outcomes
        == Counter(
            {
                ("original", "parity_contradiction"): 484,
                ("original", "parity_consistent"): 612,
                ("expanded_sample", "parity_contradiction"): 21,
                ("expanded_sample", "parity_consistent"): 4,
            }
        ),
        "complete outcome census",
    )
    damages = damage_controls(sample_bad, sample_good)
    save(HERE / "case-replay.json", checked)
    selected = {
        str(row["pair_ordinal"]): row["outcome"]
        for row in checked
        if row["catalog"] == "original" and row["pair_ordinal"] in (55433, 48366, 51739, 135193)
    }
    require(
        selected
        == {
            "55433": "parity_consistent",
            "48366": "parity_contradiction",
            "51739": "parity_contradiction",
            "135193": "parity_contradiction",
        },
        "held pilot cases",
    )
    receipt = {
        "passed": True,
        "checker_sha256": digest(Path(__file__)),
        "producer_result_sha256": PINS["result.json"],
        "producer_manifest_sha256": PINS["manifest.json"],
        "executed_source_sha256": PINS["executed-source.txt"],
        "original_survivor_audit_sha256": AUDIT_SHA,
        "input_pins": manifest["inputs"],
        "extra_pins": extra_pins,
        "complete_input_cases": 1121,
        "completion_columns_reconstructed": 3003,
        "exact_rows_reconstructed": 456,
        "contradiction_certificates_checked": 505,
        "consistent_systems_independently_checked": 616,
        "original_outcomes": {"parity_contradiction": 484, "parity_consistent": 612},
        "expanded_sample_outcomes": {"parity_contradiction": 21, "parity_consistent": 4},
        "rank_metadata_checked": True,
        "case_replay_sha256": digest(HERE / "case-replay.json"),
        "held_completion_case_outcomes": selected,
        "damaged_controls_rejected": damages,
        "producer_elapsed_seconds": result["elapsed_seconds"],
        "producer_cooperative_seconds": 10,
        "producer_imports": 0,
        "producer_reruns": 0,
        "optimizer_calls": 0,
        "scope": "505 exact profile/partial completion exclusions. The 616 consistent systems "
        "satisfy only a necessary mod-two condition; no full cover or global exclusion.",
    }
    save(HERE / "review.json", receipt)
    print(
        json.dumps(
            {
                "passed": True,
                "contradictions_checked": 505,
                "consistent_checked": 616,
                "damaged_controls": len(damages),
                "review_sha256": digest(HERE / "review.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
