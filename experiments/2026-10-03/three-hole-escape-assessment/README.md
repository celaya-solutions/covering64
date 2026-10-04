```text
Document:    Three-Hole Plateau and Constructive Escape Assessment
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      4aba58d694da09bd8624b24c45ccd26a222ccbf246ae41eaa9d40cf132b60e5a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The ten-minute soft-score continuation is evidence of a search plateau, not a
proof that the whole four-seven family is impossible. It completed about 491
million proposals without changing either best record. Its hard requirements
include degree 20, four selected seven-block anchor templates, and the ordinary
block family. These are narrower than unrestricted covering search.

The two known unrestricted three-hole states were independently recounted and
checked by both covering verifiers. They share 62 blocks and both retain all
60 blocks of the same recorded core. The first has holes (2,7,14), (2,7,15),
(7,14,15); the second has holes (4,7,8), (4,7,10), (7,8,10). Each hole set consists
of three faces of a four-point set. Appending that four-point set and any fifth
point produces one of 12 full 65-block covers, but deleting any one old block
leaves at least three holes. In every case four deletions attain that minimum.
Each seed has exactly four blocks with only three privately covered triples.

The existing independently checked complete four-removal core certificate,
whose bytes and recorded gate are bound in `assessment.json`, allows at most
55 of these specific 60 core blocks in a 64-block covering. Thus any successful
search from either three-hole seed must lose at least five core blocks. The
restricted five-, six-, seven- and eight-removal scans do not establish that
all larger neighborhoods are excluded. This assessment does not replay or
extend the existing proof.

A constructive alternative is an unrestricted coverage-dependency ejection
chain with a beam of distinct partial chains. Insert a block covering a
current hole, then choose an old block to eject by the private triples it
would expose. Track those obligations and jointly plan subsequent insertions
and ejections over all 4,368 possible blocks. Keep exact final cardinality 64,
permit worse intermediate deficits, and retain chains that replace at least
five core blocks. A first bounded implementation could use depths 6-12 and
separate beam diversity by removed-core set, instead of accepting only a
single best immediate swap. The full chain would be applied atomically with
independent before/after/rollback recounts and both covering checks.

This differs from the inspected unrestricted native tabu code, which selects
one exchange at a time with dynamic hole weights and tenure, and from the
existing exact LNS code, which fixes its removed block set before solving.
The core-escape LNS already keeps a small state archive and uses core-overlap
objectives, so an archive alone is not a new proposal. No implemented
coverage-dependency beam/ejection-chain search was found in the inspected
scripts. This is a source-bounded observation, not a claim about every old
raw experiment.

For the four-seven branch, the immediate next diagnostic is the independently
audited anchor-pair excess lookahead requested by the parent task. It should
rank heavy tuples by unsupported ordinary triples. A dead tuple can be
excluded only under the explicitly proved family assumptions; a long search
plateau alone cannot exclude it. Both that variant and any unrestricted chain
pilot need fresh frozen inputs and independent implementation checks before
running. This assessment launched no additional search.
