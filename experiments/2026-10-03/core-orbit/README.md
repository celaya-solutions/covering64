```text
Document:    Symmetry-Reduced Fixed-Core Obstruction for C(16,5,3)
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      eec9624a5093deebfea10b3e9ba2088c4964bb5ada909fa9255837e4037e22e6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Symmetry-reduced fixed-core obstruction

Every 64-block C(16,5,3) covering uses at most **55 of the specified 60 core
blocks**. This is a fixed-core neighborhood result. It neither rules out a
64-block covering with fewer core blocks nor raises the global lower bound.

## Exact checks

| Core blocks removed | Retained | Removal sets | Subgroup representatives | Added blocks allowed | Smallest exact dual bound | Exact margin |
|---|---:|---:|---:|---:|---:|---:|
| 3 | 57 | 34,220 | 619 | 7 | 1,864,579 / 250,000 | 114,579 / 250,000 |
| 4 | 56 | 487,635 | 8,337 | 8 | 2,035,711 / 250,000 | 35,711 / 250,000 |

Both certificates passed `python3 -I scripts/check_core_orbit_certificate.py`
with `valid_certificate=true` and `complete_obstruction=true`. There were no
uncertified representatives. In particular, retaining any 56 core blocks
requires at least 9 further blocks, giving a total of at least 65. A 64-block
cover containing more than 56 core blocks would also contain one such 56-block
subset, so the maximum core intersection is 55.

The core SHA256 is
`7011e57be2714b1e1a16d4419ecb55a0160e25806f5db5dd786891aa17d0a5db`.
Labels are 1-based; core blocks and triple ranks use lexicographic order.
Removal indices are 1-based positions in the certificate's explicit core list.
Weighted triple indices are 0-based lexicographic ranks among the 560 triples.

## Why the certificates prove the stated result

For each representative, the certificate assigns nonnegative rational weights
to triples not covered by the retained core. Every possible 5-block has total
weight at most one. Hence any completion needs at least the sum of these
weights in additional blocks. The checked sums exceed the respective allowance
of seven or eight blocks.

The independent checker enumerates all 4,368 possible added blocks and checks
every capacity with integers. It closes the three supplied point permutations
to a subgroup of order 60 and checks that every action preserves the exact
core. It then transports each representative through this group, checking that
the removal orbits are disjoint and exhaust every removal set. No LP solver,
covering64 package code, floating-point bound, or unverified solver status is
used by the checker. Full automorphism-group classification is unnecessary.

## Evidence and reproduction

- `core-remove-3.json.gz`: 23,607 bytes;
  SHA256 `ced63d0355ddd46ca8b446f9699fb464757c28b2a2c52acdcb064273aa289be5`.
- `core-remove-4.json.gz`: 450,567 bytes;
  SHA256 `9997df71457bd6f4ca5567032cd026e3956d29235515acc330f05fddc6d9c298`.
- `verification.json`: exact checker results, final source hashes, versions,
  generation times, and margins.
- Generator: `scripts/build_core_orbit_certificates.py`.
- Independent checker: `scripts/check_core_orbit_certificate.py`.
- Rejection controls: `tests/test_core_orbit_certificate.py` (18 passed).
- Raw case logs, source snapshots, generation logs, and checker output:
  `experiments/scratch/core-orbit-20261003/` (outside Git).

The generator used OR-Tools 9.15.6755 GLOP under
Python 3.13.15. Base source revision:
`d57346da01d6f8afbd65dee0981dddc97ceea27d`. The new scripts were uncommitted
at generation time; their exact hashes and snapshots identify their source.
Generation took 4.880 seconds for three removals
and 80.500 seconds for four removals, measured
across the LP loop. There was no random seed or time cutoff: representatives
were visited lexicographically and GLOP used its defaults. Its approximate
weights were rounded down at scale 1,000,000 and rescaled if necessary; the
standalone checker verifies the resulting exact rationals without trusting
optimality. The initial core and generator inputs remain in
`experiments/scratch/web-research-1803/`; each certificate embeds all core and
generator data required for independent verification.

Run the following from the repository root:

```sh
uv run python scripts/build_core_orbit_certificates.py --removed 3
uv run python scripts/build_core_orbit_certificates.py --removed 4
python3 -I scripts/check_core_orbit_certificate.py experiments/2026-10-03/core-orbit/core-remove-3.json.gz
python3 -I scripts/check_core_orbit_certificate.py experiments/2026-10-03/core-orbit/core-remove-4.json.gz
uv run pytest -v tests/test_core_orbit_certificate.py
```

The controls reject missing or overlapping orbits, a non-preserving order-60
point subgroup, malformed permutations, duplicate core blocks and removal
indices, duplicate or already-covered weighted triples, invalid denominators,
overloaded blocks, wrong orbit sizes, and false completeness claims. Bad JSON,
bad gzip, and truncated gzip return exit 2. A mathematically valid certificate
with an insufficient bound returns exit 1 and no maximum-core claim.

No five-removal cases were attempted in this run. Search beyond this certified
neighborhood remains necessary.
