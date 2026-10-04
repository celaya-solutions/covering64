```
Document:    Affine Cap and Line Extension Pool Pilot Results
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      20e4dba951984782ef5c7e069e17526ed460f5479d15e15bc12960bbb7e11e74
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Separate pool expansion

Keep the same 20 audited affine lines on the 16 labeled points. Enumerating every one of the 4,368 five-blocks by the number of collinear triples gives 288 blocks with zero, 2,400 with one, 1,440 with two and 240 with four. The zero class consists of all five-point caps. The four class is exactly the 240 line extensions already used by the inversive-plane pool.

The new pool is the union of all 288 caps and 240 line extensions, totaling 528 distinct blocks in global lexicographic order. It strictly contains the original 288-block pool, whose 48 circles form only part of the full cap class. No particular inversive plane, circle count, extension count or degree profile is fixed. The 80 collinear triples each have 12 supporting pool blocks; the 480 other triples each have nine.

# Two model versions

The base version has 528 Boolean variables and 561 rows: exact cardinality 64 and the 560 original triple-cover inequalities. The second version preserves every base variable and row and appends 16 point-incidence lower bounds and 120 pair-incidence lower bounds, for 697 rows. The base remains an unrun control model.

The added bounds are necessary for every covering, not only this pool. A given pair occurs in 14 required triples, and one block containing that pair covers only three of them. Its block incidence is therefore at least ceil(14/3)=5. For a fixed point, sum the incidences of its 15 pairs. Every block through that point contributes four to this sum, so 4r>=15*5=75 and integer r>=19. These inequalities do not impose equality or preserve an incumbent pattern. The pool restriction remains the only construction restriction.

The builder saves exact row support lists, both models, source hashes and the full universe partition. manifest.json binds all artifacts. The first 288-block model and 60-second UNKNOWN pilot remain unchanged. The separate affine-cap-extension-independent audit reconstructed the full 4,368-block classification, all 528 pool blocks, both exact protobuf models, and the complete 136-row cut suffix. It rejected 29 damaged models and five damaged pool controls. The base model was not solved. After the gate passed, root authorized one 300-second, eight-worker pilot of the incidence-cut model with seed 2026103971.

The pilot returned **UNKNOWN** at 300.02201 solver seconds, with no candidate. Its native response reports 32 conflicts and 12,602 branches; those response counters should not be treated as aggregate throughput over all parallel workers. The result is inconclusive. The response, complete log, parameters, model, pool and frozen sources remain outside Git in experiments/scratch/affine-cap-extension-pool-pilot-20261003. result.json binds their hashes. check_result.py reread the saved parameters and response without solving and rejected seven damaged result controls. No further pilot was run.

Even an INFEASIBLE response would be a restricted CP-SAT outcome, not an independently checked proof or global lower bound. Any candidate must pass both covering verifiers. Raw sources and models remain outside Git in experiments/scratch/affine-cap-extension-pool-20261003. Targeted Ruff passed.

# Six exact norm families

A separate read-only calculation confirms that all 288 caps partition into six disjoint 48-circle families over GF(4). Normalize the mixed coefficient to one in q(u,v)=a*u^2+u*v+c*v^2. With elements 0,1,omega,omega+1 encoded 0,1,2,3 and omega^2=omega+1, the six anisotropic forms are (a,c)=(1,2),(1,3),(2,1),(2,2),(3,1),(3,3). Equivalently, the field trace of a*c is one.

For each form, its 16 translated centers and three nonzero radii produce 48 distinct five-point circles. The six families are disjoint and their union is every cap in the 528-block pool. Adding the same 20 infinity lines to any family gives a 68-block Steiner plane covering every one of the 680 triples on 17 points exactly once. All six planes passed both package and standalone verifiers. The original PGL construction is the (1,2) family.

norm_families.py and norm-families.json save coefficient labels, point maps, family membership by local and global block IDs, source/pool hashes and witness hashes. Raw plane witnesses and checker outputs remain in experiments/scratch/affine-norm-families-20261003. This exact finite decomposition may guide later seeds; no family-count constraints were introduced into the completed pilot. It makes no classification claim about arbitrary C(16,5,3) coverings.
