```
Document:    Bounded Exact-Distance-Two Repair Recommendation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9dafc3ce5341856db4b7ac2c9b1dddea39e71a2a4fced7526221daf4befa3c71
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Recommended local two-block repair

Use the verified H12/D29 representative as one fixed base. Test the exact
distance-two neighborhood: remove two original blocks and add two distinct
blocks outside the original family. Keep actual lexicographic rank (holes,
summed pair-max deficit), with the full-row deficit reported separately.
This is a local test; it does not cover arbitrary 64-block families.

## Complete reduction

Enumerate outgoing pairs B<C and each possible first incoming block A outside
the original family. After removing B,C and adding A, compute each pair's
shortfall below five. If a pair is short by more than one, no single final
block D can repair it. Otherwise collect the endpoints of every pair short
by one into a point set S. A valid D must contain S. If |S|>5, completion is
impossible. If |S|<=5, enumerate every five-set containing S that is outside
the original family and satisfies D>A.

This rule is necessary and sufficient for the pair floor after D is added:
each block contributes at most one to any pair count, and a block contains
all required pairs exactly when it contains their endpoint union. The original
base has pair floor five. Pairs already meeting the floor cannot be harmed by
adding D. No intermediate single/quadruple, core, or coverage violation may be
used as a rejection unless a separate safe one-add repair bound is proved.
Check all final legal rows, coverage, and rank after the second addition.

The inequalities B<C and A<D make each removed/added pair unique. Both additions
must be absent from the original base, even after removal. Each resulting
family uniquely recovers its removed and added pairs by set difference. This
covers exactly distance two. It does not include distance zero or one and must
not be described as a complete radius-two ball without separate evidence.

## Cost and bounded trial

There are C(64,2)*4,304 = 8,676,864 outer cases before pruning. The unrestricted
exact-distance-two shell has 18,668,272,896 neighbors. Forced support can shrink
the final-block list sharply: at most 1, 12, 78, or 364 raw supersets when |S|
is 5, 4, 3, or 2. A nonempty pair union cannot have size one. An empty support
can admit up to 4,304 final blocks before the order filter and is the main
cost risk. Record pruning counts, support-size bins, completion counts, and
outer-loop progress within the sole authorized 120-second pass.

Keep only strict best improvements and all final best ties strictly below the
baseline. Empty improving ties with unchanged rank (12,29) are a valid result.
This storage rule must not skip candidate evaluations. If the budget ends
before every outer case and completion is checked, report an incomplete local
search. Do not relaunch or reassign unused budget automatically.

The recommendation is to prepare and independently gate this one bounded pass.
The exact-search agent separately confirmed the reduction and unique-neighbor
proof. No two-swap implementation, solver, or enumeration was launched by this
runtime auditor while forming this recommendation.
