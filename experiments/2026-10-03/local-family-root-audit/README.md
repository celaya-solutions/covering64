```text
Document:    Root Replay of the Local Family Classification
Version:     v1.0.0
Author:      Celaya Solutions
Contact:     hello@celayasolutions.com
Date:        2026-10-03
SHA256:      61447fc11157fd5aefa1c4366fec29e47c1d18151c1a7362429f0a3e356469ee
Chain:       n/a
Tx:          [not anchored]
License:     All Rights Reserved / Celaya Solutions
```

# Root replay of the local-family classification

The root agent compiled and ran the frozen, direct C++ enumerator independently. It completed all26 normalized hole patterns in4,197 nodes and produced88 labelled families. This method does not use the Python enumerator's Gram determinant filter, positive-excess matching enumeration, or graph-library quotient.

A separate NetworkX3.7 incidence-graph check found explicit point bijections from every family to one of the three representatives:72 projective-plane families, eight four-hole families, and eight six-hole families. Each stored point map was then checked directly against every block. Different hole counts distinguish the three classes without a graph-isomorphism assumption. Duplicate-block, invalid-label and nonbijective-map controls were rejected.

The completeness review checked the normalization through a hole-free point, all4-vertex degree-at-most3 multigraph patterns, and monotone degree/excess pruning in the direct enumeration. Early return when all required pairs are already covered cannot discard a completion: any additional quadruple would create three excess incidences at each of its four points, while each point's remaining excess allowance is at most one.

This establishes the three local types for13 distinct quadruples on13 points, every point having degree four and missing pairs forming a matching. Applying it to the regular sevenfold-triple branch additionally uses the separately checked two-spoke obstruction. It does not establish a global lower bound or provide a complete64-block cover.

Run from the repository root:

```sh
clang++ -std=c++17 -O3 -Wall -Wextra -Werror experiments/2026-10-03/local-family-classification/replay.cpp -o /tmp/local-family-replay
/tmp/local-family-replay 60 > experiments/2026-10-03/local-family-root-audit/replay.json
uv run --with networkx python experiments/2026-10-03/local-family-root-audit/check.py
```

The output contains all88 explicit mappings and the byte hashes of the enumerator, replay and independent checker. Timing fields can differ between runs.
