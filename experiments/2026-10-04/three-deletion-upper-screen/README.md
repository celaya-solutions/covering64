# Three-deletion coverage screen

~~~text
Document:    Three-Deletion Coverage Upper-Bound Screen
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      08c2fd1b386dd946afdc84a5e2b6d86fbb3f584e37339d45741ef26d5c921bc8
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

## Bounded screen

This screen examines deletion triples from two named partial 64-block families.
It scores the 4,304 pentads outside each entire original family, seeking a strict
hole-count improvement. It does not enumerate any addition tuple or call an
optimizer. Each run had a 29-second native cap and 30-second watchdog.

For retained-family holes U and strict target H, demand is |U| - H.
The sum of the three highest eligible adder counts is an upper bound on their
union coverage, since it ignores overlap. A smaller sum safely rules out that
deletion triple. Every participating adder must cover at least demand minus
the two largest eligible counts; this also ignores overlap and is necessary,
not sufficient. No pair, weak, or core filter is applied.

| Input | Target holes | Deletions | Excluded | Survive | Necessary addition triples |
| --- | ---: | ---: | ---: | ---: | ---: |
| a0a737 H9 | at most 8 | 41,664 | 41,455 | 209 | 279,150 |
| 2d018f H6 | at most 5 | 41,664 | 41,555 | 109 | 31,891 |

Both native screens completed, taking about 0.34 seconds each. Each scored
179,321,856 individual adder/deletion combinations and zero replacement tuples.
The last column sums the binomial pool-size counts across surviving deletions;
it estimates the exact union-check workload and does not count successful
replacements. Detailed rows, command lines, source revision, versions, hashes,
and exact runtime receipts are linked from the frozen runs.json.

## Supplementary independent replay

The supplemental replay script rebuilds the lexicographic universe using Python
combinations. It represents each triple's original owners by a bitset and
independently recounts all 83,328 deletion sets and their uncovered triple counts.
It directly scores all 4,304 eligible adders for every surviving deletion:
209 H9 rows and 109 H6 rows. It also checks 33 deterministically sampled excluded
rows from each run. All checks pass, including the necessary pool sizes and the
279,150 / 31,891 workload sums.

This replay does not independently recount every excluded row's top adder
counts. It is not a replacement search or a global covering-number proof.
The H6 strict-hole radius-three pilot is a separate gated experiment that
recomputes all its deletion sets, instead of trusting this survivor list.

The original screen.cpp and runs.json remain unchanged. Supplemental replay
and documentation were added after the original files were frozen.
