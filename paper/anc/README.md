```text
Document:    Ancillary Files for The Covering Number C(16,5,3) Is at Least 62
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-06
SHA256:      d3aa2dcc839625eb162112f164310525589ce91c73266600cf5ddbf095ed1e0d
Chain:       solana-mainnet
Tx:          2v276PFHeZ8CxBBXQ3fsGjU1bpMdPqaVma4qqH9ihMPYPMZdDKheQAJk4Wcyjy77XcQebLcKzAindo4EUozxpZvT
License:     CC BY 4.0 / Celaya Solutions
```

# Ancillary files

Christopher B. Celaya, Celaya Solutions Research. Licensed CC BY 4.0, which
supersedes the older "All Rights Reserved" header line in `cpsat_check.py`
(that line is kept because the file's bytes are pinned by SHA256 hashes).

| File | What it is |
|---|---|
| `shape-1-class-0.txt`, `shape-4-class-0.txt`, `shape-44-class-0.txt`, `shape-47-class-0.txt` | The representatives R_1, R_2, R_3, R_4 of the paper, each written as the 19 blocks {1} u R, R in R_i (Table 1 with the point 1 added) |
| `gen_cnf.py` | Writes the formula F_i for one representative as DIMACS and prints its SHA256; no solver is called |
| `cpsat_check.py` | The separately written CP-SAT model of Section 6, as run |
| `SHA256SUMS.txt` | SHA256 of the four CNF formulas and four DRAT proofs (uncompressed and zstd-compressed) and of the other files in the Zenodo record |

Regenerate a formula and compare its hash (needs python-sat 1.9.dev15, since
the CNF bytes depend on its variable numbering):

```sh
pip install python-sat==1.9.dev15
python gen_cnf.py shape-1-class-0.txt F1.cnf
grep lb61-shape-1.cnf SHA256SUMS.txt
```

The formulas, the DRAT proofs and the drat-trim logs are on Zenodo,
https://doi.org/10.5281/zenodo.23191655. The full code and evidence are at
https://github.com/celaya-solutions/covering64. `cpsat_check.py` reads the
representatives from the repository layout; run it from a checkout as
`python experiments/2026-10-05/lb61-crosscheck/cpsat_check.py shape-1-class-0.txt 3600 3`.
