# Neutral four-block deletion screen

~~~text
Document:    H6 Neutral Four-Deletion Workload and Resource Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      1e9f7f9fb0ed0d9f0f4d3ce8198bc8a2594680c93ac25e8f43a2f74179d6d8cd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The sole authorized deletion-only screen completed all 635,376 deletion sets
in 6.75588 native seconds, within its 28-second internal cap and 30-second
watchdog. It excluded 629,917 deletion sets by the coverage upper bound and
retained 5,459 sets. Necessary pools range from four to 1,470 eligible adders.
No addition tuple or addition prefix was explored.

The input is the same raw H6 exact64 witness, SHA256
2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855.
All 4,304 blocks outside the entire original family remain eligible. The target
is at most six holes, with no pair, weak, or named-core filtering.

## Minimal scorer change and replay

The native body is identical to the previously checked independent four-deletion
scorer except that demand changes from uncovered-minus-five to uncovered-minus-six.
The driver verifies this exact body equality against the frozen source hash.
Original triple-owner masks determine residual holes; every adder score is rebuilt
from scratch. The top-four sum bound and necessary individual floor are unchanged.
The worst-case total binomial count fits unsigned64 arithmetic.

Every finite row is saved under ignored scratch storage. Python independently
recounts all uncovered sets from owner-subset masks and directly checks the
full eligible universe for all 5,459 survivor pools plus 127 sampled excluded
rows. All pool, floor, hole, and workload counts agree.

## Exact loose ceiling and resource decision

The necessary addition-pool count is 816,777,496,562 unordered quadruples.
Four pool-size-1,470 cases contribute 775,075,572,180, about 94.9% of the total.
Their first lexicographic deletion set is [277,1039,3209,4075].

This is a loose ceiling on distinct exact-distance-four coverage endpoints,
not their measured number. It does not show that 816.8 billion candidates
exist, nor that the actual prefix search is slow. The safe prefix bounds may
remove most of the work, as they did for the strict five-hole target.
However, this screen alone does not establish manageable output size or full
completion within 60 seconds.

The proposed resource-safe option is a separately authorized 60-second prefix
pilot with an explicit stop after 1,000 fully persisted candidates, a 65-second
watchdog, and five-second termination grace. Reaching the candidate limit must
be recorded as incomplete; every captured family would still be dual-verified
and postclassified. The witness text alone is then bounded by 960,000 bytes
per copy, excluding logs and verifier receipts. This is a proposal, not an
implemented or launched limit.

No full neutral-four prefix pilot has been prepared or frozen on the strength
of this screen. Root must choose the resource limit or defer that route.
Earlier frozen sources remain unchanged.
