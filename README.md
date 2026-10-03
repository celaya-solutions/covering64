# covering64

Find 64 distinct five-element subsets of {1,...,16} covering all 560 triples.
The verified archival benchmark uses 65 blocks; the supported lower bound is 61.
No 64-block witness or global nonexistence proof has been obtained.

This is a reconstructed starter package. The original temporary workspace reset,
so the code was rebuilt from retained conversation records and checked again.
The original commit history, attached report, dependency lock and raw experiment
logs were not recovered. See [recovery notes](docs/recovery.md).

## Setup

Install Python 3.11 or later and [uv](https://docs.astral.sh/uv/).
Open a terminal in the extracted `covering64` folder:

```sh
uv sync --frozen
uv run pytest
uv run covering64 verify data/baselines/belic-1997.txt --expected-blocks 65
uv run python scripts/check_cover.py data/baselines/belic-1997.txt --expected-blocks 65
```

The standalone checker uses no package code or solver state. Both verifiers
must accept any claimed construction. The known benchmark SHA-256 is:

```text
89e4f68acba5d2cbee73e22d07dd1030e540b920fc7541619a065e998dc7d43f
```

## Run research

```sh
uv run covering64 model
uv run covering64 solve --target 65 --hint data/baselines/belic-1997.txt --seconds 15
uv run covering64 solve --target 64 --seconds 60 --seed 2 --workers 1 \
  --output experiments/scratch/exact.json --save-witness experiments/scratch/candidate.txt
uv run covering64 audit data/baselines/belic-1997.txt
uv run covering64 search data/baselines/belic-1997.txt --remove 4 --attempts 100 \
  --seconds-per-attempt 1 --seed 42 --output experiments/scratch/search.json
uv run covering64 encode experiments/scratch/atmost64.cnf --target 64 \
  --output experiments/scratch/cnf.json
```

The CP-SAT formulation uses exactly the requested block count and the complete
universe of 4,368 candidate blocks. Each of 560 triples must occur in a selected
block. The default applies no symmetry constraint. An optional first-block
normalization is justified by point relabeling. `OPTIMAL` means feasibility
success in this model, not optimality of the mathematical covering number.

The proof CNF uses at most the requested number of blocks, equivalent to exact
cardinality for existence because smaller covers can be padded with unused
distinct blocks. A checked unrestricted UNSAT proof at 64, with the known
65-block witness, would prove C(16,5,3)=65. A valid 64-block witness improves
the upper bound; it does not establish the exact covering number.

To check a DRAT proof after separately installing a proof solver and checker:

```sh
DRAT_TRIM=/path/to/drat-trim bash scripts/verify_drat.sh INSTANCE.cnf PROOF.drat
```

No global proof has been checked. Timeouts, UNKNOWN and neighborhood-only
infeasibility are not global nonexistence results. Consult the
[campaign](docs/campaign.md) and [evidence policy](docs/evidence-policy.md).

## Prior pilot

The retained conversation records two unrestricted 20-second searches ending
UNKNOWN, 48 larger exchanges with no improvement, and an exhaustive audit of
65 deletions and 2,080 pairs with no compression of this witness. These are
historical summaries, not recovered raw logs. Fresh rebuild verification is
saved separately under `experiments/`.

## Source and delivery

The baseline comes from LJCR version 1.2,
[DOI 10.5281/zenodo.19735294](https://doi.org/10.5281/zenodo.19735294), credited to
Rade Belic on 6 August 1997. The source-data license is archived in provenance.
The full 4.2 GB `covers.json` checksum remains unverified. The exact versioned
entry is reproducibly retrievable with `python scripts/fetch_ljcr.py`.

GitHub creation was previously rejected with HTTP 403. This package does not
claim a remote repository exists. Its source ZIP can be extracted anywhere;
initialize Git locally with `git init` if desired. No new-code license is selected.
