```text
Document:    Independent Audit of the First Five Feature Rules
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      6e3b9fa875c86b8d195ddcb23adc15e71cf49e391cc8019a7ebc4e22f46f1a75
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope and result

The five original feature rules are necessary only for integer normalized
regular 64-block covers with four sevenfold triples. Relabeling transports
each inequality to all four anchor groups; it does not assume the cover is
invariant under any relabeling. This audit gives no unrestricted lower bound.

The frozen helper adds 8 cycle rows or 12 matching rows and no variables.
`check_model.py` independently reconstructs every coefficient from the 4,368
lexicographic global blocks, checks both directions of each transport, and
compares all earlier proto fields. The two model reports passed, including
12 damaged-model controls per case. `check_scope.py` rejected 16 invalid
scopes without changing their models.

# Evidence and replay

The proof input is `../four-seven-link-orbits/safe-linear-cuts.json`.
The frozen model archive is
`../../scratch/four-seven-feature-cuts-v1.0.0`.
The reports contain exact input, helper, model and checker hashes.

Run `uv run python experiments/2026-10-03/four-seven-feature-independent/check_model.py`
and `uv run python experiments/2026-10-03/four-seven-feature-independent/check_scope.py`.

`feature-screen-audit.json` replays the subsequent 158-record LP screen from
`../../scratch/four-seven-link-lp-features`. All 158 returned numerical
OPTIMAL status and no new exclusion. Numerical feasibility is not an integer
cover or an exact rational primal witness. The prior 100 checked restricted
exclusions remain unchanged.
