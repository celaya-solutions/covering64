```text
Document:    Encoder Audit of the Fixed-Link 61-Block CNFs
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-06
SHA256:      c11d3665733f2f864c001f9c890c7200b46ea280324144d3be8d76126bca0232
Chain:       solana-mainnet
Tx:          5mPA4xYpzJQzQyNZxuvdeTsMPy97MWD8vd5wzRE7uwpKD4cm8wDgTTcmDyMCT9Cs8ySPjapw12AcSEYvvyNxzQ91
License:     CC BY 4.0 / Celaya Solutions
```

# Encoder audit of the fixed-link 61-block CNFs

A proof checker shows that a formula is unsatisfiable, not that the formula
says what it should. This folder checks the second part for the four CNF
formulas F_1..F_4 that Lingeling refuted and drat-trim verified in
`../../2026-10-05/lb61-certified/`. These are the "Checks on the formulas" in
the paper's section on computation and certification.

## What was computed

1. **The CNFs are what the encoder produces.** `gen_cnf.py` is the encoder of
   `experiments/2026-10-05/lb61-certified/run_case.py` with the solver left
   out. Its lines 34-83 are byte-identical to `run_case.py` lines 23-72 (the
   encoder), and its lines 85-87 to lines 75-77 (the DIMACS writer). Line 33
   differs from `run_case.py` line 22 only in that the link file path comes
   from the command line (`logs/gen_cnf_diff.log`). It writes the DIMACS file
   and prints its SHA256. The four hashes are compared with the ones recorded
   in the certified README and in `solve-*.json`.
2. **Per-family counts and variable ownership.** `instrument.py` is the same
   encoder with bookkeeping lines added (marked `# AUDIT`) that tag every
   clause with its family and key and record every family's variable ids. It
   prints the SHA256 of the DIMACS text built in memory, which must equal the
   file hashes from step 1. `family.py` uses it to count variables and
   clauses per family, and checks clause by clause that each clause uses only
   its own family's main variables and the auxiliary variables of its own
   counter or cardinality encoding.
3. **The counter is exact.** `counter_bf.py` reads `counter()` from
   `run_case.py` lines 29-44 at run time and executes it unchanged. Part A,
   with no solver, tries every assignment of all variables (inputs and
   auxiliaries) for the 30 cases with n inputs, bound K and n + nK <= 22 (n =
   1..8, K = 1..6). Part B uses minisat on the counter clauses alone for n =
   1..12 with K = 1..6, and for (n, K) = (14, 3), (14, 5), (14, 6): for every
   one of the 2^n input assignments there is a model whose auxiliaries equal
   "at least j of the first i+1 inputs", and blocking those values leaves no
   other model. (14, 5) is the per-pair counter of the formulas.
4. **Exactly-4 and matching clauses.** `card_match_bf.py` takes the 160
   exactly-4 clauses on a_3..a_16 and the 1,288 matching clauses (182
   exclusion, 1,092 at-most-one, 14 at-least-one) as the encoder emits them.
   It checks all 16,384 assignments of the a_v against "exactly four true",
   and for each of the 1,001 four-sets A it enumerates every model on the
   m_uv and compares the set with the perfect matchings of the other ten
   points.
5. **The representatives.** `links_check.py` checks each of the four link
   files: format (19 sorted lines, each starting with 1), (15,4,2) covering,
   hub 2, the excess graph (star at 2 with leaves {3,4,5,6} plus a perfect
   matching of the rest), and the constants the CNF derives from it.
6. **End-to-end meaning test.** `semantic.py` draws random assignments of the
   main variables (x, d, a, m), extends them to the auxiliaries canonically,
   evaluates all 512,424 clauses, and compares the set of violated clauses,
   keyed by family and block, triple, pair or point, with the set of violated
   conditions predicted from the intended definitions. 300 trials per class.

