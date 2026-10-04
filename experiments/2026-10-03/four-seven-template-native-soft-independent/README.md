```text
Document:    Independent Soft-Score Native Search Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      3185a23a96a278db8e9bb58faac7dd4ff67e6e3862328e76edd004467880741d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked behavior

The v1.1 native search keeps the previously audited catalogs, degrees, legal
moves and rollback rules. The changed source was reviewed as an exact diff
against the independently checked v1.0 source. The new score is five times
uncovered triples, plus the L1 distance from target pair counts, plus five
times excess above two for nonheavy triples. Pair penalties guide the search;
they are not additional hard restrictions.

The checker imports only the previous independent legality/catalog checker,
then independently reconstructs pair targets and all triple/pair counts. It
checks operation deltas from the explicit removed/added blocks and separately
recounts before/after snapshots. Every score field is tested with a damaged
value. Best raw-hole and best-score files are separately bound to final logs
and checked against all eligible saved states. The raw best alias is checked.

Both seeds have 64 distinct blocks of degree 20. Matching starts at 21 holes,
pair L1 30, nonheavy excess 4, score 155; cycle starts at 19 holes, L1 24,
excess 3, score 134. The gate rebuilds the exact source with warning errors,
AddressSanitizer and UndefinedBehaviorSanitizer, exercises all four move modes
and rollback, and records fresh checks in `audit.json`. The current receipt
is authoritative for snapshot counts.

Static review confirms a projected zero-hole main-loop move bypasses score
acceptance, is saved as the raw best and stops the search. A cover reached in
forced controls or restart perturbations is also retained. No claim of move
connectivity, search completeness, exact exclusion or a new cover follows.
