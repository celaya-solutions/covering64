```text
Document:    Lazy Heavy Master Bounded Continuation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      fb5ef8a6294cd30aed4fc787704cffd9b511c8e062362c590a519313e1b84f88
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Lazy heavy master continuation

The authorized continuation completed all 100 cases in 43.193832 seconds,
below the 90-second wall target. Every sampled heavy tuple was separated by an
exact signed-dual certificate. No fractional completion and no integer cover
was found. The run stopped at the 100-case limit.

The start contains the 14 original cuts plus the ten cuts checked after the
short pilot. A complete initial protobuf comparison passed for 276 variables
and 629 rows, and the master-builder AST is unchanged. The parent reviewed the
source delta before launch. The continuation caps each CP call at five seconds,
each of two possible LP phases at ten seconds, and uses one worker. Before each
case it requires 27 seconds remaining, reserving two seconds beyond those solver
limits. Seeds are 2026104061 through 2026104160. No extra run followed.

| Measure | First ten cases | Last ten cases |
| --- | --- | --- |
| Mean master time | 0.059193 s | 0.226222 s |
| Mean total case time | 0.337585 s | 0.528137 s |
| Mean exact dual gap | 21.7122 | 19.7248 |
| Smallest exact dual gap | 17.098 | 15.718 |
| Largest exact dual gap | 28.279 | 23.603 |

Across all 100 cases, mean gap was 20.85407 and the range was 15.077 to 28.279.
These gaps are certificate margins, not numbers of uncovered triples or a
measure of distance to an integer cover. Master solve times rose as cuts were
added; the modest gap change does not establish convergence.

`postcheck.py` reconstructed and checked every saved incremental master,
assignment, exact parameter file, all 697 residual rows per case, and all 100
new cuts without invoking a solver. The 124 total cuts are checked for this
restricted regular four-sevenfold family. Each learned cut excludes its source
heavy tuple's fractional completion. No ordinary integrality or unrestricted
lower-bound claim follows. The four anchors and all six hub graphs are retained.

Large models, solver logs, LP rows, numerical duals, and exact certificates are
in ignored scratch storage. `hash-index.json` binds its 802 frozen files.
Console files are outside that indexed directory and were hashed after process
exit in `execution-receipt.json`; standard error was empty. Compact metadata,
results, gates, source, and checks remain here. Scoped Ruff passed.

The commands were `uv run --no-sync python` with `run.py prepare`, then
`initial_check.py`, then the single `run.py run`, then `postcheck.py`.
The frozen prepared/output folders intentionally reject an in-place repeat.
