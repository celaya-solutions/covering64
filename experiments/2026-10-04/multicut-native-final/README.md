```
Document:    Native v1.4.1 Terminal-State Receipt Supplement
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d23ba80b9480c5fcde9075505cd74bb463ca13f6da23d0c82cbc2f7922290baf
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Terminal-state receipt supplement

Native v1.4.1 is the separate source
`scripts/four_seven_template_multicut_final_heuristic.cpp`. The frozen v1.4.0
source and receipts remain unchanged. The full body delta adds three calls to
save `-final.txt`: normal completion, an initial cover, or a cover found during
forced startup controls. The existing state audit still runs before the normal
terminal save. There are no changes to cut data, score, legal moves, proposal
selection, or acceptance. See `terminal-state.diff`.

The optimized and AddressSanitizer/UndefinedBehaviorSanitizer builds were
warning-clean. The complete prior control suite was repeated on these binaries:
4,150,944 catalog cut-sum comparisons, 286 saved states, 88 moves, 15 rejected
metric mutations, and 16 rejected invalid CLI arguments. Both cover verifiers
checked the ten distinct state contents. The disabled guide still matches the
original lookahead trajectory. These were control paths, with no optimization
pilot.

`preparation.json`, `build.json`, and `audit.json` bind the v1.4.1 source,
binaries, bundle and oracle. Large outputs are in the ignored
`experiments/scratch/multicut-native-v1.4.1/` directory. The root independently
replayed the embedded data and reviewed the complete three-save delta in
`../multicut-native-root/audit-v1.4.1.json`. The separate runtime review is in
`../multicut-independent/audit-v1.4.1.json` once written.

A separately authorized single 180-second cycle pilot uses this version so its
actual terminal state can be audited alongside raw-best and score-best states.
The pilot and its outcomes are recorded in `../multicut-pilot/`.
