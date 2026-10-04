```
Document:    Independent Neutral Queue Combined Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      cb17a2d2300f8eb7a7e690557835c6860e077966a4b1e39148f99af4a1a7044b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Combined neutral-queue gate

The combined gate passed and binds the producer manifest, runner, adapter,
binaries, independent wrapper controls, and separate native review.
`gate.json` SHA256 is
`e808301cec82a6ea805dba9ab2aa58debb56233b7cf9eac9615f485f448f8e90`.
The producer manifest SHA256 is
`5a1082e2f28194ee4c90ee0d16bf0d5b22502164e082e757a35842547eae2a82`.
The native review receipt is in `../weak-pair-neutral-native-review/review.json`,
SHA256 `213a27f1940aa49506ccce310a8a333c357f2f6ddbed8ff05b5ccd295bdf9049`.

Independent wrapper controls passed 13 transition cases, three invalid-transition
cases, two saved actual neutral families with direct metric and ordinal recounts,
and 46 damaged recorder cases. The transition controls use explicitly abstract
states; the recorder controls use explicitly synthetic metadata around previously
verified families and saved strict logs. None represents a new search. They cover
historical exclusions, duplicates, global full-ID queue ordering, strict priority,
clearing the old frontier, both incomplete stop paths, cover handling, and both
neutral and strictly improving chains at the 16-center/32-shell limit.

The native reviewer confirmed exact equality with the old search bodies after
removing the observer-only additions, and byte identity of all four evaluation
headers. Five synthetic sampling/count/order cases and eight damaged cases passed
against the frozen native observer. The sampler retains the first at most 64
qualifying equal-rank families in deterministic traversal order, then sorts those
families by full IDs. It does not retain the globally smallest 64 families, and
reaching the cap never stops shell enumeration. Observer overhead may affect
how far an incomplete wall-clock-limited pass reaches.

The initial D26 family is the sole allowed revisit of a previously processed
center and counts toward the 16-center limit. Other historical centers are excluded.
Each new center runs both fixed shells from the same family before adopting a
noncover result. Any strict best improvement takes precedence over neutral moves;
a lower rank clears the old frontier. Otherwise the next unvisited retained family
is chosen by full-ID lexicographic order. Every retained candidate passes the
existing direct metric checks and both covering verifiers before use.

Per-shell limits remain 120 seconds, with a 135-second watchdog and five-second
termination grace; there is no relaunch, transfer, or budget extension. Early
cover or incomplete results preserve their explicit scope. `sample_exhausted`
means the retained queue is empty, not that the equal-rank region is exhausted.
Only individual fully completed shells support their finite neighborhood claims.
The campaign provides no unrestricted existence or global lower-bound theorem.

No optimizer was launched by this combined audit. The native review, controls,
and gate are frozen; raw synthetic fixtures are retained in the ignored scratch
folder and hashed by the gate.