No solver was run on any full 61-block formula. minisat is used only on the
counter clauses alone (step 3), on the exactly-4 and matching clauses alone
(step 4), and on the 160 exactly-4 clauses to extend random assignments
(step 6).

## Commands

Run from the repository root. `python` is the repo environment (`uv sync`,
then `uv run python` or `.venv/bin/python`). Versions used: Python 3.13.15,
python-sat 1.9.dev15, NumPy 2.5.3. The CNF bytes depend on python-sat's
sequential counter and IDPool numbering, so the hashes are tied to that
python-sat version.

```bash
A=experiments/2026-10-06/lb61-encoder-audit
L=experiments/2026-10-03/link-classification

# Step 1: regenerate, hash, then delete the four DIMACS files (9.6 MB each)
for s in 1 4 44 47; do
  python $A/gen_cnf.py $L/shape-$s-class-0.txt $A/out/shape-$s-class-0.cnf
done
shasum -a 256 $A/out/*.cnf
rm -r $A/out

# The verbatim claim
RC=experiments/2026-10-05/lb61-certified/run_case.py
diff <(sed -n 23,72p $RC) <(sed -n 34,83p $A/gen_cnf.py)
diff <(sed -n 75,77p $RC) <(sed -n 85,87p $A/gen_cnf.py)

# Steps 2 to 6
python $A/instrument.py shape-1-class-0.txt shape-4-class-0.txt shape-44-class-0.txt shape-47-class-0.txt
python $A/family.py shape-1-class-0.txt shape-4-class-0.txt shape-44-class-0.txt shape-47-class-0.txt
python $A/counter_bf.py
python $A/card_match_bf.py
python $A/links_check.py
python $A/semantic.py 300 shape-1-class-0.txt shape-4-class-0.txt shape-44-class-0.txt shape-47-class-0.txt
```

The scripts find the repo files relative to their own location, so steps 2
to 6 also run from any other directory. The logs of these runs are in
`logs/`.

## Results

**CNF hashes** (`logs/gen_cnf.log`, `logs/gen_cnf_vs_readme.log`). All four
formulas have 144,553 variables, 512,424 clauses and 9,645,089 bytes. All four
SHA256 values equal the recorded ones in the certified README and in
`solve-*.json`:

| Link class | CNF SHA256 (regenerated) | Recorded |
|---|---|---|
| shape-1 | `b02c6558801b615f44bb35876b1aef2ec43ec9c9d4316332bcf3355c061d8b68` | same |
| shape-4 | `61b97d1ac13cef65b096b74ee8c2b0efaadabc79e00fb27f74e0ddff184b2c45` | same |
| shape-44 | `567e02283ef694feb5d5f5e49925e835b09bc05571b9b6f7b1b5340728c7b33b` | same |
| shape-47 | `90389853552621affc8a203dc900e6e7e94b52bc3989556e4cca10b26f055e51` | same |

`instrument.py` gives the same four hashes in memory (`logs/instrument.log`),
so the bookkeeping lines do not change the output. The DIMACS files were
deleted after hashing.

**Families** (`logs/family.log`). The same table holds for all four classes.
A counter over n inputs with bound K has nK variables and
(K+1) + (n-1)(4K-1) clauses.

| Family | Variables | Clauses |
|---|---:|---:|
| Fixed blocks through point 1 (unit clauses) | 1,365 | 1,365 |
| Free block variables | 3,003 | 0 |
| d_T, one per triple | 560 | 0 |
| Triple counters (560 x (78 inputs, K = 3)) | 131,040 | 476,560 |
| Triple outputs (mu in {1,2}, d_T iff mu = 2) | 0 | 2,240 |
| Exactly-4 on a_3..a_16 (14 a_v + 80 auxiliary) | 94 | 160 |
| Matching variables m_uv | 91 | 0 |
| Matching: exclusion, at most one, at least one | 0 | 182 + 1,092 + 14 |
| Pair (1,2): counter, output | 70 | 253 + 3 |
| Pairs (1,v), 14: counters, outputs | 980 | 3,542 + 28 |
| Pairs (2,v), 14: counters, outputs | 980 | 3,542 + 56 |
| Pairs inside 3..16, 91: counters, outputs | 6,370 | 23,023 + 364 |
| **Total** | **144,553** | **512,424** |

