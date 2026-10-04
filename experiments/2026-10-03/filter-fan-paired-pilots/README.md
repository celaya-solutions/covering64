```
Document:    Paired Filter-and-Fan Construction Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      8e15a618231abcf217489a1b8a1935d195fd62b9560a997a7001a83d96159f83
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Paired result

All twelve approved 30-second runs finished at three missing triples. Both covering checkers agreed on every saved best family: 64 distinct blocks covering 557 of 560 triples. No new covering witness was found. This is a bounded construction experiment, not a lower bound or impossibility result.

| Seed | Beam best missing | Greedy best missing | Beam trees | Greedy component moves |
|---|---:|---:|---:|---:|
| 2026100361 | 3 | 3 | 854 | 53,511 |
| 2026100362 | 3 | 3 | 683 | 42,934 |
| 2026100363 | 3 | 3 | 745 | 46,664 |
| 2026100364 | 3 | 3 | 825 | 52,064 |
| 2026100365 | 3 | 3 | 730 | 45,954 |
| 2026100366 | 3 | 3 | 712 | 44,619 |

The exact six seeds were 2026100361–2026100366; each mode received 30 seconds, with at most two single-thread search processes running concurrently. The total recorded native time was 360.001200 seconds, including small deadline-return overheads. There were 16,041,605,632 evaluated proposals across both modes. The frozen root-reviewed source and binary were used unchanged. No extra search runs or enlarged budgets were added after these outcomes.

# Checks and limitations

Every saved best passed a package/standalone cross-check of distinct cardinality, coverage status and the exact missing-triple set. All 290,295 saved traces and 290,295 component moves were independently replayed using the frozen Python checker. Each replay checked exact triple counts, point degrees, scores, legality and full inverse rollback. Full logs, scores, witnesses and 888,972,219 bytes of uncompressed trace data remain outside Git in the raw campaign folder. Raw metadata binds source revision, execution snapshot, source, binary, seed and root-gate hashes.

The comparison concerns whole policies: greedy accepts its best component move even when raw coverage worsens; beam accepts only a prefix that improves raw deficit. Triple-weight updates occur between attempts, which are one move for greedy and one tree for beam. Therefore these results do not isolate beam width or establish a statistically reliable performance ranking. Shared-host concurrent execution also limits throughput comparisons.

A read-only inspection found 4,549 saved beam prefixes, all of length one and deficit three. They represented 48 distinct families sharing 60 blocks; each differed from the original seed by one block. This describes saved lowest-deficit prefixes only. The code also explored deeper branches up to its depth cap; nonwinning internal branches are not all serialized. It would be incorrect to conclude from the saved prefixes that every explored branch preserved that 60-block core.

The execution runner snapshot was frozen before three long lines were wrapped for Ruff. runner-format-audit.json checks that the tracked and executed runners have identical Python ASTs and records both hashes. The native source and binary did not change. Targeted Ruff passed; root owns the full repository checks and commit.

# Next direction

Root proposed a separate algebraic construction: build an inversive plane S(3,5,17) over GF(16), delete infinity, and use a pool of 48 remaining circles plus all 240 extensions of its 20 affine four-point lines. The planned model selects 64 blocks from that 288-block pool with all 560 triple constraints, without forcing a 20-extension/44-circle split. The plane, pool and exact model must pass an independent check before the separately authorized 60-second CP pilot. This changes the construction pool; it does not extend the completed filter-and-fan campaign.
