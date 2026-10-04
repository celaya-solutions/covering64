```text
Document:    Native Three-Core-Cap Escape Preparation
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9a79e6bf862e5ff29abe1a516673e961d824e24a7ac68ebd5ac82eb3786c8d49
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Preparation status

The native experimental copy is built and frozen. No native search has run.
An independent gate is required before the two authorized 60-second calls.
The old native sources and all earlier experiment records are unchanged.

This copy keeps the existing full-universe, 64-slot mutation kernel, temperature
and restart schedule, and global five-heavy profile behavior. It adds three
hard core-at-most-55 checks from independently proved and transported cuts.
A proposed move computes the exact change in all three overlaps before any
state mutation. A cap violation rejects the proposal immediately. Counts are
committed only when the existing energy rule accepts a move; energy rollback
leaves the old counts intact.

The initial state, every restart and every best/improvement record must pass
all three core bounds and the global profile predicate. Periodic audits recount
the complete state. Accepted traversal states may still violate the global
profile predicate because the original profile penalty is soft. Final-current
snapshots retain such states as explicitly identified diagnostics; final-best
and improvement records must be eligible. A shared snapshot helper is called
on both zero-hole return paths and ordinary/interrupted termination.

# Frozen build and inputs

- Native source SHA256: `a258152abc38bc60869516cec5e6e5dba6fd6027ef964bbe1e7dfaee2c8f48cd`.
- Native binary SHA256: `ad9381fd30775b5552190e876fa0183f90c578b245fd17cbf61f6cfc6863c446`.
- Preparation manifest SHA256: `2a643e5c2385ced79cf0c42789161c710bd1bb18aa44fa66fa28af5df33a4c88`.
- Main controls SHA256: `d4916d1d13e9adc6c09f2ccbf31cafd778a82b19dc65eaeab8812ae45be1e2cf`.
- Supplemental rejection controls SHA256: `1b3d26dd604007eb168d1566500c61bc2d78be1d33686cd6a8c83814e5c2225e`.

The compiler is Apple clang 21.0.0 (clang-2100.3.27.1). The manifest binds its
resolved path, binary hash, complete version, flags and commands, together with
the native binary, dependency snapshot, generated membership header, recorder,
source revision, proof audits, hint and all primary raw control artifacts.
The shared `heuristic_search.cpp` dependency is byte-identical to the audited
baseline. Raw files and binaries remain under
`experiments/scratch/native-core-cap-escape-20261004/` outside Git.

The three membership tables have 60 distinct blocks each. Core intersections
are `[[60,0,1],[0,60,8],[1,8,60]]`. Table entries are zero-based lexicographic
block-variable IDs; output point labels remain 1-based. The native dump matches
all 4,368 independently generated block masks, 560 triple masks and 13,104 core
membership bits.

# Completed preparation controls

The controls execute predicates and fixed transitions; they do not enter the
native optimization loop.

| Control | Result |
| --- | --- |
| Overlap 54, 55 and 56 for each core | 9 checked; cap boundary correct |
| Four in/out membership transitions at 54 and 55 | 24 checked |
| All available joint membership transitions | 35 checked |
| Independent global-profile oracle | 4,000 profiles; 1,906 positive obstructions |
| Move and full-state recount | 4,934 checked moves |
| Energy rollback and full-state recount | 2,511 checked rollbacks |
| Restart eligibility and recount | 10 checked restarts |
| Invalid record/initialization states | 4 rejection controls |
| Damaged count/state | 2 rejection controls |
| Cap, row, universe-order or membership damage | 8 rejected variants |
| Malformed/duplicate/label/size/cardinality input | 7 rejected witnesses |
| Process watchdog | ordinary exit, graceful termination and forced kill checked |

The original random transition walk happened to encounter zero core-rejected
proposals. That does not cover the rejection branch. The supplemental control
therefore constructs one explicit 55-to-56 crossing for each core, using the
frozen source. All three reject before mutation and preserve IDs, triple counts,
weights, selected flags, deficit, core counts and the exact heavy-index vector.
Its result is separately hash-bound to the unchanged primary manifest/source.

Both native control programs ran under address and undefined-behavior sanitizers
with no diagnostics. Rollback recounts compare sorted heavy IDs because a legal
rollback can change vector order; pre-mutation core rejection compares the exact
vector. The explicit regression with four sevenfold and one sixfold disjoint
triple still triggers the global profile predicate. A core-valid but
profile-forbidden eight-hole state tests record rejection and preservation of a
final diagnostic snapshot; the known third-core-60 state tests the core guard.

The same frozen ten-hole hint passed the package verifier and standalone
`scripts/check_cover.py` recounts, all three core bounds and the global profile
scan. These verifiers identify it as a partial cover, not a complete cover.
Its SHA256 is `011fcce3b4568a211a357c2e0a608a8f5f5b8cb801ace1c324024fc35a670adc`
and its three overlaps are `1,8,55`.

`uv sync --frozen` and `uv run ruff check .` passed. The full package test run is
tracked separately while the independent native gate is prepared.

# Frozen proposed calls

After a passed independent gate, the recorder permits exactly two sequential
60-second native calls, seeds 2026104201 and 2026104202, from the same ten-hole
hint. It permits one native process at a time. A 75-second process watchdog sends
termination, waits at most five more seconds, then kills a nonresponsive process.
It never relaunches a failed call. A start marker prevents repeating the bundle.
A verified cover, validation failure or watchdog event stops further calls.

Every saved improvement and final snapshot is preserved and checked by both
covering verifiers, exact core recounts and the full global five-heavy scan.
Profile-forbidden final-current snapshots remain diagnostics. Compiler artifacts,
stdout/stderr, clocks, seeds, budgets, exit status, counters and watchdog receipts
are retained. The independent gate and run manifest must match exactly.

The three core inequalities are necessary conditions for a full 64-block cover.
They do not establish connectivity of the remaining mutation graph. Bounded
failure, a plateau, or a timeout cannot prove that no cover exists. Passing the
three named core bounds does not certify every point relabeling.
