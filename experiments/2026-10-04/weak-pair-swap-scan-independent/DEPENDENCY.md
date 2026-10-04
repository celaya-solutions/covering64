```
Document:    Weak-Pair One-Swap Completeness and Dependency Proof
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9828309ca933a157047c4e4276b1c98073ff12569768da4aee1a3a9d428515da
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Local completeness and affected-row proof

Let B be the fixed initial family of 64 distinct blocks from the lexicographic
universe of 4,368 five-subsets of {1,...,16}. A trial removes O in B and adds I
outside B. The resulting family is (B minus {O}) union {I}. There are exactly
64 times (4,368 minus 64) = 275,456 trials. Every one-for-one replacement is
included. No two trials give the same family: O and I can be recovered as the
unique elements of the two set differences with B. Updating the best record
must never update B or the outgoing/incoming lists.

## Complete dependency set

For any point subset S, its count changes by

    delta c(S) = 1[S is contained in I] - 1[S is contained in O].

Let A be the union of the pairs contained in O and the pairs contained in I.
If a pair P is outside A, neither changed block contains P. No triple or
quadruple containing P can then lie in either changed block. Therefore c(P),
all c(P+a), and all c(P+a+b) remain unchanged. Every single and quadruple row
for P, and every stronger two-triple deficit for P, also remains unchanged.
A fully legal initial family therefore needs its weak rows rechecked only for
pairs in A. The pair floor can be checked globally or on this same set. Core
overlap changes are computed separately for each of the four fixed core sets.

Pairs in the intersection of O and I must remain in A even when their pair
count changes by zero. A containing triple or quadruple may still change.
When O and I share s points, with s from 0 through 4, A has 20 minus C(s,2)
pairs. The independent controls cover every one of these intersection sizes.

## Rows and ranking

The legal filters are exact cardinality 64, pair counts at least 5, all 1,680
single rows 3c(P)-c(P+a)>=13, all 10,920 quadruple rows
3c(P)-2c(P+a+b)>=12, and all four named core overlaps at most 55.
The count variables are direct subset counts. Row deficits are nonnegative;
a zero sum of deficits is equivalent to every row passing.

For each pair P, the maximum stronger-row deficit is

    max(0, 12 - 3c(P) + largest c(P+a) + second-largest c(P+a)).

This equals the maximum over all 91 outside-point pairs because adding the two
largest entries gives the greatest sum. The search ranks actual metrics in
lexicographic order: first holes, then the sum of these 120 per-pair maxima.
The sum of deficits across all 10,920 stronger rows is a separate diagnostic.
It must not replace the sum of per-pair maxima or become the primary rank.

## Limits

A completed scan can establish facts only about these 275,456 neighbors and
the declared legal filters. The four core caps restrict this local scan; this
proof does not declare them unrestricted necessary conditions. A deadline or
interruption before all trials finish is an incomplete scan. It cannot be
reported as a complete neighborhood result. A failed or complete bounded scan
is not a global nonexistence theorem or a global lower bound.

This proof was separately challenged by the exact-search agent, which found
the dependency and unique-neighbor arguments sound. It is combined with source
review and finite direct-count controls in the independent gate.
