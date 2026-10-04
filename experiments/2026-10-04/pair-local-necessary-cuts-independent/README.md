```
Document:    Unrestricted Pair Local Necessary Cuts
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      e288df46fa893d069b983d4d8a8fe08d5636ce2ca2d96600a719a94f61672be7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

Let c(S) count selected five-point blocks containing S. For every full
C(16,5,3) cover, every pair P, every triple T containing P, and every
quadruple Q containing P, the following are necessary:

`3*c(P) - c(T) >= 13`

`3*c(P) - 2*c(Q) >= 12`

There are 1,680 pair/triple rows and 10,920 pair/quadruple rows. These
statements impose no block-count, equal-degree, symmetry or incumbent
assumption. They follow from full triple coverage and are redundant in an
exact covering model. In a construction model that permits holes, enforcing
them restricts the partial states to necessary conditions for the target cover.

For T = P union {a}, each block through P contributes three triple
incidences through P. Thus

`3*c(P) - c(T) = sum(c(P union {x}) for x outside T)`.

The sum has thirteen terms, each at least one in a full cover. For
Q = P union {a,b}, the exact identity is

`3*c(P) - 2*c(Q) = sum(c(P union {x}) for x outside Q)`

`  + [c(P union {a}) - c(Q)] + [c(P union {b}) - c(Q)]`.

Here the sum has twelve terms, each at least one. Both differences are
nonnegative by containment. These identities also handle zero counts;
no separate positive-count assumption is needed.

The independent checker verifies all 611,520 nonzero-column triple identities
and 3,974,880 nonzero-column quadruple identities. Columns not containing P
have zero coefficients throughout. Two damaged coefficients fail these
identities. Raising either right-hand side by one is refuted by a verified
full-cover control. The existing 65-block benchmark attains thirteen in the
triple inequality. An explicit unbalanced 4,010-block cover attains twelve
in the quadruple inequality. The latter tests the unrestricted constant; it
is neither a 64-block candidate nor a new upper bound. Both controls pass
the package verifier and the separate standalone verifier.

The selected six-hole state with SHA256
`797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`
fails four triple rows by one. For the pairs (4,7) and (4,12) inside
T=(4,7,12), and (10,14) and (10,15) inside T=(10,14,15), both c(P) and
c(T) equal six, so the left side is twelve. It passes every quadruple row.
The new native nine-hole state fails 56 triple rows and 48 quadruple rows.
These are partial states, so violations do not contradict the proof.

Both local counting inequalities already appear in
`experiments/2026-10-03/regular-heavy-hub-bound/README.md`, at lines 20 and
26. That note's later hub conclusions depend on degree twenty. The two
local inequalities proved here do not. Targeted indexed-source and Markdown
searches did not locate an implementation of the full unrestricted row
families; existing selected-hub code applies stronger conditional rules in
the regular branch. No optimizer was called for this audit.

Run `uv run python experiments/2026-10-04/pair-local-necessary-cuts-independent/check.py`
to reproduce the arithmetic and verifier receipt in `audit.json`.
