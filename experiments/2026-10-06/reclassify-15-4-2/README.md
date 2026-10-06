```text
Document:    Independent Reclassification of Minimum (15,4,2) Coverings
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-06
SHA256:      647c65346fc9b1d74cde1b46ab25de8d09c2bae3728f947756775bc3bc42d43a
Chain:       solana-mainnet
Tx:          4hQruM2puReSmedy3pRiC9UXFnRo3W7AKyCJ7N76Ben4xtTyzRccGUEUgSr2rcBA7hYVMP8hp1GdPj3SwDELwHqk
License:     CC BY 4.0 / Celaya Solutions
```

# Independent reclassification of minimum (15,4,2) coverings

This folder is the second classification computation of the paper (the
"direct enumeration" in the section on minimum (15,4,2) coverings). It lists
every labeled 19-block (15,4,2) covering in standard form and splits the list
into isomorphism classes.

## What was computed

**Standard form.** Points 0..14, hub 0, leaves 1..4, matching {5,6}, {7,8},
{9,10}, {11,12}, {13,14}. The nine excess pairs ({0,1}, {0,2}, {0,3}, {0,4}
and the five matching pairs) are covered exactly twice and the other 96 pairs
exactly once, by 19 distinct 4-subsets. The paper's counting lemma shows that
every minimum (15,4,2) covering can be relabeled into this form, and that every
isomorphism between two such coverings lies in the group G of the excess graph
K(1,4) + 5K(2): S_4 on the leaves times S_2 wr S_5 on the matching, of order
4! x 5! x 2^5 = 92,160. So the isomorphism classes are the G-orbits on the
labeled standard coverings.

**Steps.**

1. `enum_par.c` (exact cover with multiplicities, in C) enumerates every
   labeled standard covering. Items are the 105 pairs with demand 2 or 1;
   options are the 1,365 quadruples. Each node branches on one pair with
   remaining demand r over all r-subsets of valid quadruples through it, so
   every covering is produced exactly once. Two branching rules: mode 1 takes
   the lowest-index pair with remaining demand, mode 0 the pair with the
   fewest candidate r-subsets. A deterministic K-way split at a fixed tree
   level lets K processes share the work. `enum.c` is the same search without
   the split (single thread).
2. `analyze.py` reads the raw output, checks every solution (19 distinct
   quadruples, exact multiplicity on all 105 pairs), checks there are no
   duplicates, builds G and checks it (92,160 distinct permutations, each
   preserving the excess graph), and splits the set into G-orbits: for each
   unvisited covering it applies all of G, checks that every image is in the
   enumerated set, and checks orbit size x |Aut| = 92,160.
3. `check_shapes.py` reads the repo's four representatives
   (`experiments/2026-10-03/link-classification/shape-{1,4,44,47}-class-0.txt`),
   checks each is a 19-block covering with hub 2 and the standard excess
   graph, relabels it to standard form, finds its orbit, and counts its
   automorphisms twice: with G, and by plain backtracking over all point
   bijections (no use of G). It also counts isomorphisms between every pair of
   representatives by backtracking.
4. `hubsets.py` and `cpsat_hub.py` are a second method. `hubsets.py` lists
   every labeled hub-block set (the six blocks through the hub) and its
   G-orbits. `cpsat_hub.py` fixes the six hub blocks of each orbit
   representative and lets OR-Tools CP-SAT enumerate every completion. Then
   N = sum over orbits of |orbit(H)| x completions(H), and each
   representative's CP-SAT completion set is compared, as a set, with the
   DFS coverings that have exactly those hub blocks.
5. `cpsat_spot.py` repeats step 4 without any symmetry reduction on 5,999
   labeled hub-block sets: 3,000 drawn uniformly at random and 3,000 taken
   from DFS solutions (seed 20261006).
6. `compare_repo.py` compares the results with the repo's
   `automorphisms.json` and `classification.json` in the same folder as the
   representatives.

The enumerator, `common.py` and the steps above were written from scratch;
the notes of the first run record that no repo code was read or imported,
in particular not the repo's first classification code
(`experiments/2026-10-03/link-hub-independent/`,
`docs/independent-link-classification.md`). The repo's representatives and
JSON files were read only in steps 3 and 6, after steps 1 and 2 were done.

