```
Document:    H6 Two Point Star Independent Runtime Audit
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      3efac3b7908a2036b609588d29df53ea5e2925384dab9c8609637ac9d9bb643c
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# H6 two-point star runtime: independent result audit

The audit passed. The single approved call ended UNKNOWN with no callback,
final solution vector, saved family, or cover. The response objective field 6.0
is not a feasible incumbent: UNKNOWN returned an empty solution vector and there
is no witness. This run is inconclusive even within the fixed neighborhood.

The native solver reported 120.01227200000001 seconds; the wrapper elapsed time
was 120.39716295793187 seconds. The child returned zero. No watchdog fired, and
there was no retry or second call. The frozen four-worker seed 2026106001 parameter
file is unchanged, as are all model, gate, source, input, and dependency bindings.

The checker verified the complete raw-file inventory, launch and exclusive child
start records, exact child command, parameter copy, response/outcome agreement,
callback/final-file absence, and result flags. It independently evaluates every
variable domain and active model row for saved vectors; there were zero such
vectors to validate in this run. Saved witnesses, if present, would also undergo
separate package and standalone verification. No candidate-validation claim is
made for nonexistent output.

The starting hint remains complete but infeasible on exactly rows 1164, 1175,
and 1221, corresponding to the three pair counts of four. Relaxing only those
three rows to four accepts that starting vector in a control copy. Seven damaged
vector controls were rejected: boolean, float, out-of-domain value, both wrong
hole-flag directions, and short or long vectors. No model was solved by the audit.

The decision gate remains independently frozen at 7e52c187…. The terminal producer
result is 3add8432…, and this passing runtime receipt is d86f6d09…. Full hashes are
in `postcheck.json` and `files.json`.

Reproduce in a checkout with the current receipt preserved elsewhere:

```sh
uv run python experiments/2026-10-04/h6-two-point-star-repair-runtime-independent/postcheck.py \
  --result-sha256 3add8432ae877dc87f8d24292fbb81df9bf986dd4c0b1184a6410a7c0352a537
```

The checker refuses to overwrite its receipt. Ruff passes. This result makes no
claim about unrestricted existence, other stars, or all-relabel exclusion.
