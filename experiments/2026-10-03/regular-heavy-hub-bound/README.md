```
Document:    Regular Heavy Hub Bound and Independent Escape Seed Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e685e653c863fcc927601b0725f5ffb3bd95b288e83b977d1739edcf3f0f20c0
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Repeated hubs of heavy triples in a regular cover

Assume a full 64-block C(16,5,3) cover with point degree 20. All labels are
one-based. Write λ(a,b) for pair multiplicity and μ(T) for triple multiplicity.
Each pair has λ≥5. At every point a, the total pair excess is
Σ(b≠a)(λ(a,b)−5)=4·20−15·5=5.

If μ({a,b,c})≥6, then 3λ(a,b)≥13+μ≥19, so each internal pair has λ≥7.
The two internal pairs spend at least four excess units at each anchor.
Heavy triples are disjoint: sharing one or two anchors would force at least
three distinct internal heavy pairs at an anchor, already costing six units.

Suppose an outside point h occurs r≥2 times among the common blocks of a heavy
triple {a,b,c}. The pair (a,h) must cover all fourteen other labels. Since b and
c each occur at least r times, 3λ(a,h)≥14+2(r−1)=12+2r. Thus λ(a,h)≥6, and the
same holds for (b,h) and (c,h). Each anchor has only one spare excess unit.
Therefore:

- There is at most one repeated outside point for each heavy triple.
- If a repeated hub exists, all three internal pair multiplicities equal seven.
- Its outside multiplicity is at most three, since λ(a,h)≤6 implies r≤3.
- Serving as a hub costs at least three excess units at h. It cannot belong to
  another heavy triple, which already costs at least four there.
- Hubs for distinct heavy triples are distinct, since two disjoint anchor sets
  would cost at least six units at their shared hub.

For μ=6, the twelve outside incidences therefore have one of three degree
patterns: twelve singletons; one double point and ten singletons; or one triple
point and nine singletons. Their supports have sizes twelve, eleven, and ten.
For μ=7, the internal λ=7 pair has no extra block beyond the common seven, so
all thirteen outside points must occur. Its fourteen incidences give exactly
one double point and twelve singletons. These degree patterns are necessary;
this note does not claim that every pattern extends to a cover.

Let n6 count exact-six triples, n7 count sevenfold triples, and h6 count the
exact-six triples having a repeated outside hub. The heavy triples occupy
3(n6+n7) distinct points. Their n7+h6 hubs are distinct and outside all heavy
triples. Hence the strengthened necessary bound is

**3n6 + 4n7 + h6 ≤ 16.**

This uses the already established multiplicity cap of seven in a regular
full cover. The explicit hub restrictions remain necessary in addition to the
count bound; the count alone does not detect two triples using the same point.
The statements here are conditional on regularity and full coverage, and are
not global lower bounds for arbitrary partial states.

Scope correction: without a repeated hub, point-excess accounting alone permits
an internal multiplicity-eight edge in an exact-six triple: internal values
(8,7,7) spend (5,5,4) units at the anchors. We therefore assert internal λ=7 only
when a repeated hub exists; the count proof needs no stronger claim.

# Independent nine-hole seed check

The separately reconstructed candidate in `structured-hub-escape/candidate-h9.txt`
has 64 distinct blocks, point degree 20, and nine holes. The package and standalone
verifiers agree with a third raw subset recount. Its heavy triples are:

| Triple | Multiplicity | Repeated hub |
|---|---:|---:|
| 1,2,3 | 7 | 4 |
| 5,11,16 | 6 | none |
| 7,10,13 | 7 | 12 |
| 8,9,14 | 7 | 15 |

The triples are disjoint; their hubs are distinct and outside all heavy triples.
Here n6=1, n7=3, h6=0, so the refined sum is 15. The previous six-hole seed is a
negative control: its four sevenfold triples reuse hub 4. The new witness differs
by a single point swap between two outside blocks, and its local families are
unchanged. Their full-completion hub row still sums to **25 > 24**. Thus this is
only a seed passing the explicit heavy/hub tests; outside-only repair cannot
complete those fixed local families in this regular branch.

`check.py` independently recounts the witness, validates both cover checks,
checks the changed blocks, and enumerates 896 anchor-budget controls plus the
outside endpoint degree patterns. Three malformed witnesses are rejected by the
independent parser and package verifier. The old duplicate-hub witness is also
rejected by the new explicit hub test. No solver is used in this audit.

Run from the worktree root:

```sh
uv run python experiments/2026-10-03/regular-heavy-hub-bound/check.py
```

`result.json` records exact holes, common blocks, outside degrees, all hashes,
verifier reports, and the fixed-family obstruction. No earlier artifact was
modified to produce this evidence.
