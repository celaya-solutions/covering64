```
Document:    Four Pinned Sevenfold Links Force Regularity
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      71af802b57242cbeed79da43086b2130c931be2f4b526a12caa906913585b590
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Statement and hypotheses

Let a family of 64 distinct five-element blocks cover every triple on 16
points. Suppose it contains four pinned seven-block links with these properties:

- The four anchor triples are pairwise disjoint.
- Each link consists of seven distinct blocks containing its anchor triple.
- Each anchor has an assigned hub outside all four anchors. The four assigned
  hubs are distinct, so they are precisely the four remaining points.
- At least two pinned blocks in each link contain its assigned hub.

Then every point occurs in exactly 20 blocks. No degree or pair regularity is
assumed in this statement. It is conditional on these pinned links and does not
prove that an arbitrary 64-block cover has this structure.

# Proof of regularity

Write r(p) for the number of selected blocks through point p and r(p,q) for
the number through a pair. Any pair needs r(p,q) >= 5: its blocks must cover
14 possible third points and each block supplies only three third points.
Also sum over q != p of r(p,q) = 4 r(p).

Fix an anchor point a and its assigned hub h. Two pinned blocks through
(a,h) both contain the other two anchor points. Each of those two third points
therefore already occurs twice. Covering all 14 third points requires at least
16 third-point incidences through (a,h), including these two unavoidable
duplicates. Consequently 3 r(a,h) >= 16 and r(a,h) >= 6. This argument does
not assume r(a) = 20.

An anchor point has two internal pairs of count at least seven. Thus its
pair-count sum is at least 15*5 + 2*(7-5) = 79, so r(a) >= 20. Each hub has
three own-anchor pairs of count at least six, giving a pair-count sum of at
least 15*5 + 3*(6-5) = 78, so r(h) >= 20. All 16 points therefore have degree
at least 20. Their degree sum is exactly 64*5 = 320, forcing every degree
to equal 20.

# Consequences needed by the completion LP

Each anchor point has pair-count sum 80. Its two internal pairs use four of
the five excess units above the baseline of five; its own-hub pair uses the
last unit. Thus internal pairs have count seven, own-hub pairs count six,
and every other pair involving that anchor point count five. These are the
114 exact anchor-pair equalities.

Every internal anchor pair is already supplied by its seven pinned blocks.
No additional selected block may contain an internal anchor pair. Hence
every additional block contains at most one point from each anchor triple.
There are exactly 1,200 such ordinary blocks, in the inherited lexicographic
order. Exactly 36 must be selected. Across the whole structural family, the
allowed universe has 1,476 blocks: these 1,200 ordinary blocks and 276 possible
anchor-containing blocks. Pinning the 28 chosen anchor-containing blocks
eliminates every other anchor-containing block.

For an outside point q other than an anchor's own hub, the pair (a,q) has
count five. If q appears in d pinned link blocks, two triples through (a,q)
already have multiplicity d. Its 12 other third points still need coverage,
so 2d + 12 <= 15 and d <= 1. Coverage of an internal anchor pair together
with q forces d >= 1. Thus every such outside point appears once. The seven
link edges have 14 endpoints on 13 outside points, leaving degree two for
the assigned hub. These link-profile conditions are consequences of a
completion, not additional assumptions for the regularity theorem.

A hub's pair-count sum to the 12 anchor points is 3*6 + 9*5 = 63. Its three
hub-pair counts sum to 17. Subtracting five from each gives a nonnegative
integer weighted graph on four hubs with degree two at every vertex. There
are exactly six labeled graphs: three simple four-cycles and three doubled
perfect matchings. Therefore each hub-pair count lies from five through seven.
The LP retains all six graphs through these bounds and the degree rows.

Every nonanchor triple has multiplicity at most two. If it contains two
points of one anchor, only that anchor's pinned link can cover it; the outside
degrees just proved give count one or two. Otherwise, every one of the six
hub graphs gives the triple at least one pair of multiplicity five. The
14 triples through that pair have total incidence 15, so none can exceed two.
The four anchor triples have multiplicity seven. The completed triple profile
would therefore be four sevenfold triples, 56 double triples and 500 single
triples, from total incidence 64*10 = 640.

# Independent check and present consequence

`check.py` uses only the pinned blocks from the current LP manifest; it does
not assume the binding near-cover's point degrees. It derives the pair lower
bounds directly from unavoidable repeated third points, enumerates all six
hub graphs, and checks all 556 nonanchor triple caps. It reconstructs every
support and bound of the 697-row LP, all 1,200 variable names and Boolean
domains, and rejects hidden model fields. It verifies that every one of the
3,140 unpinned nonordinary blocks is excluded by a saturated internal pair.

The checker then replays the saved signed dual directly against these newly
derived rows. Its 526 integer row weights give right side 5,587 and box maximum
162, with denominator 1,000. The strictly positive exact gap is
(5,587 - 162)/1,000 = 217/40. This independently excludes any completion of
these particular 28 pinned blocks to a 64-block cover, even when every one of
the 4,368 five-element blocks was initially available.

The audit rejects 25 damaged controls: eight damaged pin hypotheses, eight
damaged model fields, and nine damaged certificate fields. It makes no solver
calls. The proposed 120-second full-universe pinned-28 solve was not launched,
because this proof and certificate already answer that conditional question.

The general regularity theorem applies to any four pinned links satisfying
the hypotheses. The numerical LP exclusion applies only to the specific
28-block tuple bound by the saved manifest and certificate. No global lower
bound is raised, no degree-19 branch is removed from the unrestricted problem,
and no first-link registry entry is changed.

Run the audit with:

```sh
uv run python experiments/2026-10-04/four-seven-pinned-regularity/check.py
```

Input model, manifest, and certificate hashes are in `audit.json`. Large model
artifacts remain outside Git. `files.json` binds the compact source, document,
and audit.
