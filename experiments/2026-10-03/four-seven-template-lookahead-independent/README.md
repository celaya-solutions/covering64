```text
Document:    Independent Native Anchor-Lookahead Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      78d10c1c9f1bd89bfc936bfe4ba11f21af8c0d20660de31c9990eeaa65003a7c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent gate passed

The frozen v1.2.0 native source was reviewed as a diff against the previously
checked v1.1.0 source. A fresh warning-clean AddressSanitizer and
UndefinedBehaviorSanitizer build passed the tests below. The exact source,
checker, oracle, fixture, binary and build-command hashes are in `audit.json`.

The independent Python oracle rebuilds all triple counts from H plus each
of the 1,200 ordinary candidates. It uses the 114 pairs that touch an anchor
point; it never imposes a target on the six hub-only pairs. It independently
recounts pair excess and compares the complete admissible-block set and
unsupported-triple set with the native output, as well as every count and
score field.

The gate tested 32 fresh catalog tuples, 16 in each case, using fixture seed
2026104201. They include nonzero heavy-pair excess, zero excess with no
unsupported triples, and zero excess with one, two or five unsupported
triples. Repeated queries in each native process exercise cache hits. Separate
controls in both cases set capacity two, trigger the actual eviction branch,
refill the original tuple, then restore production capacity 100,000.

Two fresh short sanitizer searches produced 38 saved states and eight forced
operation records, covering all four move types. Each state was checked
against the independent legality/catalog checker and complete lookahead
oracle. Ordinary moves preserve the heavy tuple and cache counters. Whole
heavy-template moves and their rollbacks restore the exact lookahead sets
and scores. Raw-hole and score minima are checked separately. Fourteen
altered output fields are rejected.

The native code executes an explicit zero-hole acceptance assertion with a
positive score change of one million. Static review also checked the retained
initial/control/main-loop/perturbation save paths and unconditional zero-hole
acceptance. A synthetic acceptance assertion is not a discovered cover.

The primary search agent separately checked 74 saved smoke states and 12
operation records with both covering verifiers, rejected 17 malformed inputs,
and exercised one actual production-capacity eviction. Those are separate
receipts in `four-seven-template-native-lookahead`. The independent gate here
cleared only the already approved single 300-second, one-worker cycle pilot.

# Scope and replay

The necessary anchor-pair budgets and their degree-20 native-family proof are
recorded with the seven-block obstruction in `cycle-soft-heavy-completion`.
Lookahead counts unsupported triples as a soft penalty of weight 100; it does
not prove that a tuple with count zero has a completion. This gate establishes
neither a new cover, search completeness nor an exclusion registry change.

`oracle.py` is the independent arithmetic oracle. `prepare_oracles.py` saved
32 fresh seed states and expected sets in ignored scratch; its manifest is
`oracle-fixtures.json`. `check.py` binds those bytes, rebuilds the native
sanitizer binary, compares all fresh tuples and exercises cache/search controls.
Large detailed query logs and sidecars remain in ignored scratch.
