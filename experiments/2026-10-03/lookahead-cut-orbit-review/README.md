```text
Document:    Independent Review of Heavy-Cut Orbit Separation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      12cf05ea762909464aa74fbb447b3b9e183a5efd17fa656b455be43382bdb92a
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The frozen v1.1.0 orbit checker passed this independent mathematical replay and
input-integrity review. There are no unresolved actionable findings. No source
owned by the primary checker was changed, and no solver was called.

The review constructs the group by composition closure of ten generators using
three-cycles and swaps, independently of the primary checker's direct product
enumeration. Both methods give exactly the same 31,104 maps. Every map preserves
the four anchor/hub groups. The independent generators explicitly preserve the
276 heavy-block and 1,200 ordinary-block domains.

Fresh integer coefficient sums reproduce minimum 98,144, maximum 156,905, and
19 violated relabelings for the frozen ten-hole baseline. The exact minimizing
map and pulled-back coefficients match the saved receipt. Two nontrivial full
witness relabelings preserve all three numerical results. Ten malformed or
family-invalid witness controls are rejected by the primary parser.

# Receipt issue found and resolved

Version 1.0.0 parsed a candidate before enumerating the orbit, then reread the
file to compute the reported hash. A file rewritten in between could receive a
passed receipt for bytes never checked. The preserved old checker remains in
ignored scratch storage; its frozen baseline was not affected.

The primary author fixed this in v1.1.0 by capturing witness and cut bytes once,
then parsing and hashing those same bytes. A deterministic control rewrites
only a temporary candidate to an invalid one-newline file immediately after
parsing. Version 1.0.0 reproduces the wrong final-file hash. Version 1.1.0 correctly
records the hash of the valid bytes actually checked. Primary source files and
the real baseline witness remain unchanged throughout both tests.

The reviewed v1.1.0 checker SHA256 is
`7e71d05ed94b99977564ed6742ab0bb7575335788a4e0a2cc9823f7c230658c8`.

# Scope

A violated transformed cut excludes completion of that fixed heavy tuple within
the regular four-sevenfold template family. A tuple passing all these cuts is
not thereby proved extendable. The group covers all stated anchor/hub family
relabelings; it is not the group of every arbitrary permutation of sixteen
points. No whole first-link family, unrestricted covering problem, or global
bound is excluded by this receipt.

`review.py` reproduces the finite review, `review.json` records all inputs,
controls and findings, and `manifest.json` hashes the compact evidence.

```sh
python3 -I experiments/2026-10-03/lookahead-cut-orbit-review/review.py
```
