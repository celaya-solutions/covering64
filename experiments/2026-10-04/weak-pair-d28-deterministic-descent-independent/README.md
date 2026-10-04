```
Document:    Independent Bounded Descent Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      4f2ab2a214dd8eb69464421cbd276e0857653ba8d2f6b553d078f29a352015bb
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Bounded descent gate

The wrapper is approved for one root-launched campaign with at most four rounds
and eight shell calls. The independent gate is `gate.json`, SHA256
`88a0e128b20bbff8287ee50749cdd8e46bd1267b30191faad3879e19c13f3c05`.
It binds producer manifest
`c985387e9429ca012c001dc03a105b702c8c231b55d005515e478c267cd5c17c`
and runner
`cd36b47116fb4ac44f52481cbe104f2f1df2b6acf972c4f7ab7058a7e6a70d91`.

The starting H12/D28 family was independently recounted. Both binary copies
match the previously gated one-swap and two-swap-v2 binaries exactly. The
named pair, single, quadruple, and core restrictions remain fixed. Each call
has its own 120-second native limit, 135-second watchdog, and five-second
termination grace. No relaunch, budget transfer, or random seed is permitted.

The finite independent controls passed 11 abstract campaign cases, six invalid
choice cases, two accepted and 13 rejected event-grammar cases, and four malformed
real-family inputs. Nine process controls replayed existing recorded logs through
fake processes: valid one/two shells, terminate and kill watchdog paths, duplicate
ties, damaged candidate metrics, non-object events, unknown events, and missing
final events. Raw output, valid observed witnesses, and failure receipts survived
all recovery tests. Duplicate references yielded one saved canonical family;
damaged records did not turn into covers. No optimizer, solver, or native search
binary was invoked by this audit. The replay and abstract cover fixtures are
explicitly synthetic controls, not new searches or real cover witnesses.

Both shells use the same fixed center in each round. A noncover center changes
only after both shells complete, with a strictly better (holes, summed pair-max
deficit) rank. The full sorted 64-ID family breaks best-rank ties. Any incomplete
or invalid terminal stops without adoption. A dual-verified cover may be preserved
and stop early without a completed-round or best-neighbor claim. Four rounds is
an absolute cap. Only two completed shells with no strict improvement establish
no improving radius-two neighbor of that exact center under the named filters;
plateau moves and longer escape paths remain open. This provides no global bound.

`check.py` refuses to replace the existing gate or raw-control folder. Its raw
fixtures and receipts are retained in the ignored scratch directory and hashed
in the gate. The original producer artifacts and prior gates remain unchanged.
