```
Document:    Integer Double Triple Patterns for the Four-Sevenfold Branch
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      4c19e55837383b0769eec8c18cad2ec24062a40bd762ac1c5c00aeda576fc4ad
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Integer patterns for the 44 remaining double triples

Both four-sevenfold pair-demand systems have integer solutions. Each saved
pattern has 44 distinct triples, at most one anchor per group, all 120 prescribed
pair counts, degree 7 at each anchor, and degree 12 at each hub. These are necessary
triple-multiplicity patterns, not 64-block covers and not proofs that such covers exist.

| Case | Seed | Status | Solver seconds | Zero/one/two/three-anchor triples |
| --- | --- | --- | --- | --- |
| Cycle | 2026103901 | OPTIMAL | 0.045085 | 2 / 12 / 18 / 12 |
| Matching | 2026103902 | OPTIMAL | 0.035126 | 1 / 15 / 15 / 13 |

Each run used OR-Tools 9.15.6755, one worker, a 60-second budget, 400 Boolean
variables and 108 nonzero pair-demand equations. The metadata records the source
revision and hashes. Raw models, source snapshots, and full logs are preserved in
`experiments/scratch/four-seven-double-patterns-20261003/{cycle,matching}/`.

The original post-solve checker rejected an incorrect bookkeeping formula after
both witnesses had been saved. Its metadata and source snapshots were preserved.
The corrected checker v1.0.1 independently accepted the unchanged witnesses;
`*-result.json` explicitly records its reconstruction from the saved solver log
and hashes the log and corrected report. No new solver run was substituted.

`check.py` reconstructs the pair demands directly, checks cardinality, labels,
structure and degrees, and rejects duplicate, repeated-label, out-of-range, and
wrong-case controls. It also runs both cover checkers with `(v,k,t)=(16,3,2)`:
both correctly return `valid:false` with exactly the twelve internal anchor pairs
uncovered. This is expected for the pair-demand witness.

For z all-hub triples, the correct counts are
`(N0,N1,N2,N3)=(z,18-3z,12+3z,14-z)`, with `z` in `{0,1,2}`.
See the separate arithmetic correction in `../four-seven-independent/`.

Reproduce validation from the repository root:

```sh
uv run python experiments/2026-10-03/four-seven-double-patterns/check.py cycle experiments/2026-10-03/four-seven-double-patterns/cycle-pattern.txt /tmp/cycle-pattern-check.json
uv run python experiments/2026-10-03/four-seven-double-patterns/check.py matching experiments/2026-10-03/four-seven-double-patterns/matching-pattern.txt /tmp/matching-pattern-check.json
```

The header hash is over this body, including its initial blank line.
