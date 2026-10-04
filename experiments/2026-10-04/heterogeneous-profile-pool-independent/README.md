```
Document:    Independent Heterogeneous Profile Pool Preparation Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      32498eec627980eb9faf0947ca3a756d01bae725dc810557d2adf990df5b6929
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Heterogeneous profile pool preparation gate

This solver-free gate reconstructs both complete 4,948-variable, 1,166-row models.
The original 277-block and 337-block pools and two 60-block core-avoidance rows
remain unchanged. Twenty exact threshold Booleans and two weighted inequalities
apply the saved five-heavy-triple obstruction to the two named partitions only.
Both directions of each threshold are encoded.

All 243 category combinations per partition are independently checked: 217 are
allowed and 26 are forbidden. The inequality is exactly 5*sum(six)+sum(seven)<=26.
It forbids five triples all at least sixfold with two or more at least sevenfold;
if any selected triple has multiplicity below six, it imposes no restriction.
All 79 possible local counts uniquely determine the two threshold Booleans.

The partitions are reconstructed from the original saved five triples and the
saved point map. Both full hints satisfy every active model row. The package and
standalone verifiers independently confirm 64 distinct blocks and 17 holes in the
saved g5 raw hint. Four damaged threshold, reverse-literal, profile-bound and hint
controls are rejected. The inspected runner allows two 60-second, four-worker
calls, seeded 2026104091 and 2026104092, minimizing only uncovered triples.

The partial states are subject to declared construction restrictions. This gate
makes no unrestricted lower-bound or all-partitions claim. Root owns campaign
execution and the separate result postcheck. An initial checker attempt used an
incorrect receipt field name; that source/log is retained in ignored scratch,
and the final checker verifies the partitions directly.
