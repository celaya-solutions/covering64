# Neutral H6 replacement workload

~~~text
Document:    H6 Neutral Radius-Three Deletion Workload Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      2665a186d16727024309acbff2cfcc06023a806c8a5f241c628fc00502d2425f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The sole root-authorized deletion-only screen completed in 0.363421 native
seconds. It examined all 43,744 deletion sets in exact-distance shells one,
two, and three from the pinned raw H6 family, using target at most six holes.
It did not enumerate a replacement tuple, call an optimizer, or prepare or
launch a full replacement search.

| Distance | Deletions | Excluded | Survive | Necessary pool size | Necessary addition tuples |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 64 | 63 | 1 | 3 | 3 |
| 2 | 2,016 | 2,002 | 14 | 2–23 | 1,043 |
| 3 | 41,664 | 41,311 | 353 | 3–50 | 185,917 |
| Total | 43,744 | 43,376 | 368 | | 186,963 |

## Scope and safe bounds

The input is the exact64 raw H6 witness with SHA256
2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855.
Every adder is drawn from all 4,304 pentads outside the entire original family.
No pair, weak, or core condition filters this screen. Labels are 1-based and
global block IDs are lexicographic.

For k deleted blocks, U is the uncovered triple set and demand is |U| - 6.
The sum of the k largest eligible coverage counts upper-bounds any k-adder
union. A smaller sum safely excludes the deletion set. Any participating
adder must individually cover at least demand minus the k-1 largest counts.
The resulting pool includes every full block meeting that necessary floor;
equal coverage masks are not collapsed. The table sums C(pool size, k) for
surviving deletions without visiting those tuples.

Original triple-owner masks determine U. Scores are rebuilt from scratch for
each deletion, avoiding dependence on state restoration. Exact reviewed the
source before launch and found the bounds, binomial arithmetic, recursion, and
timeout handling sound. The native cap was 28 seconds with a 30-second watchdog.
All shells completed normally.

## Verification and next decision

The wrapper rejected six malformed input controls before the sole valid screen.
It retained every finite row in ignored scratch storage. Python independently
recounted U for every deletion from owner subsets and directly intersected
560-bit block masks for all 368 surviving pools plus 88 sampled excluded rows.
Every count, pool histogram, and workload total matches.

The 186,963-tuple necessary workload supports preparing a straightforward
bounded coverage enumeration, with pair floor five and D3 = D4 = 0 measured at
candidate endpoints. It is not a weak-feasibility result: none of these tuples
has yet been checked for exact coverage union or weak qualification. Any future
enumeration should retain all coverage candidates, dual-verify them, and
postclassify the existing six named caps, preserving the pair-bad input as a
valid starting point. Root must separately authorize preparation and launch.

This folder is frozen after the screen and replay receipts. Earlier sources
and experiments remain unchanged.
