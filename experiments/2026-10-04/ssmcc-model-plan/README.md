```
Document:    SSMCC Covering Model Equivalence and Generator Plan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0ed7bee672b5abc5b86529e35ab20258d411e0f793e3439624ac2982d63cad78
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# SSMCC model equivalence and generator plan

This is a read-only formulation and preparation plan. No SSMCC program was compiled, generated instance searched, or construction optimizer launched for this plan. The source review lives in the neighboring `next-route-source-review` artifact. Native parser and option-selection behavior still need an independent gate before any solver run.

## Exact mathematical encoding

Enumerate all 4,368 five-subsets of labels 1 through 16 in lexicographic order. Give each subset exactly one distinct option row and bind its row index to the same global block ID. Use 560 primary triple items with multiplicity interval [1,64], one cardinality primary item [64,64], and two named core primary items [0,55] whose 60-row incidence sets come from the audited original and mapped cores. Each option contains its ten triples, the cardinality item, and any applicable core item. This is 563 items and 48,168 incidences: 4,368 times 11 plus two times 60.

Every 64-block cover supplies 64 distinct rows. All triple lower bounds hold by coverage, the cardinality is exactly 64, the upper triple bound is automatic, and the two core bounds follow from the separately checked core-cap theorem and exact point-map transport. Conversely, selecting rows at most once and satisfying these intervals gives exactly 64 distinct five-subsets and covers each triple. Hence the intended model is equivalent to existence of a 64-block cover, provided the native option semantics really select each row at most once. No fixed heavy set, point-incidence pattern, graph family, or symmetry assumption enters the encoding.

A newly witnessed third core may be added only after its independent point-map/core-cap audit passes and the exact 60 IDs are bound. That would give 564 items and 48,228 incidences. The generator must record its selected core list explicitly rather than silently changing the original two-core model.

## Generator and parser gate

1. Freeze exact upstream source bytes and SHA256 values for base SSMCC and any separately chosen weighted change file, toolchain version, and generated program. Keep large source archives and build outputs outside Git.
2. Derive deterministic item labels and all 4,368 rows directly from combinations. Independently regenerate every row, all 43,680 block/triple incidences, exact cardinality/core incidences, row uniqueness, and variable order. Save a small manifest with dimensions and hashes.
3. Validate the interval syntax against Knuth's DLX3/SSMCC source documentation, including [0,55]. Check native parsing and chosen-row identity on tiny independently enumerable controls before claiming equivalence of the emitted text to the mathematical model. Controls must include zero lower bounds, exact cardinality, optional core membership, repeated option attempts, malformed bounds, duplicate item labels, and out-of-range row IDs.
4. Check both package and standalone covering verifiers on each extracted candidate. Preserve budgets, seeds or deterministic settings, source revisions, solver versions, logs, witnesses, and status. A timeout remains inconclusive. A native no-solution report is not an independently checked theorem without a suitable audited proof path.

Knuth describes SSMCC as a rewrite of DLX3 for sparse-set dancing cells. The proposed WTD change uses failure weights for branching; it must not be confused with DLX5 cost semantics or assumed to optimize a covering objective. Base and weighted variants need separate frozen identities and configuration receipts.

Primary sources: [Knuth programs](https://www-cs-faculty.stanford.edu/~knuth/programs.html), [DLX3 source](https://www-cs-faculty.stanford.edu/~knuth/programs/dlx3.w), [SSMCC source](https://www-cs-faculty.stanford.edu/~knuth/programs/ssmcc.w), and [SSMCC WTD change](https://www-cs-faculty.stanford.edu/~knuth/programs/ssmcc-wtd.ch). These were supplied by the web agent's read-only source review; this plan does not claim an executed native-format validation.
