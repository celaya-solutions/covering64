# Document:    Independent Two-Swap V2 Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      416d5fedaa723fa488ec6cb8ce5df0ac67b54965a44b1d5fdcfd53bc3f490d02
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read-only runtime audit; reconstruct saved families without repeating the scan."""

import hashlib
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-two-swap-scan-v2"
AUDIT = HERE.parent / "weak-pair-two-swap-scan-v2-independent"
RAW = ROOT / "experiments/scratch/weak-pair-two-swap-scan-v2-20261004"
MANIFEST_SHA = "0f006df5844a67bf5595378e8dc156890a117ecab613b5e2ead9f74b463d9287"
GATE_SHA = "77c9f3fa9eccfb89229be8d9a09bdc4e26e64a0a296b19af44179473059a9a64"

INNER = math.comb(4304, 2)
OUTERS = math.comb(64, 2) * 4304
TOTAL = math.comb(64, 2) * INNER


def shell_started(count):
    groups, remainder = divmod(count, 4304)
    return groups * INNER + sum(4303 - i for i in range(remainder))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    output = HERE / "postcheck.json"
    require(not output.exists(), "preserve runtime receipt")
    require(sha(PRODUCER / "manifest.json") == MANIFEST_SHA, "manifest changed")
    require(sha(AUDIT / "gate.json") == GATE_SHA, "pre-run gate changed")
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    gate = json.loads((AUDIT / "gate.json").read_text())
    require(gate["passed"] is True and gate["decision"] == "GO", "gate decision")
    require(gate["manifest_sha256"] == MANIFEST_SHA, "gate manifest binding")
    require(sha(ROOT / gate["proof_path"]) == gate["proof_sha256"], "pruning proof changed")
    for binding in gate["artifact_bindings"]:
        require(sha(ROOT / binding["path"]) == binding["sha256"], "gate artifact changed")
    for relative, digest in gate["raw_files"].items():
        require(sha(ROOT / relative) == digest, "gate raw file changed")
    result_path = PRODUCER / "result.json"
    result = json.loads(result_path.read_text())
    require(
        result["manifest_sha256"] == MANIFEST_SHA and result["gate_sha256"] == GATE_SHA,
        "runtime binding mismatch",
    )
    for group in ("source_files", "input_files", "raw_files"):
        for relative, digest in manifest[group].items():
            require(sha(ROOT / relative) == digest, f"producer binding changed: {relative}")
    for relative, digest in result["raw_files"].items():
        require(sha(ROOT / relative) == digest, f"runtime binding changed: {relative}")
    for name, digest in gate["independent_sources"].items():
        require(sha(AUDIT / name) == digest, f"gate source changed: {name}")
    require(sha(RAW / "frozen-sources/manifest.json") == MANIFEST_SHA, "frozen manifest")
    require(sha(RAW / "frozen-sources/gate.json") == GATE_SHA, "frozen gate")
    for relative, digest in manifest["source_files"].items():
        require(sha(RAW / "frozen-sources" / Path(relative).name) == digest, "frozen source")
    require(result["validation_passed"] is True, "producer validation failed")
    require(result["passes"] == 1 and result["seed"] is None, "campaign multiplicity")
    require(result["budget"] == manifest["budget"] == gate["budget"], "budget changed")
    require(all(type(v) is bool for v in result["watchdog"].values()), "watchdog types")
    require(not any(result["watchdog"].values()), "watchdog or relaunch occurred")
    require(
        result["command"]
        == [
            str(ROOT / manifest["binary_path"]),
            str(ROOT / manifest["initial"]["path"]),
            "120",
            str(RAW / "scan"),
        ],
        "runtime command changed",
    )
    require(0 <= result["elapsed_seconds"] <= 140.5, "wall budget")
    start_receipt = json.loads((RAW / "start.json").read_text())
    require(
        start_receipt["manifest_sha256"] == MANIFEST_SHA
        and start_receipt["gate_sha256"] == GATE_SHA
        and start_receipt["budget"] == manifest["budget"],
        "launch receipt mismatch",
    )
    require(not (RAW / "stderr.txt").read_text(), "native stderr")
    events = [json.loads(line) for line in (RAW / "stdout.jsonl").read_text().splitlines()]
    require(
        events[0]
        == {
            "event": "start",
            "budget_seconds": 120,
            "total": TOTAL,
            "outer_total": OUTERS,
            "control_limit": None,
            "baseline": manifest["initial"]["metrics"],
        },
        "native start mismatch",
    )
    final = events[-1]
    require(final == result["final"] and final["event"] == "final", "terminal log mismatch")
    require(type(final["complete"]) is bool, "completion type")
    for key in (
        "total",
        "outer_total",
        "outer_started",
        "outer_completed",
        "evaluated",
        "pair_floor_pruned",
        "eligible_generated",
        "pending_eligible",
        "accounted",
        "last_evaluated_ordinal",
        "legal",
        "strictly_improving_neighbors",
        "strict_improvement_records",
        "best_ties",
    ):
        require(type(final[key]) is int and final[key] >= 0, "counter type/range")
    require(final["total"] == TOTAL == 18668272896, "exact-distance-two shell size")
    require(final["outer_total"] == OUTERS == 8676864, "outer size")
    require(
        0
        <= final["strict_improvement_records"]
        <= final["strictly_improving_neighbors"]
        <= final["legal"]
        <= final["evaluated"]
        <= TOTAL,
        "counter ordering",
    )
    require(final["best_ties"] <= final["strictly_improving_neighbors"], "tie count bounds")
    require(
        0 <= final["outer_completed"] <= final["outer_started"] <= OUTERS,
        "outer count ordering",
    )
    gap = final["outer_started"] - final["outer_completed"]
    started = shell_started(final["outer_started"])
    require(gap in (0, 1), "too many unfinished outers")
    require((gap == 1) == (final["pending_eligible"] > 0), "pending/outer gap mismatch")
    if gap:
        tail = 4303 - ((final["outer_started"] - 1) % 4304)
        require(final["pending_eligible"] <= tail, "pending beyond current outer tail")
    require(
        final["accounted"] == final["pair_floor_pruned"] + final["evaluated"] <= TOTAL,
        "accounted mismatch",
    )
    require(
        final["eligible_generated"] == final["evaluated"] + final["pending_eligible"],
        "eligible count mismatch",
    )
    require(
        final["pair_floor_pruned"] + final["eligible_generated"] == started,
        "started shell mismatch",
    )
    require(
        0 <= final["last_evaluated_ordinal"] <= started
        and bool(final["last_evaluated_ordinal"]) == bool(final["evaluated"]),
        "last evaluated ordinal range",
    )
    for key in ("support_bins", "support_shell_bins"):
        require(
            type(final[key]) is list
            and len(final[key]) == 8
            and all(type(n) is int and n >= 0 for n in final[key]),
            "support bin type/range",
        )
    require(final["support_bins"][3] == final["support_shell_bins"][3] == 0, "size-one support")
    require(sum(final["support_bins"]) == final["outer_started"], "outer bin sum")
    require(sum(final["support_shell_bins"]) == started, "shell bin sum")
    require(
        all(
            s <= 4303 * n
            for s, n in zip(final["support_shell_bins"], final["support_bins"], strict=True)
        ),
        "shell bin overflow",
    )
    require(
        sum(final["support_shell_bins"][:2]) <= final["pair_floor_pruned"],
        "impossible-support pruning count",
    )
    require(
        final["complete"]
        == (final["outer_completed"] == OUTERS)
        == (result["returncode"] == 0)
        == (final["reason"] == "complete"),
        "completion mismatch",
    )
    if final["complete"]:
        require(final["accounted"] == TOTAL and final["pending_eligible"] == 0, "complete shell")
    require(type(result["returncode"]) is int and result["returncode"] in (0, 1), "native exit")
    require(final["reason"] in ("complete", "time_limit", "interrupted"), "terminal reason")
    require(
        type(final["seconds"]) in (int, float)
        and math.isfinite(final["seconds"])
        and 0 <= final["seconds"] <= result["elapsed_seconds"] + 1,
        "native time",
    )
    require(
        type(final["best_rank"]) is list
        and len(final["best_rank"]) == 2
        and all(type(n) is int and n >= 0 for n in final["best_rank"]),
        "rank type/range",
    )
    if final["reason"] == "time_limit":
        require(final["seconds"] >= 120, "false early timeout")
    require(all(row["event"] == "improvement" for row in events[1:-1]), "unknown event")
    records = events[1:-1]
    require(len(records) == final["strict_improvement_records"], "record count")
    require([r["serial"] for r in records] == list(range(1, len(records) + 1)), "record serials")
    ties = json.loads((RAW / "scan-ties.json").read_text())
    require(len(ties) == final["best_ties"], "tie count")
    require(
        sha(ROOT / result["candidate_audit_path"]) == result["candidate_audit_sha256"],
        "producer candidate audit changed",
    )
    saved = json.loads((ROOT / result["candidate_audit_path"]).read_text())
    require(
        saved["passed"] is True
        and saved["final"] == final
        and saved["strict_improvements"] == records,
        "candidate audit/log disagreement",
    )
    oracle_path = HERE.parent / "weak-pair-swap-scan-independent/oracle.py"
    oracle = load("independent_runtime_oracle", oracle_path)
    sys.path.insert(0, str(ROOT / "src"))
    from covering64.core import verify_cover

    separate = load("standalone_runtime_verifier", ROOT / "scripts/check_cover.py")
    initial = oracle.parse(ROOT / manifest["initial"]["path"])
    require(initial == manifest["initial"]["ids"], "initial IDs")
    base = oracle.analyze(initial, manifest["core_rows"])
    require(
        base["legal"] and base["metrics"] | {"cardinality": 64} == manifest["initial"]["metrics"],
        "initial recount",
    )
    original = set(initial)
    pairs = list(itertools.combinations(initial, 2))
    absent = [i for i in range(4368) if i not in original]
    require(len(pairs) == 2016 and len(absent) == 4304, "enumeration axes")
    producer_rows = {tuple(r["outgoing"] + r["incoming"]): r for r in saved["audited_families"]}
    require(len(producer_rows) == len(saved["audited_families"]), "duplicate audit family")
    family_hashes = {}
    checked = {}

    def verify(row):
        outgoing, incoming = row["outgoing"], row["incoming"]
        require(type(outgoing) is list and type(incoming) is list, "exchange list types")
        require(len(outgoing) == len(incoming) == 2, "exchange size")
        require(all(type(i) is int and 0 <= i < 4368 for i in outgoing + incoming), "ID types")
        require(outgoing == sorted(set(outgoing)) and incoming == sorted(set(incoming)), "ID order")
        require(set(outgoing) <= original and not set(incoming) & original, "exchange roles")
        pair_index = pairs.index(tuple(outgoing))
        ai, di = (absent.index(i) for i in incoming)
        ordinal = pair_index * INNER + sum(4303 - j for j in range(ai)) + di - ai
        outer = pair_index * 4304 + ai + 1
        require(type(row["shell_ordinal"]) is int and row["shell_ordinal"] == ordinal, "ordinal")
        require(
            ordinal <= final["last_evaluated_ordinal"] and outer <= final["outer_started"],
            "record beyond scanned prefix",
        )
        key = tuple(outgoing + incoming)
        if key not in checked:
            ids = sorted((original - set(outgoing)) | set(incoming))
            direct = oracle.analyze(ids, manifest["core_rows"])
            actual = direct["metrics"] | {"cardinality": 64}
            require(direct["legal"] and actual == row["metrics"], "saved family legality/metrics")
            blocks = [oracle.SUBSETS[5][i] for i in ids]
            package = verify_cover(blocks, 16, 5, 3)
            standalone = separate.verify_cover(blocks, 16, 5, 3, expected_blocks=64)
            holes = [
                list(oracle.SUBSETS[3][i])
                for i, count in enumerate(direct["counts"][3])
                if count == 0
            ]
            require(
                sorted(map(list, package["uncovered"])) == holes == standalone["uncovered"],
                "verifier hole mismatch",
            )
            require(package["valid"] == standalone["valid"] == (not holes), "cover verdict")
            text = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
            witness = HERE / ("swap-" + "-".join(map(str, key)) + ".txt")
            require(not witness.exists(), "preserve independent witness")
            witness.write_text(text)
            digest = sha(witness)
            require(
                digest == package["canonical_sha256"] == standalone["canonical_sha256"],
                "canonical family mismatch",
            )
            require(digest not in family_hashes, "distinct exchange aliases same family")
            family_hashes[digest] = key
            producer = producer_rows[key]
            require(
                producer["sha256"] == producer["canonical_sha256"] == digest
                and producer["metrics"] == actual
                and producer["shell_ordinal"] == ordinal,
                "producer saved receipt disagreement",
            )
            require(
                producer["package_valid"] == producer["standalone_valid"] == (not holes),
                "producer covering label",
            )
            checked[key] = {
                "outgoing": outgoing,
                "incoming": incoming,
                "shell_ordinal": ordinal,
                "outer_index": outer,
                "path": str(witness.relative_to(ROOT)),
                "sha256": digest,
                "metrics": actual,
                "package": package,
                "standalone": standalone,
            }
        require(checked[key]["metrics"] == row["metrics"], "repeated record differs")
        return checked[key]

    baseline_rank = (base["metrics"]["holes"], base["metrics"]["D2max"])
    previous_rank, previous_ordinal, previous_evaluated, previous_seconds = baseline_rank, 0, 0, 0.0
    for record in records:
        row = verify(record)
        rank = (row["metrics"]["holes"], row["metrics"]["D2max"])
        require(
            type(record["evaluated"]) is int
            and previous_evaluated < record["evaluated"] <= final["evaluated"]
            and type(record["outer_index"]) is int
            and record["outer_index"] == row["outer_index"],
            "record evaluated count/outer index",
        )
        require(rank < previous_rank and row["shell_ordinal"] > previous_ordinal, "rank regression")
        require(
            type(record["seconds"]) in (int, float)
            and math.isfinite(record["seconds"])
            and previous_seconds <= record["seconds"] <= final["seconds"],
            "record time",
        )
        previous_rank, previous_ordinal = rank, row["shell_ordinal"]
        previous_evaluated, previous_seconds = record["evaluated"], record["seconds"]
    require(list(previous_rank) == final["best_rank"], "terminal rank")
    tie_keys = [tuple(row["outgoing"] + row["incoming"]) for row in ties]
    require(tie_keys == sorted(set(tie_keys)), "tie order/duplicates")
    require(bool(ties) == (previous_rank < baseline_rank), "missing/spurious improving ties")
    tie_rows = []
    for tie in ties:
        row = verify(tie)
        require((row["metrics"]["holes"], row["metrics"]["D2max"]) == previous_rank, "nonbest tie")
        tie_rows.append(row)
    require(set(checked) == set(producer_rows), "unaccounted saved family")
    require(
        [row["sha256"] for row in tie_rows] == result["complete_best_tie_hashes"],
        "result tie hashes",
    )
    require(
        [row["sha256"] for row in saved["best_ties"]] == [row["sha256"] for row in tie_rows],
        "audit tie hashes",
    )
    require(
        result["cover_found"] is any(row["metrics"]["holes"] == 0 for row in tie_rows),
        "cover-found label",
    )
    if tie_rows:
        require(
            sha(ROOT / result["best_representative_path"])
            == result["best_representative_sha256"]
            == tie_rows[0]["sha256"],
            "representative",
        )
        require(result["representative_standalone_cli_passed"] is True, "standalone CLI receipt")
        cli = json.loads((RAW / "representative-standalone.json").read_text())
        require(
            cli["canonical_sha256"] == tie_rows[0]["sha256"]
            and cli["uncovered_count"] == tie_rows[0]["metrics"]["holes"],
            "CLI metrics",
        )
    receipt = {
        "passed": True,
        "source_sha256": sha(Path(__file__)),
        "manifest_sha256": MANIFEST_SHA,
        "pre_run_gate_sha256": GATE_SHA,
        "producer_result_sha256": sha(result_path),
        "runtime_raw_bindings": result["raw_files"],
        "oracle_sha256": sha(oracle_path),
        "source_revision": manifest["source_revision"],
        "pruning_proof_path": gate["proof_path"],
        "pruning_proof_sha256": gate["proof_sha256"],
        "production_binary_sha256": manifest["binary_sha256"],
        "full_enumeration_relaunches": 0,
        "solver_launches": 0,
        "final": final,
        "budget": result["budget"],
        "elapsed_seconds": result["elapsed_seconds"],
        "baseline_rank": baseline_rank,
        "complete_exact_distance_two_shell": final["complete"],
        "family_aliases": 0,
        "checked_family_count": len(checked),
        "all_saved_families": list(checked.values()),
        "best_ties": tie_rows,
        "enumeration_evidence": (
            "Frozen audited exact-distance-two loops, safe pair-floor pruning proof, "
            "terminal shell accounting, normal exit, and unique exchange identities."
        ),
        "limitation": (
            "Unrecorded trial metrics are not individually recomputed; "
            "no second enumeration was run. The result applies only to the "
            "pinned exact-distance-two shell and legal filters, excluding distances zero and one."
        ),
    }
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    require(sha(AUDIT / "gate.json") == GATE_SHA, "gate mutated")
    print(
        json.dumps(
            {
                "passed": True,
                "postcheck_sha256": sha(output),
                "saved_families": len(checked),
                "best_ties": len(tie_rows),
                "complete": final["complete"],
                "best_rank": final["best_rank"],
            }
        )
    )


if __name__ == "__main__":
    main()
