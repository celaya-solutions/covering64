```text
Document:    Independent Soft Pair-Two Preparation Gate
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-04
SHA256:      bd39f5c8bd60792f77964c75b37a6de3b2cb6b1dc7beb74726e54d50ff69b73b
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Independent soft pair gate

The gate independently compares the serialized soft model with the previously checked hard pair-two model. It permits changed variable names only; all existing variable domains and other proto fields remain exact. It checks each of 10,920 softened rows, all 120 deficit domains, the fourth independently justified core cap, the objective, frozen proof and source hashes, complete hint, and solver parameters.

The H49 family has actual per-pair deficit sum 74 and objective 41,563. It is feasible for this soft model. It is not a feasible hint for the hard stronger-pair model and is not a covering solution. A decremented required deficit is rejected; an increased deficit is allowed as auxiliary slack. The sole run is limited to 120 seconds, four workers, seed 2026104302. This gate itself calls no optimizer.

The independent runner review is recorded separately in `../soft-pair-two-postcheck/`. Native results and all saved callback/final assignments require that independent postcheck before conclusions are recorded.
