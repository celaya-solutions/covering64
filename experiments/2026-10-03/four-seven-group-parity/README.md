```
Document:    Elementary Parity Certificates for Two Restricted Group Actions
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      4dfb4f36c7e3b6f535b83a75a77ab371a4b13de86cdcc9a69fac63cf82fe7852
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Elementary exclusion of the two order-four construction pilots

A family of five-element blocks invariant under a fixed-point-free involution
cannot have odd multiplicity on a transposed pair of points. Indeed, an invariant
five-set would have to be a union of two-point orbits, which is impossible.
The blocks containing the transposed pair are preserved as a set and split into
two-element orbits. Their selected count is therefore even.

In the normalized four-sevenfold branch, every pair of anchors in different
groups has multiplicity five. Apply the lemma to these two explicitly proposed
actions, which keep anchor offsets and hub offsets fixed:

- Cycle case: rotate the four groups. The square of that rotation is a
  fixed-point-free involution transposing anchors 1 and 9.
- Matching case: use the Klein-four action on group indices by XOR with 1 and 2.
  The XOR-1 generator is a fixed-point-free involution transposing anchors 1 and 5.

Both chosen pairs require multiplicity five. In either restricted model their
pair equation reduces to **2 times an integer = 5**, a contradiction. This is an
elementary integer certificate independent of CP-SAT status.

`check.py` enumerates all 4,368 five-subsets and verifies that none is fixed by
the chosen involution. For the chosen pair, it records all 182 two-block orbits
covering the 364 possible containing blocks. The reduced coefficients are all
two, whose gcd does not divide the required right-hand side five. Four controls
reject the identity, an order-four map incorrectly presented as an involution,
a nontransposed pair, and an even target that has no parity contradiction.

The checker also verifies the exact group actions, invariance of all pair
targets and allowed blocks, and their free block orbits: 1,092 on all blocks,
369 on the 1,476 allowed blocks. No solver is used.

This excludes only covers invariant under these two specific simultaneous
group actions. It does not exclude either unrestricted four-sevenfold case,
and it does not classify all possible automorphisms. In particular, a
permutation swapping only two groups has fixed points, so this proof does not
apply to it automatically.

Run `python3 experiments/2026-10-03/four-seven-group-parity/check.py` from the
worktree root. The complete finite certificate and damaged controls are in
`result.json`.
