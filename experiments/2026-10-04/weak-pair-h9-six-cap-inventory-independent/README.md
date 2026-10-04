```text
Document:    Independent H9 Six-Named-Cap Saved Family Inventory
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      20c99b5f87389d128ba38a259967aa6f0389a027899683db674e4fe9a7e01a42
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# One saved family passes the proposed sixth cap

Among the 21 independently saved H9-queue families, exactly one passes the old five named-core caps, all weak pair rules, and the proposed new overlap limit of 59 against the original f5f24 H9/D23 family. The sixth cap was still awaiting its separately bound independent proof when this inventory was written. The original receipt preserves that pending status; this inventory does not prove the cap.

The selected family is `a0a737c4010f68fcd5bfba8ccc7c20b4b8d9f06a96bb0086c7a63dbfc43f5ecc`, at `../weak-pair-h9-d23-neutral-queue-runtime-independent/family-a0a737c4010f68fc.txt`. Fresh direct inclusion counts and both covering verifiers agree on 64 distinct blocks, nine uncovered triples, minimum pair count five, D3=D4=0, D2max19, and D2sum27. Its old four overlaps are [1,0,1,1], fifth overlap is one, and new overlap is 59. It lies five one-block exchanges from the original f5f24 family.

It ties the queue's best declared (holes,D2max) rank of (9,19). The earlier lexicographic representative e2a004 has D2sum25; the selected family has D2sum27. D2sum is reported metadata, not the declared rank tie-breaker. All other saved families have new-core overlap greater than 59. This is selection from existing saved records, not a new covering result. No cover was found.

A direct triple-count supplement finds maximum triple multiplicity three for all 21 families. This supplement does not itself prove or apply an all-relabel core bound. In particular, it does not merge statements about the older 60-block cores with those about the newer 62- and 64-block cores.

The original `inventory.json` SHA256 is `de1653eca6de927e511efd316d0893f870e9e8731afc6bd5091a72042c287b55`. It retains all IDs, metrics, source witness hashes, overlap values, and the selected family's fresh dual receipts. Its bytes are preserved. `triple-multiplicity.json` SHA256 is `6dc7dc61a8b0f33b7fc8b98d2262f25afdb82eaee284448b1aa715ec58f5858e`.

The reproducible `check.py` independently replays both inventories, freshly recomputes every family's counts, and dual-checks the selected family again. Its `check.json` receipt SHA256 is `2c545a2bf064ec80232cd0485c76353a2e7a9ce3543d8c861c37fa08989a0944`. The checker pins the earlier full H9 runtime receipt, producer manifest, direct oracle and both verifiers. It launches no optimizer or native search.

All six overlap tests refer to these named core images. No all-relabel or unrestricted existence conclusion follows.
