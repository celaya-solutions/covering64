#!/usr/bin/env python3
# Document:    Independent Fourteen Cut Native Runtime Review
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Read frozen native controls; rebuild scores and moves without optimization."""

import functools
import hashlib
import importlib.util
import itertools as it
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "experiments/2026-10-03"
SOURCE = ROOT / "scripts/four_seven_template_multicut_heuristic.cpp"
PRIMARY = HERE.parent / "multicut-native/audit.json"
ORACLE = OLD / "four-seven-template-lookahead-independent/oracle.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    output = HERE / "audit.json"
    assert not output.exists(), "Preserve completed evidence"
    primary_bytes, source_bytes = PRIMARY.read_bytes(), SOURCE.read_bytes()
    primary = json.loads(primary_bytes)
    bundle_bytes = (OLD / "cut-survivor-lp-screen/cut-bundle.json").read_bytes()
    bundle = json.loads(bundle_bytes)
    assert primary["passed"]
    assert sha(source_bytes) == primary["source_sha256"]
    assert sha(bundle_bytes) == primary["cut_sha256"]
    assert sha(ORACLE.read_bytes()) == primary["oracle_sha256"]
    spec = importlib.util.spec_from_file_location("prior_independent_lookahead", ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    heavy_index = {tuple(b): i for i, b in enumerate(bundle["heavy_blocks"])}
    anchors = [tuple(range(start, start + 3)) for start in (1, 5, 9, 13)]
    triples, pairs = list(it.combinations(range(1, 17), 3)), list(it.combinations(range(1, 17), 2))
    lookahead = functools.cache(oracle.analyze)
    witnesses, scores, holes, receipts, folders = {}, {}, {}, [], set()
    max_penalty = max(max(0, c["rhs"] - sum(sorted(c["coefficients"])[:28]))
                      for c in bundle["cuts"])
    max_penalty = 1000 * ((max_penalty + 999) // 1000)
    assert max_penalty < 2**31
    for snapshot in primary["snapshots"]:
        path = ROOT / snapshot["path"]
        captured = path.read_bytes()
        assert sha(captured) == snapshot["sha256"]
        blocks = tuple(tuple(map(int, line.split())) for line in captured.decode().splitlines())
        assert len(blocks) == len(set(blocks)) == 64 and list(blocks) == sorted(blocks)
        assert all(len(b) == 5 and tuple(sorted(set(b))) == b
                   and all(1 <= p <= 16 for p in b) for b in blocks)
        heavy = tuple(oracle.heavy_blocks(blocks))
        assert len(heavy) == 28 and all(b in heavy_index for b in heavy)
        name = path.parent.name
        original, enabled = "-original-" in name, "-on-" in name
        weight = int(name.rsplit("-w", 1)[1])
        matching = name.startswith("matching-")
        detail_path = path.with_name(path.name + ".lookahead.json")
        detail_bytes = detail_path.read_bytes()
        detail = json.loads(detail_bytes)
        tc = Counter(t for b in blocks for t in it.combinations(b, 3))
        pc = Counter(p for b in blocks for p in it.combinations(b, 2))
        targets = {p: 5 for p in pairs}
        for anchor in anchors:
            targets.update({p: 7 for p in it.combinations(anchor, 2)})
            targets.update({(p, anchor[-1] + 1): 6 for p in anchor})
        extra = [(4, 8), (12, 16)] if matching else [(4, 8), (8, 12), (12, 16), (4, 16)]
        targets.update({p: 7 if matching else 6 for p in extra})
        missing = sum(tc[t] == 0 for t in triples)
        pair_error = sum(abs(pc[p] - targets[p]) for p in pairs)
        over = sum(max(0, tc[t] - 2) for t in triples if t not in anchors)
        base = 5 * missing + pair_error + 5 * over
        look = lookahead(heavy)
        values = [sum(c["coefficients"][heavy_index[b]] for b in heavy)
                  for c in bundle["cuts"]]
        violations = [max(0, c["rhs"] - lhs)
                      for c, lhs in zip(bundle["cuts"], values, strict=True)]
        guide = weight * ((max(violations) + 999) // 1000) if enabled else 0
        score = base + 100 * look["unsupported_count"] + guide
        expected = {"holes": missing, "base_score": base, "score": score,
                    "unsupported_count": look["unsupported_count"],
                    "admissible_count": look["allowed_ordinary"]}
        if not original:
            expected.update(cut_enabled=enabled, cut_weight=weight, cut_count=14,
                            cut_lhs=values, cut_rhs=[c["rhs"] for c in bundle["cuts"]],
                            cut_violations=violations, cut_violation=max(violations),
                            cut_penalty=guide, cut_denominator=1000,
                            cut_sha256=sha(bundle_bytes))
        assert all(detail[k] == value for k, value in expected.items())
        assert (snapshot["holes"], snapshot["score"], snapshot["cut_lhs"],
                snapshot["cut_penalty"]) == (missing, score, values, guide)
        if not enabled:
            base_name = ("matching" if matching else "cycle") + "-search-original-off-w1"
            assert captured == (path.parent.parent / base_name / path.name).read_bytes()
        witnesses[path], scores[path], holes[path] = set(blocks), score, missing
        folders.add(path.parent)
        receipts.append({"path": snapshot["path"], "sha256": sha(captured),
                         "detail_sha256": sha(detail_bytes), "score": score,
                         "holes": missing, "cut_penalty": guide})
    operations, logs = 0, {}
    for folder in sorted(folders):
        captured = (folder / "stdout.jsonl").read_bytes()
        logs[str(folder.relative_to(ROOT))] = sha(captured)
        assert not (folder / "stderr.log").read_bytes()
        for line in captured.decode().splitlines():
            event = json.loads(line)
            if event.get("event") != "operation":
                continue
            before_path, after_path = Path(event["before"]), Path(event["after"])
            before, after = witnesses[before_path], witnesses[after_path]
            removed, added = set(map(tuple, event["removed"])), set(map(tuple, event["added"]))
            assert len(removed) == len(event["removed"]) == len(added) == len(event["added"])
            assert removed <= before and not (before - removed) & added
            assert after == before - removed | added
            assert (event["holes_before"], event["holes_after"], event["score_before"],
                    event["score_after"]) == (holes[before_path], holes[after_path],
                                             scores[before_path], scores[after_path])
            rollback = before_path.with_name(before_path.name.replace("-before", "-rollback"))
            assert witnesses[rollback] == before
            operations += 1
    assert len(receipts) == 286 and operations == 88
    result = {"passed": True, "snapshots": len(receipts), "operations": operations,
              "unique_states": len({r["sha256"] for r in receipts}),
              "source_sha256": sha(source_bytes), "primary_audit_sha256": sha(primary_bytes),
              "bundle_sha256": sha(bundle_bytes), "oracle_sha256": sha(ORACLE.read_bytes()),
              "checker_sha256": sha(Path(__file__).read_bytes()),
              "maximum_weight1000_penalty_bound": max_penalty,
              "default_off_blocks_match_original": True, "fresh_full_scores": True,
              "source_review": "14-cut maximum guide; heavy swap updates all cut sums; ordinary "
                               "moves preserve them; rollback restores them; zero-hole acceptance "
                               "override retained. No domain restriction added.",
              "receipts": receipts, "trace_sha256": logs,
              "optimization_runs": 0,
              "scope": "Restricted regular four-sevenfold native search only."}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in
                      ("passed", "snapshots", "operations", "unique_states")}))


if __name__ == "__main__":
    main()
