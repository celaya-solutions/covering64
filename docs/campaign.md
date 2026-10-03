# C(16,5,3) research campaign

The initial goal is a set of exactly **64 distinct five-element subsets** of
`{1,...,16}` covering all 560 triples. A checked witness establishes
`C(16,5,3) <= 64`; it does not establish optimality or priority. A checked global
nonexistence proof at 64, together with a valid 65-block witness, establishes
`C(16,5,3) = 65`.

## Recovery status

This starter repository was reconstructed from retained conversation context
after the original filesystem became unavailable. The original uploaded
research report, raw pilot logs, source-download artifacts, dependency lock,
and commit history are not reproduced as originals. Historical outcomes below
come from the conversation record. Rebuilt source files and fresh checker/test
outputs must be identified as such. There is no claim that the original
repository, its commits, or its complete evidence package was recovered.

The conversation records a 65-block witness attributed by the LJCR v1.2 archive
to Rade Belic on 6 August 1997. Reconstructing that witness and matching the
recorded SHA-256 provides a useful recovery check, but it does not restore
the unavailable upstream artifacts. Its validity can be freshly established
by checking all triples again. The archive's current status and worldwide
novelty remain separate questions.

## Mathematical baseline

There are `binom(16,5) = 4,368` candidate blocks and `binom(16,3) = 560` required
triples. Each block covers ten triples, and each triple lies in 78 candidate
blocks. The Schönheim recursion gives:

```text
ceil(14/3) = 5
ceil((15/4) * 5) = 19
ceil((16/5) * 19) = 61
```

For the recursion, the blocks incident with any point, with that point deleted,
cover all `(t-1)`-subsets of the other points. Every point therefore lies in at
least `L(v-1,k-1,t-1)` blocks. Summing point incidences proves
`k*b >= v*L(v-1,k-1,t-1)` and taking a ceiling yields the next lower bound.
Fresh verification of a 65-block witness together with this derivation gives
the supported interval `61 <= C(16,5,3) <= 65`. This does not certify that no
stronger bound has appeared elsewhere.

## Historical pilot, reported in the conversation

The previous session reported two independent checks of the 65-block witness,
complete coverage, and canonical SHA-256
`89e4f68acba5d2cbee73e22d07dd1030e540b920fc7541619a065e998dc7d43f`.
Its triple multiplicities were 497 covered once, 56 twice, two three times,
and five seven times. The pilot reportedly exhausted all 65 deletions and
2,080 two-to-one exchanges of this incumbent without an improvement.

Two unrestricted 64-block CP-SAT runs reportedly returned `UNKNOWN` at
20 seconds each. Forty-eight sampled exchanges of sizes three through six
reportedly found no improvement; 32 had local infeasibility reports and 16
were unresolved. A proof-ready global CNF was generated, but no independently
checked global UNSAT proof was produced. These summaries are historical;
their original raw logs are unavailable. They do not settle the target.

## Two search lanes

**Constructive search.** Verify a starting covering before using it. Reproduce
small-exchange claims before relying on them. Remove `r` incumbent blocks,
identify newly uncovered triples, and seek at most `r-1` distinct replacements
from the full candidate universe, excluding retained blocks. Start with
`r = 3,...,6`, record budgets and seeds, and prioritize low-deficit removals.
Give unresolved larger neighborhoods meaningful budgets before interpreting
their outcomes. Equal-size exchanges can create different incumbent structures;
point relabeling alone produces an isomorphic covering and mainly changes
search ordering. A timeout leaves a neighborhood unresolved.

**Exact search.** Use one Boolean per candidate block, one coverage clause per
triple, and a cardinality bound of at most 64. Existence at most 64 is equivalent
to existence exactly 64: pad any smaller cover with unused distinct blocks.
Check the encoding on small instances and against the 65-block positive control
with a relaxed bound. CP-SAT can construct candidates; its infeasibility status
alone is not a checked certificate of global nonexistence. A global lower-bound
claim needs a proof-producing solver, independent proof checker, and audited
encoding.

Do not impose the incumbent's replication vector, high-multiplicity triple
structure, or cyclic/abelian symmetry on the global model. Selecting one block
as `{1,2,3,4,5}` can be justified by relabeling any nonempty cover; stronger
symmetry breaking needs a completeness proof. Deliberately restricted families
must be separate, explicitly named experiments.

## First 30 campaign days

| Window | Work | Required outcome |
| --- | --- | --- |
| Days 1–3 | Reproduce provenance when available; check benchmark and damaged controls; derive 61; check small encodings. | Fresh baseline checks, hashes, exact commands, and clear recovery limitations. |
| Days 4–10 | Run larger exchanges, diverse constructive starts, and bounded global seeds. | Checked witnesses or explicit unresolved run outcomes. |
| Days 11–14 | Benchmark proof-producing SAT and justified partitions. | Observed completion rates and proof sizes; no unmeasured runtime predictions. |
| Around day 14 | Apply the stop gate below. | Evidence-supported next experiment or a scoped fallback. |
| Days 15–18 | Complete viable proof shards or one defined restricted-family question. | Checked certificates for a complete scope or a clearly conditional result. |
| Days 19–24 | Reconstruct/check witnesses or proofs independently; audit reductions and encoding. | Evidence package meeting the [evidence policy](evidence-policy.md). |
| Days 25–30 | Recheck current records and literature; write the smallest supported claim. | Correctness, scope, and novelty distinguished. |

The schedule is a campaign structure, not a promised solution time. Initial
computations are CPU-based; no GPU speedup, hardware requirement, or full-proof
runtime was established by the historical pilot. Measure actual resource use.

**Two-week stop gate.** If no 64-block witness appears and exact search yields
neither manageable proof shards nor useful proved constraints after roughly
two weeks, stop the unrestricted campaign for that cycle. Define one precise
structural question from the logs, check whether it is already settled, and
state its restriction. Unsuccessful compute and infrastructure are not theorems.

**Success gate.** Preserve a candidate immediately and pass it to two separately
implemented checkers. Freeze the checked witness before further modifications.
A global UNSAT artifact requires independent proof checking and an encoding
audit. Preserve failed controls and runs that influenced the final conclusion.

## Source provenance and remaining leads

The retained conversation identifies pinned DOI
[`10.5281/zenodo.19735294`](https://doi.org/10.5281/zenodo.19735294),
LJCR v1.2 dated 24 April 2026. During this rebuild, the versioned metadata was
retrieved again, the complete `coverdata.json` MD5 was checked, and the exact
witness was fetched from its pinned HTTP byte range. Both rebuilt checkers
verified it anew. See [fresh provenance](../data/provenance/README.md).
The entire 4.19 GB `covers.json` MD5 remains unverified. The original download
artifacts and historical raw pilot logs were not recovered.

The original report's opaque citation markers were not usable bibliographic
links. Its recent symmetry-restricted claims remain unverified leads. Check
current primary records and exact-parameter literature before substantial
compute or a novelty claim. No outreach is authorized by this starter package.
