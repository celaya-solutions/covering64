```text
Document:    Exhaustive Hub Count Split for the Four-Sevenfold Branch
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      e9e742f553ad27fec5ede1f751dbaff9747417c5768ef2c0d9eddb0c9fde7011
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Six exhaustive integer cases

This split applies only to the normalized regular 64-block branch with four
sevenfold triples. It imposes no extra symmetry on the cover. The hubs are
4, 8, 12 and 16. Let z count doubled all-hub triples, and let m_j count
nonheavy blocks with j hubs. Every nonheavy block has at least one hub because
it has at most one anchor from each of four groups. The 28 heavy blocks have
at most two hubs, so every block with three or four hubs is nonheavy.

For a hub pair of multiplicity five, the fourteen covered triples through that
pair have fifteen incidences in total. Their total excess above one is exactly
one. Every all-hub triple contains such a pair, so its multiplicity is one or
two. In the cycle case each all-hub triple contains exactly one of the two
nonedge pairs. In the matching case it contains exactly two of the four
nonedge pairs. Charging doubled all-hub triples to these excess units proves
z <= 2 in both cases.

Counting hub-triple incidences gives m_3 + 4 m_4 = 4 + z. All quantities are
nonnegative integers, hence m_4 is zero or one. Every integer covering thus
belongs to exactly one of the following six cases; retaining only one case
would restrict the search.

| Four-hub blocks m_4 | Doubled hub triples z | m_1 | m_2 | m_3 | Heavy hub-pair edges H |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 16 | 16 | 4 | 6 |
| 0 | 1 | 17 | 14 | 5 | 5 |
| 0 | 2 | 18 | 12 | 6 | 4 |
| 1 | 0 | 14 | 21 | 0 | 7 |
| 1 | 1 | 15 | 19 | 1 | 6 |
| 1 | 2 | 16 | 17 | 2 | 5 |

The other columns follow from 36 nonheavy blocks, 60 nonheavy hub incidences,
and 34 total hub-pair incidences: m_1=16+z-2m_4, m_2=16-2z+5m_4,
m_3=4+z-4m_4 and H=6-z+m_4. They are consequences, not new restrictions.

The helper adds only two equalities: the sum of all-four-hub block variables
is m_4, and the sum of all-hub-triple incidences is 4+z. It preserves every
existing variable and row. Case identifiers and model hashes must be kept
with future results. A branch exclusion requires checked exclusions for all
six cases. A timeout or numerically feasible LP does not settle a case.
