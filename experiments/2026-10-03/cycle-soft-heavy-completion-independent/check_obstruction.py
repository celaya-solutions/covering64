# Document:    Independent Seven-Block Completion Obstruction Replay
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CERT = HERE.parent / "cycle-soft-heavy-completion/heavy-obstruction.json"


def main():
    data = json.loads(CERT.read_text())
    heavy = list(map(frozenset, data["heavy_blocks"]))
    support = list(map(frozenset, data["support_blocks"]))
    groups = [frozenset(range(i, i + 3)) for i in (1, 5, 9, 13)]
    assert len(heavy) == len(set(heavy)) == 28 and len(support) == 7
    assert set(support) <= set(heavy)
    bounds = {}
    for group in groups:
        hub = max(group) + 1
        local = [block for block in heavy if group <= block]
        assert len(local) == 7
        external = Counter(p for b in local for p in b - group)
        assert external == Counter({p: 2 if p == hub else 1
                                    for p in range(1, 17) if p not in group})
        for p in group:
            degree_lower_sum = 0
            for q in set(range(1, 17)) - {p}:
                minimum = 7 if q in group else 6 if q == hub else 5
                bounds[frozenset((p, q))] = minimum
                degree_lower_sum += minimum
            assert degree_lower_sum == 4 * 20
    target = frozenset(data["uncovered_triple"])
    assert len(target) == 3 and not any(target <= block for block in heavy)
    candidates = [frozenset(b) for b in itertools.combinations(range(1, 17), 5)
                  if target <= set(b) and all(len(set(b) & group) <= 1 for group in groups)]
    assert len(candidates) == 18
    replay = []
    for block in candidates:
        multiplicity = Counter(frozenset(t) for b in support + [block]
                               for t in itertools.combinations(sorted(b), 3))
        blockers = []
        for pair, pair_count in bounds.items():
            excess = sum(max(0, n - 1) for triple, n in multiplicity.items() if pair <= triple)
            budget = 3 * pair_count - 14
            if excess > budget:
                blockers.append({"pair": sorted(pair), "excess": excess, "budget": budget})
        assert blockers
        replay.append({"block": sorted(block), "blockers": blockers})
    assert {tuple(row["block"]) for row in replay} == {
        tuple(row["block"]) for row in data["blocked_candidates"]}
    report = {"passed": True, "ordinary_candidates": 18, "support_blocks": 7,
              "replay": replay, "certificate_sha256": hashlib.sha256(CERT.read_bytes()).hexdigest(),
              "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "Fixed heavy tuple, regular point degree 20; anchor-pair budgets only"}
    (HERE / "obstruction-audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "replay"}))


if __name__ == "__main__":
    main()
