```text
Document:    Independent Template Hull First Link Exclusions
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      bfceee1729ed2d2b2b6e79083fd96bac60dbfdfaad4ad27c39094e8c54d922e5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independently replayed certificates

All three template-hull certificates passed exact replay against the matching
matrix and seven independently reconstructed fixed-link rows. The matrix has
61,576 variables in [0,1], 4,550 base rows and seven fixed rows per case.
Eight damaged-certificate controls were rejected for each proof.

| Representative | Exactly checked positive gap |
| --- | ---: |
| matching-017 | 1193423/1000000000 |
| matching-077 | 161/1000000 |
| matching-083 | 19029/1000000 |

`encoding-chain-audit.json` confirms that each proof uses the exact matching
matrix already independently checked in
`../four-seven-template-hull/independent-audit.json`. That audit covered the
complete template catalog, all transports, simplex and marginal equations,
base-row preservation and damaged controls. Its source and frozen manifest
hashes were checked again here; its matrix audit was not repeated.

The matrix SHA256 is
`7bfcfd3b82f52016c9c594778d19443b2ed803c1f6e121461230bda28cbfb0ee`.
The frozen hull manifest SHA256 is
`21c243c87f44aebe780d8a48e330684d5fcaefbc2a587fa236516d64d8cfc38a`.

# Combined scope

Matching-077 was already excluded by checked certificates in all six hub-count
cases. Thus these three template proofs add two new first-link exclusions to
the previous 103. `combined-first-link-exclusions.json` takes the union of all
checked IDs, retaining every proof source and counting duplicates once. The
total is 105 excluded representatives and 153 open: 102 cycle and 51 matching.

Every exclusion is restricted to its fixed-first-link integer regular
four-sevenfold branch. The whole branch remains unresolved, and this is not
an unrestricted lower bound for C(16,5,3).

# Durable evidence and replay

`evidence.json.gz` preserves all three complete sparse integer certificates,
all fixed rows, exact replay reports and encoding-chain hashes. It is
53225 bytes, SHA256 `c73323280792268cf67314cdf40e3979c60c570b46078272634905f404555986`. The large base matrix remains
in ignored scratch storage under
`../../scratch/four-seven-template-link-screen-20261003/matching`.

The checker uses the earlier independently written raw exact-arithmetic
checker, never the LP runner's certificate evaluator. To replay one proof:

```sh
uv run python experiments/2026-10-03/four-seven-template-link-independent/check.py \
  experiments/scratch/four-seven-template-link-screen-20261003/matching \
  matching-017 certificate-1000000000.json NEW_AUDIT.json
```

The other two use `certificate-1000000.json`. The checker refuses to overwrite
an existing result and calls no optimizer.
