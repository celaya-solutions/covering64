# Evidence and claim policy

Each mathematical claim must identify its scope and supporting artifact.
A verified witness proves an upper bound; a failed search does not prove a
lower bound. Recovered summaries are not substitutes for original evidence.

## Recovery distinctions

Label retained conversation summaries as **historical, raw artifacts unavailable**.
Label rebuilt code and witnesses as **reconstructed**. Label checks actually
executed against the reconstructed files as **fresh rebuild checks**. Do not
fabricate original solver logs, download metadata, timestamps, commits, or the
uploaded discovery report. New hashes identify rebuilt artifacts unless their
equality with a specifically recorded historical hash is freshly checked.
Neither a reconstructed source file nor a ZIP restores the lost Git history.

## Supported claims

| Evidence | Supported statement |
| --- | --- |
| Freshly verified cover with `b` distinct blocks | `C(16,5,3) <= b`. |
| Reproduced Schönheim derivation | `C(16,5,3) >= 61`. |
| Budget exhausted, timeout, or solver `UNKNOWN` | No witness found within that run; feasibility unresolved. |
| CP-SAT `INFEASIBLE` without checked proof | Outcome for the saved model; no certified global nonexistence theorem. |
| Independently checked proof for an audited unrestricted at-most-64 encoding | `C(16,5,3) >= 65`; with a valid 65-cover, equality follows. |
| Checked proof for a restricted model | Nonexistence only within that named family. |
| Exhausted local exchanges | A property of that incumbent and specified neighborhood. |
| Conversation-recorded old outcome without raw logs | A historical summary, not a fresh experiment or recovered certificate. |

## Witness acceptance

Labels must be exact integers in `1..16`. Each block must contain five distinct
labels. Blocks must be distinct after sorting their labels. JSON booleans,
floats, strings, and nulls are rejected as labels. Never silently repair input.
Require all 560 triples covered and, for the initial target, exactly 64 blocks.

Preserve original submitted bytes and their SHA-256. Canonical bytes sort labels
within blocks, sort the block list lexicographically, and write ASCII space-
separated rows with one LF per row. Their hash identifies the object with its
current point labels; it does not identify isomorphism classes under relabeling.

The [standalone checker](../scripts/check_cover.py) shares no package code,
parser, incidence masks, or solver state. It enumerates every required subset
and counts the block sets containing it. Its JSON includes uncovered subsets,
multiplicities, incidence counts, point replication, and source/canonical hashes.
Run it separately, without installing the package:

```bash
python scripts/check_cover.py PATH_TO_WITNESS --expected-blocks 64
```

Exit 0 means coverage and requested cardinality passed; exit 1 means valid
structure with deficient coverage or wrong cardinality; exit 2 means malformed
input or read error. Retain its output with a separately implemented package
checker. Use deleted-block, duplicate-block, out-of-range-label, and malformed-
label controls. Repeating a model run does not provide independent verification.

## Nonexistence acceptance

Save the entire formula, variable mapping, cardinality encoding, parameters,
generator revision, solver version/flags, logs, and proof bytes. Use a proof
checker independent of the generator; retain its version, command, exit code,
output, and artifact hashes. A solver's `UNSAT` terminal word is not the proof.

Proof checking establishes unsatisfiability of the formula supplied. Separately
audit that the formula represents the unrestricted mathematics: all 4,368
distinct blocks, all 560 triples and their 78 admissible containing blocks,
equisatisfiable cardinality auxiliaries, and complete symmetry breaking.
For case decomposition, prove case coverage and check every leaf certificate.
An unresolved leaf leaves the global question unresolved.

Positive benchmark and damaged controls test implementation; they do not
replace an encoding completeness argument, proof of safe reductions, or
independent certificate checking. State restricted assumptions prominently in
both run metadata and mathematical claims. CP-SAT `OPTIMAL` on a feasibility
model does not establish the covering number's mathematical optimality.

## Provenance and novelty

Archive attribution and mathematical validity are separate. A verified
transcription proves coverage but does not establish its claimed historical
source. Preserve actual downloaded bytes, hashes, upstream published hashes,
retrieval dates, usable URLs, extraction rules, and derived witness artifacts.
Record external claims as verified, unresolved, or contradicted. Opaque research
session citation markers are not standalone primary references.

Before claiming a public-record improvement, compare with current primary
repository entries and exact-parameter literature. Log search terms, dates,
and limitations. A valid 64-cover remains valid if an earlier one is found;
its novelty and attribution change. Negative literature searches cannot prove
worldwide priority. This initial work does not authorize contacting researchers.

## Run records

Fresh runs should retain exact commands, code revision, dependencies and solver
versions, OS/architecture, parameters, resource budgets, seeds, starting witness,
output witnesses, complete solver logs, and checker results. Separate observed
outcomes from hypotheses and estimates. Record prompts that materially affect
mathematical choices and only model metadata actually exposed by the interface.

Choose labels such as `witness_verified`, `budget_exhausted`,
`solver_infeasible_unchecked`, and `unsat_proof_checked` only when the matching
evidence exists. Record full-universe, restricted-family, or neighborhood scope.
Retain failed experiments that motivated new hypotheses. Historical outcomes
with unavailable logs should never be relabeled as fresh checked runs.
