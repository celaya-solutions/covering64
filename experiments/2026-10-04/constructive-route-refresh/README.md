```text
Document:    Refreshed Bounds and Four-Link Classification
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      e7d012a67cee4721ab17f2e50f21c1905c5039b8195e965fea7760986c62d94d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Refreshed bounds and four-link classification

This refresh identifies no new four-link construction route. The four published
minimum links, their exhaustive degree split, and their independently replayed
classification were already present in this project.

## Public bound: dated archive evidence

The [maintainer page](https://dmgordon.org/covering-designs/) links the official
[Zenodo database](https://zenodo.org/records/19735294). Its README states that the
database was frozen in March 2026. Freshly downloaded metadata records
`61 <= C(16,5,3) <= 65` and `C(15,4,2) = 19`. The 65-block entry credits Rade
Belic on 1997-08-06. These are verified archive values, not a claim that every
later result has been surveyed. The older LJCR host failed DNS during this
refresh. Only metadata, README and reader code were downloaded; the large cover
archive was not downloaded, and downloaded code was not executed.

## Four classes means exhaustive minimum-link classification

Allston, Buskens and Stanton, *An examination of the non-isomorphic solutions to
a problem in covering designs on fifteen points*, JCMCC 4 (1988), 189–206,
[primary PDF](https://combinatorialpress.com/article/jcmcc/Volume%2004/vol-004-paper%2015.pdf),
studies minimum 19-block pair coverings by quadruples. In that scope,
Theorem 12 (printed page 204) states there are four distinct coverings: B3,
B4, D1 and D2. The theorem is an exhaustive classification up to isomorphism,
not merely four examples and not a classification of larger pair coverings.
Theorem 5 covers exactly two extension cases, and the final cases establish
the other two classes. The theorem and its scope were checked in the primary paper; its full case
analysis was not independently re-proved in this refresh.

For any covering on 16 points with at most 64 pentads, a fixed pair must occur
at least `ceil(14/3) = 5` times. Summing the 15 incident pair counts at a point
therefore gives `4 r >= 75`, hence point degree `r >= 19`. Total point degree
is at most 320. Thus either some point has degree 19 and its link is one of
these four minimum pair covers up to relabeling, or every point has degree 20
and there are exactly 64 blocks. This complete degree split is a prior project
result, not a new restriction on the unrestricted problem.

## Exact lists and existing witnesses

The fresh PDF matches the previously archived PDF byte for byte. The lists
were checked against printed pages 195, 196 and 199. Each freshly transcribed
19-block list passes both package and standalone verifiers for `(15,4,2)`.
Direct standard-library pair counting and replay of the saved explicit point
maps also pass. The receipt contains every published symbolic block and map.

| Published class | Existing shape | Existing solution number |
| --- | ---: | ---: |
| B3 | 47 | 042 |
| B4 | 44 | 001 |
| D1 | 4 | 004 |
| D2 | 1 | 006 |

These are the four classes in `docs/degree-branch-reduction.md`. The project
already independently replayed the normalized hub enumeration: 206 hub
classes, 114 labeled links, and four isomorphism classes. Its four fixed-link
extension models cover the degree-19 branch jointly. Earlier B3/B4 searches
and later D1/D2 runs are documented in the 2026-10-03 checkpoint; their
UNKNOWN outcomes do not exclude any whole branch. This refresh did not rerun
that enumeration or launch any solver.

One printed sentence on page 191 says four disjoint excess edges beside the
four-ray star; the counts require five. The project correctly uses
`K1,4 + 5 K2`. The old mapping receipt uses labels 2–16 and hashes the 19
pentads obtained by adjoining point 1. The refreshed receipt explicitly
separates those anchored hashes from the 1–15 quadruple witness hashes.

## Next work

Do not repeat four-link transcription, isomorphism classification, or a fixed
link timeout as a new route. Neutral exploration has a separate, already saved
literature note. A generic pair-preserving four-for-four trade remains an
unverified idea only: no accessible primary method source or candidate-support
check was established in this refresh, so no novelty or performance claim is
made for it. The separate 8+8 construction proposed during this refresh is not
assessed by the four-link theorem.

The machine-readable evidence is [source-checks.json](source-checks.json).
Raw source files remain in ignored scratch; their URLs, sizes, hashes, archive
entries, link blocks, dual-verifier results and exact witness maps are in the
receipt. No researcher was contacted and nothing was published externally.
