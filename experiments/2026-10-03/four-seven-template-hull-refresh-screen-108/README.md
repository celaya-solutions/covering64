```text
Document:    Matching-Only LP Screen of the 108-Exclusion Template Hull
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      c7d006685c83b38b2ed5638685ebfc083f0a612a2156106f5e08a6fe616f6107
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Matching-only screen of the 108-exclusion catalog

This wave preserves every earlier catalog, runner and result. It uses the newly
independently audited matching matrix with 12,042 templates per heavy group,
52,936 unit-box variables, and 4,550 base rows. The checked 108-ID union leaves
48 matching first-link representatives. The run first tests the whole matching
branch, then every one of those 48 representatives.

Each case has a 15-second total requested solver budget, shared between
feasibility and optional phase I. The maximum campaign allocation is 735 solver
seconds. Construction, preflight, exact certificate arithmetic and evidence
writing are outside that solver-time budget; measured solver durations are
saved. The run is sequential.

The whole-branch phase I adds 560 nonnegative unbounded slacks only to the 280
template extension equalities, leaving all 4,270 original rows hard. A fixed-link
model appends seven explicit block equalities and its phase I softens only
those seven rows with 14 nonnegative unbounded slacks. Every slack objective
coefficient is one. The original matrix, unit boxes, objective fields and
lexicographic block-variable order stay unchanged. These are the same checked
layouts as the preceding screen, newly bound to this immutable matrix.

## No-solve preflight and launch

The new preflight checks every matrix coefficient and bound, byte-identical
canonical matrix records and stripped original protobuf cores, all variable
boxes/types/objectives, all slack signs/support/bounds/objectives, and all four
layouts. It exercises all 48 selected links on both fixed models: 96 fixed/reset
transitions. It rejects unreset transitions and 46 damaged controls. It made
zero Solve calls. Root's passing catalog audit and the passing preflight are
both bound by hash before launch.

- Runner SHA-256: `3b62a11a5617a927ec7ec734d3b5787ed85e6ba4ca4e1977c262cc85573d7127`.
- Preflight checker SHA-256: `0ffc22e9df58232026a71eb361310a12622bba8562ae8c2eac152e5fd8f0ee31`.
- Preflight result SHA-256: `3dfff17a52b94568c1b3e5acce5fc61ee92ab5202420d89e50db5ac8ccdf73a3`.
- Matrix SHA-256: `e9b2289291479c5f1119f432f0131d8fda8130ace2e64c773cf93dd8928ceade`.
- Catalog manifest SHA-256: `dcbdfd83d9c1952fbcbc0e2e192897ce96fae126aa0d527011ca6f0e13eb8c87`.
- Independent catalog audit SHA-256: `67526fe1dca68a1a67c770f8e9abf88f675869bf33064fa0877432251cf9ddaf`.
- Preserved exclusion union SHA-256: `2809b2f39fac1971ca6bf3997e789a4a41463b62394e7525e5d282d084527f88`.

```sh
uv run python experiments/2026-10-03/four-seven-template-hull-refresh-screen-108/run.py \
  --output experiments/scratch/four-seven-template-hull-refresh-screen-108-20261003 \
  --preflight experiments/2026-10-03/four-seven-template-hull-refresh-screen-108/preflight.json \
  --seconds 15 \
  > experiments/2026-10-03/four-seven-template-hull-refresh-screen-108/run.log 2>&1
```

All source copies, input hashes, source revision, solver version, command,
serialized models, exact fixed rows, native logs, timings, reset audits and
sparse primals are saved. Any phase-I duals and rounded integer certificate
attempts are retained. Large files stay in the ignored scratch output.

Every positive certificate is sent for independent exact replay before an
exclusion claim. Every near-integral block selection must pass the package and
standalone covering verifiers. Final readback checks all 49 records and saved
primals using exact arithmetic on their stored binary values. Numerical
feasibility is not an exact witness, and timeouts/UNKNOWN are inconclusive.
A complete screen with no new checked exclusions ends this LP-pruning wave;
new checked exclusions instead justify another separately audited immutable
refinement. This process makes no unrestricted lower-bound claim.
