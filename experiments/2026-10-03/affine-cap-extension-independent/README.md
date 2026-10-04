```text
Document:    Independent Affine Cap and Extension Model Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      43ebc3ce2b4910c84091053c69440e279abd35702b9d983f60cf5e816dc16a2b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The independent gate passed. Starting from the previously norm-verified 20
four-point affine lines, this checker enumerated all 4,368 five-blocks. Exactly
288 contain no collinear triple and 240 contain four; the latter are exactly
line extensions. The other counts are 2,400 blocks with one collinear triple
and 1,440 with two. The selected 528 blocks and global variable IDs use
lexicographic order.

The checker rebuilt the entire pool payload and both protobuf models without
using the builder. The base has 528 Boolean variables and 561 rows: exactly
64 selected blocks and 560 triple-coverage constraints. The strengthened model
has 697 rows and adds only 16 point-degree lower bounds of 19 and 120 pair
lower bounds of 5. Removing those rows restores the identical base protobuf.
All variable names, domains, supports, coefficients, bounds and extra fields
were compared. Twenty-nine damaged model controls and five damaged pool
controls were rejected.

The cuts are necessary for every covering: each pair has 14 triples to cover,
and each five-block containing that pair covers three, requiring at least
five blocks. For a fixed point, its 15 pair incidences sum to four times its
block incidence. Thus its degree is at least ceil(75/4) = 19. Neither model
fixes a degree profile, cap/extension split, or symmetry.

`audit.json` binds the source manifest, pool, prior construction gate and both
model hashes. Large source models remain under the original ignored archive.
No solver was called here. Any later result applies only to this 528-block
pool and is not a global covering-number bound or independently checked proof.
