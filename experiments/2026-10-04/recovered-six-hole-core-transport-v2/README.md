```
Document:    Recovered Six-Hole Declared-Partition Core Transport
Version:     v1.0.1
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      dc352429dbe2f08d283587b1203ce93031d78645df584a292efee9ecf47fa1b5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Recovered six-hole guidance contains a relabeled core

The recovered six-hole guidance contains 59 of the 60 blocks in an explicitly
relabelled original core. The audited necessary core cap is 55. This is an
obstruction in the guidance, not a covering witness or a global lower bound.
The currently frozen three-cap model and its run remain unchanged.

The saved candidate is SHA256
`797dada195b23eecc808798eb12c8e4e7ccd7edd026fbdf22dea5b341f9ea2de`.
Its independent all-relabel necessary screen found exactly one possible target
partition: {1,2,3}, {4,7,12}, {5,8,11}, {9,13,16}, {10,14,15}, with multiplicities
[7,6,7,5,6]. The original core has five disjoint source triples of multiplicity
six. The candidate and screen hashes are bound in `manifest.json`.

## Complete finite map enumeration

A point bijection carrying the source partition onto this target partition is
uniquely determined by a permutation of its five target triples, one of six
internal bijections for each triple, and the forced image of the remaining point.
Thus there are exactly 5! times (3!)^5 = 933,120 such point maps. Conversely,
every one of these choices is a bijection with the required partition image.
The choices are unique for any resulting map, so no map is omitted or duplicated.

The existing finite C++ enumerator checks all 933,120 maps against all 60 source
blocks. The maximum overlap is 59, attained by 60 maps. The witness selects the
lexicographically largest 16-label map among those maximizers. This enumeration
is complete for the declared partition; it is not an enumeration of all 16!
point permutations. Its explicit violating map alone suffices for the finding.
No construction optimizer was called.

Python separately confirms that the selected map is a permutation, rebuilds all
60 distinct transported blocks and their lexicographic global IDs, and recounts
the 59-block intersection. The complete map, image, and intersection are saved
in `witness.json`, SHA256
`bdc25945621e88cb71a0ef250437b9d6accfa6064565a8039908ba5f44139b0e`.
The finite result is SHA256
`674e5f149d4f9eee87a38f1afbaad61c54907f92bbe5ec10e8e07d7b3026894b`.
Independent map replay is pending in this producer record. A future model must
bind that replay and the already audited core-cap proof before adding its row.

Any valid cover uses at most 55 blocks of this transported core, so at least four
of the candidate's 59 intersecting blocks must leave in any repair to a valid
64-block cover. This consequence is confined to the witnessed core cap; it does
not rule out larger repairs or other 64-block covers.

The raw binary, compiler version, input, stdout, and stderr are preserved under
ignored `experiments/scratch/recovered-six-hole-core-transport-v2-20261004/`.
The original transport sources and previous experiments remain unchanged.

This v2 sibling only wraps a long source string to satisfy Ruff. It repeats the
finite enumeration and produces the identical witness. All v1 source, input,
result, witness, and raw paths remain unchanged for existing references.
