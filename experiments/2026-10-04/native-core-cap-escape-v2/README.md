```text
Document:    Native Three-Core-Cap Escape Pilot Outcome
Version:     v1.2.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      7d5ad498aedf25b801be3d77128e743fcb300c5041d1c67c8d724c4f48838cb4
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Result

The independently gated second revision ran exactly twice, for 60 seconds per
seed. Seed 2026104201 improved the checked starting state from ten holes to nine.
Seed 2026104202 retained ten holes. Neither found a cover. Both native processes
ended normally with return code 1, no watchdog intervention and no recorder
validation error. No further native call was made.

| Seed | Wall seconds | Proposals | Restarts | Core rejections | Best holes | Final current holes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026104201 | 60.00555058394093 | 318,360,448 | 213 | 37 | 9 | 56 |
| 2026104202 | 60.00494216696825 | 297,376,832 | 199 | 36 | 10 | 66 |

The nine-hole record was saved at 33.0214 native seconds and proposal
174,841,873. Its three named core overlaps are `1,0,0`; its canonical SHA256 is
`15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46`.
The second best state is the unchanged ten-hole hint with overlaps `1,8,55`.
The final current states, preserved separately as diagnostics, have overlaps
`1,1,1` and `3,1,1`. Both happen to pass the global profile predicate.

The recorder and independent postcheck checked all seven snapshot records,
representing four distinct families, with both covering verifiers, all three
core bounds and the complete global five-heavy scan. All passed those recounts
as partial covers. The postcheck also verified the final event fields, native
logs, counters, exit/watchdog status and frozen archive/input chain.

The separate exact relabeled-core screen found zero necessary partitions in
the new nine-hole state. By the audited necessary-condition test, that certifies
core overlap at most 55 for every point relabeling of this specific 60-block
core. Its limited explicit-map check also found no violation among 242 images
(maximum observed overlap four). The all-relabel conclusion comes from absence
of a necessary partition, not from the limited explicit-map sample. This does
not establish that the nine-hole state extends to a cover.

Run result SHA256:
`2f26949888d578aff355417ba260e90737fcf7bfb26a7e95073f5fcb24431844`.
Independent gate SHA256:
`8bbe6c45ed2289648f66bbbdcc109d1eabeae4baad0dcba974b4493dc805c458`.

Independent postcheck SHA256:
`ac615583b1091f916e7759038bb8b605209235c16d15149a32aaeb4e69ad1ad3`.
Exact relabeled-core screen SHA256:
`121fe4d0352102def5371509510ffaefec1b15be5efa24af4b1a97a9e12be1a7`.
Both receipts are in `../native-core-cap-escape-independent/`.

# Preparation history

The first frozen preparation is preserved as `../native-core-cap-escape/` and
was never launched: independent review found that its zero-hole exits omitted
final status and counters. This sibling revision corrected that reporting gap.
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
on both zero-hole return paths and ordinary/interrupted termination. A common
finish handler then emits the event, best/current deficits and core overlaps,
profile status, proposal/restart/rejection counters and time. The recorder
checks all these fields for every successful process exit.

# Frozen build and inputs

- Native source SHA256: `d80d069518fcd6774d9396f69200767ab5f9d3660f2893093c2924116c83bab5`.
- Native binary SHA256: `6520d509b7cafa9aab58cf01b38df147c0ff419c8442e6f745e1a3c59724b785`.
- Preparation manifest SHA256: `2e5212440a92ea66cdc819da4300e6b75496ddf7ef3cb412f77c3b27bfca7293`.
- Main controls SHA256: `da3f92b772c79a658255b0ee74d9616426b731be273bd54917b29eaa06265dbe`.
- Supplemental rejection controls SHA256: `96c29ec0dd5ae823c09c64c77d35f6b8aac7f85d53632a2dab24d55134cc08fe`.

The compiler is Apple clang 21.0.0 (clang-2100.3.27.1). The manifest binds its
resolved path, binary hash, complete version, flags and commands, together with
the native binary, dependency snapshot, generated membership header, recorder,
source revision, proof audits, hint and all primary raw control artifacts.
The shared `heuristic_search.cpp` dependency is byte-identical to the audited
baseline. Raw files and binaries remain under
`experiments/scratch/native-core-cap-escape-v2-20261004/` outside Git.

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
| Common finish handler | finished/interrupted dictionaries checked; false-cover/unknown statuses rejected |

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

`uv sync --frozen` and `uv run ruff check .` passed. The full existing package
suite passed 369 tests with three dependency deprecation warnings. The fresh
native experiment is covered by the separate controls above. A positive
zero-hole exit cannot be tested without a real 64-cover; both zero-hole branches
delegate to the common finish handler, and a false cover status is rejected.

# Frozen calls and independent gate

The independent gate passed before both sequential 60-second native calls,
seeds 2026104201 and 2026104202, from the same ten-hole hint. Its fresh audit
reconstructed every membership from the original core and the two point maps;
checked 210 joint boundary cases with 25 rejections before mutation, 92 commits
and 93 rollbacks; checked 216 cap vectors; and rejected seven malformed
witnesses. No optimizer was called by the gate. The recorder permits one native
process at a time. A 75-second process watchdog sends
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
