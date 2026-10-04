```text
Document:    Five Core Record Only Partial Start Pilot
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3bbe94ac5916a50199d1003e9f24fda8c366de3b78b1bbcb17e2e81dc70b2649
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Bounded pilot

Start seed 2026105601 from the checked f621 H11/D25 partial, and seed 2026105602
from the historical 439d5153 H11/D27 partial. Each call lasts at most 300 seconds.
Use one process at a time, a 315-second watchdog,
and five-second termination grace. Root alone launches after independent review.
Stop after any verified complete family of at most 64 blocks. Preparation builds
the driver and runs only bounded zero/eight-step controls and record fixtures.

This changes which records are saved. It does not force the live walk to obey
any core, weak-profile, or hole-count condition. The variable-cardinality kernel,
old four-core header, and weak-profile evaluator are reused byte for byte.
Weights, tie ordering, randomness, tabu behavior, and add/drop choices are
unchanged. Computing an extra record profile consumes time but no random draws.

The old four named 60-block cores retain thresholds 55. The separately audited
named 62-block common core has threshold 56. Its 15 holes are linear triples;
every five-block contains at most two. Any 64-block cover therefore needs at
least eight blocks outside this core and can retain at most 56. The exact core
witness and certificate are pinned. This is one named image; passing the cap
does not establish escape from all relabelings or nonisomorphism.

The first starting family retains all 62 common blocks, so it fails the new cap.
It is explicitly an ineligible hint and initializes only the raw partial bucket.
The second start has zero overlap with the new core and passes the weak and
five-cap conditions, so it initializes all three partial record buckets.
No cap is applied to other live cardinalities.

Four independent record buckets retain the best complete family, the fewest-hole
raw exact-64 family, the fewest-hole five-cap exact-64 family, and the best
weak-qualified exact-64 family **among candidates with at most 11 holes**.
The last bucket also requires minimum pair count five and D3=D4=0. This explicit
11-hole recording threshold bounds observer work. It is not a claim that no
weak-qualified families with more holes exist. A low-hole family that fails the
weak conditions cannot suppress a later useful weak-qualified record. Weak
records rank by (holes, D2max); D2sum is reported without breaking ties. Raw and
five-cap records remain hole-only. The final
live family and its direct profile are always saved as well.

The old H9 and H10 partials already pass all five named core caps but fail weak
conditions. They are not new successes of this pilot. The independent saved-file
inventory also recovered an existing H11/D27 family, hash 439d5153, that passes
the weak conditions and all five caps. Merely reaching those thresholds is not
a new result. This pilot tests diversification from two historical starts.
The inventory is bound in the manifest. New saved hashes, holes, D2max, and D2sum
are compared with that finite bank, including its qualified baseline (11,27).
An unseen hash is not an isomorphism claim. Every saved family is checked with the
package verifier, the standalone checker, and direct overlap and weak metrics.
Raw, complete, and five-cap records remain useful diagnostics even when no
weak-qualified record is found. Only a verified complete cover settles existence.

Controls check overlap 55, 56, and 57 against the new threshold; each old cap
still rejects 56; partial cardinalities 63 and 65 are never exact-64 qualified;
the real H11 hint remains unqualified; and low-hole weak-ineligible metrics
cannot qualify for the separate weak bucket. The unchanged production driver is
also exercised with sanitizer builds limited to zero and eight transitions.
An equal-hole lower-D2 weak record must be retained; equal or worse ranks are
rejected, and fewer holes take priority over D2.

No fixed partial, pair-profile, rotational, or incidence assumption is added to
an unrestricted model. This is a bounded heuristic walk with named-image record
filters, not a global lower-bound or connectivity proof.
