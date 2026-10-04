```text
Document:    Auditable Bound Propagation Before CNF Translation
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      df67ba59b235827b7dd247613136f98e032a279042ebbb49a3864f38a852450c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Separate propagated variant

This separate v1.0.0 preparation preserves the two original restricted CP
models and the previously audited threshold encoder. Matching-063 passed the independent propagation and clause audit before its
binary-DRAT pilot. The matching-029 propagated variant remains preparation only. The original source variables, including all
4,368 lexicographic block variables, retain their indices and Boolean domains.
The source models and all reason traces are hash-bound in the manifest.

For each original linear or exactly-one row, the builder aggregates repeated
variables and signs into an integer linear expression with bounds. Already
proved values contribute a constant. An unknown Boolean term with coefficient
a contributes the interval `[min(0,a),max(0,a)]`. The sum of these intervals is
the exact attainable minimum and maximum; holes within the interval are not
assumed attainable.

For each unknown variable, the builder recomputes the interval with that
variable fixed to 0 and to 1. It forces a value only if the other value's
interval misses the original row bounds. Missing the interval is sufficient
for impossibility, even when coefficients create internal gaps. All values
forced by one visit are derived from the same prior state, then applied as a
batch. Single-variable rows are visited first, followed by repeated full row
passes until no more values are proved. There is no guess or incumbent-derived
assumption.

# Trace and equivalence

The compressed reason file has `steps`, `values`, `origins`,
`contradiction_step`, and `substitutions`. A step records its original row,
prior supporting step IDs, assigned-variable count, constant, minimum/maximum,
original lower/upper bounds and forced entries. Each forced entry is
`[variable,value,min_at_0,max_at_0,min_at_1,max_at_1]`; indices are zero-based
source variable IDs. Dependencies point only to earlier events. The independent
checker can reconstruct each original row and arithmetic interval in sequence.

Inductively, every recorded value is entailed by the original model. Substituting
those values in each row preserves its solutions. Clipping bounds to the
remaining Boolean expression's minimum and maximum also preserves solutions.
Every propagated assignment is retained as an explicit original-variable unit
row, so every residual solution satisfies all original rows, and every original
solution satisfies every residual row. The unchanged threshold encoder then
provides its previously proved existential equivalence for the residual rows.

Both prepared models retain 55,528 original variables. There are 15,663 proved
assignments, no contradiction, and 20,222 residual rows including every explicit
unit. Matching-029 has 2,925 reason events, 709,162 CNF variables and 2,286,622
clauses. Matching-063 has 2,928 events, 708,916 variables and 2,285,639 clauses.
All large residual models, traces and CNFs remain in ignored scratch. The original CNFs and their proof attempts remain unchanged.

# Matching-063 gate and bounded binary pilot

The root independent checker replayed all 2,928 reason events and 15,663
assignments, rebuilt every residual row and all 2,285,639 clauses, and rejected
eight damaged reason traces. Its receipt is in the sibling
`four-seven-template-cnf-propagated-independent` directory. Binary-format toy
controls accepted the eight-byte valid proof and rejected an empty proof and
a proof paired with the wrong satisfiable model. No tools were rebuilt.

The single approved matching-063 pilot used seed 2026104001, CaDiCaL's default
binary DRAT output, a 300-second native limit, 330-second hard wait and
512-MiB per-file cap. It ended UNKNOWN with exit 0 after 300.068461 measured
seconds and saved 123,770,022 bytes of partial proof. No checker was run, no
witness was produced and no exclusion follows. The saved solution marker
`c UNKNOWN`, proof size and proof/log hashes were read back. Do not repeat
this unchanged pilot.

The wrapper and tool/gate snapshots are preserved under
`experiments/scratch/four-seven-template-propagated-binary-drat-v1.0.0/`.
`binary-proof-results.json` is the compact result receipt. The 109-case union
therefore remains unchanged, with matching-063 still open.
