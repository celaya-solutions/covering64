# Document:    Fresh Readback of Six Protected-Novelty Tests
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      bb867b507075030fde941f49d04c090d1357fd4152dd85e9b04261be0447eec8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check saved families by direct subset containment and reject damaged records."""

import copy
import hashlib
import itertools
import json
import runpy
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def family(path):
    rows = [tuple(map(int, row.split())) for row in Path(path).read_text().splitlines()]
    assert rows == sorted(rows) and len(rows) == len(set(rows))
    assert all(len(row) == 5 and tuple(sorted(set(row))) == row for row in rows)
    assert all(1 <= point <= 16 for row in rows for point in row)
    return rows


def check_record(record, initial, elite):
    path = ROOT / record["path"]
    assert sha(path) == record["sha256"]
    blocks = family(path)
    assert len(blocks) == record["blocks"] == 64
    block_sets = list(map(set, blocks))
    counts = {
        triple: sum(set(triple) <= block for block in block_sets)
        for triple in itertools.combinations(range(1, 17), 3)
    }
    holes = [list(triple) for triple, count in counts.items() if count == 0]
    assert holes == record["uncovered"] and len(holes) == record["holes"]
    assert record["cover"] == (not holes) and record["both_verifiers_agree"]
    assert len(set(blocks) - elite) == record["outside_elite"]
    assert len(set(blocks) - initial) == record["distance_from_initial"]
    heavy = [(triple, count) for triple, count in counts.items() if count >= 6]
    assert [[list(triple), count] for triple, count in heavy] == record["profile"]["heavy_triples"]
    forbidden = any(
        len(set().union(*(set(triple) for triple, _ in group))) == 15
        and sum(count >= 7 for _, count in group) >= 2
        for group in itertools.combinations(heavy, 5)
    )
    assert forbidden == record["profile"]["forbidden_five_heavy_profile"]
    return {
        "sha256": sha(path),
        "point_degree_multiset": sorted(
            sum(p in block for block in block_sets) for p in range(1, 17)
        ),
        "triple_multiplicity_histogram": dict(sorted(Counter(counts.values()).items())),
        "outside_elite": len(set(blocks) - elite),
        "forbidden_five_heavy_profile": forbidden,
    }


def main():
    metadata = json.loads((HERE / "metadata.json").read_text())
    summary = json.loads((HERE / "summary.json").read_text())
    assert summary["metadata_sha256"] == sha(HERE / "metadata.json")
    for collection in (metadata["sources"], metadata["artifacts"]):
        for relative, expected in collection.items():
            assert sha(ROOT / relative) == expected
    raw = ROOT / "experiments/scratch/forced-novelty-20261004"
    elite = set(family(raw / "inputs/elite66.txt"))
    starts = {label: set(family(raw / f"inputs/{label}.txt")) for label in ("A", "B")}
    core_path = ROOT / "experiments/2026-10-03/partial-core-holes/core.txt"
    screen_path = ROOT / "experiments/2026-10-03/partial-core-holes/screen_structure.py"
    core = set(family(core_path))
    assert len(core) == 60 and core <= starts["A"] and core <= starts["B"]
    screen = runpy.run_path(str(screen_path))["screen"]
    reports, controls = [], []
    all_low = {}
    for result in summary["cases"]:
        name = f"{result['label']}-f{result['forced']}-s{result['seed']}"
        assert json.loads((HERE / f"{name}.json").read_text()) == result
        for relative, expected in result["artifact_sha256"].items():
            assert sha(raw / name / relative) == expected
        initial = set(family(raw / f"inputs/{result['label']}.txt"))
        low = []
        for record in result["saved"]:
            checked = check_record(record, initial, elite)
            if record["holes"] == 3:
                if checked["sha256"] not in all_low:
                    candidate = set(family(ROOT / record["path"]))
                    structure = screen(candidate, core, seconds=2)
                    mapping = structure["mapping_images_of_1_to_16"]
                    if mapping is not None:
                        assert sorted(mapping) == list(range(1, 17))
                        assert {
                            tuple(sorted(mapping[p - 1] for p in block)) for block in core
                        } <= candidate
                    checked["structure"] = structure
                    checked["original_core_overlap"] = len(candidate & core)
                    checked["differences_from_starts"] = {
                        label: {
                            "removed": sorted(start - candidate),
                            "added": sorted(candidate - start),
                        }
                        for label, start in starts.items()
                    }
                    all_low[checked["sha256"]] = checked
                low.append({"label": record["label"], **checked})
        final = next(r for r in result["saved"] if r["label"] == "final")
        assert final["holes"] == result["native"]["final_holes"]
        assert min(r["holes"] for r in result["saved"]) == result["native"]["overall_best"]
        repair = [r for r in result["saved"] if r["label"].startswith("repair-")]
        assert min(r["holes"] for r in repair) == result["native"]["repair_best"]
        reports.append(
            {"case": name, "checked_states": len(result["saved"]), "three_hole_states": low}
        )
        for field, replacement in (("holes", -1), ("sha256", "0" * 64), ("outside_elite", -1)):
            damaged = copy.deepcopy(result["saved"][0])
            damaged[field] = replacement
            try:
                check_record(damaged, initial, elite)
            except AssertionError:
                controls.append({"case": name, "damaged_field": field, "rejected": True})
            else:
                raise AssertionError("damaged result was accepted")
    output = {
        "source_sha256": sha(__file__),
        "metadata_sha256": sha(HERE / "metadata.json"),
        "summary_sha256": sha(HERE / "summary.json"),
        "checked_states": sum(r["checked_states"] for r in reports),
        "distinct_three_hole_families": len(all_low),
        "all_three_hole_families_have_forbidden_five_heavy_profile": all(
            r["forbidden_five_heavy_profile"] for r in all_low.values()
        ),
        "core_sha256": sha(core_path),
        "structure_screen_sha256": sha(screen_path),
        "three_hole_families": list(all_low.values()),
        "cases": reports,
        "rejected_damaged_records": controls,
        "global_lower_bound_claim": False,
    }
    (HERE / "readback.json").write_text(json.dumps(output, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in output.items()
                if k not in ("cases", "rejected_damaged_records", "three_hole_families")
            }
        )
    )
    print(json.dumps({"damaged_records_rejected": len(controls)}))


if __name__ == "__main__":
    main()
