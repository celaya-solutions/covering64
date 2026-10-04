```
Document:    D29 Tie Relabel and Profile Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7818d445edb8442158bef9b2da487ae32447b090c06dc25d9600f6a56e83cdb3
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Four checked D29 ties

All four saved best ties from the independently checked one-block scan have 64 distinct blocks, 12 uncovered triples, D2max=D2sum=29, D3=D4=0, minimum pair count five, and named core overlaps `[1,1,1,2]`. The package and standalone verifiers separately confirm each noncover and its complete uncovered-triple list. These are not zero-deficit hints for the hard top-two model.

The frozen old-core relabel helper finds zero necessary partitions for each family. Its arithmetic controls passed. Thus every relabeling of the original 60-block core overlaps each exact saved family in at most 55 blocks. The maximum among 242 explicit images is four for each family; that finite maximum is not a global maximum. The empty necessary-partition set supplies the all-relabel certificate.

The representative is `weak-pair-swap-scan-runtime-independent/swap-881-1142.txt`, SHA256 `44e0ee69fb32f37eed00955e25c699a72430d85871ca03a348c0bf572edb7a0a`. The other incoming IDs are 1143, 1154, and 1359, all paired with outgoing ID 881. Each pair of saved families shares 63 blocks, so every pair has replacement distance one. Their full actual profiles, source hashes, relabel receipts, and verifier receipts are bound by `screen.json` and this folder's manifest.

This audit makes no optimizer calls and does not repeat the completed single-swap enumeration. It binds that independent runtime audit at SHA256 `a491a5ae273d2eab20bff3c3992771ce130d3293236eee62d9c05c6214e1207c`. The relabel conclusion applies only to the four saved 64-block families. None is a cover, and no global lower bound or exclusion of other neighborhoods is claimed.
