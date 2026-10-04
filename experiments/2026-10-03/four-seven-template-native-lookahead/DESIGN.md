```text
Document:    Anchor-Pair Lookahead Native Search Design
Version:     v1.2.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e2396a9f6e014f9781a0e50479d348880b931eba2c142568ba305dfe82b18715
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

This separate v1.2 variant preserves the frozen v1.0/v1.1 searches and all their
evidence. Its legal states and moves are unchanged: 64 distinct blocks,
degree 20 at every point, four seven-block anchor templates from the complete
audited catalogs, and 36 ordinary blocks from the full 1,200-block family.
The scoring lookahead adds no legal-move restriction.

# Necessary anchor-pair limits

Every covered pair needs at least ceil(14/3) = 5 selected blocks. Each anchor
point has two anchor peers contained with it in seven heavy blocks. Its own
hub appears in two of those heavy blocks, doubling two distinct triples on
the anchor/hub pair. A pair count of five permits only one unit of excess,
so that anchor/hub pair needs at least six. The resulting 15 pair-count lower
bounds sum to 2*7 + 6 + 12*5 = 80, exactly four times point degree 20. They are
therefore equalities: anchor peers 7, own hub 6, all other pairs touching an
anchor point 5. This does not fix hub-hub pair counts.

For a heavy tuple let H[t] count its 28 blocks and define
`E_H[p] = sum(max(0, H[t]-1) for triples t containing p)`. A full covering with
pair count lambda has exactly `3*lambda - 14` excess on that pair. Adding an
ordinary block B increments the excess once for every triple of B that
contains p and already has H[t] >= 1. An ordinary block is individually
admissible only when the resulting excess meets every one of the 114 forced
anchor-touching pair budgets. If the heavy tuple already exceeds any such
budget, no ordinary block is admissible. Hub-hub budgets are never imposed.

A triple with H[t] = 0 and no admissible ordinary block covering it is an
unsupported triple. Such a heavy tuple cannot yield a zero-hole state within
this hard native family. The converse is not claimed: zero unsupported triples
is only a necessary lookahead condition, and individually admissible ordinary
blocks may still be mutually incompatible.

# Score, cache and cover handling

`score = 5*holes + pair_target_L1 + 5*nonheavy_excess + 100*unsupported_triples`.
The inherited hub-pair targets and nonheavy excess term remain soft. Raw best
minimizes holes, then score; score best minimizes score, then holes. A legal
zero-hole proposal is always accepted regardless of all soft penalties. The
production acceptance function is directly exercised with a synthetic positive
million-point delta and zero projected holes during startup.

Ordinary moves reuse the current heavy-tuple lookahead. Whole-template
proposals evaluate their prospective tuple through a bounded cache. Four
16-bit template indices form its unambiguous 64-bit key. At 100,000 entries,
the next insertion clears the cache. Cache contents affect speed only; full
native audits and sidecar recounts check their values. The read-only
`--cache-control` mode exercises the identical eviction branch at capacity two,
then refills, repeats, resets and restores production capacity 100,000.
`--lookahead-only` returns all admissible blocks and unsupported triples after
two same-process repeated reads. Each saved search state has a complete
`.txt.lookahead.json` sidecar for independent exact-set comparison.

# Authorized run and provenance

The final runner permits only one cycle pilot, 300 seconds and one native
worker, beginning with the independently checked v1.1 12-hole cycle state and
seed 2026103982. Its matching seed exists only for short controls. The pilot
must wait for the independent gate. The gate uses fresh Python brute recounts
from the heavy blocks rather than native incremental/cache logic.

The optimized performance smoke and two sanitizer smokes each use three-second
budgets. An earlier draft smoke predates the added read-only cache-clear mode;
its source, binaries, environment and logs remain under `draft-*` names in the
ignored raw archive and are not the final-source gate evidence. The production
source is bound by the final environment and source hashes. The complete
archive is `experiments/scratch/four-seven-template-native-lookahead-v1.2.0/`.
