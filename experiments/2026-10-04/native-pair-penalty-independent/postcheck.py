# Document:    Independent Native Pair-Penalty Outcome Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
import json
import subprocess
from collections import Counter
from itertools import combinations

from check import HERE, ROOT, SOURCE, read, sha

BLOCKS = list(combinations(range(1, 17), 5))
RANK = {b: i for i, b in enumerate(BLOCKS)}
TRIPLES = list(combinations(range(1, 17), 3))
PAIRS = list(combinations(range(1, 17), 2))
QUADS = list(combinations(range(1, 17), 4))


def forbidden(counts):
    heavy = [(sum(1 << p for p in t), int(counts[t] >= 7))
             for t in TRIPLES if counts[t] >= 6]

    def visit(start, used, number, sevens):
        if number == 5:
            return sevens >= 2
        if len(heavy) - start < 5 - number:
            return False
        return any(not used & mask and visit(i + 1, used | mask, number + 1, sevens + seven)
                   for i, (mask, seven) in enumerate(heavy[start:], start))

    return visit(0, 0, 0, 0)


def recount(path, cores):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    assert len(blocks) == len(set(blocks)) == 64 and all(b in RANK for b in blocks)
    counts = Counter(t for b in blocks for t in combinations(b, 3))
    pairs = Counter(p for b in blocks for p in combinations(b, 2))
    quads = Counter(q for b in blocks for q in combinations(b, 4))
    d3 = sum(max(0, 13 - 3 * pairs[p] + counts[t])
             for p in PAIRS for t in TRIPLES if set(p) <= set(t))
    d4 = sum(max(0, 12 - 3 * pairs[p] + 2 * quads[q])
             for p in PAIRS for q in QUADS if set(p) <= set(q))
    holes = sum(counts[t] == 0 for t in TRIPLES)
    f = forbidden(counts)
    ids = {RANK[b] for b in blocks}
    return {
        "holes": holes, "D3": d3, "D4": d4,
        "energy": 20 * holes + 5 * d3 + d4 + 160 * f,
        "pair_min": min(pairs[p] for p in PAIRS), "forbidden": f,
        "core_overlaps": [len(ids & set(core)) for core in cores],
    }


def main():
    gate, manifest, result = (read(HERE / "gate.json"), read(SOURCE / "manifest.json"),
                              read(SOURCE / "result.json"))
    assert gate["passed"] and result["gate_sha256"] == sha(HERE / "gate.json")
    assert result["manifest_sha256"] == gate["manifest_sha256"] == sha(SOURCE / "manifest.json")
    assert result["binary_sha256"] == gate["binary_sha256"]
    assert result["optimizer_calls"] == len(result["cases"]) == 2
    assert not result["global_lower_bound_claim"]
    assert [c["seed"] for c in result["cases"]] == manifest["budget"]["seeds"]
    checked, verifier_calls = [], 0
    cache = {}
    for case in result["cases"]:
        assert case["validation_error"] is None
        assert case["exit_code"] in (0, 1)
        assert case["wall_seconds"] < 76
        for path, digest in case["raw_files"].items():
            assert sha(ROOT / path) == digest
        log_path = next(ROOT / p for p in case["raw_files"] if p.endswith("stdout.jsonl"))
        events = [json.loads(line) for line in log_path.read_text().splitlines()]
        assert events[0] == {"event": "start", "seed": case["seed"], "budget": 60}
        records = [e for e in events if e["event"] == "record"]
        assert [e["serial"] for e in records] == list(range(1, len(records) + 1))
        final = events[-1]
        assert final["event"] == ("cover_found" if case["exit_code"] == 0 else "finished")
        assert final["seconds"] >= 59 and final["seconds"] < 76
        assert 0 <= final["core_rejections"] <= final["iterations"]
        observed = {}
        for index, row in enumerate(case["snapshots"]):
            path = ROOT / row["path"]
            assert sha(path) == row["sha256"]
            metrics = recount(path, manifest["core_rows"])
            assert metrics == row["metrics"]
            assert max(metrics["core_overlaps"]) <= 55
            if row["role"] != "final_current":
                assert not metrics["forbidden"]
            if row["role"] in ("qualified", "final_qualified"):
                assert metrics["D3"] == metrics["D4"] == 0
                assert metrics["pair_min"] >= 5
            if row["sha256"] not in cache:
                receipts = []
                for name, prefix in (
                    ("package", ["uv", "run", "covering64", "verify"]),
                    ("standalone", ["uv", "run", "python", "scripts/check_cover.py"]),
                ):
                    run = subprocess.run(prefix + [str(path), "--expected-blocks", "64"],
                                         cwd=ROOT, capture_output=True, text=True, check=False)
                    assert run.returncode == int(metrics["holes"] != 0) and not run.stderr
                    payload = json.loads(run.stdout)
                    assert payload["blocks"] == 64 and payload["valid"] == (metrics["holes"] == 0)
                    key = "covered" if name == "package" else "covered_subsets"
                    assert payload[key] == 560 - metrics["holes"]
                    output = HERE / f"seed-{case['seed']}-state-{index:02d}-{name}.json"
                    output.write_text(run.stdout)
                    receipts.append({"path": str(output.relative_to(ROOT)), "sha256": sha(output),
                                     "canonical_sha256": payload["canonical_sha256"]})
                    verifier_calls += 1
                assert receipts[0]["canonical_sha256"] == receipts[1]["canonical_sha256"]
                cache[row["sha256"]] = receipts
            observed[path.name] = metrics
            checked.append({"seed": case["seed"], "role": row["role"], "path": row["path"],
                            "sha256": row["sha256"], "metrics": metrics,
                            "verifiers": cache[row["sha256"]]})
        last = {}
        for record in records:
            role = record["role"]
            name = f"search-record-{record['serial']}-{role}.txt"
            assert observed[name] == record["metrics"]
            key = ((record["metrics"]["energy"], record["metrics"]["D3"] +
                    record["metrics"]["D4"], record["metrics"]["holes"])
                   if role == "score" else (record["metrics"]["holes"],))
            assert role not in last or key < last[role][0]
            last[role] = (key, record["metrics"])
        assert {"raw", "score"} <= set(last)
        for role in ("current", "raw", "score", "qualified"):
            if final[role] is None:
                assert role == "qualified" and role not in last
            else:
                assert final[role] == observed[f"search-final-{role}.txt"]
                if role != "current":
                    assert final[role] == last[role][1]
        assert len(observed) == len(records) + 3 + int("qualified" in last)
    report = {
        "passed": True, "optimizer_calls": 0, "source_sha256": sha(__file__),
        "gate_sha256": sha(HERE / "gate.json"), "result_sha256": sha(SOURCE / "result.json"),
        "checked": checked, "distinct_families": len(cache), "verifier_calls": verifier_calls,
        "cover_found": any(row["metrics"]["holes"] == 0 for row in checked),
        "scope": "All saved and final roles independently recounted. Both verifiers rerun "
        "for every distinct family; identical file hashes share receipts. Three named core "
        "caps only. A profile-clear raw record may still violate necessary pair rows.",
    }
    (HERE / "postcheck.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "checked"}))


if __name__ == "__main__":
    main()
