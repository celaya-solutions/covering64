```text
Document:    Independent Native H9 H10 Reuse Pilot Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      02111d99729b55fb54c046241ff0b63118491f0d01e068d50c47bd4834484bdd
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent native H9/H10 reuse pilot gate

**GO for one root-launched campaign** bound to the exact hashes in `gate.json`. No native search or optimizer ran during this focused review. The native kernel, recorder, process control, and dual verifier were reused from the existing gate by frozen hashes, without repeating the kernel audit.

## Exact changes checked

The new wrapper imports the unchanged five-cap base runner `c0052cbf52dc40eb3547d40df7c619e8187698e932541180d7101a3133f03ba3` and reuses binary `079eaf578f1e7b29c4408185e77953b4d337d722e428e12b7c653392e1c2163c`. Its only assignments into the imported base module change `HERE`, `RAW`, and the declared `BUDGET`. It calls the unchanged `base.main` first and then classifies saved results. The five core rows, thresholds `[55,55,55,55,56]`, weak-record eligibility, and `(holes,D2max)` rank match the earlier manifest. D2sum remains diagnostic.

The sixth named core is the exact `f5f24` 64-block starting partial. The manifest binds both its producer certificate and independently replayed radius-four proof. Its exact 64 overlap threshold is 59. The wrapper applies this cap only to saved record/final metadata after the unchanged search and dual validation. It does not add a live filter, change native recording, or claim the best six-cap state seen anywhere in the walk.

Both starts are bound to the independent qualification receipt `5ffc16c887a338c8eff63cf38709257b2d9b785baa404920964e5f1d105f46c0` and freshly parsed for 64 distinct, sorted blocks. Their IDs, hashes, weak metrics, five old named overlaps, and sixth overlap were checked against those receipts and the manifest.

| Seed | Starting partial | Rank | D2sum | Sixth overlap |
| --- | --- | --- | --- | --- |
| 2026105901 | `a0a737c4…` | H9 / D2max 19 | 27 | 59 |
| 2026105902 | `85f6e38a…` | H10 / D2max 22 | 32 | 0 |

The classifier preserves both qualified inputs as explicit initial fallbacks even when the second seed never launches. They are kept separately from native saved references. The best saved result is selected only from distinct saved families, ordered by `(holes,D2max,full IDs)`; an empty eligible saved set may correctly have no best saved result while both input fallbacks remain available.

## Independent controls

The checker rehashed 166 unique source, input, and raw artifact pins. A 72-case synthetic post-validation matrix checks sizes 63/64/65, overlaps 58/59/60, old five-cap success/failure, weak qualification, and complete status. It verifies that the sixth-cap verdict is null for non64 sizes and that complete-at-most 64 classification does not depend on cap eligibility. Both verifier reports must be valid to classify a complete family. The actual known 65-block cover is also checked as a non64 control; it receives no sixth-cap verdict and is not an at-most 64 result. Synthetic complete cases are control metadata, not covering witnesses.

Nine saved-report cases check preservation of both input fallbacks with no native references, duplicate reference counting, best-rank selection, ID tie-breaking independent of D2sum, and rejection of changed saved hashes, changed unlaunched-input hashes, lost fallback eligibility, inconsistent duplicate metrics, and failed native validation. These tests write only disposable JSON reports in ignored scratch storage. They launch no shell search.

The wrapper inherits unconditional complete-bucket dual verification from the byte-identical base runner, before this added classification step. Failure and early-cover stopping behavior remain in that same base runner.

## Bound budget and files

At most two sequential 300-second calls, seeds 2026105901 and 2026105902. Each has a 315-second watchdog and 5-second termination grace. Stop after the first checked complete cover of at most 64 blocks or any existing failure condition. No relaunch, retry, budget transfer, parallel child, or extension is authorized by this gate.

`check.py` reproduces the focused controls. `checks.json` records results and bindings. `gate.json` is the root launch receipt. Ruff passed on the new checker; source and document body hashes are checked separately. This gate makes no existence or nonexistence claim.
