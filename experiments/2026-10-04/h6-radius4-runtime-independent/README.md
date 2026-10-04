# Four-block runtime audit and next-step assessment

~~~text
Document:    H6 Exact-Distance-Four Runtime Audit and Next-Step Assessment
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fe69f715a24e26005c4cdc9cb9ee0bdecca0ba62b190276890b9601bcdaf166c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

## Audited outcome

The sole root-launched exact-distance-four search completed normally in 5.0625
native seconds and 5.066140750073828 wrapper seconds, without a watchdog timeout.
It visited all 635,376 deletion sets. The first coverage bound excluded 633,208.
The remaining search visited 31,516 prefix nodes, recorded 28,021 prefix-bound
exclusions, and performed 1,047,902 residual-gain evaluations. It reached zero
full addition tuples and saved zero candidates.

The runtime audit rehashes all 180 pinned files, the root gate, launch receipt,
and raw output. It checks the complete deletion count against the independent
screen and confirms that the native and tracked candidate file sets are empty
and the ledger has only its header. Normal completion is distinguished from
timeout. Prefix counters are checked against saved output; no prefix or search
is rerun.

The starting witness is independently recounted and checked by both verifiers.
It still has six holes, minimum pair count four, D2max 14, D2sum 498, D3 80,
and D4 72. It passes the six named overlap caps but fails weak qualification.
There are no candidate rows requiring additional endpoint classification.

Combining this exact-fourth-shell result with the separately audited complete
first, second, and third shells for the identical input establishes no neighbor
with at most five holes within four replacements of this named H6 family.
This is a finite local result, not an unrestricted lower bound.

## Recommended next bounded route

Prefer an unanchored neutral H6 repair within three replacements before extending
the strict search to five replacements. Its three shells have 43,744 deletion
sets, compared with 7,624,512 for exact distance five: about 174 times fewer.
The endpoint would retain at most six holes while meeting pair floor five and
D3 = D4 = 0. The existing strict-improvement exclusions do not test this endpoint.
An improved neutral family could open routes beyond the original local basin.

The raw H6 deficits are concentrated. Pairs (4,6), (5,6), and (10,12) each occur
four times and account for every D4 violation. These pairs account for 78 of
the 80 D3 deficit units; the other two units occur at (4,10) and (5,10).
These are descriptive counts, not restrictions on a future unrestricted
neutral-neighborhood search.

Exact distance five has a valid residual-width bound of 56 and can use the
same proved-safe prefix logic. But it has twelve times the deletion sets of
distance four. Scaling the current implementation's time alone gives about
60.75 seconds before allowing for changed branching. This is only a rough
planning comparison, not a timing lower bound: an incremental histogram could
make the deletion stage faster, while surviving prefixes could add more work.
Completion under a 60-second cap is not established.

First estimate the neutral-target workload with a small bounded deletion-only
screen using target at most six holes. Then gate an at-most-three-replacement
search if that estimate supports it. Pair floor and D3/D4 may be checked at
endpoints, or used earlier only with separately proved-safe pruning. Do not reuse
an engine that rejects the pair-bad initial H6 family. Larger neighborhoods and
equal-hole moves remain outside the completed strict-radius-four result.

This assessment prepares or launches no additional production experiment.
