```text
Document:    Circulant All-Profile Global Runtime Independent Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      83578be63689044856f9f256400dd168ba2285a872e04a46bb406da47db69e7c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent saved runtime audit

The sole global all-profile call ended UNKNOWN without a candidate, response
vector, or watchdog intervention. The saved response reports 300.131092 seconds
of native solver time, 3,215,239 branches, and 5,519 conflicts. The wrapper reports
300.6850745000411 seconds and exit code 0. UNKNOWN is inconclusive; this run does
not establish a lower bound or rule out a 64-block cover.

The independent checker bound the terminal result to the frozen producer,
manifest, model gate, launch receipt, all 15 preparation pins, and complete raw
file index. It replayed the response protobuf and log status, counters, timings,
and the logged 300-second, four-worker parameters. Fourteen malformed candidate
controls were rejected. No optimizer call or native requery was made by this
audit. No witness was present to pass through the two covering verifiers.

The global model permits every profile orbit for the specified circulant pair
graph, with 52 representatives covering 1,300 enumerated excess profiles. That
scope remains conditional on the named pair graph; it is not the unrestricted
C(16,5,3) problem. Model completeness and reduction details are preserved in the
separate global model gate.

## Reproduction

Run the saved-only checker from the research worktree:

```sh
uv run python experiments/2026-10-04/circulant-all-profile-global-runtime-independent/check.py --result-sha256 d926ee76ee85b3c6c3f3d739d8fd0b6ee3ad139041071fa0cda512c854d10375
```

The terminal result SHA256 is
`d926ee76ee85b3c6c3f3d739d8fd0b6ee3ad139041071fa0cda512c854d10375`.
The independent review SHA256 is
`1c1a8ac7b14d6c65162845abe54d9f2af0978ce0a9219b49671419b51f75e771`.
The checker SHA256 is
`9a7a15f8a56f6c1c35e8ead989e0679a95c83f7e157fda3747bc9488cacd6ec0`.
