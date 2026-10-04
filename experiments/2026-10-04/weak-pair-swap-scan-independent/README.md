```
Document:    Independent Weak-Pair Swap Scan Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      8f2279ff531bd011ce8678b61386368b239905187a5192fe20f78dc87191c571
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent weak-pair swap-scan gate

Decision: GO for the frozen one-pass scan. Only the parent agent may launch it.
No full enumeration or optimizer was launched by this audit. Preserve the gate
and every source, input, and control artifact it binds.

- Producer manifest SHA256:
  `71c0586872f86f4b367cf410beb6718707266bc55463f84aaf095513ac601764`.
- Independent gate SHA256:
  `3f6247263cb75a0258357e2e356158388fad434e8b89bb6c9210f9871adc889c`.

## Checked scope

The fixed initial family is the CP final H12 family, with actual summed
per-pair maximum deficit 32, full-row deficit 32, pair floor 5, zero single
and quadruple deficits, and core overlaps [1,1,1,2]. The known positive control
removes lexicographic block ID 3145 from the old H12 family and adds ID 3752.
It keeps 12 holes and reduces both deficit diagnostics from 34 to 32.

The driver visits every initial selected block and every initially absent
block. This yields exactly 64 times 4,304 = 275,456 distinct one-swap neighbors.
The base never follows an improving trial. Legal trials satisfy the pair floor,
all 1,680 single rows, all 10,920 quadruple rows, and four core caps of 55.
Actual rank is lexicographic (holes, summed per-pair maximum stronger deficit).
The full 10,920-row deficit is separate. The recorder keeps strict improvement
events and every final best tie strictly below the initial rank. Compact
outgoing/incoming identities and family hashes make every saved family exact.

`DEPENDENCY.md` gives the affected-pair and unique-neighbor proofs. Every pair
contained in either changed block is rechecked, including intersection pairs
whose pair-count delta cancels. Larger subsets containing a pair outside this
union cannot change. A separate agent challenged and accepted this argument.

## Independent finite controls

A separate Python oracle computes counts by direct bitmask subset inclusion.
It imports no producer count updates, incidence tables, legality calculation,
or ranking logic. It independently expands all stronger rows rather than
reusing the producer's top-two calculation.

The C++ harness was compiled against the final frozen header with ASan and
UBSan. All 4,368 block columns and 120 pair-row groups matched independent
lexicographic subsets. Fifty fixed swaps covered intersection sizes 0 through
4, the known improving swap and reverse, and increases/decreases in every core
overlap. All 125,000 trial subset counters, all per-pair metrics, affected-row
evaluations, and exact rollback checks passed. The two initial states were
also checked in full. All 52 saved control families passed both verifiers at
their actual coverage levels; they remain incomplete families.

Twenty-four invalid native operations were rejected without changing state.
Ten synthetic legality checks and four synthetic rank checks passed. These
are metadata controls, not claimed covering witnesses. Five damaged input
families were rejected. A synthetic recorder fixture used the actual improving
family at its true ordinal, 201,680, without executing that prefix. Nine
damaged recorder fixtures were rejected, including false completion, early
timeout, wrong numeric types, wrong ordinal, wrong metrics, duplicate ties,
and an invalid outgoing ID.

`gate.json` records exact compiler flags/version/hash, final control binary,
source/input bindings, verifier receipts, and raw artifact hashes. The full
control snapshots, binaries, and logs remain in ignored scratch storage.
An initial compile attempt used a nonexistent helper name and was corrected
before any final control build; no producer code was changed by this audit.

## Budget and interpretation

The budget is one deterministic pass, at most 120 seconds of enumeration,
with a 135-second watchdog and a 5-second termination grace. No relaunch or
unused-budget reallocation is permitted. Deadline checks precede each trial;
one trial and final serialization can finish after the enumeration deadline.
The completion flag must agree with exactly 275,456 evaluated neighbors and
the terminal reason. A timeout is explicitly incomplete.

This gate does not establish a covering result or a global lower bound. A
completed scan applies only to this fixed family's one-swap neighborhood and
the declared legal filters. Every reported cover still requires both covering
verifiers. The core caps are restrictions of this local scan.
