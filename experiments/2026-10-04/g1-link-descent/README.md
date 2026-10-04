```text
Document:    Fixed-g1 Registry-Filtered Heavy-Link Descent
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8c72058e0f10fd162099298ad3249c779acec796570cd93d1ee4fb2ee940f02a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```
# Fixed-g1 registry-filtered descent

The bounded run starts from nearest-heavy case 038 with hub graph g1 fixed:
excesses `(0,1,1,1,1,0)` and exact hub-pair targets `(5,6,6,6,6,5)`.
Its separately checked elastic baseline is **8.024244815488677**. The broad-model
score 5.966796868079938 is reference data only and was never used as a fixed-g1
OPTIMAL cache entry.

The 697-row basis changes exactly six hub-pair bounds. The original degree-
preserving two-edge switch generator retains 28 distinct heavy blocks, seven
per anchor, the 276-block universe, outside degrees, and the nonanchor heavy
triple cap. Each generated profile receives all four first-link classifications
before LP evaluation. Registry membership in the 109 checked exclusions rejects
a profile. Both graph-preserving transports, explicit point maps, representative
edges and proof-source references are saved for accepted and rejected profiles.

| Round | Generated | Admitted | Rejected | Fresh LPs | Cached LPs | Starting score | Best neighbor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 136 | 122 | 14 | 122 | 0 | 8.024244815488677 | 7.52051548546158 |
| 2 | 136 | 122 | 14 | 121 | 1 | 7.52051548546158 | 7.978655120128314 |

All 244 evaluations were numerical OPTIMAL. Round two was complete and had no
improving admitted neighbor, so the run stopped after one accepted improvement.
The best profile still has first-link representatives
`cycle-061 / cycle-061 / cycle-086 / cycle-086`.
The selected move replaces the two `[9,10,11]`-anchor outside edges `(5,14)` and
`(6,15)` with `(5,15)` and `(6,14)`.

Actual cost was 243 fresh LPs, **31.963778204168193 solver seconds** and
**35.75381783291232 wall seconds**. The authorized caps were five rounds,
600 fresh LPs, 120 total solver seconds, 160 wall seconds, one worker and
one second per fresh GLOP call; seed 2026104, OR-Tools 9.15.6755.
No exact fractional completion and no covering witness were found. Stitching
the best heavy tuple with the original 36 ordinary blocks gives a 64-block
family with **17 holes**, agreed by the package and standalone cover verifiers.

Only numerical OPTIMAL records in the same fixed-g1 family can enter the cache.
The key binds the complete branch family, heavy profile and shifted rows; each
reuse verifies heavy IDs, primal and dual hashes and saves its origin-record
hash. The sole reuse was the separate branch baseline in round two.

The independent gate and postcheck in `../g1-link-descent-independent/` replayed
the six branch rows, complete neighborhoods and cut rankings, every registry
receipt and mapping, all 244 numerical vectors, cache origins and raw hashes.
Malformed/duplicate heavy input and a damaged point-map control were rejected.
The original 14 broad cuts order candidates only; they never prune an admitted
neighbor. No branch-specific certificate is added to the broad 353-cut inventory.

`result.json`, `manifest.json` and `preflight.json` bind the run and inputs.
All raw rankings, accepted and rejected profiles, vectors, cache records, frozen
sources and execution records are preserved under the ignored directory
`experiments/scratch/g1-link-descent-20261004/`. Launch revision was
`5d4d2b252037b965ef6834908dc825a6d79fd391`.

The reusable stitch helper requires an absolute output path. A first relative-
path invocation wrote the same 17-hole family and then failed while forming
its root-relative report path; that output remains in the ignored
`g1-link-descent-stitch-relative-20261004` directory. The absolute-path invocation
completed successfully. No optimization was repeated.

This is a finite registry-filtered neighborhood result, not an exact local
optimality theorem or a global covering-number lower bound. Numerical objectives
and the stitched integer hole count measure different quantities.
