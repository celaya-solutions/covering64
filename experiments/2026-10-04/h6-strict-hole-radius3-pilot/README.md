# H6 strict-hole replacement pilot

~~~text
Document:    H6 Strict-Hole Radius-Three Replacement Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cbb2b43abb8ed7c79cdc1cc4e3f4918a7ac17b2dbcee8ba76f23adb16d8a02de
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
~~~

## Prepared scope

Root alone may launch this pilot after a matching independent gate. Preparation
does not run a production replacement search. Its input is the raw 64-block H6
family with SHA256
2d018ffa5e3e424193a4197b23891b52fa59b7ca411d06108e0ab1666bb85855.
This family fails pair floor 5; no pair, weak, or core condition enters the search.

The deterministic native process enumerates exact replacement distances 1, 2,
and 3, seeking every family with at most 5 holes. It removes respectively
64, 2,016, and 41,664 possible sets of original blocks. Additions are unordered
distinct blocks among all 4,304 pentads outside the entire original family.
Labels are 1-based; block IDs follow the lexicographic 4,368-block universe.

The native cap is 59 seconds and the subprocess watchdog is 60 seconds. There
is one process, one launch, no restart, and no random seed. It runs to natural
exhaustion or the budget, including after an H5 partial or provisional H0 record.
All native candidates are saved. The Python runner subsequently checks them with
the package verifier and the separate standalone checker.

## Safe coverage bounds

For a deleted set D of size k, let U be the triples uncovered by the retained
family. Put q = |U| - 5, and let c(a) count U-triples in eligible adder a.
Let M1 >= ... >= Mk be the k largest counts from distinct eligible blocks.
Any k adders cover at most M1 + ... + Mk elements of U, since ignoring overlaps
only increases this upper bound. A deletion is safely excluded when this sum
is smaller than q.

For any adder a in a feasible tuple, its other k-1 adders contribute at most
M1 + ... + M(k-1). This bound remains safe even if it includes a. Thus each
participating adder must have c(a) >= max(0, q - M1 - ... - M(k-1)).
Every surviving full block remains in the pool, including equal coverage masks.

U has at most 6 + 3*10 = 36 elements. Each adder gets an exact 64-bit U-mask.
Every unordered k-tuple from the necessary pool is checked by exact union
popcount. Sparse carrier counts are checked against these exact masks. Deletion
updates are fully restored before the next deletion set. No other pruning occurs.

Each resulting family has a unique removed set and added set relative to the
original family. Excluding all original blocks from additions makes the stated
distance exact and makes the three shells disjoint.

## Evidence and limits

The preparation script compiles with warnings as errors, compares a tiny v7
fixture against all unpruned direct triple-set replacements, rejects malformed
witnesses and bad budgets, and verifies that a zero budget visits no deletion
set. It saves these controls and source/binary/input hashes. Root performs a
separate independent fixture replay before gating.

The runner requires an independent gate with passed and launch_permitted both
true and the exact manifest_sha256. It checks every pinned dependency before
launch. It saves a launch receipt before validation, preserves raw output, and
does not relaunch an existing native output directory.

Every saved family is dual-verified, checked for exact distance, and postclassified
using the existing pair/weak/five-core verifier and sixth named-cap classifier.
The six cap thresholds are [55,55,55,55,56,59], used only for saved exact64 records.
Candidate acceptance depends solely on coverage, cardinality, and exact distance.

Only successful completion of all three shells supports a complete radius-three
statement for this one named H6 family. Timeouts are partial enumerations.
Neither a completed neighborhood nor a failed pilot gives an unrestricted lower
bound or proves that a 64-block cover does not exist.

The older three-deletion upper screen is separate and remains byte-for-byte
unchanged. Its H6 survivor estimate is 109 deletions and 31,891 necessary
addition triples; this pilot recomputes all deletion sets and does not trust a
prefiltered survivor list.