## Commands

Run from this folder. `python` is the repo environment (`uv sync` at the repo
root, then `uv run python` or `.venv/bin/python`). Versions used: Python
3.13.15, NumPy 2.5.3, OR-Tools 9.15.6755, Apple clang 21.0.0 (arm64).

```sh
cd experiments/2026-10-06/reclassify-15-4-2

# Steps 1 and 2, lowest-index pair (mode 1), 14 processes split at level 2
./run_enum.sh 1 14 2 out/dfs1        # builds enum_par with cc -O2, then runs it
python analyze.py out/dfs1 out/dfs1.npz dfs1_orbits.json
cmp dfs0_orbits.json dfs1_orbits.json

# Step 3
python check_shapes.py               # reads out/dfs1.npz and the repo's representatives

# Steps 4 to 6
python hubsets.py out/hubsets.npz
python cpsat_hub.py out/hubsets.npz out/dfs1.npz 16
python compare_repo.py               # reads out/dfs1.npz and out/hubsets.npz
python cpsat_spot.py out/hubsets.npz out/dfs1.npz 3000 3000 14

# Second branching rule (mode 0), 16 processes split at level 3
./run_enum.sh 0 16 3 out/dfs0
python analyze.py out/dfs0 out/dfs0.npz out/dfs0_orbits.json
cmp out/dfs0_orbits.json dfs0_orbits.json
python -c "import numpy as np; a=np.load('out/dfs0.npz'); b=np.load('out/dfs1.npz'); \
print((a['sols']==b['sols']).all() and (a['orbit_of']==b['orbit_of']).all())"
```

The logs of these runs are in `logs/`. `out/` holds the raw solution files
(`s*.bin`, 19 uint16 point masks per covering) and the `.npz` arrays; it is
ignored by Git and is rebuilt by the commands above. `dfs0_orbits.json` and
`cpsat_hub.log` at the top of this folder are the outputs of the first run of
this code (mode 0, in a scratch folder, earlier on 2026-10-06), copied
unchanged.

## Results

**Enumeration.** Both branching rules find the same set of
**N = 138,240** labeled standard coverings. Every one passes the
multiplicity check and none is repeated.

| Run | Processes | Coverings | Search nodes | Wall time | CPU time |
|---|---:|---:|---:|---:|---:|
| Mode 1, lowest-index pair | 14 | 138,240 | 5,156,672,630 | 41.0 s | 521 s |
| Mode 0, most constrained pair | 16 | 138,240 | 635,790,532 | 85.1 s | 1,350 s |

The node counts include the part of the tree above the split level once per
process. They equal the counts of the first run exactly. The two `.npz`
arrays (sorted coverings and orbit ids) are identical.

**Orbits.** G splits the 138,240 coverings into **four orbits**:

| Orbit | Size | Aut order = 92,160 / size | Leaves per hub block | Repo representative |
|---|---:|---:|---|---|
| 0 | 23,040 | 4 | 3, 2, 2, 1, 0, 0 | shape-1 |
| 1 | 46,080 | 2 | 3, 2, 2, 1, 0, 0 | shape-4 |
| 2 | 46,080 | 2 | 3, 2, 1, 1, 1, 0 | shape-44 |
| 3 | 23,040 | 4 | 3, 1, 1, 1, 1, 1 | shape-47 |

The sizes add up to 138,240 = N, and so do the values 92,160 / |Aut|. The
rerun's `dfs1_orbits.json` and `out/dfs0_orbits.json` are byte-identical to
the first run's `dfs0_orbits.json`.

**Repo representatives** (`logs/check_shapes.log`). Each of the four files is
a 19-block covering of 2..16 with distinct blocks, largest pair multiplicity
2, hub 2 of degree 6, leaves {3,4,5,6} and matching {7,8}, {9,10}, {11,12},
{13,14}, {15,16}. Each lies in the enumerated set, in a different orbit (see
the table). Automorphism counts by G and by plain backtracking agree: 4, 2,
2, 4. Plain backtracking finds 0 isomorphisms for each of the 6 pairs. Every
representative has a hub block containing three leaves, {2,3,4,5}.

