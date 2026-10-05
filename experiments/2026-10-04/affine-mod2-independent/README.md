```text
Document:    Independent Affine Parity Certificate Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      a2d46b14be9be7073ca2f326318371ffc06d0c092c6c478a868fd09cc62f0645
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent parity certificate audit

All 505 saved parity contradictions passed independent certificate checks.
All 616 saved parity-consistency claims also passed an independent column-space
calculation. The complete 1,121-case input and outcome stream was verified.
No producer code was imported or rerun, and no optimizer was called.

| Input scope | Checked contradictions | Mod-two consistent |
| --- | ---: | ---: |
| Original chosen-witness catalog survivors | 484 | 612 |
| Expanded catalog sample survivors | 21 | 4 |
| Total | 505 | 616 |

The four held completion cases therefore have these outcomes: pair 55433 is
mod-two consistent; pairs 48366, 51739, and 135193 have independently checked
parity contradictions. This confirms that three of the held search cases can
be excluded without launching them. Passing parity does not establish that the
remaining case has a completion.

## Independent reconstruction

The checker independently enumerates all 4,368 lexicographic five-subsets,
identifies the 1,365 containing point one and all 3,003 avoiding it, and builds
each completion column from its ten triples plus the exact cardinality row.
There are 455 outside-triple rows, each with 66 columns, and one cardinality row.

Every pinned partial has twenty distinct blocks containing point one. Direct
integer counting verifies all 105 point-one equations, eighty distinct outside
triples, 185 covered triples in total, and 200 triple incidences. Subtracting
those exact counts from the complete profile gives nonnegative residual demands
summing to 440, plus the demand for forty-four remaining blocks.

Only zero-demand rows remove columns. Since every variable is nonnegative,
every column occurring in such a row must be zero in any integer completion.
All other 3,003-domain columns remain eligible. No propagated assignments,
incumbent incidence assumptions, or symmetry assumptions enter this test.

## Certificate and consistency checks

For each contradiction, the checker validates strict, sorted, unique row IDs.
It sums the selected exact equations modulo two and checks every eligible
column directly: all coefficients cancel, while the summed right-hand side is
odd. Thus an integer completion would require zero to equal one modulo two.
This is a finite checked certificate for that exact profile/partial case.

For each consistency claim, an independent algorithm forms the column space
with highest-row pivots, unlike the producer's lowest-column row elimination.
It checks that the right-hand-side vector belongs to that space and verifies
the reported matrix rank. For contradiction records, it also independently
checks the rank and consistency of the row prefix before the first contradictory
row. All saved rank metadata agrees.

The checker verifies every input identity and its ordinal in the respective
original or expanded catalog, every output position, and both input substream
counts. The expanded binary catalog is bound by its compressed and uncompressed
hashes and fixed forty-byte record format. The executed producer source is
pinned through the unchanged `executed-source.txt` archive; the reformatted
current source is not claimed to have produced the result.

Sixteen damaged controls were rejected, including missing, duplicated,
reordered, malformed or altered certificate rows, an even right-hand side,
wrong case identities, a wrong rank, and a damaged consistency right-hand side.
Ruff passes. Individual replay records and aggregate counts are saved in small
tracked receipts, each below one million bytes.

## Scope and reproduction

These certificates exclude 505 exact partial/profile completion cases only.
The 616 consistent systems pass a necessary parity condition, not the full
integer covering equations. The expanded group is a 25-case sample, and the
original group belongs to the four chosen-witness catalog. No full cover or
unrestricted nonexistence claim follows.

```sh
uv run python experiments/2026-10-04/affine-mod2-independent/check.py
uv run ruff check experiments/2026-10-04/affine-mod2-independent
```

Independent review SHA256:
`abfc1ee5faa0b1ec34f827d1f7f1fbcee287de6137c4a32ebcc89d5f46fae607`.
