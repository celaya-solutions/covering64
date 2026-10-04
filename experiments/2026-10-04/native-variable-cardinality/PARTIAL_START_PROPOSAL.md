```text
Document:    Partial Start Comparison Proposal
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8397bc08a4146219780eb093d5b8caeda8b2e06a7678ac8533aa56e92d70f7d6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Proposed warm-start comparison — not launched

The completed Belic 65 pilot produced no cover and best admissible records with
13 and 12 holes. Both walks escaped the named old core, so the outcome does not
establish an old-core trap. A narrow follow-up can test whether beginning from
a better, structurally different partial family improves this trajectory.
It would change only initial-state handling and its records, leaving the frozen
search kernel and scoring/move policy unchanged.

Use the existing 64-block, 9-hole family:

`experiments/2026-10-04/native-core-cap-escape-v2/seed-2026104201/search-final-best.txt`

SHA256:
`15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46`.
Producer wrap-up rechecked it through both verifiers using expected count 64:
it is structurally valid and incomplete, with exactly 9 holes. Its four named
core overlaps are `[1,0,0,0]`. The existing independent receipt
`native-core-cap-escape-independent/relabel-screen.json`, SHA256
`121fe4d0352102def5371509510ffaefec1b15be5efa24af4b1a97a9e12be1a7`,
binds the same witness bytes and exhausts the necessary old-core partitions.
It reports zero such partitions, certifying old-core overlap at most 55 under
every relabeling. Its maximum 4 over 242 explicit images is only an additional
finite-image observation, not the reason for that universal certificate.
This differs structurally from merely relabeling Belic 65.

Keep the independently verified Belic 65 as the known best complete incumbent:
`data/baselines/belic-1997.txt`, SHA256
`89e4f68acba5d2cbee73e22d07dd1030e540b920fc7541619a065e998dc7d43f`.
The H9 family is initial guidance only; impose no extra search constraint,
core cap, incumbent incidence pattern, protected block, or repair restriction.

# Narrow implementation changes, if approved

1. Put the variant in a new experiment folder. Reuse byte-identical kernel.hpp
   and diagnostic core data. The completed pilot and all its receipts stay fixed.
2. Give the driver separate complete-incumbent and current-family inputs. Check
   the first is the pinned complete 65 and the second is the pinned partial 64/H9.
   Construct the live state from H9 but initialize best-complete from Belic 65.
3. Split record consideration from mutation accounting. At initialization save
   complete 65, raw64/H9, and admissible64/H9 with zero mutations. Future records
   remain strict improvements. Actual current cardinality starts 64, so live
   min/max size counters exclude the separate stored 65 incumbent.
4. Keep initial weights 1, all configuration flags true, timestamps 0, and step 0.
   This preserves the current kernel's initialization rule. It also means the
   first four incomplete iterations can use its age<4 fallback; do not silently
   change the tabu clock to suppress that behavior.
5. Keep ranking, novelty, incoming/outgoing policy, double drops, weight updates,
   no decay, RNG policy, and immediate complete<=64 stopping unchanged. Preserve
   raw64, admissible64, best-complete and actual-final records separately.
6. Adapt runner validation to the two input hashes and initial records. Live
   cardinality starts 64 and stays at most 64 under incumbent 65, unless a smaller
   complete cover ends the run. Both verifiers use actual counts for all records.
7. Add focused controls for initial recording with zero mutations, retained
   separate 65 incumbent, four early fallback ages, strict H9 improvement records,
   and complete<=64 stopping. Repeat the independent gate before any launch.

A possible fresh budget is two sequential 120-second calls with newly assigned
seeds, no transfer, no relaunch, and whole-campaign stop on the first real cover
of at most 64 blocks. This is a proposal, not execution authority. No new driver,
runner, control, build, or optimizer run was created for this variant. Root
will choose the exact budget/seeds only after reviewing independent outcomes.

The comparison should report improvement below the initial 9 holes, time and
iterations to each improvement, all-relabeled old-core status of the best 64,
and the actual final state. A smaller hole count would support further testing;
continued failure would still establish no global lower bound.
