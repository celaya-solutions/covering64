# Document:    Normalized Heavy Hub Restrictions
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      666deae6bdce1b9315d2159bcc43e5e1a6c67f989b4c57b7097af4155438b1b1
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Full-cover consequences for the regular model with triple123 and hub4.

Preconditions: point degrees20, pair incidences(4,a)=6 for a=1,2,3,
and exact heavy6 flags. These are supplied by the first-family builder and
add_heavy_count_cuts. In partial mode these rows restrict construction states.
"""


def add_normalized_hub_cuts(universe, model, xs):
    variables = {v.name: model.get_int_var_from_proto_index(i)
                 for i, v in enumerate(model.proto.variables)}
    for index, triple in enumerate(universe.triples):
        heavy = variables[f"heavy6_{index}"]
        if 4 in triple:
            # Hub4 already spends three of its five pair-excess units on123.
            # A heavy triple through4 would require at least four more units.
            model.add(heavy == 0)
        elif min(triple) >= 5:
            # Two common blocks through4 force three more excess units at4.
            count = sum(xs[i] for i in universe.containing[index] if 4 in universe.blocks[i])
            model.add(count <= 1).only_enforce_if(heavy)
