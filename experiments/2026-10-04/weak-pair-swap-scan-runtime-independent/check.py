# Document:    Independent One-Swap Runtime Postcheck
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e67f9adf1db2b8e9cf0ce0d8d12251aec9f6356e85ae4cf56e80e5e4a920d682
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Read-only runtime audit; reconstruct saved families without repeating the scan."""

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRODUCER = HERE.parent / "weak-pair-swap-scan"
AUDIT = HERE.parent / "weak-pair-swap-scan-independent"
RAW = ROOT / "experiments/scratch/weak-pair-swap-scan-20261004"
MANIFEST_SHA = "71c0586872f86f4b367cf410beb6718707266bc55463f84aaf095513ac601764"
GATE_SHA = "3f6247263cb75a0258357e2e356158388fad434e8b89bb6c9210f9871adc889c"


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
            "total": 275456,
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
        "evaluated",
        "legal",
        "strictly_improving_neighbors",
        "strict_improvement_records",
        "best_ties",
    ):
        require(type(final[key]) is int and final[key] >= 0, "counter type/range")
    require(final["total"] == 64 * 4304 == 275456, "neighborhood size")
    require(
        0
        <= final["strict_improvement_records"]
        <= final["strictly_improving_neighbors"]
        <= final["legal"]
        <= final["evaluated"]
        <= 275456,
        "counter ordering",
    )
    require(
        final["complete"]
        == (final["evaluated"] == 275456)
        == (result["returncode"] == 0)
        == (final["reason"] == "complete"),
        "completion mismatch",
    )
    require(result["returncode"] in (0, 1), "native exit")
    require(final["reason"] in ("complete", "time_limit", "interrupted"), "terminal reason")
    require(
        type(final["seconds"]) in (int, float)
        and 0 <= final["seconds"] <= result["elapsed_seconds"] + 1,
        "native time",
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
    oracle = load("independent_runtime_oracle", AUDIT / "oracle.py")
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
    outgoing_rank = {v: i for i, v in enumerate(initial)}
    incoming_rank = {v: i for i, v in enumerate(i for i in range(4368) if i not in original)}
    require(len(outgoing_rank) == 64 and len(incoming_rank) == 4304, "enumeration axes")
    producer_rows = {(r["outgoing"], r["incoming"]): r for r in saved["audited_families"]}
    require(len(producer_rows) == len(saved["audited_families"]), "duplicate audit family")
    checked = {}

    def verify(row):
        outgoing, incoming = row["outgoing"], row["incoming"]
        require(type(outgoing) is int and type(incoming) is int, "swap ID types")
        require(outgoing in outgoing_rank and incoming in incoming_rank, "swap roles")
        ordinal = outgoing_rank[outgoing] * 4304 + incoming_rank[incoming] + 1
        require(ordinal <= final["evaluated"], "record beyond scanned prefix")
        key = (outgoing, incoming)
        if key not in checked:
            ids = sorted((original - {outgoing}) | {incoming})
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
            witness = HERE / f"swap-{outgoing}-{incoming}.txt"
            require(not witness.exists(), "preserve independent witness")
            witness.write_text(text)
            digest = sha(witness)
            require(
                digest == package["canonical_sha256"] == standalone["canonical_sha256"],
                "canonical family mismatch",
            )
            producer = producer_rows[key]
            require(
                producer["sha256"] == producer["canonical_sha256"] == digest
                and producer["metrics"] == actual
                and producer["ordinal"] == ordinal,
                "producer saved receipt disagreement",
            )
            require(
                producer["package_valid"] == producer["standalone_valid"] == (not holes),
                "producer covering label",
            )
            checked[key] = {
                "outgoing": outgoing,
                "incoming": incoming,
                "ordinal": ordinal,
                "path": str(witness.relative_to(ROOT)),
                "sha256": digest,
                "metrics": actual,
                "package": package,
                "standalone": standalone,
            }
        require(checked[key]["metrics"] == row["metrics"], "repeated record differs")
        return checked[key]

    baseline_rank = (base["metrics"]["holes"], base["metrics"]["D2max"])
    previous_rank, previous_ordinal, previous_seconds = baseline_rank, 0, 0.0
    for record in records:
        row = verify(record)
        rank = (row["metrics"]["holes"], row["metrics"]["D2max"])
        require(
            rank < previous_rank
            and record["evaluated"] == row["ordinal"]
            and row["ordinal"] > previous_ordinal,
            "record rank/ordinal regression",
        )
        require(previous_seconds <= record["seconds"] <= final["seconds"], "record time")
        previous_rank, previous_ordinal, previous_seconds = rank, row["ordinal"], record["seconds"]
    require(list(previous_rank) == final["best_rank"], "terminal rank")
    tie_keys = [(row["outgoing"], row["incoming"]) for row in ties]
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
        "full_enumeration_relaunches": 0,
        "solver_launches": 0,
        "final": final,
        "budget": result["budget"],
        "elapsed_seconds": result["elapsed_seconds"],
        "baseline_rank": baseline_rank,
        "complete_neighborhood": final["complete"],
        "checked_family_count": len(checked),
        "all_saved_families": list(checked.values()),
        "best_ties": tie_rows,
        "enumeration_evidence": (
            "Frozen audited nested loops, fixed64/4304 axes, terminal count, "
            "normal exit, and unique swap ordinals."
        ),
        "limitation": (
            "Unrecorded trial metrics are not individually recomputed; "
            "no second enumeration was run. The result applies only to the "
            "pinned one-swap neighborhood and legal filters."
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