The ownership check found 0 literals outside their family in all four
formulas, and the variable id ranges of the families are disjoint and cover
1..144,553 with no gap.

**Counter** (`logs/counter_bf.log`). Part A: all 30 cases pass (exactly 2^n
models, each with the intended auxiliary values). Part B: all 75 cases pass,
including (14, 5).

**Exactly-4 and matching** (`logs/card_match_bf.log`). The exactly-4 clauses
are satisfiable for exactly the 1,001 assignments with four a_v true (0
mismatches out of 16,384). For each of the 1,001 four-sets A the models on
the m_uv are exactly the 945 perfect matchings of the other ten points:
945,945 models in total, 0 mismatches.

**Representatives** (`logs/links_check.log`). All four files pass: 19 sorted
lines through 1, a covering of 2..16, degrees 6 (point 2) and 5 (the other
14), largest pair multiplicity 2, excess graph the star at 2 with leaves
{3,4,5,6} plus the matching {7,8}, {9,10}, {11,12}, {13,14}, {15,16}. The
pair (1,2) gets 4 doubled triples and every pair (1,v) gets 1, as the CNF
requires. Each has a hub block with three leaves.

**Meaning test** (`logs/semantic.log`). 1,200 trials (300 per class), 0
mismatches. Every family was violated in some trials, so every family was
tested: triple 267,805 times, pair 108,060, at-most-one 1,063, exclusion 422,
fixed block 255, at-least-one 159, exactly-4 146.

**Run times** (Apple M5 Max, 18 cores, macOS 27.0, other jobs running):

| Script | Wall time |
|---|---:|
| `gen_cnf.py`, per class | 0.3 s |
| `instrument.py`, four classes | 1.3 s |
| `family.py`, four classes | 4.3 s |
| `counter_bf.py` | 4.7 s |
| `card_match_bf.py` | 138 s |
| `links_check.py` | under 0.1 s |
| `semantic.py`, 1,200 trials | 26.8 s |

## What this does and does not prove

It shows that the four DIMACS files certified in
`../../2026-10-05/lb61-certified/` are exactly what this encoder produces from
the four representatives, and that each clause family states its intended
condition: the counters are exact equivalences (by brute force for the sizes
above, and by the induction in the paper in general), the exactly-4 and
matching clauses are exact (exhaustively), no clause reaches into another
family's variables, and on 1,200 random assignments the violated clauses are
exactly the violated conditions.

It does not prove:

- **Unsatisfiability.** That comes from the Lingeling DRAT proofs and
  drat-trim, recorded in `../../2026-10-05/lb61-certified/`. The proofs (7.0
  to 8.8 GB each) were not rechecked here.
- **The reduction.** That every 61-block covering, relabeled, gives a model
  of one of F_1..F_4 is the paper's argument, not a computation here.
- **Completeness of the four representatives.** That is the classification;
  see `../reclassify-15-4-2/`.
- **Exactness in every case.** The meaning test is a random sample, not an
  exhaustive check, and the counter brute force covers the listed sizes only
  (the formulas use (78, 3) and (14, 5); the (78, 3) case rests on the
  induction).

## Files

| File | Role |
|---|---|
| `gen_cnf.py` | generation-only copy of the certified encoder; writes DIMACS, prints SHA256 |
| `instrument.py` | the encoder with clause tags, used by the scripts below |
| `family.py` | per-family counts and the variable ownership check |
| `counter_bf.py` | brute force of `counter()` |
| `card_match_bf.py` | exhaustive check of the exactly-4 and matching clauses |
| `links_check.py` | checks on the four representatives |
| `semantic.py` | the random end-to-end meaning test |
| `logs/` | logs of the runs above |
