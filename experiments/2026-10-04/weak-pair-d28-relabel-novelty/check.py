# Document:    D28 Two-Swap Tie Relabel and Novelty Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      cf66796553c6888a78922be54e31a426026586c1c1930786aae3da148cef074a
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Reconstruct, preserve, recount and screen saved ties; no search or solver."""

import hashlib
import importlib.util
import itertools
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
DAY = HERE.parent
ROOT = HERE.parents[2]
PRODUCER = DAY / "weak-pair-two-swap-scan-v2"
BINDINGS = {
    "weak-pair-two-swap-scan-v2/manifest.json": (
        "0f006df5844a67bf5595378e8dc156890a117ecab613b5e2ead9f74b463d9287"
    ),
    "weak-pair-two-swap-scan-v2/result.json": (
        "d766613497903306106f45807b8ec7ccd8ead762f49f976acc17c0035f1a640e"
    ),
    "weak-pair-d29-relabel-screen/manifest.json": (
        "8de73d082aae946e5bc4c4c2a609de6a46f8ebe8916cd0b3f7780f2ad86aab00"
    ),
    "soft-pair-hole-priority-relabel-novelty/manifest.json": (
        "882e2eff54d1e1a62df3056466e1e1504bf88ef409289bb1824438f626660b07"
    ),
    "soft-pair-h12-relabel-novelty/manifest.json": (
        "bf4ecc8092a39c50fcb4d6918352cf0aa0c9d0d705ed70f17cc3e8746566e9f8"
    ),
    "weak-pair-d29-relabel-screen/check.py": (
        "fa9301f7ad252f64a70657d6e443815b5e6b13c5e5e7297691687cb2cd0942a4"
    ),
    "six-hole-strong-core-release-independent/relabels.py": (
        "9cdcd511eb94954bb45c1cf209c5d51517b46c11e46b44a22ce7221d9309f74a"
    ),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def metrics(profile):
    return {
        "cardinality": profile["cardinality"],
        "holes": profile["holes"],
        "D2max": profile["deficits"]["two_triple"]["sum_of_per_pair_maxima"],
        "D2sum": profile["deficits"]["two_triple"]["full_row_sum"],
        "D3": profile["deficits"]["single"]["full_row_sum"],
        "D4": profile["deficits"]["quad"]["full_row_sum"],
        "minimum_pair_count": profile["minimum_pair_count"],
        "core_overlaps": profile["four_named_core_overlaps"],
    }


def compare(before, after, blocks):
    old, new = set(before["ids"]), set(after["ids"])
    old_holes = set(map(tuple, before["uncovered_triples"]))
    new_holes = set(map(tuple, after["uncovered_triples"]))
    changes = []
    for left, right in zip(before["pair_details"], after["pair_details"], strict=True):
        assert left["pair"] == right["pair"]
        a, b = left["two_triple"]["maximum"], right["two_triple"]["maximum"]
        if a != b:
            changes.append({"pair": left["pair"], "before": a, "after": b, "change": b - a})
    return {
        "replacement_distance": 64 - len(old & new),
        "shared_blocks": len(old & new),
        "removed_ids": sorted(old - new),
        "added_ids": sorted(new - old),
        "removed_blocks": [blocks[i] for i in sorted(old - new)],
        "added_blocks": [blocks[i] for i in sorted(new - old)],
        "filled_holes": sorted(old_holes - new_holes),
        "new_holes": sorted(new_holes - old_holes),
        "unchanged_hole_set": old_holes == new_holes,
        "changed_pair_deficits": changes,
        "D2max_change": metrics(after)["D2max"] - metrics(before)["D2max"],
        "point_histogram_changed": before["point_histogram"] != after["point_histogram"],
        "pair_histogram_changed": before["pair_histogram"] != after["pair_histogram"],
    }


def main():
    assert not (HERE / "audit.json").exists(), "preserve completed audit"
    inputs = {str((DAY / path).relative_to(ROOT)): digest for path, digest in BINDINGS.items()}
    for relative, digest in inputs.items():
        assert sha(ROOT / relative) == digest, relative
    manifest = json.loads((PRODUCER / "manifest.json").read_text())
    result = json.loads((PRODUCER / "result.json").read_text())
    assert result["manifest_sha256"] == sha(PRODUCER / "manifest.json")
    assert result["returncode"] == 0 and result["validation_passed"]
    assert result["final"]["complete"] and result["final"]["best_rank"] == [12, 28]
    assert result["final"]["best_ties"] == 6 and not result["cover_found"]
    assert not any(result["watchdog"].values())
    inputs.update(manifest["source_files"] | manifest["input_files"] | result["raw_files"])
    inputs[result["best_representative_path"]] = result["best_representative_sha256"]
    for folder in (
        "weak-pair-d29-relabel-screen",
        "soft-pair-hole-priority-relabel-novelty",
        "soft-pair-h12-relabel-novelty",
    ):
        old = json.loads((DAY / folder / "manifest.json").read_text())
        assert old["passed"]
        inputs.update(old["files"])
    for relative, digest in inputs.items():
        assert sha(ROOT / relative) == digest, relative
    candidate_audit = json.loads((ROOT / result["candidate_audit_path"]).read_text())
    assert candidate_audit["passed"]
    ties = candidate_audit["best_ties"]
    assert len(ties) == 6
    assert [row["sha256"] for row in ties] == result["complete_best_tie_hashes"]
    profiler = load("frozen_d29_profiler", DAY / "weak-pair-d29-relabel-screen/check.py")
    profiler.HERE = HERE
    relabel = load("frozen_relabels", DAY / "six-hole-strong-core-release-independent/relabels.py")
    controls = relabel.selfcheck()
    assert controls["passed"]
    base_ids = set(manifest["initial"]["ids"])
    assert len(base_ids) == 64
    profiles, screens = {}, {}

    def check_one(name, path, digest, holes):
        blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
        assert blocks == sorted(blocks) and len(set(blocks)) == len(blocks) == 64
        assert all(block in profiler.RANK for block in blocks)
        screen = relabel.check([profiler.RANK[block] for block in blocks])
        screen_path = HERE / f"{name}-relabel.json"
        dump(
            screen_path,
            {
                "candidate_sha256": digest,
                "helper_sha256": BINDINGS["six-hole-strong-core-release-independent/relabels.py"],
                "screen": screen,
            },
        )
        source = {
            "path": str(path.relative_to(DAY)),
            "sha256": digest,
            "holes": holes,
            "screen": str(screen_path.relative_to(DAY)),
            "screen_sha256": sha(screen_path),
        }
        profiles[name] = profiler.profile(name, source, manifest["core_rows"])
        screens[name] = screen
        return profiles[name]

    base_path = ROOT / manifest["initial"]["path"]
    d29 = check_one("d29", base_path, manifest["initial"]["sha256"], 12)
    assert set(d29["ids"]) == base_ids
    prior_sources = {
        "d31": (
            DAY / "soft-pair-hole-priority-relabel-novelty/final-family.txt",
            "a00c567a97a00429063ec599728e8b16fe3ed2c230c9eaffdf99939d7632563c",
        ),
        "d32": (
            DAY / "soft-pair-h12-relabel-novelty/final-family.txt",
            "cadb86e4f2243eada269dc314bca0bc5c238f5b0ca2bd9525dd0b67aad24c970",
        ),
    }
    for name, (path, digest) in prior_sources.items():
        check_one(name, path, digest, 12)
    saved = []
    for number, row in enumerate(ties, 1):
        outgoing, incoming = set(row["outgoing"]), set(row["incoming"])
        assert len(outgoing) == len(incoming) == 2 and outgoing <= base_ids
        assert not incoming & base_ids
        ids = (base_ids - outgoing) | incoming
        text = "".join(" ".join(map(str, profiler.SETS[5][i])) + "\n" for i in sorted(ids))
        path = HERE / f"tie-{number}.txt"
        with path.open("x") as handle:
            handle.write(text)
        assert sha(path) == row["sha256"] == row["canonical_sha256"]
        name = f"tie-{number}"
        profile = check_one(name, path, row["sha256"], 12)
        assert metrics(profile) == row["metrics"]
        assert metrics(profile)["D2max"] == metrics(profile)["D2sum"] == 28
        assert metrics(profile)["D3"] == metrics(profile)["D4"] == 0
        saved.append(
            {
                "name": name,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "recorded_swap": row,
                "preservation": "Canonical reconstruction from pinned D29 and recorded swap; "
                "byte hash matches producer's saved tie hash.",
            }
        )
    representative = HERE / "representative.txt"
    shutil.copyfile(ROOT / result["best_representative_path"], representative)
    assert sha(representative) == saved[0]["sha256"]
    comparisons = {
        row["name"]: {
            old: compare(profiles[old], profiles[row["name"]], profiler.SETS[5])
            for old in ("d29", "d31", "d32")
        }
        for row in saved
    }
    distances = [
        {
            "left": a["name"],
            "right": b["name"],
            "replacement_distance": 64
            - len(set(profiles[a["name"]]["ids"]) & set(profiles[b["name"]]["ids"])),
        }
        for a, b in itertools.combinations(saved, 2)
    ]
    old_d29 = json.loads((DAY / "weak-pair-d29-relabel-screen/screen.json").read_text())
    d29_tie_distances = {
        row["name"]: [
            {
                "incoming": old["incoming"],
                "replacement_distance": 64
                - len(set(profiles[row["name"]]["ids"]) & set(old["profile"]["ids"])),
            }
            for old in old_d29["families"]
        ]
        for row in saved
    }
    report = {
        "passed": True,
        "optimizer_calls": 0,
        "enumeration_calls": 0,
        "checker_sha256": sha(Path(__file__)),
        "input_files": inputs,
        "producer_result_sha256": sha(PRODUCER / "result.json"),
        "producer_final": result["final"],
        "helper_controls": controls,
        "saved_ties": saved,
        "representative_path": str(representative.relative_to(ROOT)),
        "representative_sha256": sha(representative),
        "profiles": profiles,
        "relabel_screens": screens,
        "comparisons": comparisons,
        "pairwise_replacement_distances": distances,
        "distances_to_all_d29_ties": d29_tie_distances,
        "scope": "Six saved D28/H12 two-swap ties and three prior families, each still a noncover. "
        "No optimizer or neighborhood enumeration is replayed. All-relabel certificates "
        "apply only to each exact 64-block family. No hard-zero qualification, center "
        "change for the frozen radius-four run, or global lower-bound claim.",
    }
    dump(HERE / "audit.json", report)
    print(
        json.dumps(
            {
                "passed": True,
                "optimizer_calls": 0,
                "saved_ties": 6,
                "audit_sha256": sha(HERE / "audit.json"),
                "screens": {name: screens[name]["necessary_partition_count"] for name in profiles},
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
