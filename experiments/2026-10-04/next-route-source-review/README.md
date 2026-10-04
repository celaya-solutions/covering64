```text
Document:    Refreshed Public Record and Native Multicover Search Route
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      87d4c7080794a8435735e47bf9a38aec379faecde1668c0a526ecc340a9d9823
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Current public record

At 2026-10-04 10:29:52 UTC, the live
[Covering Repository target table](https://coveringrepository.com/systems.aspx?v=16&k=5&t=3&m=3)
still displayed **61 <= C(16,5,3) <= 65**: 65 blocks, lower bound 61,
creator Rade Belic, and date 06/08/1997. The selected filters were V=16, K=5,
T=3, M=3. The row linked download record 108633 and history record 110841.
`target-table-snapshot.txt` preserves the browser table. The initial browser
challenge completed normally before the final table was read. No record change
or 64-block witness was found in this inspected current entry.

The freshly retrieved [maintainer page](https://dmgordon.org/covering-designs/)
still recommends Covering Repository as including its older database plus newer
improvements. Search-engine queries were unhelpful or challenged, so this is not
an exhaustive literature search and does not establish that no other result
exists. The table's lower bound is a source-reported record, not a new proof here.

# A different implementation route

Donald Knuth's [program list](https://www-cs-faculty.stanford.edu/~knuth/programs.html)
describes **SSMCC** as the November 2023 sparse-set rewrite of DLX3. The downloaded
[CWEB source](https://www-cs-faculty.stanford.edu/~knuth/programs/ssmcc.w) uses native
binary include/exclude depth-first search, forced moves, reversible sparse sets,
and lower/upper item multiplicities. This is a specialized multicover engine,
rather than another CP-SAT pool repair or a fixed-heavy completion LP.

The [DLX3 source](https://www-cs-faculty.stanford.edu/~knuth/programs/dlx3.w)
defines a primary-item interval [a,b] with input syntax `a:b|item`; exact counts
can use `b|item`. Zero lower bounds are supported. Each option is a set and can
be chosen once. The SSMCC `include_option` routine hides the chosen option and
updates the remaining capacities, so a single row per block enforces distinct
blocks without duplicating rows into 64 interchangeable slots.

The published
[SSMCC-WTD change file](https://www-cs-faculty.stanford.edu/~knuth/programs/ssmcc-wtd.ch)
adds failure-driven item weights: when including an option makes an item
uncoverable, that item receives a weight increment. Branch selection divides
its remaining branching degree by its weight, except for forced choices.
The code attributes this idea to Boussemart, Hemery, Lecoutre and Sais, ECAI 2004,
pp. 146-150. This is **branching weight**, not a weighted covering objective.
The base SSMCC includes weight fields but does not use them in its default
branching rule; applying the matching change file is a substantive variant.

The optional
[SSMCC-FRB change file](https://www-cs-faculty.stanford.edu/~knuth/programs/ssmcc-frb.ch)
uses failure-rate branching and cites Li, Yin and Li, CP 2021, LIPIcs 210:9.
It was read as a secondary variant, not selected for an additional experiment.
No performance improvement on C(16,5,3) is established by these source listings.
The source itself describes weighting parameters as experimental and cautions
that extreme-weight rescaling has not been thoroughly tested. Start with the
published defaults rather than inventing an aggressive growth schedule.

Do not substitute [DLX5](https://www-cs-faculty.stanford.edu/~knuth/programs/dlx5.w):
its documented option costs extend the colored exact-cover solver, not the
interval-multiplicity solver. Combining its minimum-cost semantics with SSMCC
would require a new, separately audited implementation. Plain exact-cover rows
would incorrectly forbid overlapping triples and would not encode this target.

# Concrete complete encoding to prepare

Use 4,368 option rows in the package's lexicographic five-block order. Each row
contains one cardinality item and its ten triple items. Add the two checked
core-membership items exactly when the block belongs to those cores.

| Item group | Number | Allowed count |
| --- | ---: | --- |
| One item for each triple | 560 | 1 through 64 |
| Selected-block cardinality | 1 | Exactly 64 |
| Original and mapped certified core images | 2 | 0 through 55 |

This gives 563 items and 48,168 incidences: 4,368 times eleven, plus two times
sixty. Use short rank-based item names such as `T000` and `CORE0`, preserve a
separate exact mapping to 1-based point labels, and keep the block-row order
lexicographic. A sample header begins `64|COUNT 1:64|T000 ... 0:55|CORE0`.

The equivalence argument is direct. Any accepted row set contains 64 distinct
blocks because of COUNT and unique option rows. Every triple is covered because
its lower bound is one. Conversely, every 64-block cover is represented because
all 4,368 blocks are available, no triple can occur more than 64 times, and the
two cap-55 rows are independently proved necessary conditions. Thus these two
specific core caps do not impose a new construction-family assumption. There
is no point-degree pattern, heavy-triple pin, rotational invariance, incumbent
neighborhood, SQS pool, inversive geometry or exact excess-vector restriction.

The cap-55 source is the existing four-removal certificate, freshly replayed and
transported in `../core-cap-independent/`. It proves the two declared core rows,
not a cap of 54 and not a global covering-number lower bound. More relabeled core
rows may later be added only with separately checked transports. Nonlinear
five-heavy profile cuts do not become ordinary item columns automatically; the
initial multicover formulation does not pretend otherwise.

# Next bounded step, not yet run

1. Write a solver-free generator and an independent reader that reconstructs all
   4,368 rows, 563 bounds and 48,168 incidences. Reject duplicate/missing rows,
   wrong labels, bounds and core membership, including repaired-hash controls.
2. Freeze the external CWEB source, matching change file, CWEB and GraphBase
   dependencies, generated C, compiler flags, executable and input hashes. Run
   tiny satisfiable/unsatisfiable multicover controls and the known 65-cover
   input restricted to its own 65 rows. The cap-55 rows must be omitted from that
   65-block control because their proof is specific to the 64-block target.
3. After an independent gate and authorization, compare base SSMCC and SSMCC-WTD
   on the same full 64-block input with one bounded worker each. Record a wall
   watchdog, native node/memory counts, branching profile, first-solution output
   and termination status. The source's `T` option is a memory-operation budget,
   not a seconds limit; do not label it as elapsed time.
4. Stop on a candidate and pass its 64 distinct blocks through both verifiers.
   Timeout or bounded tree termination remains inconclusive. A native report of
   zero solutions is not an independently checked global theorem.

This route changes the global search representation and implementation; it does
not claim a new covering algorithm or expected success. Existing native
multicover DFS in the repository handled smaller fixed-link classifications,
not this full 4,368-block interval instance. Earlier cyclic, inversive, SQS,
LP/MIP, tabu, forced-novelty and profile-LNS work was checked before selecting
this candidate, and none is presented as new here. The corrected cap-55 CP pilot
is a separate ongoing comparison, not evidence for this unrun SSMCC route.

# Evidence

`sources.json` binds all retrieved URLs, timestamps, byte counts and SHA256s,
plus the live table capture. Full source files are preserved unchanged in the
ignored `experiments/scratch/next-route-source-review-20261004/` folder. They
were read only: no external solver was built or executed, no search was launched,
and no researcher was contacted. Primary source hashes include:

- SSMCC: `a932c2253c3bf3eac6a0b180cff97ef9132ef4543011b2ac0aebde760ac35cc4`.
- DLX3: `0acc801044d60d9d951663e9270c420b8b43c40ad6f7c2819c65bd5dff9820b7`.
- SSMCC-WTD: `00291e8d1ab5e758fed4fc07c066ecb6a0353e66ecb578672e5fc25524d8030c`.
