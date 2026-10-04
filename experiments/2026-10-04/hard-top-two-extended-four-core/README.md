```
Document:    Hard Top-Two Extended Four-Core Model
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      2a3fcdec9191b19d43a11132ef12bfeeb48c3d03f3e206d294f4c6c6bbac97b7
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Hard top-two model with four core caps

Status: prepared only. No optimizer was invoked. A later, separately frozen
runner is documented in `RUNTIME.md` and `runner-manifest.json`.
A separate independent serialized-model gate and root authorization are needed
before the proposed120-second, four-worker run, seed2026104601.

This model keeps all4,368 lexicographic block variables mutable and selects
exactly64 blocks. It imposes no regularity, degree20, symmetry, fixed block,
incumbent-incidence, restricted-family, or global-profile constraint. Its only
objective is the exact number of uncovered triples.

## Exact semantics for the independent gate

The frozen comparison is `../compact-pair-two-counts/manifest.json`, SHA256
`82372b924493eed1e3a24c48e580d0b15796cc1d2c50bbe71b400bee23910aad`.
Compared with that explicit stronger-cut model:

- Preserve the domains and indices of all first5,608 variables:4,368 Boolean
  blocks,120 pair counts[5,64],560 triple counts[0,64],560 exact hole flags.
- Preserve exactly the first1,801 rows: one cardinality,680 exact incidence
  equations, and1,120 enforced equations/inequalities making each hole flag
  equivalent to its triple count being zero.
- Omit all1,680 explicit single-triple rows, justified below.
- Replace all10,920 explicit two-triple rows by1,680 hinge rows and120 budgets.
- Preserve all three original core caps at55; append the independently audited
  fourth transported-core cap at55.
- Replace the prior65*holes+original-core overlap objective by holes alone,
  with560 unit coefficients, zero offset, and scale1.
- Replace the prior H6 block guidance by all4,368 H49 block values, including
  all zero positions. Add no auxiliary hint values.

There are7,408 variables and3,605 rows. New integer thresholds z_P occupy
indices5608..5727 in lexicographic pair order. New integer hinges y_Pa occupy
5728..7407 in lexicographic pair then ascending outside-point order. Each new
integer variable has domain[0,64]. The row order after the first1,801 rows is
fourteen hinges then one budget per pair, followed by the four core caps.

For r=c(P) and t_a=c(P+a), with fourteen distinct outside-point positions:

    y_Pa >= t_a-z_P
    2*z_P + sum_a y_Pa <= 3*r-12.

For any distinct a,b, t_a+t_b<=2*z+y_a+y_b<=2*z+sum(y), proving every original
stronger cut. Conversely choose z equal to the second-largest position count,
including tied values at distinct positions, and y_a=max(0,t_a-z). This makes
2*z+sum(y) exactly the largest-two sum. The canonical extension is within the
stated domains and integral whenever the count variables are integral. This
proves equality of the existential integer projections. Relaxing all variables
to reals gives the same argument for continuous LP projection.

Exact incidence gives sum_a t_a=3*r. Summing the thirteen original stronger
rows that contain a fixed position a yields
13*t_a+(3*r-t_a)<=13*(3*r-12), hence t_a<=3*r-13. This is the omitted single
cut over reals as well as integers. No count or regularity assumption beyond
the exact incidence definitions is used. The real-valued derivation is bound
by the independent topmax proof README, and the extended-formulation algebra
was independently reviewed; the new serialized encoding still needs its gate.

The projected feasible region equals the explicit stronger-cut model after
adding the fourth cap to both. The added cap may tighten the older three-cap
region; the reformulation itself does not claim a stronger LP relaxation.
Changing the objective does not change the feasible region. No solver speed
or covering result has been established.

## H49 is infeasible guidance

H49 SHA256 is
`a7feb783eb9f36e710feba5356857514cde146104b95de03fa47716126afd9c4`.
Both covering verifiers agree on49 holes. Independent subset recount gives
D2max74, D2sum170, D3=D4=0, and core overlaps[0,2,2,4]. Its canonical extension
fails74 pair budgets with total deficit74. By the projection proof, no other
z/y assignment can repair these counts. Thus H49 has no feasible auxiliary
extension to this model. It is not a feasible warm start.

Only the4,368 block variables are hinted:64 ones and4,304 zeros. There are
3,040 unhinted auxiliaries. The optimizer may attempt to change this guidance;
no execution has occurred and no success is assumed.

## Producer checks and remaining gate

`check_diff.py` reads both frozen serialized models and checks all5,608 retained
domains, all1,801 retained base rows, all1,800 new variable domains, every hinge
and budget coefficient/domain/index, the retained and added core rows, exact
holes-only objective, and complete block-only hint indices. Every new row is
accounted for. This producer-side check is not the independent gate.

The current `semantic-diff-v2.json` receipt SHA256 is
`0dd92f46e486fbf407efb8a6340fb014a0424d51c81dc80299969fc04f9af939`.
The v1 checker and receipt remain preserved; `producer-diff-history.json`
records the formatting-only source change and exact snapshot binding.
The independent gate should reconstruct the full lexicographic incidence universe,
all four justified core supports, exact hole semantics, all variable domains,
all new row terms, the two projection implications, the real-valued redundant-cut
proof, the objective, and actual H49 block binding directly from the frozen model.
It should reject extra rows/restrictions and malformed or changed controls.

Raw model, parameters, guidance, and source snapshots remain in Git-ignored
scratch. Manifest records versions, revision, hashes, model size, variable and
row layouts, core supports, proof bindings and explicit infeasible-guidance label.
Ruff, model validation, and frozen read-back checks passed. No Solve call was made.

## Frozen bindings

- model: `experiments/scratch/hard-top-two-extended-four-core-20261004/model.pbtxt`, SHA256 `0121b0f0f7837880402e4df43079474d7a1491db16e925622bda476c8a558a8b`.
- parameters: `experiments/scratch/hard-top-two-extended-four-core-20261004/parameters.pbtxt`, SHA256 `7680ff36e2b4709758e249632dfe99ea51a06fa933b8104f47ac0d5a028b153f`.
- guidance: `experiments/scratch/hard-top-two-extended-four-core-20261004/block-only-h49-guidance.json`, SHA256 `7ca79ef60e017d6fbf57cdc1219643458a9f071e30a120f37afc6dd2b4ad44eb`.
- Manifest SHA256: `91400d274bf722afa92b208021909b0900903b8e10d99f74a6e5e609acb8d833`.
- Preparation source SHA256: `c32954a8368086c30f1c7d570f5eccb51cd3d4d09b7005ace5beaa18257512f5`.
