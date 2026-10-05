```text
Document:    Draft Link Enumerator for the Degree-20 Point
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-05
SHA256:      05c9fadb9115485a3fdba4affa49a91224d39c2f27c97230ca382a16226579f6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Draft: C++ enumerator for the degree-20 point's link

`zlink.cpp` lists every set of 20 quadruples on 15 points that covers each pair
once, or twice for pairs in a given X_z, optionally requiring the hub rule of
Lemma 5. Build with
`clang++ -O3 -std=c++20 zlink.cpp -o zlink`. As a positive control without the
hub rule it found 2,082 links for one affine X_z in 120 seconds (165 million
nodes, incomplete). With the hub rule it found none in 132 million nodes,
also incomplete. It is a draft tool and supports no result.
