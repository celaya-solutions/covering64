```text
Document:    Native Variable Cardinality Covering Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9ee056e2b1428c3be0f73f952466a45826cf15fb65fc49b9b921aecdf2e2da7f
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Prepared pilot

This is an independent implementation of the NuSC search rules reviewed in
[the source report](../post-d2-literature/README.md). It starts from the verified
65-block Belic family. Both verifiers independently report all 560 triples
covered. Its raw file SHA256 is
`89e4f68acba5d2cbee73e22d07dd1030e540b920fc7541619a065e998dc7d43f`.

The universe contains all 4,368 five-blocks in lexicographic order, each with
unit cost. Point labels remain 1-based. The search state has variable size;
no core cap filters additions, removals, or intermediate states. With incumbent
65 the source policy visits 64, 62, and 63 blocks, and swaps at 64. It does not
force excursions to 65 or 66. A complete family of size at most 64 stops the
entire campaign immediately after the mutation that creates it.

For an unselected block, score is the weight of uncovered triples and pscore is
the weight of singly covered triples. For a selected block, these are minus
the weights of singly and doubly covered triples. Rank by `5*score+pscore`,
then pscore, then oldest last-flip time, then smallest global lexicographic ID.
The last tie rule is an explicit deterministic adaptation.

An incoming block covers a sampled uncovered triple. Configuration checking
and age at least four filter its 78 carriers. If all are filtered, take the
first lexicographic carrier. The source expression is
`(random() % 100)/(double)101 < novelty_p`, with `novelty_p=0.1`.
Thus second-best selection occurs for integer residues 0 through 10: 11/100.
This implementation uses an injected integer draw for controls and a uniform
0..99 draw from mt19937_64 in the pilot. It does not claim to reproduce the
upstream generator's full random sequence.

At a complete family, remove a redundant block if possible, otherwise the
ranked outgoing block. At an incomplete family choose incoming first. Add it
alone when the resulting size is strictly below the incumbent, then increase
weights on triples still uncovered. Otherwise swap only when its raw weighted
gain exceeds the outgoing block's raw weighted loss. If not, remove two blocks,
recomputing the outgoing ranking after the first. Weight increments do not
change configuration flags. Adding or removing a block enables neighbors
sharing a triple; a removed block is then disabled. There is no weight decay.

# Saved evidence and scope

The driver separately saves every strict improvement and the final values for:

- Best complete family, initialized to the verified 65-block family.
- Best raw family of exactly 64 blocks, ranked by fewest uncovered triples.
- Best exact-64 family whose overlap with each of four diagnostic cores is at
  most 55. If none is encountered, this record is explicitly null.
- Actual last state, including its actual cardinality.

Four core rows are copied as data from the prior audited pilot's manifest;
that manifest and all four rows are bound in this manifest. They only classify
the admissible exact-64 record. Initial Belic65 overlaps are `[60,0,1,1]`,
which demonstrates why imposing these caps on the live walk would change the
algorithm. Partial families remain incomplete even if they pass all four caps.

The runner checks every saved family through the package verifier and the
independent standalone checker using its actual block count. It also compares
reported holes, core overlaps, record order, final files, and process status.
A search timeout or unsuccessful heuristic run proves no lower bound.

# Controls and reproduction

`prepare.py` builds the native executable and an AddressSanitizer plus
UndefinedBehaviorSanitizer control executable. It runs only a fixed 48-step
replay and primitive controls. It never launches the timed search. Controls
exercise all four reached transition branches: complete drop, double drop,
add-only, and swap; add/remove inverse counts; duplicate and absent operation
rejection; age3 versus age4; novelty residues10 versus11; all-locked fallback;
weight updates; and immediate callback stopping. A synthetic target predicate
check deliberately changes only diagnostic fields; it is explicitly not a
cover witness and is never saved as one.

Saved control families have actual sizes63,64,64, holes17,8,56, respectively.
Both checkers agree. Invalid duplicate, out-of-range, and short rows are rejected
by both checks. Own controls are not the separate independent control gate.

The pilot budget is two sequential 120-second calls, seeds2026104701 and
2026104702, with no unused-budget transfer or relaunch. A135-second watchdog
allows5 seconds for termination before kill. The main agent owns launch after
the independent gate passes. No timed optimization was launched during
preparation. Invocation, only after that gate:

```sh
uv run python experiments/2026-10-04/native-variable-cardinality/run.py \
  --gate experiments/2026-10-04/native-variable-cardinality-independent/gate.json
```

The manifest binds native/Python sources, input cover, core origin, checkers,
lockfile, compiler/version, binaries, sanitizer output, deterministic replay,
and malformed controls. Raw binaries, logs, and source snapshots live in the
ignored scratch folder. Source revision and all wall budgets are recorded.
Upstream GPLv3 material remains read-only ignored evidence; no upstream code
was copied or linked into this independent implementation.

An initial manifest was issued before Python line wrapping passed ruff. Its
hash was37013af979a2b7bf30d5ef30783ec6604bce2930eebf3efb126ee6c1bd4f7097
and it is retained as `pre-format-manifest.json` in scratch. The only code
changes after that receipt were Python line wrapping and shorter manifest
prose; C++ sources, binaries, controls and control output are unchanged.
The literature report then corrected its shorthand novelty expression to show
the actual floating-point cast. The current manifest binds that corrected report.
