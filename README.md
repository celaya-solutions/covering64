```text
Document:    covering64: Research on the Covering Number C(16,5,3)
Version:     v2.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-06
SHA256:      08265f2304fc18bf947774106a97461fb7fd5d9d4a1a98706621e3458115ec1f
Chain:       solana-mainnet
Tx:          3UGyXq8sne5vS74rBgk8WLNvEJPvb4ANpRiaSLFbTpwpVd2DepTVT5mojnatSnN641Kh3Dsk1vM9Qvkjrue1bdTj
License:     CC BY 4.0 / Celaya Solutions
```

# covering64

Computer-assisted research on the covering number **C(16,5,3)**.

## The problem

A covering design C(v,k,t) is a smallest family of k-element subsets
("blocks") of a v-element set such that every t-element subset lies in at least
one block. This project studies **C(16,5,3)**: the fewest 5-element subsets of
{1, ..., 16} that together contain all 560 triples.

In plain words: sixteen people are split into teams of five. How few teams do
you need so that every group of three people shares at least one team?

**Recorded bounds before this work: 61 <= C(16,5,3) <= 65.** The 65-block
cover is due to Rade Belić (1997) and is archived in the La Jolla Covering
Repository (Daniel M. Gordon). The lower bound 61 is the Schönheim bound; these
are the values recorded by the Covering Repository as of October 2026.
**With result 1 below: 62 <= C(16,5,3) <= 65.**

## Results so far (October 2026)

1. **No 61-block cover exists, so C(16,5,3) >= 62.**
   [docs/lower-bound-61-structure.md](docs/lower-bound-61-structure.md) proves
   the rigid structure any 61-block cover must have: one point in 20 blocks and
   fifteen in 19, forced pair and triple multiplicities, and at every
   19-block point a minimum C(15,4,2) "link" from one of four known
   isomorphism classes (Allston, Buskens and Stanton, 1988). Fixing one link in
   each class leaves four SAT problems, and all four are unsatisfiable:
   Lingeling refutations with DRAT proofs of 13 to 15.6 million lines each all
   pass the independent proof checker drat-trim, CaDiCaL agrees, and a
   separately written CP-SAT model is infeasible in every case
   ([certificates](experiments/2026-10-05/lb61-certified/README.md)). To our
   knowledge this improves the recorded lower bound of 61. It is a
   computer-assisted proof that also relies on the published classification of
   minimum C(15,4,2) covers, which this repository reconstructs independently.
2. **A structured branch is closed.** Within the regular branch whose
   six-fold pairs form the circulant graph C16(+-1,+-3,8), every one of the
   6,739,200 cases with an affine point link is excluded by checked support,
   propagation and exact linear-programming certificates
   ([report](docs/research-continuation-2026-10-03.md)).
3. **No symmetric 64-block cover** exists for any of 579 settled permutation
   groups, including every tested group of order at least 21
   ([details](experiments/2026-10-04/km-prescribed-groups/README.md)).
4. **No 64-block cover has been found.** The best search state misses 3 of the
   560 triples. Near-optimal covers rely on a "seven-fold triple" pattern that
   is provably impossible at 64 blocks, which explains why local search stalls.

Every negative result is stated only for its exact scope. Solver timeouts and
unchecked solver answers are never counted as proofs.

## How to check

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/), then:

```sh
uv sync --frozen
uv run pytest
uv run covering64 verify data/baselines/belic-1997.txt --expected-blocks 65
uv run python scripts/check_cover.py data/baselines/belic-1997.txt --expected-blocks 65
```

Each experiment folder under `experiments/` has a README with its exact command,
inputs, hashes and an independent checker. Large proof streams are regenerated
by those scripts and are not stored in Git.

## Repository map

| Path | Contents |
|---|---|
| `docs/` | Research log, proofs of structural lemmas, evidence policy |
| `experiments/` | Dated experiments: sources, receipts, certificates, checkers |
| `src/covering64/` | Package: cover verification, models, search tools |
| `scripts/` | Standalone checker and research tools |
| `data/` | The archived 65-block cover and its provenance |

## Credit, license and citation

Research directed by **Christopher Celaya, Celaya Solutions Research** (El
Paso, Texas), working with AI coding agents (OpenAI Codex and Anthropic Claude
Code).

Released under [CC BY 4.0](LICENSE): you may share and adapt this work, but you
must credit **Celaya Solutions Research (Christopher Celaya), covering64,
2026, https://github.com/celaya-solutions/covering64** and note any changes.
Citation metadata is in [CITATION.cff](CITATION.cff).

Built on the work of Daniel M. Gordon (La Jolla Covering Repository, CC BY 4.0),
Rade Belić (the 65-block cover), J. L. Allston, R. W. Buskens and R. G. Stanton
(classification of C(15,4,2) covers), and the authors of CaDiCaL, Lingeling,
drat-trim, PySAT and Google OR-Tools.

Questions or independent checks: hello@celayasolutions.com
