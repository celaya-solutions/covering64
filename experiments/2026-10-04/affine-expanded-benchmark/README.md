~~~text
Document:    Expanded Affine Catalog Support Benchmark
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b5984443b13af58a9ec396ca43cca26ff5de7898df7cbff90ceb9c4b6a7a181b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

# Result

The frozen 1,000-pair benchmark completed normally in 0.13565 seconds, including
0.05576 seconds of loading. The unchanged support function used 0.06630 seconds
in its calls. It returned 813 insufficient-support exclusions, 162 immediate
forced-conflict exclusions, and 25 single-pass survivors. No full expanded
screen or optimizer was launched. A survivor is only a case not excluded by
this single pass; it is not a feasible completion or cover witness.

| Class | Samples | Insufficient support | Forced conflict | Survived |
|---|---:|---:|---:|---:|
| C5 | 210 | 174 | 28 | 8 |
| C4 with a leaf | 314 | 260 | 47 | 7 |
| Triangle with a length-two path | 423 | 335 | 79 | 9 |
| Triangle with leaves at distinct vertices | 53 | 44 | 8 | 1 |
| Total | 1,000 | 813 | 162 | 25 |

The sample is stratified across all 38 actual excess graphs, using only new
pairs. Its weights differ from the full pair distribution. `benchmark.json`
saves each fiber's new-pair population, sample count, outcome counts,
operation counts, and time inside the support function. The sample does not
measure a full screen's runtime or prove an outcome for any unsampled pair.

# Frozen arithmetic and budget

The runner imports the previously checked source
`../circulant-chosen-link-support-screen/run.py`. Its source hash must match the
original source manifest. It calls that module's `screen`, `locate`, and
`global_ids` functions unchanged. The only module constant override is
`TOTAL: 195296 -> 6739200`, explicitly recorded in this benchmark's manifest.
There are no other module overrides.

The supplied data changes to the expanded catalog's fibers, pair boundaries,
and sampled partials. The mathematical model is unchanged: all 3,003
five-subsets avoiding point 1, all 455 residual triple equations, and a
cardinality row requiring exactly 44 selected blocks. Each triple carrier is
checked to contain all 66 eligible five-subsets before any support filtering.
No iterative propagation or optimization occurs.

For profile excess indicator e_t and selected point-one link indicator l_t,
the required residual triple count is `1 + e_t - l_t`. Zero residual rows
exclude all blocks meeting those rows. A row with insufficient remaining
support is an exclusion. A row whose support equals its demand forces its
remaining blocks; an immediate conflict between these forced choices is also
an exclusion. The unchanged function saves the support IDs and forcing-row
evidence needed to replay each exclusion.

The source and manifest were frozen before this authorized benchmark. The
10-second cooperative deadline covers input/source validation, reading the
packed catalog, loading the sampled masks, and processing the cases. The
runner checks the deadline before each case and saves a cursor if it expires.
As a cooperative deadline, it is checked between operations rather than by an
external process kill. The completed run stayed far below that budget.

# Loading and records

The loader reads the full packed catalog but constructs partial triple masks
only for the 1,000 sampled partial IDs. It loads all 1,300 profile masks and
all 455 complete carrier masks. This loading time must not be described as the
time to construct all 196,992 partial masks. Sampled partial IDs and full pair
ordinals remain unchanged; the saved plan is checked against the original
`locate` function for every case.

The detailed gzip streams are retained only in ignored scratch space:

`experiments/scratch/affine-expanded-benchmark-v1.0.0/cases.jsonl.gz`

`experiments/scratch/affine-expanded-benchmark-v1.0.0/survivors.jsonl.gz`

Every record includes its sample index, actual excess-link ID, full pair
ordinal, partial ID, and profile ID. The cases stream has all 1,000 records;
the survivors stream has the 25 survivors. No discarded sample or hidden
restart is involved. The sample cursor is 1,000 with no next ordinal. The
full-screen cursor is null because no full screen started; these sparse
samples do not cover a continuous ordinal interval.

Cases SHA256:
`872c0613153c912530b4368a735f668e46d5c7ce2a2680930dcc664a28074369`.
Survivors SHA256:
`02bb146ce942743a5e26d4e1cead68d6c7449e58b3b856ccafe086eb6c8b3624`.
Source SHA256:
`141a1eafb5632f4fb162c31cd9c63bc63af9703c52d8ee254f649b905a5a7987`.
Manifest SHA256:
`6f828f40aef64b2e1c0e8f8e95341354b8e9d6787f8d193d4e185fb56debee06`.

Preparation and benchmark modes reject overwriting frozen receipts. The source
has no full-screen mode. A larger screen requires separate authorization and
must skip exactly the mapped 195,296 old pairs. All 6,543,904 new-pair
associations are already specified by the catalog and its small fiber table.

# Full new-pair planning estimate

`estimate.py` uses the saved benchmark records and per-fiber timing; it does
not run another pair screen. A separate preparation-only measurement streams
all 196,992 partial masks in 2.322 seconds, checks their eighty distinct triple
rows, and hashes the mask stream. It discards each mask after hashing and does
not measure retaining all masks in memory. `estimate.json` records this result.

Weighting each fiber's measured mean call time by its full new-pair population
gives an estimated 433.98 seconds in the support function. The measured
benchmark time outside loading and support calls is 0.01359 seconds, including
certificate serialization, gzip output, bookkeeping, and finalization.
Scaling that overhead by the estimated emitted bytes gives 88.93 seconds;
scaling by case count instead gives 88.90 seconds. Adding measured full
streaming mask preparation and the full sampled startup time gives a planning
estimate of **525.28 seconds, about 8.75 minutes**, for all 6,543,904 new pairs.
The startup allowance slightly double-counts the 1,000 sampled mask builds.

The sampled cases stream is 495,166 raw bytes and 77,166 gzip bytes. Its
survivor stream is 10,932 raw bytes and 2,039 gzip bytes. Per-fiber mean emitted
bytes predict about 3.242 GB of raw cases plus 71.1 MB of raw survivor records.
Applying each stream's observed compression ratio gives about **505.2 MB of
case gzip data and 13.3 MB of survivor gzip data**. Units here are decimal.

These are estimates from a short deterministic sample, not a confidence
interval or runtime bound. Unseen expensive cases, output volume, retained
memory, filesystem behavior, scheduling, and thermal changes may alter the
result. A later batch-member format also has extra commit and fsync overhead
that this estimate does not measure. No full screen or full certificate stream
was produced for this estimate.
