```
Document:    Independent double-hub anchor-reversal quotient audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      c06c84ca062b37ed58a320a6e611313d85f5f5957434dbc48922ac17b325570e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent anchor-reversal quotient audit

The quotient of 270 saved double-hub seeds has exactly 196 isomorphism classes: 122 singleton classes and 74 two-seed classes. This independently agrees with the recorded anchor-reversal involution.

The audit uses nauty through pynauty 2.8.8.1 to compute canonical certificates of each complete point-block incidence graph. All 16 points share one color; all 32 block nodes share another. The anchors are not separately marked. Equal certificates group isomorphic graphs, and the resulting groups are compared exactly with the supplied quotient.

All 270 supplied point maps are checked as bijections, explicitly swap points 1 and 2, and map every source block directly to its stated target. The degree check independently confirms that points 1 and 2 are the only degree-19 vertices; all other points have degree eight or nine. Thus every union isomorphism must preserve or reverse the anchor pair. Combined with the separately audited complete first-link automorphism quotient, anchor reversal accounts for every remaining equivalence.

Five damaged controls are rejected: a broken point map, wrong target, omitted reversal, incorrectly merged classes and missing representative. `result.json` stores all classes, certificate hashes, source/archive stamps and control results. Ruff passes for the checker. The search sources were not changed.

This is an exact isomorphism quotient of the saved partial seeds. Completeness for the branch remains conditional on the separately audited link enumeration. It establishes neither feasibility nor infeasibility of any extension and gives no global covering bound.

Run from the worktree root:

```sh
uv run --with pynauty==2.8.8.1 python experiments/2026-10-03/anchor-reversal-audit/check.py
```
