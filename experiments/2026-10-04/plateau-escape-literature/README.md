```text
Document:    Escape Options After a Strict Radius Two Local Minimum
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      23902c792ba4569475664b1a228139b60b985ce2fb8602ed147016a03e1bed35
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Recommendation

If completed radius-one and radius-two scans reach a strict local minimum with
holes remaining, first try a small bounded queue of **already saved, independently
checked families at exactly the same `(holes,D2max)` rank**. Deduplicate by
canonical family hash, skip previously scanned centers, fix a center/time limit,
and reuse the audited scans. A strict improvement returns to descent. This is
a proposed next experiment, not authorization to launch.

This reuses existing evidence before changing the kernels. Tied siblings need
not be adjacent. If no unseen saved ties remain, genuine neutral-neighbor
exploration needs a reviewed recorder change: current scans discard ties equal
to their starting rank. Empty improving output therefore does not establish
that no neutral neighbor exists. Prevent cycles and label any capped collection
as incomplete. Allowing higher D2max at equal holes would be a distinct uphill
policy, not an equal-rank step.

Why another center can help: `d(F,G)=64-|F intersection G|` is half the symmetric
difference and is a metric on 64-block families. A radius-two scan from a center
at distance q may reach outside the old radius-two neighborhood, while staying
inside radius q+2. This proves additional possible reach, not improvement or
plateau exhaustion.

# Published evidence versus our variant

- **NuSC:** the previously audited authors' implementation uses weighted coverage,
  configuration checking, age/tabu rules, and two-drop/add trajectories. Our
  earlier variable-size pilots already use that direction; an equal-rank queue
  is not NuSC. [1]
- **Covering-design VND:** the institutional abstract describes systematic block
  removal/addition. Its full text was restricted; no unread acceptance rule is
  inferred. [2]
- **Fresh primary source:** Lourenco, Martin, and Stutzle's ILS chapter, section
  3.3, separates perturbation/local search from acceptance and contrasts strict
  improvement with accepting the latest local optimum regardless of cost. Its
  VNS discussion stresses that local optimality depends on the neighborhood.
  This supports changing acceptance or center after stagnation. It does not
  establish good performance here. Our deterministic tie queue is a narrower
  experimental variant, not a new algorithm or a reproduction. [3]

# Why defer a larger CP radius

The D29-centered complete two-swap scan took 4.21857 native seconds and retained
six H12/D28 ties. The separate D29-centered radius-four CP call took 300.009194
seconds and returned UNKNOWN without a vector. These different tasks and regions
are not a controlled performance comparison: the scan has hard quad rows; the
inherited soft CP model lacks them. The current descent endpoint is not assumed.

Keep larger-radius CP as the next distinct experiment if bounded tied starts
fail to improve or diversify. Use the actual checked endpoint, a hole target
below its H, and an explicit frozen row set. A larger radius adds candidates but
has uncertain effect on bounded CP search. A positive-hole result is partial;
UNKNOWN excludes nothing. No cover or comparative-speed claim follows.

# Sources

1. Luo et al., *NuSC*, [DOI](https://doi.org/10.1109/TCYB.2022.3199147),
   [authors' audited source revision](https://github.com/chuanluocs/NuSC-Algorithm/tree/fdacd80d92e7143b4fe305bddce471a1e8982e90).
   Reused evidence: `post-d2-literature/README.md` and `sources.json`.
2. Nikolic et al., *Variable neighborhood descent heuristic for the covering
   design problem* (2012), [institutional abstract](https://rfos.fon.bg.ac.rs/handle/123456789/1006),
   [DOI](https://doi.org/10.1016/j.endm.2012.10.026). Earlier abstract evidence only.
3. Lourenco, Martin, Stutzle, *Iterated Local Search*,
   [arXiv author submission](https://arxiv.org/abs/math/0102188),
   [full HTML v1](https://arxiv.org/html/math/0102188v1), section 3.3 and VNS
   discussion. The record lists *Handbook of Metaheuristics* (2002), pp. 321–353.
   Freshly accessed 2026-10-04; abstract and full HTML both HTTP 200.

Local receipts: `weak-pair-two-swap-scan-v2/result.json` and
`radius-four-feasibility-v2-postcheck/postcheck.json`. Source bytes and hashes
are recorded in the accompanying `sources.json`. No solver/model/code preparation.
