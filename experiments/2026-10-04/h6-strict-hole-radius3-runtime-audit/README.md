# H6 radius-three runtime audit

~~~text
Document:    H6 Strict-Hole Radius-Three Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      70b9cb4bb1f54b8b3361c139002c28e69726d4b996fbbd2ed24ba92ac0abe8d2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

The sole root-launched search finished in 0.310721 native seconds, with no
watchdog timeout. All three exact replacement shells completed. No candidate
with at most five holes was found from the named raw H6 family.

| Distance | Deletion sets | Excluded by upper bound | Addition tuples examined |
| --- | ---: | ---: | ---: |
| 1 | 64 | 64 | 0 |
| 2 | 2,016 | 2,011 | 22 |
| 3 | 41,664 | 41,555 | 31,891 |

The audit rehashes all 174 frozen pins and the matching gate, checks launch and
runtime receipts, confirms the empty candidate ledger and both empty candidate
file sets, and checks all shell completion counts. The distance-three counts
match the earlier screen and its supplementary replay exactly. The starting
family again passes both verifier parsers and has six holes. No search is rerun.

This is a statement about strict improvement within three replacements of one
named family. The source review and independent fixture gate are in the separate
radius-three independent folder. The runtime audit itself checks saved evidence
and accounting; it does not independently repeat the whole search. Equal-hole
moves, larger replacement neighborhoods, and unrestricted existence remain open.