**CP-SAT by hub-block sets** (`logs/hubsets.log`, `logs/cpsat_hub.log`).
There are 5,745,600 labeled hub-block sets in 206 G-orbits. Only 4 orbits
have completions:

| Hub-set orbit size | Stabilizer order | Completions | Orbit size x completions |
|---:|---:|---:|---:|
| 1,920 | 48 | 12 | 23,040 |
| 11,520 | 8 | 4 | 46,080 |
| 23,040 | 4 | 2 | 46,080 |
| 240 | 384 | 96 | 23,040 |

Their sum is N = 138,240. For all 206 representatives the CP-SAT completion
set equals the DFS set (0 mismatches). The spot check without symmetry
(`logs/cpsat_spot.log`) checked 5,999 labeled hub-block sets, 3,020 of them
with completions, with 0 mismatches.

**Repo JSON files** (`logs/compare_repo.log`). `automorphisms.json` lists 4,
2, 2 and 4 maps; each is a distinct automorphism and each listed set equals
the automorphism group found here. In `classification.json`, `input_links`
= 12, 4, 2, 96 equals the completions per hub set above,
`hub_automorphisms` = 48, 8, 4, 384 equals the stabilizer orders, each shape
has one class, and all cross-shape pairs are non-isomorphic.

**Run times** (this rerun, Apple M5 Max, 18 cores, macOS 27.0, other jobs
running at the same time):

| Step | Wall time |
|---|---:|
| `run_enum.sh 1 14 2` (build and enumeration) | 41.0 s |
| `analyze.py` | 0.9 s |
| `check_shapes.py` | 0.3 s |
| `hubsets.py` | 101.9 s |
| `cpsat_hub.py` (16 processes) | 1.2 s |
| `compare_repo.py` | 8.1 s |
| `cpsat_spot.py` (14 processes) | 14.6 s |
| `run_enum.sh 0 16 3` (build and enumeration) | 85.1 s |

`enum.c` (one thread, mode 0) was not rerun. In the first run it found the
same 138,240 coverings with 635,736,097 nodes in 2,282 s on a busy machine.

## What this does and does not prove

It shows, given the paper's counting lemma (every minimum (15,4,2) covering
is isomorphic to a standard one, and isomorphisms between standard coverings
lie in G), that there are **exactly four isomorphism classes** of minimum
(15,4,2) coverings, with automorphism groups of orders 4, 2, 2 and 4, and
that the repo's four representatives are one from each class. This agrees
with Allston, Buskens and Stanton (1988) and with the repo's first
classification, and it supplies the completeness of the enumeration that
`classification.json` itself does not claim.

It does not prove:

- **The counting lemma.** The standard form and the group G are inputs here,
  not outputs. They are proved by hand in the paper.
- **That the search code is correct.** There is no certificate. The evidence
  is agreement: two branching rules, a CP-SAT enumeration split by hub-block
  sets, and an unreduced CP-SAT spot check all give the same set. CP-SAT
  reports no proof of its enumerations either.
- **Full independence of the two methods.** The DFS and CP-SAT runs share
  `common.py` (the excess pairs, the demands and G), so an error in the
  definition of standard form would affect both. Steps 3 and 6 check the
  result against files produced separately, and the backtracking
  automorphism counts in step 3 do not use G.
- **Anything about C(16,5,3) by itself.** The classification is one input of
  the reduction to the four CNF formulas; see `../lb61-encoder-audit/`.

## Files

| File | Role |
|---|---|
| `enum.c`, `enum_par.c` | the enumerator, single thread and split |
| `run_enum.sh` | builds `enum_par` and runs K processes |
| `common.py` | standard form, G, validation and mapping helpers, folder paths |
| `analyze.py` | validation, deduplication, G-orbits |
| `check_shapes.py`, `compare_repo.py` | comparison with the repo's representatives and JSON files |
| `hubsets.py`, `cpsat_hub.py`, `cpsat_spot.py` | the CP-SAT cross-checks |
| `dfs0_orbits.json`, `cpsat_hub.log` | outputs of the first run, unchanged |
| `dfs1_orbits.json` | one representative per orbit from this rerun, in standard labels |
| `logs/` | logs of this rerun |
| `out/` | raw solutions and `.npz` arrays (ignored by Git, regenerable) |
