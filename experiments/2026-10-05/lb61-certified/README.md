```text
Document:    Certified 61-Block Fixed-Link Runs
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-06
SHA256:      8e6c33fc213191f66d0639d813bbb0ca8323428d020eb01fa9098f593421a88f
Chain:       solana-mainnet
Tx:          5yEnCTwE3qAegnXykuM6k7q8sU69UWr6UCjxK3kwc3LjKKdCe2QBMVT6ADGrA55XLgvDtGeZ4AjSJNhMinAcHZRE
License:     CC BY 4.0 / Celaya Solutions
```

# Certified proofs: no 61-block cover

`run_case.py` rebuilds each fixed-link CNF with the encoder copied verbatim
from the probe, writes it as DIMACS, solves it with Lingeling through PySAT while
recording a DRAT proof, and checks the proof with drat-trim (commit
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985`, built locally). PySAT's CaDiCaL
proofs fail drat-trim even on a small pigeonhole test, while Lingeling,
Glucose 4 and MapleChrono proofs verify, so Lingeling was used.

The runs started on 2026-10-05 at 09:27 MDT with the header line
`SHA256: [pending]`; the saved script differs only by its filled header.
All four finished:

| Link class | Lingeling | Solve time | Proof lines | Proof size | drat-trim | Check time |
|---|---|---:|---:|---:|---|---:|
| shape-1 | UNSAT | 4.1 h | 13,065,165 | 7.0 GB | s VERIFIED | 88 min |
| shape-4 | UNSAT | 5.4 h | 15,609,452 | 8.8 GB | s VERIFIED | 59 min |
| shape-44 | UNSAT | 5.5 h | 15,471,588 | 8.5 GB | s VERIFIED | 57 min |
| shape-47 | UNSAT | 4.1 h | 13,044,849 | 7.3 GB | s VERIFIED | 80 min |

The receipts `solve-*.json` and `drat-trim-*.log` are saved here. Each CNF has
144,553 variables and 512,424 clauses. Hashes:

| Link class | CNF SHA256 | DRAT proof SHA256 |
|---|---|---|
| shape-1 | `b02c6558801b615f44bb35876b1aef2ec43ec9c9d4316332bcf3355c061d8b68` | `0da466434a98e50f73ea878df05c7b05f4c26663e0e5be33587f1718c1847a9f` |
| shape-4 | `61b97d1ac13cef65b096b74ee8c2b0efaadabc79e00fb27f74e0ddff184b2c45` | `0f5c55d099f9b4fd4d1527a95f4493edec1cb79cf59a76f96fcd8a5071e79034` |
| shape-44 | `567e02283ef694feb5d5f5e49925e835b09bc05571b9b6f7b1b5340728c7b33b` | `64afef43cc5b162a048bac3b20a6baeff78b70d24c913a6a8edce0a4f2a9b631` |
| shape-47 | `90389853552621affc8a203dc900e6e7e94b52bc3989556e4cca10b26f055e51` | `ce9094d6ebcec09ffe10ffaf156705a8df0f50c4d060f840d160c56048d9a459` |

The CNF files (9.6 MB each) are regenerated exactly by `run_case.py`. The proofs
(7.0 to 8.8 GB each) are too large for Git; they are kept by Celaya Solutions
Research and can be regenerated with the same script, then checked with
`drat-trim case.cnf case.drat -t 1000000`.

Every clause of the CNF is a necessary condition of a 61-block cover after the
relabeling of `docs/lower-bound-61-structure.md`, so these verified
refutations, with the four-class classification of minimum C(15,4,2) covers,
prove that no 61-block cover exists: **C(16,5,3) >= 62**.
