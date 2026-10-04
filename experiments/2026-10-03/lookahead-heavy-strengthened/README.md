```
Document:    Fixed-Heavy Pair and Triple Strengthening
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      086c2ee7fd231c8c56d59a3df1b357c7aa0322880a3e7fb857f5ab6e274c2fc2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Pair and triple strengthening

This is a separately frozen version of the ten-hole tuple completion model.
It keeps every one of the 1,200 ordinary block variables and all original rows.
It adds 114 equalities for pairs touching an anchor point and bounds each of the
six hub pairs between five and seven. The upper bound of each of the 556
nonheavy triple rows becomes two minus its fixed-heavy incidence. There are
697 rows in total. No particular hub graph is fixed.

## Why every completion is preserved

For any covered pair, each containing block covers three of its 14 triples.
The pair therefore occurs in at least five blocks. An anchor point has its two
anchor-peer pairs in the seven own heavy blocks, so both counts are at least
seven. Its own hub appears in two own heavy blocks. The triples consisting of
this point, that hub, and each of its two anchor peers are both repeated.
Thus this pair must occur at least six times: five blocks would supply only
15 triple incidences, with two repetitions leaving at most 13 distinct triples.

The sum of the 15 pair counts at a degree-20 anchor point is 80. Their lower
bounds already sum to 7 + 7 + 6 + 12*5 = 80. Every such count therefore equals
its bound. This proves all 114 anchor-touching pair equalities without a hub
pattern assumption.

At each hub, its 12 anchor-touching pair counts sum to 3*6 + 9*5 = 63.
The remaining three hub-pair counts sum to 17. Subtracting the lower bound five
on each hub pair gives a nonnegative integer degree-two multigraph on four
vertices. Each edge has multiplicity at most two, so each hub-pair count is at
most seven. Exhaustive enumeration gives six graphs: three four-cycles and
three doubled perfect matchings. All six remain allowed in the model.

A pair occurring five times supplies 15 triple incidences to 14 covered triples.
No containing triple can therefore occur more than twice. For each of the six
hub graphs, every nonheavy triple admitting an ordinary block contains such a
pair. The other 156 nonheavy triples have no ordinary support and are already
fixed by the heavy blocks at one or two incidences. Thus the upper bound two
preserves every complete cover in this family.

`check_preservation.py` independently replays these finite incidence facts,
enumerates all six hub graphs and checks all 556 nonheavy triples. It does not
import the model builder. The argument assumes coverage, degree 20 and the
regular four-sevenfold heavy templates. It makes no unrestricted reduction or
global lower-bound claim.

## Artifacts

`manifest.json` binds the source model, source gate, builder and strengthened
model. Removing the new pair rows and restoring the old triple upper bounds
reproduces the exact earlier model. Large model and LP artifacts stay in ignored
scratch directories. The linear relaxation is screened separately; only an
exact rational primal or a replayed rational dual establishes its outcome.

## Checked completion obstruction

The stronger fixed-heavy LP returned an exact rational separating certificate.
Root independently reconstructed the strengthened model and replayed all 531
signed rows against all 1,200 ordinary columns. The weighted lower bound is
10629/1000, while the maximum over the unit box is 87/1000, leaving a positive
gap 5271/500. Five damaged certificates were rejected.

This proves that the ten-hole state's fixed 28 heavy blocks cannot complete in
the regular four-sevenfold family, even with every hub graph allowed. It does
not exclude a complete first-link representative or change the 109-entry
first-link exclusion union. A reusable inequality in variable heavy patterns
has not yet been derived or audited.
