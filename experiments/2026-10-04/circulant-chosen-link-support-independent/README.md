~~~text
Document:    Independent Gate for the Full Chosen Link Support Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      faf714434a774671b4f7bc71c70eaf7ee439b5a4079f2de3ebd63de0a65bee4e
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The finite support screen passes independent review. Launch permission is
conditional on the separately pinned external watchdog wrapper. This audit
does not launch the full screen, run an optimizer, or infer feasibility from a
surviving case.

The scope is exactly the supplied catalog: all excess-link-isomorphism images
of four chosen saved point links, paired with their compatible excess profiles.
It is not an enumeration of every possible point-link block realization. Any
eventual exclusions apply only to these chosen catalog cases.

## Domain, residual rows, and pair ordering

The audit binds the separate catalog check, which independently verified all
5,536 chosen fixed block families and their complete profile fibers. It then
builds the complete ordered list of 195,296 distinct partial/profile pairs
directly from the thirty-eight fibers. This list agrees with the frozen
ordering: excess-link ID, then partial ID, then ascending profile ID. No support
screen is run over this full list during the gate.

Each selected point-one link fixes twenty distinct pentads containing point
one. The named profile requires point degree twenty, so the remaining forty-four
blocks avoid that point. The residual domain is all 3,003 such pentads, global
lexicographic IDs 1365 through 4367. There are 455 triples on labels 2 through
16, each initially contained in all sixty-six of its possible residual blocks.

For every benchmark case, the checker directly recounts the fixed blocks'
outside triples and reconstructs each residual demand as one plus the excess
indicator minus that fixed multiplicity. The eighty outside fixed triples are
distinct; residual demands are nonnegative and sum to 440. Any residual block
containing a zero-demand triple is forbidden because all remaining variables
are nonnegative.

## Independent benchmark replay

The checker imports neither producer and uses no producer bitmask routines.
It visits all residual candidate blocks as sets of triple ranks, tests them
against the zero-demand set, and builds support lists by direct incidence.
It separately constructs the documented 376-byte eligible-domain encoding to
compare the saved hash.

The exact fixed sample contains ordinals floor(i*195296/1000) for i=0..999.
All 1,000 saved records match the new method, including eligible counts and
hashes, failed row identities, demands, full support lists, forced block IDs,
every forcing-row certificate, survivor forced counts, and operation totals.

| Benchmark outcome | Cases |
| --- | ---: |
| Insufficient support | 794 |
| Immediate forced conflict | 141 |
| Survives the single pass | 65 |

A support row with fewer available blocks than its exact demand is impossible.
If support equals demand, every supporting block is forced. The audit checks
each recorded forcing cause against its complete support list. If those forced
blocks exceed any triple demand or the remaining cardinality forty-four, the
case is impossible. Only this initial support pass and its immediate conflict
check are reviewed; there is no iterative propagation or cover search.

Twelve damaged certificates are rejected: altered ordinal, profile, eligible
count or mask hash; wrong demand; missing support; wrong forcing row or demand;
missing forcing support or forced block; wrong survivor count; and an invented
survival label.

## Complete-loop and budget review

The pinned full runner imports the unchanged benchmark arithmetic. Source and
AST checks confirm one loop over range(195296), exactly one support-screen call
per started ordinal, no iterative outer loop, and a deadline check before each
new case. An exclusive launch marker prevents a second run. Normal completion
or cooperative cutoff records the exact processed prefix [0,next_pair_ordinal).
The outcome total must equal that cursor, and survivors are saved separately.

The forty-five-second figure is a cooperative processing budget. The runner
stops starting cases at 44.5 seconds. It does not guarantee a forty-five-second
whole-process limit, and its processing timer precedes final proof-file hashing
and result output. The gate therefore requires the pinned external wrapper:
fifty seconds before terminate, then five seconds before kill. The wrapper
checks all frozen dependencies and the catalog audit, saves an exclusive launch
receipt, captures stdout/stderr and process status, and records actual child
elapsed time including final child hashing and output. Its unchanged executable
body was inspected for normal, terminate, and kill paths; this audit does not
claim a new runtime test of those wrapper paths.

If the external watchdog interrupts the child, that is an incomplete run.
An absent final producer receipt or unfinalized compressed stream must not be
treated as a complete checked prefix. No automatic retry or continuation is
authorized by this gate.

## Frozen evidence

The gate binds the full manifest, full source, benchmark source and all thirteen
manifest dependencies, plus the independent catalog audit and external wrapper.
The new checker passes Ruff. Replay only the audit with:

~~~sh
uv run python experiments/2026-10-04/circulant-chosen-link-support-independent/check.py
~~~

Gate SHA256:
5a19e29f6dec86514298dc00dc8e6bebaee3b21a0fb38a7bbf39dfa662ba1fa1.
Full-screen manifest SHA256:
2c12c4372ef388026d7a6238b7789f72ad8dcaf74ba471035cb2dcdf86dc4439.
Required external wrapper SHA256:
c780d84eaa535fe2fc6966ee175d5dee862cd858504b55710c667b71dc51747b.
