```text
Document:    C(16,5,3) Research Checkpoint
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      ab436808078d7f8f309636b1d70d8a9cae6067df42e7cdac0cd794ea3dc1bae8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# C(16,5,3) research checkpoint

The 64-block goal remains open. The best saved 64-block state covers 557 of 560
triples. Both cover verifiers reject it as incomplete. The known full cover uses
65 blocks. Current primary-source tables still report bounds 61 through 65.

## Checked restricted results

The Belic cover has a rigid 60-block core. Keeping it leaves 15 triples uncovered;
each possible added block covers at most three. Its five independent completion
supports each allow 12 fifth-point choices, giving 248,832 valid 65-block completions.
Two covers derived from C(17,6,4) are nonisomorphic as full covers but have this
same core up to relabeling; they do not establish a new search basin.

Exact rational LP dual certificates rule out every 64-block completion retaining
at least 58 of the specified core blocks. All 1,831 zero-, one-, and two-block
removal cases were checked with a separate standard-library verifier. The smallest
exact margin above the available replacement budget is 9/14. This is a restricted
core-distance result, not a global lower bound or nonexistence theorem.

Run `uv run python scripts/check_core_certificate.py
experiments/2026-10-03/core-distance-2.json.gz` on one shell line to check the
compact certificate. Its SHA256 is
`e3ab243e3e198c3e785b8561e53319c45b55fd8683fd9d9eeeab8683817112cb`.
The original helper used to generate it is archived alongside the certificate;
the current helper uses bounded common denominators to keep new evidence small.

Seventeen explicitly specified regular permutation actions were each checked by
enumerating all 226,387,980 four-orbit selections. No complete cover occurred.
The best actions covered 34 of 35 triple orbits (544 triples). This is neither a
classification of 17 distinct groups nor an unrestricted exclusion. An independent
reconstruction of all group actions and orbit masks agreed with the saved masks.

## Search and validation

Search tools now include weighted local search, fixed-link and neighborhood
CP-SAT searches, native-cardinality SAT, group-orbit enumeration, valid-cover
trade walks, and exact rational LP screening. LP screening rejects a neighborhood
only when independently checkable dual weights exceed its replacement budget.
UNKNOWN and timeouts are inconclusive. Ongoing campaigns and larger raw logs stay
in `experiments/scratch`; compact witnesses, controls, provenance and certificates
are retained here. No discovery was published and no researcher was contacted.

The test suite passed 96 tests plus 10 subtests before this checkpoint. Compiler
controls reject malformed and damaged inputs. The restricted search modes are
explicitly documented and are not imposed on the unrestricted model.

## Next search split

For any cover of at most 64 blocks, every point occurs at least 19 times. Thus
either every point occurs exactly 20 times, or one point has degree 19. In the
second case its 19-block, four-point link has fourteen vertex degrees 5 and one
degree 6. The pair-excess graph must be a four-edge star plus five disjoint edges.
This pattern can be normalized by relabeling without fixing an incumbent link.
The next exact search treats these two exhaustive cases separately and avoids
combining their normalization with an incompatible degree ordering.
