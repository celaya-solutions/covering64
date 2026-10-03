```text
Document:    Released Point Repairs of the Fresh Six-Hole Candidate
Version:     v1.0.1
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      5e4c68c6b28b6b39dd2fd6b63791f32fcfdd5b0b55b1d7b72eafa7fffc0d4351
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Results and scope

The point-12 neighborhood has an independently checked exact dual bound of
43/2 additions. Its 20-block budget is therefore impossible. The larger
points-6-and-12 neighborhood remains unresolved after a 300-second search.
Neither run found a cover or establishes a global lower bound.

For a release set P, retain exactly the input blocks disjoint from P and
allow every five-subset meeting P as an added block. Added blocks disjoint
from P are outside this neighborhood. Require exactly 64 distinct blocks
and coverage of all triples. The models impose no regularity, heavy-profile,
pair-degree, or rotational constraints. Variables preserve global
lexicographic block IDs and labels remain 1-based.

| Release points | Retained | Allowed additions | Addition budget | Deficient triples | Exact dual bound | CP-SAT result |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 12 | 44 | 1,365 | 20 | 171 | 43/2 | UNKNOWN, 120.001151 s |
| 6, 12 | 30 | 2,366 | 34 | 292 | 32799899/1000000 | UNKNOWN, 300.025692 s |

The point-12 dual gives a lower bound of 22 integer additions, exceeding
the available 20. The larger neighborhood's dual is below its 34-block
budget; it supplies no exclusion. Both CP-SAT statuses are inconclusive.

# Input and method

Both runs used `reduced-family-heuristic/full-penalty-2026100366/`
`search-score_improvement-25-h6.txt`, relative to the dated experiment folder.
It has 64 distinct blocks and six uncovered triples:
`4,5,12`; `4,6,12`; `4,12,15`; `5,7,12`; `6,7,12`; `7,12,15`.
Both package and standalone verifiers agree that this is a partial candidate,
not a cover. Its canonical SHA256 is
`ecd5b6e0bab73c12d9581ea6f7a414b53006756813765fc8d774b840e03f388e`.

The source revision was `bcf4fcc1b998d11227cd04145470f2ace79b71e2` with
uncommitted runner snapshots preserved in each archive. OR-Tools was
`9.15.6755`. Point 12 used seed `2026102901`, 120 seconds and two workers;
points 6 and 12 used seed `2026102902`, 300 seconds and four workers.

GLOP supplies nonnegative weights on deficient triples, with capacity one
for every allowed block. The runner rounds weights down to millionths and
enlarges the common denominator if any column needs it. These integer
inequalities, independently reconstructed by `check.py`, are the evidence
for a bound; solver status is not used to establish one.

The original point-12 weights yield `21499971/1000000`. Rationalizing
individual weights with denominator limit 108 gives a second certificate
with common denominator 54, total numerator 1161 and maximum column load
54. Exact checks validate all 1,365 columns, so every cover of the deficient
triples requires at least `ceil(1161/54) = 22` allowed blocks. The original
and simplified certificates are both preserved. The same simplification
attempt for points 6 and 12 failed a column-capacity check and was rejected.

The standalone checker imports only standard-library modules. It rebuilds
all 4,368 blocks and 560 triples using `itertools`, reconstructs the retained
set, complete allowed set and deficient set, then checks nonnegative support,
all column capacities and the exact bound with integer arithmetic. Twelve
damaged controls are rejected, including changed scope, bad weights,
duplicate input and malformed input.

A second independent checker, `point12_bitmask_check.py`, enumerates all
16-bit masks without production imports. It separately reconstructs the
44 retained blocks, 171 deficient triples and 1,365 allowed columns. Its
70 positive weights have total 1,161 and maximum column load 54, confirming
the same 43/2 bound. Six additional damaged dual controls are rejected;
`point12-bitmask-result.json` records the audit.

# Evidence and recheck

`point12.json.gz` and `points6-12.json.gz` preserve input blocks, metadata,
certificates, check results, solver summaries, parameters, frozen sources,
and hashes for full models and logs. Large models and logs remain in the
ignored scratch directories recorded inside the archives. Historical source
snapshots remain unchanged; current `run.py` clarifies scope wording and wraps
four long lines. The checker validates the explicit IDs rather than relying
on the older metadata's abbreviated scope sentence.

Run from the repository root:

```sh
uv run python experiments/2026-10-03/released-point-repair/check.py \
  experiments/2026-10-03/released-point-repair/point12.json.gz
uv run python experiments/2026-10-03/released-point-repair/check.py \
  experiments/2026-10-03/released-point-repair/point12.json.gz \
  --dual-name simplified-dual.json
uv run python experiments/2026-10-03/released-point-repair/check.py \
  experiments/2026-10-03/released-point-repair/points6-12.json.gz
```

Archive SHA256 values:

- `point12.json.gz`: `95413306da7f0230b562f8d513566643d8fd00477bfd79aff6816195c14b9c6b`
- `points6-12.json.gz`: `4a3dd60b8b8c402984a5722a8b54d2f2789a098162f2475431a3e8738dc44592`

Model SHA256 values:

- Point 12: `272de47f84abc116f1a07be713ddeb880ba24c047485f67862457a030a7c64f1`
- Points 6 and 12: `98b2a251ec13907cf7b23d947bad295ffee2be1d1c696d6c60119eb47ce9336f`
