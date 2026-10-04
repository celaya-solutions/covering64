```
Document:    Source-Backed Filter-and-Fan Repair Experiment
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      fc728e30bc644bcea792cafd8d34cca0ccb2f8f337bde2db195f1f4bbe0d6110
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# New mechanism and its source

Cesar Rego and Fred Glover, **Ejection chain and filter-and-fan methods in combinatorial optimization**, Annals of Operations Research 175 (2010), 77–105, DOI [10.1007/s10479-009-0656-7](https://doi.org/10.1007/s10479-009-0656-7). The [author-hosted PDF](https://leeds-faculty.colorado.edu/glover/fred%20pubs/399%20-%20ejection%20chain%20%26%20filter-and-fan%20w%20rego%20ANOR.pdf) is linked from [Glover's publication list](https://leeds-faculty.colorado.edu/glover/Publications-541.htm). PDF SHA256: `be5feccae174d9da6f10174510a2b4468f90ced532f7cc7ff2b8ef4b98dac1b0`. sources.json preserves exact URLs, UTC retrieval times, byte counts, hashes and access limitations. The modest 1,000,433-byte paper and rendered pages stay outside Git.

The author-hosted copy has no printed page numbers. The following references use 1-based PDF pages; pages 3–6 were text-extracted and visually inspected.

- **PDF pages 3–4, Section 2.1 and Figure 1:** filter-and-fan keeps eta1 selected states at each level. Each generates eta2 legitimate descendants; the best eta1 from the combined eta1*eta2 candidates continue. If a descendant improves the starting local optimum, return to local search. The depth cap, beam width and fan size control cost.
- **PDF pages 4–5, Section 2.2:** branch memory discourages reversals; tree memory diversifies different paths. More advanced variants adapt width and combine neighborhood types.
- **PDF pages 5–6, Section 3:** an ejection chain chooses later changes from the cumulative effect of earlier changes. The useful transition can end at the best intermediate level, rather than at the maximum chain depth. Ejection and trial-completion scores may be kept separate.

The paper covers generic methods and applications including routing, assignment, facility location and protein folding. It does not provide a C(16,5,3) result, and no speedup or success for this instance is inferred.

# Why this adds something to the saved search

`scripts/heuristic_search.cpp:78–90` already provides exact triple counts, block selection and incremental replacement. Lines 251–288 enumerate replacements covering a sampled missing triple, select a single winner, and commit it immediately. Lines 178–207 similarly commit one directed two-block trade. Dynamic weighting and decay are already present at lines 295–297. The essential/fixed-link/template solvers also already have longer atomic cycles. Those facts rule out advertising weighting, ordinary tabu, or merely larger swaps as a new mechanism.

The new proposal retains multiple partially repaired states and rebuilds their candidate moves from each state's newly exposed holes. A shallow losing move can survive while its continuation is evaluated. This mechanism was not found in inspected current native sources. Existing breadth-first experiments in docs/heuristic-search.md preserve every point degree at 20; the earlier 1,000-state beam repairs three excess point incidences. Those are prior beam experiments, but not this unrestricted, defect-directed replacement tree. Text searches alone do not establish absence from every historical artifact.

# Concrete adaptation, not a source claim

Use the already double-checked unrestricted 64-block three-hole seed, canonical SHA256 `d6dcfd2f1778f76c90ca67698865f683a44a6b69ddacad8f77cc4ee9021eacdf`, at `experiments/scratch/heuristic-tabu-2026100301-deficit-3.txt`. Reverify it before use. Keep exactly 64 distinct 5-subsets at every intermediate node, using global lexicographic block IDs and 1-based labels in files. Impose no point-degree, pair-multiplicity, incumbent-core, rotational or template restrictions. History and new-hole preference are soft ranking features only.

1. At stagnation, copy the current state and freeze triple weights for one search tree. For every current missing triple, enumerate all 78 containing blocks and all 64 outgoing slots. Reject only existing incoming blocks and malformed transitions. Deduplicate identical (slot,incoming) proposals reached from different missing triples.
2. Score each replacement with its exact weighted missing-triple change. Outgoing-only triples lose coverage precisely when their old count is one; incoming-only triples gain it precisely when their old count is zero. The correction for shared triples must be exact. Retain six best distinct children per parent, using seeded ties and soft history/new-hole preferences.
3. Across parents, retain twelve distinct resulting block sets; count sorting for state deduplication must not change saved block IDs or the global universe. Continue to depth twelve, updating each path's hole frontier. Freeze weights until the tree completes.
4. Save the best strictly improving prefix whenever discovered, even if the deadline cuts off a deeper search. If no prefix improves the root, leave the root intact. Separate tree attempts may change ties or weights; these remain heuristic choices with no completeness claim.

The ordinary exchange score/State move are natural insertion points, but use a separate experimental source so existing methods and their recorded evidence stay frozen. A faithful first prototype may omit a separate infeasible reference structure: every node is a valid distinct 64-block family, though its covering deficit can be positive. Therefore call it **filter-and-fan repair** rather than claiming it implements every part of the paper's ejection-chain framework.

# Proposed bounded evaluation

After source/model review, compare tree search against its single-path component move with six seeds 2026100361–2026100366 and 30 seconds per mode/seed. Both use the same seed family, scoring, weights and total wall-clock budget. Suggested tree parameters are width12, fan6, depth12; these are proposed settings, not values validated by the paper. Record evaluated moves, retained states, attained depth, best deficits, improved-prefix lengths, raw coverage traces, seed hashes, source/compiler hashes and wall-clock overruns. Report per-seed results, not a significance claim from six pairs.

Before pilot runs: replay every saved prefix from the starting family; independently recount all 560 triples and point degrees; undo each move in reverse and require byte-identical logical state; reject duplicate or damaged moves/traces and seeds; check time limits and interruption; run compiler warnings and sanitizer smoke. A putative zero-deficit family must pass both the package verifier and scripts/check_cover.py. Failure or timeout proves no lower bound.

Root has authorized prototype construction but requires a frozen review pack before paired pilots. No paired pilot was run while writing this source note.
