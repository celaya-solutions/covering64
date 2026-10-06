# Document:    Independent CP-SAT Cross-Check of the 61-Block Fixed-Link Cases
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-05
# SHA256:      53ff22a6c09720e75c076d697a4594053de8a7d5205291e8c933d9b78c88cf9f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Re-state the 61-block fixed-link problem with linear constraints and solve it.

Written separately from the CNF encoder. Point 1 is an A-point whose link is a
classified C(15,4,2) cover with center 2 = z. Unknown: which four of points
3..16 are the other A-points, and the perfect matching E on the remaining ten.
Constraints, straight from the lemmas:

* the 19 blocks through point 1 are exactly the link blocks;
* every triple lies in one or two blocks;
* every pair {u,v} lies in 5 + [uv in E] blocks, where E consists of 1-2, 2-a
  for the four other A-points, and the matching on M;
* every pair lies in exactly one doubled triple, or four if it is in E.

No symmetry breaking is added. Usage: cpsat_check.py CLASS_FILE SECONDS WORKERS.
"""

import json
import sys
import time
from itertools import combinations
from pathlib import Path

from ortools.sat.python import cp_model

ROOT = Path(__file__).resolve().parents[3]


def main():
    name, seconds, workers = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
    path = ROOT / "experiments/2026-10-03/link-classification" / name
    link = {tuple(map(int, line.split())) for line in path.read_text().splitlines() if line}
    assert len(link) == 19 and all(block[0] == 1 for block in link)
    points = range(1, 17)
    blocks = list(combinations(points, 5))
    model = cp_model.CpModel()
    x = {}
    for block in blocks:
        if 1 in block:
            x[block] = model.NewConstant(1 if block in link else 0)
        else:
            x[block] = model.NewBoolVar(f"x{block}")
    others = range(3, 17)
    is_a = {v: model.NewBoolVar(f"a{v}") for v in others}
    match = {p: model.NewBoolVar(f"m{p}") for p in combinations(others, 2)}
    model.Add(sum(is_a.values()) == 4)
    for v in others:
        incident = [match[tuple(sorted((u, v)))] for u in others if u != v]
        model.Add(sum(incident) + is_a[v] == 1)
    for (u, v), m in match.items():
        model.AddImplication(m, is_a[u].Not())
        model.AddImplication(m, is_a[v].Not())

    def in_e(u, v):
        if (u, v) == (1, 2):
            return 1
        if u == 1:
            return 0
        if u == 2:
            return is_a[v]
        return match[(u, v)]

    cover = {t: [] for t in combinations(points, 3)}
    pair_blocks = {p: [] for p in combinations(points, 2)}
    for block in blocks:
        for t in combinations(block, 3):
            cover[t].append(x[block])
        for p in combinations(block, 2):
            pair_blocks[p].append(x[block])
    doubled = {}
    for t, terms in cover.items():
        doubled[t] = model.NewBoolVar(f"d{t}")
        model.Add(sum(terms) == 1 + doubled[t])
    for (u, v), terms in pair_blocks.items():
        e = in_e(u, v)
        model.Add(sum(terms) == 5 + e)
        through = [doubled[t] for t in cover if u in t and v in t]
        model.Add(sum(through) == 1 + 3 * e)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_workers = workers
    started = time.time()
    status = solver.Solve(model)
    print(
        json.dumps(
            {
                "class": name,
                "status": solver.StatusName(status),
                "seconds": round(time.time() - started, 1),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
