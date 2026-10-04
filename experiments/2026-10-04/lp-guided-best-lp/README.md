```
Document:    Five-Hole LP-Guided Seed and Exact Fixed-Heavy Obstruction
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      d9e9a4fd2564b2b48715e82a2e9acb362aaf8d7ed21f486ae3c9f299be6681e3
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# LP-guided best: five-hole seed and exact obstruction

The selected heavy tuple from the bounded LP-guided two-edge descent has
elastic objective 5.575882992498541, improving on the original baseline's
10.627554709636422. A fresh full six-graph diagnostic still excludes an ordinary
completion of this fixed heavy tuple by an exact signed-row certificate.

The deterministic binding family, consisting of these 28 heavy blocks and the
original 36 ordinary blocks, is a new **five-hole** 64-block near-cover. Both
the package verifier and standalone verifier report exactly five uncovered
triples. This improves the previous ten-hole near-cover; it is not a full cover.
No integer search was used to assemble it.

The missing triples are {4,5,11}, {4,6,11}, {4,8,12}, {4,8,16}, and {8,12,16}.
An independent profile recount gives base/full fourteen-cut score 49, zero
unsupported triples, 754 admissible ordinary blocks, zero heavy excess, and no
violations of the original fourteen cuts. The witness is `seed.txt`, SHA256
`8b9a64761c9547e15a82c9435e8a6837ffa05d34c12ae420533550ea2f1d6fc4`.

## Provenance and independent readback

Before this diagnostic, `../lp-guided-link-switch-independent/readback.py`
replayed all three recorded rankings, all 401 candidate row sets and all 60
saved numerical LP vectors. All reported scores, selected improvements and the
8.514734 seconds of solver use matched. Its exact rational reconstruction of
the final elastic residual gives an upper bound below 5.575883. A positive
residual alone is not an original-LP feasibility or infeasibility proof.

`run.py` binds that readback and the original audited 697-row basis. The fresh
model retains all six hub graphs, 1,200 ordinary variables, original global
lexicographic IDs and all necessary rows. The independent oracle reconstructs
every row and verifies the selected heavy IDs. The binding seed is checked by
both cover verifiers before any solve; their complete outputs are retained as
`binding-seed-package.json` and `binding-seed-standalone.json`.

## One bounded diagnostic

GLOP 9.15.6755 used one worker, seed 2026104, and ten-second limits for both
feasibility and optional elastic extraction. The sole feasibility phase
reported INFEASIBLE in 0.131475 seconds. The sole elastic phase reported OPTIMAL
in 0.147125 seconds and reproduced objective 5.575882992498541. Total solver time
was 0.278600 seconds. No CP or hub-graph branch solves ran.

`dual.json` is the accepted exact result: denominator 1000, 526 signed rows,
and gap 217/40 = 5.425. The separate integer/fraction checker replays it against
freshly reconstructed rows and rejects six damaged certificates. The numerical
dual is retained separately in ignored scratch, with the model and source
snapshot. Numerical status is not the proof.

## New necessary cut

`derive_cut.py` saves the new standalone `cut.json`; the old fourteen-cut bundle
is unchanged. The new inequality is

`sum(c[b] * h[b]) >= 132529`.

The lifted constant is 132691 and the ordinary box maximum is 162. The selected
heavy tuple has LHS 127104, giving a 5425 numerator violation. All signed row
weights have magnitude at most 1000, so 5.425 is also a valid L1-elastic lower
bound for this fixed tuple. All 276 heavy coefficients and 1,200 ordinary
combined coefficients are cross-checked by reversing the block-incidence
calculation; the constant is independently recovered from model bounds plus
fixed-heavy incidence. See `cut-audit.json`. Root replay is a separate gate.

This is a necessary inequality for the regular degree-20 four-sevenfold family
with the declared anchor triples and hubs. It is not an unrestricted bound or
a first-link exclusion. The best verified cover remains 65, and the official
109 excluded / 149 open first-link registry is unchanged. The five-hole witness
may be used by a separately authorized unrestricted repair, where its heavy
blocks are allowed to change.

All exact inputs, hashes, versions and solver phases are bound by `manifest.json`,
`lp-result.json`, `dual-audit.json` and the cut receipts. Large artifacts are in
ignored `experiments/scratch/lp-guided-best-lp-v1.0.0/`. The launcher refuses to
repeat an existing run. Narrow Ruff checks passed; global checks and Git
integration are owned by the coordinating agent.
