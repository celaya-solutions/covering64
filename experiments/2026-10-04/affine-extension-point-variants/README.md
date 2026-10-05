```text
Document:    161 Local Link Designs from Affine Extension Point Choices
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8360f17573e2813bf1c10ea89c9fa675929c975053669319d1f9f87ce001e770
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# New local constructions

Varying the extension points in four fixed affine recipes produces 675 valid
settings. These form 161 orbits under the full automorphism groups of their
prescribed excess graphs. Four orbits contain the earlier chosen witnesses;
157 orbits are new relative to that saved catalog. These are twenty-quadruple
point-link designs, not 64-block covers.

For each recipe, retain the same fifteen affine lines not through the origin
and the same function specifying each ray's target ray. Independently choose
one of the three points on each of those target rays. There are 243 raw choices
per recipe, or 972 overall. The 297 choices with a repeated extension point
cannot have the desired excess graph: an excess degree-seven vertex appears.
Every retained setting has twenty distinct quadruples, exactly the required
105 pair multiplicities, and eighty distinct triples.

| Excess core | Valid settings | Orbits | New orbits |
| --- | ---: | ---: | ---: |
| C4 with a leaf | 162 | 54 | 53 |
| C5 | 243 | 17 | 16 |
| Triangle with a two-edge path | 162 | 54 | 53 |
| Triangle with leaves at distinct vertices | 108 | 36 | 35 |

Each setting is explicitly mapped to the corresponding canonical excess graph.
Its complete automorphism group is then applied to the resulting family. The
lexicographically least twenty quadruple IDs define its orbit representative.
The saved maps reproduce every representative, and every raw setting belongs
to one recorded orbit. The enumeration is complete for these four fixed
ray-target recipes and their stated extension choices. The producer makes no
claim to enumerate all affine constructions or all local decompositions.

Independent replay rebuilds every affine setting and every excess-graph
automorphism, confirms the complete orbit partition, and rejects 22 damaged
inputs. All 161 representatives pass both local pair-cover verifiers. Each is
also transported to an actual point-one fiber of the circulant graph and checked
with both covering verifiers as a twenty-pentad partial: 185 triples covered,
375 uncovered, with nonnegative residual demands. No optimizer was called.

The independent review SHA256 is
`8e792f53ff04e6511cc5d0ea7c1274a35d13af26fa570130128922c46938b9d9`.
The representative data SHA256 is
`2db5cd79692f83847e2951fb13b08acb72d4e7b9e7f3fdba1557f931a69b9a7d`.
