```text
Document:    Checked Carrier Symmetry for the SQS Union Pool
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      481e3e1fb2d72f10185e46f53857a7856063a78305dd76272a6998615aafa4cd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Checked result

A verified subgroup of 1,536 point permutations preserves each of the two
quadruple seeds and the full 1,744-block union pool. Its setwise stabilizer of
the triple (9,10,11) has 48 elements. The 30 pool blocks containing that triple
split into six orbits of sizes 12, 8, 3, 1, 3, 3.

This supports a satisfiability-preserving representative restriction for the
audited exact-64 pool model: require at least one of the six representative
blocks below. Every cover in the pool has an isomorphic image satisfying this
restriction. It is not an inequality satisfied by every labeled cover, and it
does not require any covering to be invariant under the subgroup. No new model
or solver run was made in this finite audit.

| Representative | Pool variable ID | Global lexicographic ID | Orbit size |
| --- | ---: | ---: | ---: |
| (1,2,9,10,11) | 132 | 308 | 12 |
| (1,9,10,11,12) | 543 | 1295 | 8 |
| (9,10,11,12,13) | 1688 | 4312 | 3 |
| (9,10,11,12,16) | 1691 | 4315 | 1 |
| (9,10,11,13,14) | 1692 | 4316 | 3 |
| (9,10,11,13,16) | 1694 | 4318 | 3 |

Point labels are 1-based; pool and global variable IDs are 0-based.

# Group construction and explicit checks

For the group description only, use zero-based points in the vector space
GF(2)^4. Let U={0,...,7} and d=4. Enumerate all affine maps x -> Lx+u for which
u belongs to U, L is invertible, L(U)=U and L(d)=d. The restriction of L to U
has 24 choices: the image of the first basis vector has six choices outside
{0,d}, and the image of the second has four choices outside their span. The
outside basis vector has eight possible images outside U, and u has eight
choices. Thus this affine subgroup has 24*8*8=1,536 elements. No assertion is
made that it is the full automorphism group of the pool.

`build_certificate.py` explicitly enumerates all these maps and tests each map
against both 140-block seeds and all 1,744 pool blocks. It saves seven generators
and a map from each of the 30 carriers to the representative of its orbit.

The separate standard-library `check_certificate.py` imports no construction
code. It rebuilds the group by composition closure of the saved generators,
checks inverse membership, and explicitly tests every generated map for the
affine conditions, preservation of both seeds, and preservation of the pool.
It reconstructs the pool independently by scanning all five-subsets for a
quadruple from either seed. It derives the target stabilizer, rebuilds every
orbit, verifies disjointness and complete coverage of all carriers, and checks
every saved carrier-to-representative map. Fourteen damaged certificates are
rejected.

# Why the representative restriction is complete

Let C be any 64-block cover whose blocks belong to this pool. Since C covers
(9,10,11), it selects some carrier B. The checked certificate supplies a
stabilizer permutation g taking B to one of the six representatives R.
Applying g to every block of C preserves pool membership, distinctness,
cardinality, and coverage of every triple. The resulting cover contains R and
satisfies the proposed six-block OR.

This argument applies to the audited base model, whose only constraints are
exact cardinality and full triple coverage. Combining this restriction with
other asymmetric restrictions would require a separate compatibility argument.
Failure in this restricted pool would not establish unrestricted nonexistence.

# Frozen evidence

- `certificate.json`: generators, subgroup and stabilizer orders, all carrier
  orbits and explicit relabeling maps, source and input hashes.
- `check_certificate.py` and `audit.json`: independent replay and damaged
  controls. All 1,536 group elements were explicitly checked.
- `manifest.json`: hashes of the compact evidence.

Base model SHA256:
`d0a70c16b53c2399ed10eae2deb77b3c817e352a4fc950d7584291b3c249703f`.

Pool SHA256:
`b1e0e13ac3787643b25e920d2ce8f83d7119dedcb3c78daaf8316e04510c68c6`.

Recheck without building a model or running a solver:

```sh
python3 -I experiments/2026-10-03/sqs-union-symmetry/check_certificate.py
```
