# Document:    Independent Full Chosen Link Support Certificate Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      df0525cd31e72642ddaa912eb14a7e3977976bb8a633aa83b7ca489b15d4288e
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check every saved proof and survivor with independently built row carriers."""

import copy
import gzip
import hashlib
import itertools
import json
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FULL = HERE.parent / "circulant-chosen-link-support-full"
WRAPPER = HERE.parent / "circulant-chosen-link-independent"
CATALOG = HERE.parent / "circulant-chosen-link-catalog"
GATE = HERE.parent / "circulant-chosen-link-support-independent/gate.json"
RESULT_SHA = "aabd7d06c2a2b297b69086676e12a68ccfd6a532dcf5ea3aeca53d42fde958e3"
GATE_SHA = "5a19e29f6dec86514298dc00dc8e6bebaee3b21a0fb38a7bbf39dfa662ba1fa1"
MANIFEST_SHA = "2c12c4372ef388026d7a6238b7789f72ad8dcaf74ba471035cb2dcdf86dc4439"
PROOF_SHA = "632e8a7b23ef267323b3f414a8fd9ab7918973ec6913aba7045e9c915a283f6b"
SURVIVOR_SHA = "8914b935b63ccea864ab51f5d0837efcb0eed093b4bbdfc577ecdb2fc0ac2a0c"
BLOCKS = tuple(itertools.combinations(range(1, 17), 5))
TRIPLES = tuple(itertools.combinations(range(2, 17), 3))
RANK = {t: i for i, t in enumerate(TRIPLES)}
TOTAL = 195296
CHECK_SECONDS = 120


def require(test, message):
    if not test:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same(actual, expected, message):
    require(json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True), message)


def ids_mask(ids):
    require(
        isinstance(ids, list) and all(type(i) is int and 1365 <= i < 4368 for i in ids),
        "candidate IDs",
    )
    require(ids == sorted(set(ids)), "distinct ordered candidate IDs")
    return sum(1 << (i - 1365) for i in ids)


def prepare_data():
    # Invert the producer's construction: enumerate all pairs of extra points
    # for each triple, rather than enumerate triples inside candidate blocks.
    block_rank = {block: i for i, block in enumerate(BLOCKS)}
    row_carriers = []
    for triple in TRIPLES:
        outside = sorted(set(range(2, 17)) - set(triple))
        ids = [
            block_rank[tuple(sorted((*triple, *pair)))]
            for pair in itertools.combinations(outside, 2)
        ]
        require(
            len(ids) == len(set(ids)) == 66 and min(ids) >= 1365, "complete inverse triple carriers"
        )
        row_carriers.append(ids_mask(sorted(ids)))
    require(
        all(sum((row >> i) & 1 for row in row_carriers) == 10 for i in range(3003)),
        "each residual candidate has ten triples",
    )
    partials = json.loads((CATALOG / "partial-catalog.json").read_text())
    profiles = json.loads((CATALOG / "profiles.json").read_text())
    fibers = json.loads((CATALOG / "link-fibers.json").read_text())
    partial_rows = []
    for partial in partials:
        require(len(partial["global_block_ids"]) == 20, "fixed block count")
        require(
            all(BLOCKS[i][0] == 1 for i in partial["global_block_ids"]), "fixed point-one blocks"
        )
        counts = Counter(
            t
            for i in partial["global_block_ids"]
            for t in itertools.combinations(BLOCKS[i], 3)
            if 1 not in t
        )
        require(len(counts) == 80 and set(counts.values()) == {1}, "outside fixed multiplicities")
        partial_rows.append(frozenset(RANK[t] for t in counts))
    profile_rows = []
    for profile in profiles:
        rows = {RANK[tuple(t)] for t in profile["excess_triples"] if 1 not in t}
        require(len(rows) == 65, "outside excess triples")
        profile_rows.append(rows)
    pairs = [
        (partial, profile)
        for fiber in fibers
        for partial in range(*fiber["partial_id_range_half_open"])
        for profile in fiber["profile_ids"]
    ]
    require(len(pairs) == len(set(pairs)) == TOTAL, "complete pair domain")
    return row_carriers, partial_rows, profile_rows, pairs


def check_record(record, ordinal, data):
    row_carriers, partial_rows, profile_rows, pairs = data
    require(
        type(record["pair_ordinal"]) is int and record["pair_ordinal"] == ordinal,
        "complete prefix ordinal",
    )
    partial, profile = pairs[ordinal]
    require(record["partial_id"] == partial and record["profile_id"] == profile, "case identity")
    fixed = partial_rows[partial]
    excess = profile_rows[profile]
    zeros = fixed - excess
    eligible = (1 << 3003) - 1
    for row in zeros:
        eligible &= ~row_carriers[row]
    require(
        record["initial_domain_count"] == 3003
        and record["eligible_candidates"] == eligible.bit_count(),
        "eligible domain count",
    )
    require(
        record["eligible_mask_sha256"]
        == hashlib.sha256(eligible.to_bytes(376, "little")).hexdigest(),
        "eligible domain hash",
    )

    def demand(row):
        return 44 if row == 455 else 1 + int(row in excess) - int(row in fixed)

    def support(row):
        return eligible if row == 455 else eligible & row_carriers[row]

    outcome = record["outcome"]
    if outcome in ("insufficient_support", "forced_conflict"):
        row = record["row"]
        require(type(row) is int and 0 <= row <= 455, "contradiction row index")
        require(
            type(record["demand"]) is int and record["demand"] == demand(row),
            "contradiction demand",
        )
        if row < 455:
            same(record["triple"], list(TRIPLES[row]), "contradiction triple")
        if outcome == "insufficient_support":
            actual_support = ids_mask(record["support_global_ids"])
            require(actual_support == support(row), "complete failed-row support")
            require(actual_support.bit_count() < demand(row), "actual support deficiency")
        else:
            selected = ids_mask(record["forced_global_ids"])
            require(selected & ~support(row) == 0, "forced conflict variables are in row")
            require(selected.bit_count() > demand(row), "actual forced excess")
            evidence = record["forcing_rows"]
            same(
                [e["global_block_id"] for e in evidence],
                record["forced_global_ids"],
                "all forcing causes",
            )
            for cause in evidence:
                origin = cause["row"]
                require(type(origin) is int and 0 <= origin <= 455, "forcing row index")
                require(
                    type(cause["demand"]) is int and cause["demand"] == demand(origin),
                    "forcing demand",
                )
                required = ids_mask(cause["support_global_ids"])
                require(
                    required == support(origin) and required.bit_count() == demand(origin),
                    "tight support forces every member",
                )
                require(
                    (required >> (cause["global_block_id"] - 1365)) & 1,
                    "forced member belongs to cause",
                )
    elif outcome == "survives_single_pass":
        require(eligible.bit_count() >= 44, "survivor cardinality support")
        forced = eligible if eligible.bit_count() == 44 else 0
        for row in range(455):
            available = support(row)
            require(available.bit_count() >= demand(row), "survivor all row supports")
            if available.bit_count() == demand(row):
                forced |= available
        require(forced.bit_count() <= 44, "survivor forced cardinality")
        require(
            all((forced & row_carriers[row]).bit_count() <= demand(row) for row in range(455)),
            "survivor all immediate forced conflicts",
        )
        require(record["immediately_forced_blocks"] == forced.bit_count(), "survivor forced count")
    else:
        raise ValueError("unknown outcome")
    return outcome


def main():
    started = time.monotonic()
    require(
        sha(FULL / "result.json") == RESULT_SHA and sha(GATE) == GATE_SHA, "result and gate pins"
    )
    require(sha(FULL / "manifest.json") == MANIFEST_SHA, "manifest pin")
    manifest = json.loads((FULL / "manifest.json").read_text())
    for path, digest in manifest["dependencies"].items():
        require(sha(ROOT / path) == digest, "frozen dependency " + path)
    gate = json.loads(GATE.read_text())
    require(sha(ROOT / gate["external_wrapper"]) == gate["external_wrapper_sha256"], "wrapper pin")
    require(
        sha(WRAPPER / "catalog-audit.json") == gate["catalog_audit_sha256"], "catalog audit pin"
    )
    wrapper = json.loads((WRAPPER / "full-runtime.json").read_text())
    result = json.loads((FULL / "result.json").read_text())
    require(
        sha(FULL / "run.py") == manifest["source_sha256"] == result["source_sha256"],
        "full producer source unchanged",
    )
    require(wrapper["source_sha256"] == gate["external_wrapper_sha256"], "actual wrapper source")
    require(
        wrapper["manifest_sha256"] == result["manifest_sha256"] == MANIFEST_SHA,
        "runtime manifest binding",
    )
    same(wrapper["command"][1:], [str(FULL / "run.py"), "run"], "actual child command")
    require(
        result["full_passes"] == 1
        and result["iterative_propagation_launched"] is False
        and result["optimizer_calls"] == 0,
        "single arithmetic pass only",
    )
    require(
        wrapper["child_result_sha256"] == RESULT_SHA and wrapper["gate_sha256"] == GATE_SHA,
        "runtime identity",
    )
    require(
        wrapper["returncode"] == 0
        and all(wrapper[k] is False for k in ("watchdog", "terminated", "killed")),
        "normal process completion",
    )
    require(wrapper["elapsed_includes_child_hashing_and_outputs"] is True, "whole child elapsed")
    require(wrapper["child_process_elapsed_seconds"] < 50, "external runtime budget")
    for stream in ("stdout", "stderr"):
        require(
            sha(WRAPPER / ("full-" + stream + ".log")) == wrapper[stream + "_sha256"],
            "captured stream pin",
        )
    same(json.loads((WRAPPER / "full-stdout.log").read_text()), result, "captured producer result")
    require((WRAPPER / "full-stderr.log").read_text() == "", "clean producer stderr")
    require(
        result["complete"] is True
        and result["completed_cases"] == result["next_pair_ordinal"] == TOTAL,
        "producer complete cursor",
    )
    same(result["completed_prefix"], [0, TOTAL], "producer complete prefix")
    proof_path, survivor_path = ROOT / result["proof_records"], ROOT / result["survivor_records"]
    require(sha(proof_path) == result["proof_records_sha256"] == PROOF_SHA, "proof record pin")
    require(
        sha(survivor_path) == result["survivor_records_sha256"] == SURVIVOR_SHA,
        "survivor record pin",
    )
    data = prepare_data()
    outcomes, operations = Counter(), Counter()
    survivors, examples = [], {}
    completed = 0
    with gzip.open(proof_path, "rt") as handle:
        for ordinal, line in enumerate(handle):
            if time.monotonic() - started > CHECK_SECONDS:
                break
            require(ordinal < TOTAL, "no extra proof records")
            record = json.loads(line)
            outcome = check_record(record, ordinal, data)
            outcomes[outcome] += 1
            operations.update(record["operation_counts"])
            examples.setdefault(outcome, record)
            if outcome == "survives_single_pass":
                survivors.append(
                    {key: record[key] for key in ("pair_ordinal", "partial_id", "profile_id")}
                )
            completed += 1
            if completed % 50000 == 0:
                print(json.dumps({"verified_cases": completed}), flush=True)
    complete = completed == TOTAL
    if complete:
        same(dict(outcomes), result["outcomes"], "all independently checked outcomes")
        same(dict(operations), result["operation_counts"], "saved operation accounting")
        with gzip.open(survivor_path, "rt") as handle:
            saved_survivors = [json.loads(line) for line in handle]
        same(saved_survivors, survivors, "complete independently checked survivor file")
    controls = {}
    changes = {
        "wrong_row_demand": ("insufficient_support", lambda r: r.__setitem__("demand", 3)),
        "missing_support": ("insufficient_support", lambda r: r["support_global_ids"].clear()),
        "wrong_domain_hash": (
            "insufficient_support",
            lambda r: r.__setitem__("eligible_mask_sha256", "0" * 64),
        ),
        "changed_forcing_demand": (
            "forced_conflict",
            lambda r: r["forcing_rows"][0].__setitem__("demand", 44),
        ),
        "missing_forcing_support": (
            "forced_conflict",
            lambda r: r["forcing_rows"][0]["support_global_ids"].pop(),
        ),
        "wrong_survivor_count": (
            "survives_single_pass",
            lambda r: r.__setitem__("immediately_forced_blocks", -1),
        ),
    }
    for name, (kind, change) in changes.items():
        damaged = copy.deepcopy(examples[kind])
        change(damaged)
        try:
            check_record(damaged, damaged["pair_ordinal"], data)
        except ValueError:
            controls[name] = "rejected"
        else:
            raise ValueError("damaged certificate accepted: " + name)
    audit = {
        "passed": True,
        "complete_replay": complete,
        "cases_verified": completed,
        "verified_prefix": [0, completed],
        "requested_cases": TOTAL,
        "result_sha256": RESULT_SHA,
        "gate_sha256": GATE_SHA,
        "manifest_sha256": MANIFEST_SHA,
        "proof_records_sha256": PROOF_SHA,
        "survivor_records_sha256": SURVIVOR_SHA,
        "wrapper_runtime_sha256": sha(WRAPPER / "full-runtime.json"),
        "checker_sha256": sha(Path(__file__)),
        "outcomes": dict(outcomes),
        "survivors_verified": len(survivors),
        "true_producer_elapsed_seconds": wrapper["child_process_elapsed_seconds"],
        "replay_elapsed_seconds": time.monotonic() - started,
        "replay_cooperative_budget_seconds": CHECK_SECONDS,
        "damage_controls": controls,
        "producer_rerun": False,
        "optimizer_calls": 0,
        "scope": "All saved chosen-link records; no feasibility claim.",
    }
    (HERE / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "audit_sha256": sha(HERE / "audit.json"),
                "complete": complete,
                "verified": completed,
                "outcomes": dict(outcomes),
            }
        )
    )


if __name__ == "__main__":
    main()
