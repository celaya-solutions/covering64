```text
Document:    Exact Elastic Lower Bounds from the Complete Link Sweep
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      db5f098b73866287bc964acbfc500304e3ba12700f034b2883747f0240968a5f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The 113 fresh LP evaluations from the complete link-switch sweep yield 113
exact lower bounds on the regular-family completion model's elastic objective.
Every bound has a positive value at its source tuple. The smallest source gap
is 5.644645. No optimizer was called to derive these bounds. This does not
change the covering-number bounds or first-link exclusion registry.

`bundle.json` contains the 276 heavy coefficients and right-hand side of each
necessary inequality, with global lexicographic column IDs stored once. It
binds the frozen sweep, builder, common row basis, and all exact certificates.
The full signed weights and ordinary coefficients remain in ignored
`experiments/scratch/lp-guided-sweep-cuts-20261004/`.

# Exact lower-bound argument

Write each completion row as

    l_i <= A_i x + B_i h <= u_i,  with 0 <= x_j <= 1.

Here h selects heavy blocks, while x selects ordinary blocks. Choose integer
weights w_i with absolute value at most D = 1,000,000. A positive weight uses
the lower bound; a negative weight uses the upper bound. Infinite upper
bounds cannot receive negative weights. Let C be the weighted sum of those
bounds, a the combined ordinary coefficients, and b the combined heavy
coefficients. Then

    (C - sum_j max(0, a_j) - b h) / D <= total L1 row slack.

Each violated side contributes at most D times its violation to the weighted
deficit, and the ordinary linear form is at most its box maximum. Therefore
this inequality holds for every ordinary vector in its box. A zero-slack
completion must satisfy b h >= C - sum_j max(0, a_j).

The numerical dual only suggests useful weights. Rounding and clipping them
does not weaken the validity argument, which uses exact integer arithmetic
and does not require a numerically feasible or optimal dual. `build.py`
sets negative weights on infinite upper bounds to zero and checks every
source gap against its recorded numerical objective as an additional guard.
Only the regular degree-20 four-sevenfold family, its fixed anchors, and its
audited 697-row / 1200-ordinary-column model are covered.

Independent replay of the basis, signs, coefficients, box maxima, source gaps,
and hashes passed in `../lp-guided-complete-sweep-independent/bundle-audit.json`.
The envelope has a positive exact bound at all 136 neighbors; its minimum is
362507/500000. It exceeds the exact recounted incumbent upper bound at 116
neighbors. This distinction preserves the difference between excluding a
zero-slack completion and proving that a neighbor cannot improve the score.
