```
Document:    Independent Audit of Fixed Heavy-Link LP Screens
Version:     v1.1.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      044a21d9758ab2bf1b05a97f1e37500a540f78cbfa099e7628284fde85bd7bb5
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Scope

This audit concerns LP relaxations of individual fixed first-heavy-link representatives inside the normalized regular four-sevenfold branch. It does not establish an unrestricted bound for C(16,5,3), certify a covering, or establish completeness of the representative list. Those require their separate mathematical and encoding audits. Numerical LP feasibility is not an exact witness, and numerical infeasibility alone is inconclusive.

# Exact certificate argument

Each row has integer coefficients and a finite or infinite interval `l_i <= a_i*x <= u_i`; every variable is in `[0,1]`. Choose any integer row weights `w_i`. For a positive weight, use the lower row bound. For a negative weight, use the upper row bound. Every feasible point satisfies

`R = sum(w_i*l_i for w_i>0) + sum(w_i*u_i for w_i<0) <= c*x`,

where `c_j = sum_i w_i*a_ij`. The unit box gives `c*x <= sum_j max(0,c_j)`. Therefore a strictly positive integer gap `R - sum_j max(0,c_j)` is a contradiction. A positive scaling denominator only changes the displayed gap, not the contradiction. Infinite row bounds cannot be selected by nonzero weights.

The weights need not be optimal dual solutions, or even dual-feasible numerical vectors. Any finite vector that is rounded to integers and then passes this exact arithmetic check is sufficient. Rounding can destroy a useful positive gap but cannot create a false exclusion when the rows, bounds, unit box, and exact arithmetic are correct.

# Phase-I variants

Softening all finite row bounds with nonnegative slacks gives a feasible auxiliary LP over the unit box; minimizing total slack supplies candidate signed row weights. The initial pilot did not complete its phase-I optimizations within ten seconds, so it produced no exact exclusions.

An alternative keeps the independently audited base rows hard and softens only the seven appended `x=1` selections. The base has a separately checked fractional feasible point, so this auxiliary problem is feasible. Because each selected variable already lies in `[0,1]`, its minimum slack cost is `1-x`; the objective is `7-sum(selected x)`. This is a valid faster source of candidate row weights. Weights returned before solver optimality may also be checked, but a numerical status or objective value alone is never an exclusion certificate.

# Implementation controls

The initial implementation accepted a negative certificate denominator. On the feasible row `0 <= x <= 1`, weight one and denominator minus one reversed the displayed gap and falsely returned an exclusion. The owner corrected the implementation to require a positive integer denominator and to validate row shapes, integer coefficients, bounds, distinct indices, and index ranges. Boolean or fractional denominators are rejected.

The standalone `controls.py` tested the corrected v1.0.1 source, SHA256 `1727af53a4106373c492ad3d1eddbac921565dd154101c28c0a3487cd539faec`. Five exact toy cases cover a feasible box, fractional feasibility with integer impossibility, contradictory rows, and violations of both unit-box sides. Twenty-six damaged input/certificate controls were rejected. One hundred deterministic models containing known rational feasible points never yielded a false exact exclusion. These are algebraic test fixtures, not covering candidates; results and all source hashes are in `controls.json`.

An additional owner/exact-agent review corrected a protobuf guard: the implementation now checks `has_linear()` before accessing a constraint's linear field, rejecting unsupported rows without mutating their proto. The original pilot contains only linear rows, as independently checked from its archived protobufs, so that guard fix does not invalidate the pilot evidence.

# Independent raw-model checker

`check.py` imports neither the model builders nor a solver. It parses the frozen protobuf text with a separate protobuf implementation, rejects conditional or nonlinear constraints and non-Boolean domains, reconstructs every row, and compares the result with the archived raw-row arrays. It independently enumerates all 4,368 lexicographic five-blocks, checks their variable names and fixed IDs against the frozen link representatives, and verifies the hashes of archived sources, representatives, models, and rows. For any certificate, it independently computes all weighted bounds, column sums, box support, and the reduced rational gap; damaged certificates must agree with every recomputed field to pass.

The first pilot's ten records passed this raw-model audit. Four LPs were numerically feasible and six numerically infeasible, but all six phase-I stages exhausted their ten-second budgets without an optimal certificate vector. Every result correctly reports no proved exclusion. See `pilot-v1.0.0-audit.json`; its source was the frozen pre-guard v1.0.0 implementation with SHA256 `6b04f3f66f855c03197b4795d2630d9f484f9f43a0dc779d8baa1286c3cd8e7b`.

# Soft-row pilot and full screen

The v1.1.0 screen, source SHA256 `6767e8e7f626cd013c573b43173b234abd8767f29a8025ce7b9f2174a4d29fd4`, softens only the seven fixed selections and may submit weights from either OPTIMAL or FEASIBLE solver status to exact arithmetic checking. The updated implementation validates distinct soft-row indices and enforces at least one millisecond for a positive time budget. Independent controls confirm the hard-base/soft-selection formulation on a contradictory toy pair of rows. The original five toy cases, 35 damaged input/certificate controls, and 100 known-feasible rational models all passed; see `controls-v1.1.0-final.json`.

The revised ten-representative pilot produced six positive certificates. Every certificate, raw model, raw-row archive, fixed-ID list, and source/representative hash passed the independent audit in `pilot-v1.1.0-audit.json` before the full screen began.

The completed full screen covers all 258 entries selected from the frozen representative file. The independent checker verified complete selected coverage, no duplicates, exact agreement between both base protobufs and their row archives, and all 258 fixed-ID lists. Each branch has 4,768 unit-box variables and 4,277 rows. Exactly 100 records carry independently checked positive certificates: 27 in the cycle case and 73 in the matching case. Their positive gaps range from `1137/1000000` to `93407/62500`. The other 158 LPs were numerically feasible and remain unresolved; no exact covering witness is claimed for them. The authoritative final audit is `full-v1.1.0-final-audit.json`.

The standalone checker additionally rejected nine independent corruptions of a real positive certificate: weighted right side, box support, gap, column count, denominator, missing/opposite/duplicate row weights, and floating-point certificate fields. See `real-certificate-damage-controls.json`. The checker itself requires canonical integer fields and explicitly checks that the result IDs equal every requested representative ID. Earlier checker and control versions are preserved under `experiments/scratch/four-seven-link-lp-independent/`, with file hashes recorded in each result.

These certificates are exact exclusions of their 100 specific branches in the archived normalized regular four-sevenfold model. Completeness of the supplied representative list as a mathematical orbit reduction and correctness of the base four-sevenfold/double-triple encoding remain the subjects of their separate audits. This result does not exclude the remaining 158 entries, other heavy-triple profiles, nonregular covers, or all 64-block covers.
