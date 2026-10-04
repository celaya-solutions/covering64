```text
Document:    Independent Audit of the Signed Feature Facets
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      3a6ed2d1d5e5bd08883c039c697e84f3571c3e7f09cd98a77f4bde5d754677e2
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and result

These facets are necessary only for integer normalized regular four-sevenfold
64-block covers. They rely on separately checked exclusions of fixed first-link
models. No unrestricted lower bound or cover invariance is claimed.

`check_proof.py` first replays all 258 input records and their 100 positive
certificates. It independently reconstructs 59,940 labeled feature maps and
uses integer determinants to recover every supporting facet of the surviving
feature vectors. The cycle has 43 surviving vectors and 18 hull facets; the
matching has 33 vectors and 23 facets. Signed coefficients, equality witnesses,
violating IDs, positive gaps and relabeling transports all passed. Twelve
damaged-proof controls were rejected.

After removing the five prior rules, four cycle facet families and nine
matching families remain. Their transports add 16 cycle or 36 matching rows.
`check_model.py` independently checks all 104 appended rows across four
variants: both cases, each with and without the first five rules. All previous
proto fields are unchanged. Ten damaged-model controls per variant were
rejected. `check_scope.py` rejected 16 invalid scopes without model mutation.

# Evidence and replay

The proof input is `../four-seven-link-orbits/safe-feature-facets.json`.
Frozen bases and outputs are in
`../../scratch/four-seven-facet-independent-models`. Input, source, model and
checker hashes are recorded in the reports.

Run the three scripts in this directory with `uv run python`: `check_proof.py`,
`check_model.py`, and `check_scope.py`.

`facet-screen-audit.json` checks the subsequent 158-record screen from
`../../scratch/four-seven-link-lp-facets`. It produced no new exclusion; all
158 cases were numerically OPTIMAL. Their numerical LP status proves neither
integer existence nor exact rational primal feasibility.
