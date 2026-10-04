# Document:    Soft-Score Independent Score Controls
# Version:     v1.1.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      b602dd1796e1ea688d8297c0536b574cca70f1866f9f09db627fb19c8df05c5f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Check known initial scores and reject corrupted score-event records."""

import json
from pathlib import Path

from audit import ROOT, blocks, check_score_event, require, score_components, sha

HERE = Path(__file__).resolve().parent
RAW = ROOT / "experiments/scratch/four-seven-template-native-v1.1.0"


def main():
    cases = json.loads((HERE / "seeds.json").read_text())["cases"]
    expected = {"matching": (21, 30, 4, 155), "cycle": (19, 24, 3, 134)}
    controls = []
    for case in cases:
        name = case["name"]
        seed = blocks(ROOT / case["seed_path"])
        stats = score_components(seed, name)
        actual = tuple(stats[k] for k in ["holes", "pair_target_l1", "nonheavy_excess", "score"])
        require(actual == expected[name], "known seed score mismatch")
        controls.append({"case": name, "control": "known_seed", "actual": actual})
        events = [
            json.loads(line) for line in (RAW / "smokes" / f"{name}.log").read_text().splitlines()
        ]
        for event in events:
            if event.get("event") != "operation":
                continue
            before, after = blocks(Path(event["before"])), blocks(Path(event["after"]))
            delta = check_score_event(event, before, after, name)
            inverse = dict(event)
            for field in ["holes", "score"]:
                inverse[f"{field}_before"] = event[f"{field}_after"]
                inverse[f"{field}_after"] = event[f"{field}_before"]
            reversed_delta = check_score_event(inverse, after, before, name)
            require(all(reversed_delta[k] == -v for k, v in delta.items()), "inverse score delta")
            for field in ["holes_before", "holes_after", "score_before", "score_after"]:
                damaged = dict(event)
                damaged[field] += 1
                try:
                    check_score_event(damaged, before, after, name)
                except ValueError as error:
                    controls.append(
                        {
                            "case": name,
                            "mode": event["mode"],
                            "field": field,
                            "rejected": True,
                            "error": str(error),
                        }
                    )
                else:
                    raise ValueError("corrupted score record accepted")
    result = {
        "checker_sha256": sha(Path(__file__)),
        "controls": controls,
        "damaged_rejected": sum(c.get("rejected", False) for c in controls),
    }
    (HERE / "score-controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"damaged_rejected": result["damaged_rejected"]}))


if __name__ == "__main__":
    main()
