~~~text
Document:    Expanded Four-Class Affine Point-One Catalog
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      bd4d1adba20eb39f47deb94d88c642584474e941415a68611256f0dca192a9ed
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

# Frozen catalog

The checked four-class affine recipe is materialized as 196,992 distinct
twenty-block point-one families. Its 38 actual excess-graph fibers partition the
1,300 supplied circulant excess profiles, giving 6,739,200 implicit
profile/link pairs. This is the exact recipe defined in
`../affine-extension-semilinear-completeness/README.md`; it is not a catalog of
all local decompositions or a claim of a 64-block cover.

All 5,536 families from the previous chosen-witness catalog occur here.
`old-to-new-ids.json` is a list whose index is the old partial ID and whose value
is the corresponding new partial ID. The builder checks the complete twenty
global block IDs for every match, the old fiber membership, and uniqueness of
all new IDs. The profile associations are preserved. Skipping exactly these
old partial IDs in their saved fibers removes exactly 195,296 old pairs,
leaving 191,456 new families and 6,543,904 new pairs.

| Class | Families | All compatible pairs | New compatible pairs |
|---|---:|---:|---:|
| C5 | 41,472 | 1,544,832 | 1,449,472 |
| C4 with a leaf | 62,208 | 2,032,128 | 1,994,496 |
| Triangle with a length-two path | 82,944 | 2,757,888 | 2,706,816 |
| Triangle with leaves at distinct vertices | 10,368 | 404,352 | 393,120 |
| Total | 196,992 | 6,739,200 | 6,543,904 |

# Packed format and deterministic order

The large catalog is stored only in ignored scratch space:

`experiments/scratch/affine-expanded-catalog-v1.0.0/catalog-20xu16le.bin.gz`

After gzip decompression, it contains 196,992 fixed-width records of 40 bytes.
Record i is partial ID i. Each record contains twenty unsigned 16-bit
little-endian integers, sorted in ascending order. They are global zero-based
block IDs in lexicographic `combinations(range(1,17), 5)` order. All blocks
contain point 1, so the IDs are below 1,365. For example, a reader can decode
record i with `struct.unpack_from("<20H", payload, 40*i)`.

Records are ordered by actual excess-link ID, then by the lexicographic tuple
of twenty sorted global block IDs. Within each of the 38 fibers there are
exactly 5,184 records. `link-fibers.json` saves their half-open partial ranges,
actual/canonical point maps, actual excess edges, profile IDs, old partial IDs
in the new catalog, and new-only family counts.

The complete pair order is fiber, then partial ID, then ascending profile ID
inside the fiber. Let B_f be `summary.json`'s pair boundary for fiber f, S_f its
first partial ID, and n_f its number of profiles. The pair with partial ID p
and profile-list index j has full ordinal

`B_f + (p - S_f) * n_f + j`.

The 39 saved pair boundaries start at zero and end at 6,739,200. All later
records must retain these full ordinals even when old pairs are skipped.
An old partial is skipped for every profile in its fiber, not only for a
sampled profile. The benchmark's sparse sample is not a full-screen cursor.

# Construction and validation

The builder loads the frozen canonical image unions from the semilinear
completeness certificate. It directly verifies all 20,736 canonical families:
twenty distinct quadruples, all 105 pair multiplicities, and eighty distinct
triples. It verifies each fiber's point bijection and excess-graph transport,
then applies that bijection to every canonical family. These bijections
preserve the checked local properties. It checks all 196,992 full block-ID
tuples for global uniqueness and round-trips every packed record.

The deterministic build completed in 1.106 seconds, without screening or an
optimizer. Source revision, exact elapsed time, source hash, inputs and outputs
are saved in `summary.json`. The source and receipt are frozen and the builder
rejects overwriting them.

The compressed artifact is 2,720,667 bytes; its payload is 7,879,680 bytes.
Compressed SHA256:
`c471737a4a906ec7e5591a7fecedc6094322c6d39e285f07d615121b84d09203`.
Payload SHA256:
`dcf05e6f2a91b8a1b3134d8651ab711fecdc581cdc4e6f9f047b32890a480791`.

# Bounded benchmark plan

`benchmark-plan.json` saves 1,000 distinct new-only full pair ordinals and their
partial/profile/fiber IDs. Each fiber receives 26 samples and the first twelve
fibers receive one additional sample. For a fiber with m new pairs and k
samples, local new-only sample j is `floor((2*j+1)*m/(2*k))`. Its ordinal is then
translated back to the complete pair order above. The builder verifies that
none of the 1,000 samples uses an old partial.

The plan gives every fiber a sample; its weights differ from the full new-pair
population. The benchmark saves per-fiber populations, outcomes, and timings
to make that difference explicit. See `../affine-expanded-benchmark/README.md`
for the completed, separately frozen 10-second-budget benchmark.
