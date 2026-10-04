```text
Document:    Native Three-Core-Cap Escape Pilot Plan
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      5efe3e0f277bbc279f8152a30a4182c7203f303b543b19b9720f2c1f7213853d
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Recommendation

The existing general native heavy-profile search is a direct starting point for
a small core-cap escape experiment. Create a fresh experimental copy, add the
three independently checked core-at-most-55 predicates, and keep the existing
full-universe mutation and global five-heavy behavior. This plan makes no source
change, builds no binary and launches no optimizer. SSMCC remains documented and
unrun.

# Audited baseline

`scripts/heavy_profile_heuristic.cpp` wraps the general `heuristic_search.cpp`
state, parser, universe and swap implementation. The completed
`heavy-profile-search/pilot-2026102402` run used seed 2026102402 for 600 seconds,
made 2,500,339,392 proposals and retained a six-hole state. All three recorded
improvements were checked by both covering verifiers and the independent profile
recount. This was a construction run, not a nonexistence result.

The independent predicate audit checked 4,000 synthetic profiles, including
1,924 positive obstructions, and independently recounted 4,930 state moves and
2,481 rollbacks with clean address/undefined-behavior sanitizer output. Its
result hash is recorded in `plan.json`. The exact historical source archive
still exists in ignored scratch and both archived source hashes match the run
metadata. Current wrapper source differs from that archive only by its filled
SHA header and a strict 64-block check in `--profile` mode. The search kernel is
unchanged; the shared `heuristic_search.cpp` hash is identical. A modified copy
still needs a fresh audit.

The search chooses any of the 64 block slots. One eighth of proposals target a
missing triple using any of its carriers; the other proposals exchange one
point in the selected block. All 4,368 blocks exist in the universe, duplicate
selected blocks are rejected, and no degrees, incidence pattern, core blocks,
or heavy families are fixed. It restarts after up to 1,500,000 proposals, using
the original hint every third restart and otherwise the best recorded state.

The global five-heavy test is a record eligibility filter and an energy penalty
of eight. The search may traverse profile-forbidden states, but only saves a
state that passes the predicate. The plan preserves this exact behavior; it does
not turn the existing profile penalty into a hard global rejection.

# Minimal experimental change

Create a new `search.cpp`, frozen dependency snapshot, generated core table and
recorder under a new experiment/scratch pair. Do not edit either historical
source or earlier run folders. Generate the table from the three exact core rows
in the independently gated three-core manifest. Each row must contain 60 unique
lexicographic block IDs and match the original/transport audits. Point labels in
witnesses remain 1-based; table entries are zero-based variable IDs.

Maintain three overlap counts and a membership lookup for each of the 4,368
blocks. At initialization and every restart, reconstruct counts directly from
the 64 selected blocks and require all three to be at most 55. Require the
initial and restart state to pass the global profile predicate too; the chosen
hint and every recorded best state already do.

For a proposed distinct replacement, compute all three proposed counts as
`count - membership[old] + membership[next]` before calling `State::move`.
Reject the proposal immediately if any exceeds 55. Otherwise execute the
existing move, heavy-index update, profile test, temperature schedule and
accept/reject rule. Commit the new core counts only on acceptance. An energy
rejection follows the old rollback path while leaving core counts unchanged.
No extra core penalty, objective term, fixed block or radius is added.

At the existing periodic audits and before either recording path, independently
recount all three overlaps from the complete selected block list. Save a state
only if cardinality, distinctness, all three caps and global profile eligibility
pass. Extend status metadata with current/best overlaps and rejected-core-move
counts. Preserve the original checks of triple counts, deficit, selected flags
and heavy-index contents. This adds constant-size work per proposal.

# Required controls before a gate

1. Reconstruct all 4,368 lexicographic blocks independently. Compare every bit of
   all three membership tables with the two established transports and the new
   exact third-core transport. Check that every core has exactly 60 blocks.
2. Test overlap boundaries 54, 55 and 56 for each core; reject a declared cap 54,
   wrong core ID, duplicate/missing row entry and a wrong relabeling. Use the
   known three-hole state with third-core overlap 60 as a positive rejection
   control. Controls at the predicate level need not be covers.
3. For each core exercise swaps with membership transitions `0->0`, `0->1`,
   `1->0` and `1->1`, including overlap 55 to 56, and compare proposed counts
   with an independent full recount. Jointly exercise overlapping core images.
4. Check that core rejection leaves every state field unchanged. Check accepted
   moves, energy rejection/rollback, restarts and both recording paths against
   fresh independent counts and membership. Use deterministic direct transition
   controls, not a hidden search run.
5. Preserve the existing independent global five-heavy oracle tests, including
   a sixfold triple together with four sevenfold triples. Retain malformed,
   duplicate, wrong-label, wrong-size and wrong-cardinality witness controls.
6. Run the predicate/transition harness under address and undefined-behavior
   sanitizers. Record compiler version, exact commands and binary/source hashes.
   Run the package tests and Ruff for new Python helpers. These checks are not
   optimizer calls. Require a separate exact gate before a bounded search.

# Proposed bounded pilot

Run the fresh native binary twice, sequentially, for 60 seconds each, with seeds
2026104201 and 2026104202. Use the same checked ten-hole hint for both:
`../six-hole-strong-core-release/full-4368/best-03-h10-c1.txt`, SHA256
`011fcce3b4568a211a357c2e0a608a8f5f5b8cb801ace1c324024fc35a670adc`.
Its three overlaps are `1,8,55`; its independent global five-heavy scan is clear.
This is also the full-universe/global-DP preparation hint, so it is already
covered by the exact gate and both verifiers.

Keep all 64 slots free and preserve the existing native proposal distribution,
temperature, restart schedule and profile penalty. There is one native process
at a time and no automatic budget extension or repeat. This differs materially
from the old 600-second run because every accepted state now obeys all three
proved core bounds.

Freeze the fresh source/dependency/table/recorder hashes, source revision,
compiler and flags, binary hash, seeds, budgets, gate and hint before either
call. Preserve stdout/stderr, proposal and rejection counters, every strict
improvement, final current state and best state. Independently recount all saved
and final states with both covering verifiers, all three core overlaps and the
complete global profile scan. Use a process watchdog and record any interrupted
or abnormal exit without silently relaunching it. Keep large binaries and raw
logs in ignored scratch.

These core inequalities are valid necessary conditions for a full 64-block
cover. They do not prove that the restricted mutation graph is connected.
Failure to improve in either short run cannot rule out a cover. Any new low-hole
state still needs an explicit relabeled-core screen; named cuts do not represent
all point relabelings.
