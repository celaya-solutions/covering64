# Four-block prefix search peer review

~~~text
Document:    H6 Radius-Four Prefix Search Peer Review
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      41d1582bacb04ad6fae6468a6aecbc744e07dbfadf03bd635d74b8e36e371f4b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The read-only source review found no coverage or enumeration gap in the frozen
pilot. The review rehashed all 180 manifest pins. Root still owns the independent
launch gate and the sole production call.

For a selected prefix, let d be the remaining coverage demand, r the number of
additions still required, and g(a) an eligible suffix block's gain on the
remaining uncovered triples. The sum of the r largest gains bounds every
r-block completion from above, because it ignores overlap. If that sum is
below d, no completion exists.

Every participating block must also have gain at least d minus the sum of the
largest r-1 gains. Those gains may include the block itself, which weakens the
test but preserves safety. Filtering on this necessary floor preserves every
feasible completion. If d is nonpositive, floor zero keeps all completions.
By induction through the four prefix depths, no feasible tuple is removed.
Ascending full block IDs and suffix recursion visit each surviving tuple once.
Different full blocks remain distinct even if their residual masks match.

The residual universe has at most 46 triples, fitting the checked 64-bit mask.
Additions exclude all original blocks, so each candidate is at exact distance
four. Coverage alone drives the search. The runner dual-verifies candidates and
postclassifies pair, weak, and named-core metrics. The completion field expressly
refers to the exact-distance-four shell; the earlier radius-three result must
be combined separately for a full radius-four statement.

The independent Python replay examined every same-size family from the entire
21-block v7 universe, then selected exact-distance-four families. This differs
from the producer's deletion/addition fixture enumeration. It matched all saved
candidate families and their hole counts: 1,554, zero, and 43, over 2,380, 2,380,
and 9,100 exact-distance families respectively.

This review invoked no native binary and explored no real-H6 prefix or addition
tuple. Fixture agreement and safe pruning do not guarantee that the production
search will finish within its time cap.
