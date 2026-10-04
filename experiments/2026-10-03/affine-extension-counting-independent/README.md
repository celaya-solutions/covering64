```text
Document:    Affine Extension Counting and Circle Family Equivalence
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      865fdeeb6943fd48b9ab31bb129ffb93cea3fe8a98161f078f1ff5eda9fd28ac
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Restricted counting results

No 64-block cover in one of the six individual norm-circle families plus the
240 affine-line extensions can use exactly 20, 21, 22, 23, or 24 extensions.
These are finite counting results for those specified pools. They do not
exclude a 64-block cover using more extensions, mixed circle families, or other
five-point blocks. No solver infeasibility status is used in these counts.

The previous induced65 program was also checked. It used the 48 circles and all
240 extensions from the published Steiner17 source, with point/pair lower-bound
inequalities and target at most65. Its timeout did not exhaust the cases below.

## Independent geometry and the 20-extension case

`check.py` constructs the 20 affine lines and six 48-circle families directly over
GF(4), using the polynomial w²+w+1. The coefficients (a,c) satisfy trace(ac)=1
in q(u,v)=a*u²+u*v+c*v². The point label is
`(embed[u] XOR (embed[v] << 1))+1`, where embed=(0,1,6,7).

Every family and the lines partition the 560 triples:480 circle triples and 80
line triples. Each circle has ten secant lines. A line extension covers at most
one triple of any given circle, and does so precisely when its line is secant
and its extra point belongs to the circle.

Every line needs at least one extension because its four collinear triples
occur in no circle and no extension of another line. With exactly 20 extensions,
there is exactly one per line. If a circle is deleted, all ten of its secant
lines must contribute one covered triple. If two deleted circles share a secant
line but have no common point outside that line, its unique extension cannot
contribute to both. All1,128 circle pairs have such a line, in every family.
Thus this exact 20-extension case retains at least 47 circles, requiring at
least 67 total blocks. The independently generated first family and its complete
pair-blocker lists match the root audit exactly. Seven damaged geometry controls
are rejected.

## Safe pruning and the21-extension case

Let q be the number of extensions beyond the mandatory one per line. For a
deleted circle C, let M_C be its secant lines that contribute no covered triple.
The remaining ten−|M_C| secants contribute at most one incidence each plus at
most q extra incidences. Covering all ten circle triples requires |M_C|≤q.

For a deleted pair, every bad common secant either has an extra extension or
belongs to M_C or M_D. Therefore its bad-line count is at most 3q. For q=1,
the pair graph excludes the classes with four or five bad lines. It leaves
83,184 five-circle deletion sets in each family.

For a deletion set D, give each extension weight equal to the number of deleted
circles whose triple it covers. Let B be the sum over 20 lines of the maximum
extension weight. Among the 11 remaining choices on each line, take the q
largest weights globally. B plus these q weights is the maximum total incidence
obtainable with 20+q distinct extensions and at least one per line. It is a
necessary upper bound; it does not ensure coverage of distinct circle triples.

With q=1 every surviving five-circle set has capacity at most 45, below the 50
incidences required. All six families give identical histograms. A separate
root audit without pair pruning checks all 1,712,304 five-circle sets and obtains
maximum 46, also below 50; see `../affine-capacity-independent/`.

## Complete 22–24 extension counts

`run_capacity.py` checks all 240 affine maps x→a*x+b over GF(16), with a nonzero,
on the explicit line and circle lists. They preserve the original pool and act
transitively on its 48 circles. Each circle has a saved point permutation taking
it to circle 0. Consequently every nonempty deletion set has an equivalent set
containing circle 0. Enumerating all such sets is complete for existence in this
restricted pool; these sets are representatives, not disjoint orbit classes.

For E extensions and 64 total blocks, the number of deleted circles is r=E−16
and the number of extra extensions is q=E−20=r−4.

| Extensions E | Deleted circles r | Fixed-circle sets checked | Maximum capacity | Required capacity | Seconds |
| --- | --- | --- | --- | --- | --- |
| 22 | 6 | 1,533,939 | 55 | 60 | 0.805 |
| 23 | 7 | 10,737,573 | 66 | 70 | 5.932 |
| 24 | 8 | 62,891,499 | 75 | 80 | 47.424 |

The native program and ASan/UBSan build each match 1,000 independent geometric
oracle cases. Seven damaged models and five damaged queries are rejected by
each build. The first 1,000 enumeration cases are separately checked in Python
before a full count. All completed counts match the exact binomial totals.
The approved wall-clock limit was 60 seconds per count; the combined native
time was 54.161 seconds. These runs use no solver and no random selection;
the preflight oracle seed is 2026103981.

`family_equivalence.py` enumerates the 180 invertible linear maps over GF(4).
For each of the six circle families, exactly 30 maps carry that family to the
original while preserving the 20 lines. One explicit point map and its induced
circle map are saved for each family; four damaged-map controls are rejected.
This transfers the 22–24 results to each individual family. It does not transfer
them to the 528-block union of all six families.

## Reproduction and saved evidence

Run `uv run python experiments/2026-10-03/affine-extension-counting-independent/check.py`
to regenerate the 20/21 checks, and the adjacent `family_equivalence.py` for the
six-family equivalence certificate. Source body hashes are recorded in their
standard headers. JSON receipts bind the full source files and dependencies.

`run_capacity.py --preflight` builds the native and sanitized programs, checks
the oracle and controls, and writes a gate. The completed counts use
`--removed 6`, `--removed 7`, and `--removed 8`, each with `--seconds 60`.
The runner refuses to overwrite a previous full enumeration. Reproduction
must use a separate raw directory to preserve the frozen receipts.

Raw binaries, incidence masks, transitivity maps, queries and native outputs
are outside Git in `experiments/scratch/affine-extension-capacity-20261003/`.
Tracked receipts include `audit.json`, `preflight.json`, the three deletion
audits, and `family-equivalence.json`. No cover candidate was generated by
these counting experiments.
