```text
Document:    Four Explicit Overlap Five Pilot Results
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      f0a81a3bf087ff881216e6c5c532edeee26c185fe5e7a21299feacb89eb8c7fb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result and scope

The bounded campaign examined exactly four explicit ordered unions of two
degree-19 point links sharing five blocks. It did not screen all 4,578,210
factorized union classes. No 64-block cover was found.

| Pilot | LP result | Follow-up CP result |
| --- | --- | --- |
| pilot-000 | Independently excluded; gap 249957/1000000 | Not launched |
| pilot-001 | Numerical OPTIMAL; 262 fractional blocks | UNKNOWN after 300 seconds |
| pilot-002 | Numerical OPTIMAL; 263 fractional blocks | UNKNOWN after 300 seconds |
| pilot-003 | Numerical OPTIMAL; 263 fractional blocks | UNKNOWN after 300 seconds |

Each model retains all 4,368 lexicographic Boolean block variables, fixes its
33-block union, and leaves all 2,002 anchor-avoiding blocks available for the
31 required additions. Model encoding was independently checked before launch
in `../degree19-overlap-five-independent/pilot-audit.json`.

# LP and certificate checks

Each pilot had a total budget of fifteen solver seconds shared between
feasibility and any phase-one certificate attempt. Actual solve times were
about 1.967, 0.077, 0.086 and 0.085 seconds. Pilot-000's positive certificate
was independently replayed with separate standard-library integer arithmetic
in `../degree19-overlap-five-certificate-replay/pilot-000.json`; seven damaged
controls were rejected. The weighted lower bound is 49,766,047 and the box
maximum is 49,516,090 at denominator 1,000,000.

The other three saved primals have zero domain violation and maximum numerical
row violations of approximately 5.62e-14, 2.53e-14 and 2.63e-13. They are
fractional numerical evidence, not exact rational witnesses or covers.
`lp-audit.json` checks all frozen sources, model/row hashes and these residuals.

# CP runs and preservation

Each LP survivor received 300 seconds and two CP-SAT workers, with at most
two CP jobs together. Seeds were 2026103402, 2026103403 and 2026103404 for
pilots 001, 002 and 003. All three returned UNKNOWN. This status is
inconclusive. No integer candidate was available to send to the two cover
verifiers; the runner invokes both for every integer candidate and additionally
checks all model rows exactly.

The ignored raw archive is
`../../scratch/degree19-overlap-five-pilot-run-v1.0.0`. It preserves each model,
LP row matrix, numerical primal and dual vectors, integer certificate,
solver parameters, CP search log, CP response, statistics, subprocess command
and status, source snapshots, revision and software versions.

`collect.py` independently reads the saved CP response protobufs and checks
status, seeds, budgets, worker counts, hashes and exact survivor selection.
`evidence.json.gz` is the compact durable archive: 37359
bytes, SHA256 `c446ef4304b9bfd7178020868f367b1717a88ddfb1d83dff8ec1364f008eea06`. It includes saved primals,
complete sparse certificate, independent replay, frozen runner/checker source,
all result summaries and hashes of every raw artifact. Large input models and
logs remain outside Git. `summary.json` records the completed collection.

# Replay

The saved raw campaign can be recollected with:

```sh
uv run python experiments/2026-10-03/degree19-overlap-five-pilot-run/collect.py
```

Running new optimization is a separate action. The preparation command
requires a new output directory, and CP selection is explicit after independent
certificate review. This result excludes one conditional union only; the
other three and the overall overlap-five branch remain unresolved.
