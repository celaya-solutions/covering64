```text
Document:    Covering64 Research Workflow
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      94f1978579bf84a6de229886f78c50130d1f01e8d44b98cbc85b3b2095dccb72
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Research workflow

Recovery baseline: commit 582e7ba records the supplied reconstructed package; it
does not recover the lost historical Git history. New searches use an isolated worktree.

Investigate C(16,5,3) with an initial target of 64 distinct blocks.
Run `uv sync --frozen`, `uv run pytest` and `uv run ruff check .`.
Keep labels 1-based and preserve lexicographic block-variable ordering.

Every candidate must pass the package verifier and separate standalone
`scripts/check_cover.py`. Reject malformed, duplicate or damaged controls.
UNKNOWN/timeouts are inconclusive; CP-SAT INFEASIBLE is not an independently
checked theorem. Global lower bounds require audited unrestricted encoding and
a separately checked proof. Neighborhood results apply only to that neighborhood.

Do not impose incumbent incidence or rotational assumptions on the unrestricted
model. Prove completeness for each proposed safe reduction. Save seeds, budgets,
source revisions, solver versions, hashes, logs, witnesses and proof certificates.
Keep large source archives and proof artifacts out of Git.

This package was reconstructed after a workspace reset. Read docs/recovery.md.
Do not invent missing historical artifacts. Do not contact researchers or publish
claimed discoveries without user instruction.

<!-- graft:start -->
## Graft — repo context graph

This repo is indexed in `graft/`: small linked markdown nodes that explain each
system and carry exact file:line spans, kept in sync with the code through git.

For ANY task here — understanding how something works, finding where code lives,
or scoping a change — get context from the graph before grepping or opening
source files. Re-ask freely (it's cheap) and reuse literal identifiers you
already have (symbol, error string, file name) as the query. New to this repo?
Run `graft map` first — a token-budgeted orientation (dir clusters, hubs,
hotspots), no LLM, no key.

- Run `graft ask "<your question>" --source` → ranked nodes with the relevant
  code spans inlined (each hit's ≤8-line crux by default; `--full` for whole
  definitions when the crux isn't enough). Match the tool to the task shape:
  for understanding or editing, the top node IS the answer — cite its
  `covers:` file:line spans and edit straight from `--source`. For
  exhaustive tasks ("every occurrence / every caller of this pattern"), ranked
  results are top-N, not complete — run `graft grep "<literal>"` instead
  (exhaustive over indexed files, grouped by enclosing symbol), falling back
  to raw `grep -rn` only for unindexed files.
- `graft skeleton <file>` → every definition's signature + span, ~10× cheaper
  than reading the file; use it to skim an API surface.
- `graft callers <symbol>` gives precomputed, exact edges — who calls this.
  Add `--direction out` for what it calls, or `--depth N` to walk
  transitively for the full blast radius. For structural questions, skip
  ranking and use this directly.
- Or browse: `graft/INDEX.md` lists every node; follow the links.
- Monorepos and folders of multiple repos rank fairly across sub-projects —
  hits carry `[scope/]` labels naming which one they're from. Narrow with
  `graft ask "<task>" --in <scope>/` once you know where you're working.

If a returned span is truncated ("+N more lines"), open the file at that exact
range before finalizing. Only open source files when a node genuinely lacks a
needed detail, and then at the exact file:line the node points to — never
re-read whole files.

After big code changes, refresh the graph with `graft build` (deterministic,
no API key, $0).
<!-- graft:end -->

## Research checkpoint 2026-10-04

Commit d2bfd84 saves the checked H6 escape, unchanged qualified H9 result, current65 public listing and union bound71.
Qualified best remains H9/D2max19; raw H6 escapes every old-core relabel but fails pair floors. All strict improvements within three replacements of H6 were excluded by a checked coverage-only enumeration. Its three B*-anchored two-swap pair repairs fail D3; the {6,10} star pilot returned UNKNOWN with no candidates.
Next: a stronger exact-four search and a feasible-H9-hint star continuation are being prepared. Preserve frozen sources, ignored proof archives and unrelated `.ignore`, `opencode.json`, and `.playwright-mcp/`. OR-Tools: convert repeated containers to lists before negative reads and check optional-field presence before inspection. Historical transport v1 keeps one E501 exception.

## Independent construction checkpoint 2026-10-03

Saved three new routes, an independently replayed 16-case excess recipe and a checked 67-block minimum for the one-extension-per-line geometry recipe. Four single-worker pilots (420 seconds total) returned UNKNOWN; 267 tests and Ruff pass. See docs/independent-research-2026-10-03.md.
Next bounded test: the remaining 15 recipe profiles; neither the recipe nor these timeouts settle general existence. Use nonnegative indices when mutating OR-Tools repeated fields: a negative-index damage control crashed the native binding, then passed after correction. Raw logs preserve source whitespace and remain unchanged.

Merge checkpoint: both research histories retained; merged-tree validation passed 369 tests and Ruff. See experiments/2026-10-03/main-integration/validation.json.

Commit 0915d64 saves the checked heavy-cut escape and SQS pilots; 369 tests and Ruff passed. Next experiments stay in the research worktree.
