```
Document:    Heterogeneous Saved-State Inventory
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      f6cdd5238f9c9cddd14bff329437b357127bd6ac3a0aa9d6f0ec114320e33f60
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Heterogeneous saved-state inventory

Ten distinct, well-formed 64-block partial states are copied here from saved research outputs. No optimizer ran. Each copy was recounted independently in `check.py` and passed both the package verifier and standalone verifier for its block count, canonical hash, and exact uncovered triples. Each verifier exits 1 because every state still has holes.

The union contains 277 distinct five-element blocks. This is a restricted recombination pool, not the unrestricted universe. The entry order below also orders the common-block matrix in `inventory.json`.

| State | Holes | Point-degree histogram |
|---|---:|---|
| unrestricted-old-3 | 3 | {'19': 3, '20': 10, '21': 3} |
| unrestricted-new-3 | 3 | {'19': 1, '20': 14, '21': 1} |
| regular-5 | 5 | {'20': 16} |
| regular-8 | 8 | {'20': 16} |
| sqs-23 | 23 | {'19': 3, '20': 10, '21': 3} |
| native-cycle-12 | 12 | {'20': 16} |
| g1-initial-13 | 13 | {'20': 16} |
| g1-best-17 | 17 | {'20': 16} |
| g5-raw-17 | 17 | {'20': 16} |
| g5-score-19 | 19 | {'20': 16} |

`g1-best-17.txt` is an explicit assembly of the best descent heavy 28 blocks and the same original 36 ordinary blocks retained in the initial diagnostic. It is not an LP vector rounded into a witness. Its measured hole count is 17.

The old unrestricted three-hole state contains the original saved 60-block core. The new unrestricted three-hole state contains that core under point-map images `[1,7,2,10,15,3,8,11,4,9,12,16,14,6,5,13]`. The checker directly confirms both containments. No new isomorphism or core search was performed for the other states; a null map means no saved map was checked, not an exclusion.

The audit records source paths and hashes, copied witness hashes, both verifier receipts, degree/pair/triple histograms, all missing triples, and pairwise common-block counts. Different histograms certify some structural differences; distinct file hashes alone do not prove nonisomorphism. The SQS source has 23 holes.

Run `uv run python experiments/2026-10-04/heterogeneous-seed-inventory/check.py` to replay the inventory. The audit is an input qualification for a separately gated search; it proves neither a 64-block cover nor a global lower bound.
