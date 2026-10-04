```
Document:    Native Variable Cardinality Campaign Postcheck
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      560211b6188b78e387e1a261236a072dd27ee747ce4c8872f9f3e93e134e4840
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Native variable-cardinality campaign postcheck

Both authorized120-second runs finished without a covering family of at most64
blocks. All19 saved/final paths were independently recounted and checked with
both covering verifiers. Core-admissibility labels were applied only to64-block
records. The first32 logged move traces per run were replayed from the verified
Belic65 baseline, and every resulting trace metric matched.

| Seed | Best raw64 holes | Best four-cap-admissible64 holes | Final current holes | Best complete size |
|---|---:|---:|---:|---:|
| 2026104701 | 3 | 13 | 20 | 65 |
| 2026104702 | 3 | 12 | 26 | 65 |

The gate, source, model-independent parameters, input hashes, log hashes,
sequential seed order, elapsed limits, counters, record improvements, final best
bindings, absent-record rules, exit statuses, and first-cover stop policy all
passed. Duplicate/malformed controls were rejected, and both covering verifiers
rejected a damaged complete baseline. The independent audit launched no search.

The best four-cap-admissible family has12 holes. A separate all-relabel screen
in `../native-variable-cardinality-relabel-screen/` found zero necessary old-core
partitions for its unique best family, certifying no old-core overlap above55.
That extra structural check does not make the family a cover.

The runtime receipt SHA256 is
`3dbb4b692b4410f6df7f3b406c83d5dd3b083295f7b663726cfe4794c37d3b97`.
The pre-run gate remains unchanged at
`300677f074664d001cba3c63cb156e13e2648020cfa28908560b5f761ad3c6ff`.
The separate relabel screen SHA256 is
`159ca06adb57ed636e52d19da8d42c36a35d26a56827bfcd840f8c2b91bc3e98`.
These are failed bounded searches, not lower-bound or nonexistence proofs.
