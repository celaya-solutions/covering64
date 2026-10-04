# Independent four-deletion screen recount

~~~text
Document:    Independent H6 Four-Deletion Screen Recount
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      0373264f83b22b5a844afa8cbd21848a0e98943202a50bddfcbaacf4cd96f49a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The complete independent recount matches the frozen producer: 635,376 deletion
sets, 633,208 excluded by the coverage upper bound, and 2,168 surviving sets.
The necessary adder pools contain 4 through 364 blocks. Their combined four-adder
workload is exactly 3,697,940,975 unordered tuples. No replacement tuple was
enumerated by either screen or this audit.

## Independent calculation

The producer updates a score histogram across recursive deletions. The independent
C++ checker instead records each triple's original owners. For every deletion
set it identifies all uncovered triples from those owners, clears every adder
score, rebuilds the scores from scratch, and directly extracts the four largest.
It writes all 635,376 finite rows under the ignored scratch directory.

The checker finished in 5.34796 native seconds under a 28-second internal cap and
30-second subprocess watchdog. The separate Python check independently rebuilds
all uncovered sets from original owner-subset masks. It checks direct global
560-bit block intersections for every surviving deletion and 127 sampled
exclusions. All pool sizes, bounds, floors, and producer aggregate histograms
match. Neither algorithm performs pair, weak, or core filtering.

The producer receipt, input, source, binary, independent source/binary, raw rows,
and runtime output are pinned in the saved receipts. Previous frozen sources
and artifacts were not changed.

## Workload interpretation

Four pool-size-364 cases alone contribute 2,877,879,004 tuples, about 77.8% of the
necessary workload. The pool-size-177 and 178 cases contribute another
639,654,400. The remaining cases contribute 180,407,571.

This count does not establish that a plain full four-adder enumeration fits a
60-second cap. A stronger, separately reviewed safe pruning method could lower
the realized workload, but that requires its own gated experiment. These
deletion-only checks give no conclusion about the existence of an H5 neighbor
or an unrestricted 64-block cover.
