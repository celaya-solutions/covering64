```
Document:    H9 H10 Reuse Pilot Independent Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      9e6ee2741ee2eaa0d9c6b98f17bd2243aab42a3b97b9241cba118d42951cb787
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# H9/H10 native reuse pilot independent runtime audit

Status: prepared; not yet executed. The parent agent owns production launches.

The checker binds the frozen wrapper, reused five-cap driver, native binary,
manifest, both initial families, independent GO gate, and sixth named-core cap
proof. It independently recounts saved families, checks package and standalone
verifier agreement, replays logged mutations and bucket progression, and checks
commands, timing, source archives, watchdog flags, and sequential run limits.

The native recorder still applies five caps. The sixth cap is classified only
on saved exact-64 families. Non-64 records receive a null sixth-cap verdict.
Both initial eligible fallbacks remain explicit, including the second start if
an early stop leaves it unlaunched. This audit cannot establish the best
six-cap family over unsaved live states. D2sum is metadata, not ranking.

The original five-cap result keeps its historical H11/D2max27 baseline. The
independent runtime receipt additionally distinguishes pre-pilot saved hashes
and improvements over the current starting rank H9/D2max19.

Run only after the parent supplies a producer result hash:

```sh
uv run python experiments/2026-10-04/native-h9-h10-reuse-runtime-independent/postcheck.py \
  --gate experiments/2026-10-04/native-h9-h10-reuse-independent/gate.json \
  --result-sha256 PARENT_REPORTED_SHA256
```

An optional `--partial` audit checks a first-run snapshot. Preserve those result
bytes before the live producer result is replaced. Neither preparation nor the
checker launches an optimizer or native search. A passing audit does not prove
unrestricted infeasibility or all-relabel escape.
