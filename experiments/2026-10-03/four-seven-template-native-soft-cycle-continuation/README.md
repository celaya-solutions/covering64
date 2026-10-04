```text
Document:    Twelve-Hole Cycle Continuation Result
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      5f276cd4f3f51efb116808767902afd9cc3f0d7fecd53d842d6dd47ecc87e9f6
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

The single authorized 600-second cycle continuation completed with no
improvement and no cover. Both raw and score best remained the identical
12-hole starting state, with score 92, pair-target L1 12 and nonheavy excess 4.
Its SHA256 is
`14d7168a8dda2bcff55f99c8bc46b29b1288881264e235c8045e0e42b717fc4b`.

The unchanged v1.1 native binary attempted 490,972,432 main-loop proposals and
981 restarts using seed 2026103972 and one worker. It accepted 978,796 directed
swaps, 390,940 redistributions, 7,330 point cycles and 282,246 template moves.
Full attempted/accepted denominators are preserved in `summary.json`.

Before launch, the wrapper checked every frozen input hash and confirmed the
budget, seed and worker count. The copied seed passed both covering checkers
and the independent soft-score recount. Native source, binary, catalogs,
scoring, temperature and restart behavior were unchanged. The two baseline
five-minute pilots and their evidence were preserved.

After completion, all 40 saved states passed the package and separate
standalone covering checks. All 16 operation records passed independent hole
and score recounts, move legality and forced rollback checks. There were no
native diagnostics. The frozen baseline auditors also checked raw/score
aliases, saved minima and log scores; their verifier outputs were redirected
to this campaign's separate ignored archive. These are construction results
only, with no family exclusion, global lower bound or proof claim.

`inputs.json` records input hashes, baseline compiler/binary metadata and the
source revision. `seeds.json`, `results.json`, `pilot-audit.json` and
`summary.json` preserve the run and verification evidence. Full state and
verifier output archives are under
`experiments/scratch/four-seven-template-native-soft-cycle-continuation-v1.0.0/`.
No further pilot was launched.
