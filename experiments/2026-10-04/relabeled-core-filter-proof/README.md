```
Document:    Independent Relabeled-Core Deficit Filter Proof
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      b1324b96863596966d6307caecacc2348ea035fcc9c5c92bf1b6b17d2c2cff87
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Necessary relabeled-core filter

Let C be the hash-bound set of 60 distinct core blocks. Its five heavy triples are pairwise disjoint, cover 15 points, and each occur in exactly six blocks of C. A block has five points, so it cannot contain two of these disjoint triples.

Let B be any family of 64 distinct blocks, and let pi be any permutation of the 16 point labels. Suppose |B intersect pi(C)| is at least 56. At most four blocks of pi(C) are absent from B. For each of its five disjoint triples T_i, let r_i count absent core blocks containing T_i. Since one absent block contains at most one such triple, sum r_i is at most four. The retained core blocks alone give count_B(T_i) at least 6-r_i, and added blocks can only increase it. Therefore max(0,6-count_B(T_i)) is at most r_i, so the sum of these five deficits is at most four.

Thus, if no five pairwise-disjoint triples of B have deficit sum at most four, every relabeled copy of C overlaps B in at most 55 blocks. Finding such a partition is only a necessary-condition witness and is inconclusive about whether an overlapping core actually exists. This argument applies to any B; it makes no claim that B is a covering.

The frozen scanner enumerates this condition completely. Each admissible triple has count at least two, since a lower count alone incurs deficit above four. Its eligible triples are ordered by nonnegative deficit and then triple ID. Recursive increasing positions enumerate every unordered five-triple selection once; disjoint masks enforce exactly 15 used labels. At a node needing k more triples, when the current candidate cost times k exceeds the remaining budget, every later cost is at least as large. Breaking there is therefore safe. No other pruning assumes a special incidence pattern or core labeling.

The separate images scan covers only the two named maps and each single point transposition, 242 attempted maps. Its failure to find an overlap is not complete over all point relabelings. The necessary-condition contrapositive above is the only all-relabel certificate in this scanner.

The independent receipt verifies the 60-block source, its five multiplicities, the one-triple-per-block fact across all 4,368 blocks, exhaustive small-support comparisons, and deficit boundary cases including accepted total deficit four and rejected deficit five. It uses no optimizer. Receipt SHA256: `dff87420f7dace9498134726725ce6589c306dc01130335a1c868581545872a4`.
