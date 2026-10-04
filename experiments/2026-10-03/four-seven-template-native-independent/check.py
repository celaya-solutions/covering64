# Document:    Independent Complete-Template Native Search Gate
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Independently bind complete catalogs, reconstruct seeds, recount states and replay moves."""

import gzip
import hashlib
import itertools as it
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUT = HERE.parent / "four-seven-template-native"
RAW = ROOT / "experiments/scratch/four-seven-template-native-v1.0.0"
OWN = ROOT / "experiments/scratch/four-seven-template-native-independent"
ENCODING = HERE.parent / "four-seven-template-hull-refresh-108"
SOURCE_SHA = "9a58b77cb44d561728a63e9d7e835866f4a0dbfd6306608ee4f85009e65361a1"
ANCHORS = [frozenset(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
TRIPLES = set(it.combinations(range(1, 17), 3))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ordinary(block):
    return all(len(set(block) & group) <= 1 for group in ANCHORS)


def read(path):
    blocks = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    require(len(blocks) == len(set(blocks)) == 64 and blocks == sorted(blocks), "block inventory")
    require(all(len(b) == 5 and tuple(sorted(set(b))) == b for b in blocks), "malformed block")
    require(all(1 <= p <= 16 for b in blocks for p in b), "point range")
    return blocks


def orbit(block):
    # Explicit products of independently formed point permutations.
    result = set()
    for shift in range(4):
        for phase in range(3):
            mapping = {}
            for g in range(4):
                for a in range(3):
                    mapping[4 * g + a + 1] = 4 * ((g + shift) % 4) + (a + phase) % 3 + 1
                mapping[4 * g + 4] = 4 * ((g + shift) % 4) + 4
            result.add(tuple(sorted(mapping[p] for p in block)))
    return result


def catalogs(case, audited):
    source = ROOT / case["source_catalog_path"]
    pack = ROOT / case["catalog_path"]
    require(
        sha(source) == case["source_catalog_sha256"] == audited["group_catalogs_sha256"],
        "catalog audit chain changed",
    )
    require(sha(pack) == case["catalog_sha256"], "export pack changed")
    data = json.loads(gzip.decompress(source.read_bytes()))
    count = case["templates_per_group"]
    require(count == audited["templates_per_group"], "catalog count differs")
    maps = []
    with pack.open() as stream:
        require(
            stream.readline().split() == ["C64T1", case["name"], *([str(count)] * 4)],
            "pack header differs",
        )
        for group in range(4):
            rows = {}
            for index, edges in enumerate(data[group]["templates"]):
                expected = [group + 1, index + 1, *[p for edge in edges for p in edge]]
                require(list(map(int, stream.readline().split())) == expected, "pack edge differs")
                blocks = tuple(sorted(tuple(sorted(ANCHORS[group] | set(edge))) for edge in edges))
                require(
                    len(blocks) == len(set(blocks)) == 7 and blocks not in rows,
                    "duplicate template",
                )
                require(all(len(b) == 5 for b in blocks), "bad heavy block")
                degree = Counter(p for edge in edges for p in edge)
                require(
                    degree
                    == {
                        p: 2 if p == 4 * group + 4 else 1
                        for p in range(1, 17)
                        if p not in ANCHORS[group]
                    },
                    "wrong outside-link degree",
                )
                rows[blocks] = index + 1
            require(len(rows) == count, "template count differs")
            maps.append(rows)
        require(not stream.read().strip(), "trailing catalog data")
    return maps


def recount(path, maps):
    blocks = read(path)
    degree = Counter(p for b in blocks for p in b)
    require(degree == {p: 20 for p in range(1, 17)}, "point degree changed")
    ids = []
    heavy = set()
    for group in range(4):
        local = tuple(b for b in blocks if ANCHORS[group] <= set(b))
        require(local in maps[group], "heavy blocks not a complete surviving template")
        ids.append(maps[group][local])
        heavy.update(local)
    free = set(blocks) - heavy
    require(len(heavy) == 28 and len(free) == 36 and all(map(ordinary, free)), "ordinary family")
    require(
        Counter(p for b in free for p in b) == {p: 15 if p % 4 == 0 else 10 for p in range(1, 17)},
        "ordinary degree changed",
    )
    counts = Counter(t for b in blocks for t in it.combinations(b, 3))
    missing = TRIPLES - counts.keys()
    require(all(all(len(set(t) & a) < 2 for a in ANCHORS) for t in missing), "anchor-pair hole")
    if "-h" in path.stem and path.stem.rsplit("-h", 1)[1].isdigit():
        require(len(missing) == int(path.stem.rsplit("-h", 1)[1]), "incorrect improvement label")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path),
        "holes": len(missing),
        "template_ids_1based": ids,
    }


def operations(path, maps):
    events = list(map(json.loads, path.read_text().splitlines()))
    records = []
    for e in events:
        if e["event"] != "operation":
            continue
        before, after = set(read(Path(e["before"]))), set(read(Path(e["after"])))
        removed, added = list(map(tuple, e["removed"])), list(map(tuple, e["added"]))
        require(
            len(removed) == len(set(removed)) == len(added) == len(set(added)), "duplicate move"
        )
        require(
            set(removed) <= before and not set(added) & (before - set(removed)), "move collision"
        )
        require(before - set(removed) | set(added) == after and before != after, "move descriptor")
        require(
            Counter(p for b in removed for p in b) == Counter(p for b in added for p in b),
            "degree-unbalanced move",
        )
        if e["mode"] == 3:
            group = e["template_group"] - 1
            require(0 <= group < 4 and len(removed) == 7, "wrong template move size")
            require(
                maps[group].get(tuple(sorted(removed))) == e["template_before"],
                "wrong old template",
            )
            require(
                maps[group].get(tuple(sorted(added))) == e["template_after"], "wrong new template"
            )
        else:
            require(e["mode"] in [0, 1, 2] and 2 <= len(removed) <= 6, "ordinary move mode or size")
            require(all(map(ordinary, removed + added)), "ordinary move changed family")
            require(
                e["template_group"] == e["template_before"] == e["template_after"] == 0,
                "ordinary move claimed a template",
            )
        if e["role"] == "forced_apply":
            rollback = Path(e["before"].replace("-before.txt", "-rollback.txt"))
            if rollback.exists():
                require(set(read(rollback)) == before, "rollback changed blocks")
            else:
                require(
                    events[-1].get("reason") == "control_cover"
                    and recount(Path(e["after"]), maps)["holes"] == 0,
                    "missing rollback",
                )
        records.append({"mode": e["mode"], "role": e["role"]})
    return records


def main():
    OWN.mkdir(exist_ok=True)
    source = ROOT / "scripts/four_seven_template_heuristic.cpp"
    require(sha(source) == SOURCE_SHA, "native source changed")
    encoding = json.loads((ENCODING / "independent-audit.json").read_text())
    require(encoding["passed"] is True and encoding["checked_exclusions"] == 108, "encoding audit")
    require(
        sha(ENCODING / "check_independent.py") == encoding["checker_sha256"]
        and sha(ENCODING / "manifest.json") == encoding["manifest_sha256"],
        "encoding chain",
    )
    family = {b for b in it.combinations(range(1, 17), 5) if ordinary(b)}
    require(len(family) == 1200, "ordinary family size")
    orbits = {tuple(sorted(orbit(b))) for b in family}
    require(len(orbits) == 100 and all(len(o) == 12 for o in orbits), "ordinary orbit partition")
    require({b for o in orbits for b in o} == family, "orbit partition omitted a block")
    cases = json.loads((INPUT / "seeds.json").read_text())["cases"]
    build = [
        "clang++",
        "-std=c++17",
        "-O1",
        "-g",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-fsanitize=address,undefined",
        "-fno-omit-frame-pointer",
        str(source),
        "-o",
        str(OWN / "search-sanitize"),
    ]
    built = subprocess.run(build, capture_output=True, text=True, check=True)
    require(not built.stdout and not built.stderr, "compiler diagnostics")
    reports = []
    for c in cases:
        audit = next(a for a in encoding["cases"] if a["case"] == c["name"])
        maps = catalogs(c, audit)
        seed = ROOT / c["seed_path"]
        require(sha(seed) == c["seed_sha256"], "seed changed")
        state = recount(seed, maps)
        require(
            state["holes"] == c["initial_holes"]
            and state["template_ids_1based"] == c["template_ids_1based"],
            "seed metadata differs",
        )
        free = {b for b in read(seed) if ordinary(b)}
        require(
            free == {b for rep in c["orbit_representatives"] for b in orbit(rep)},
            "seed orbit union",
        )
        snapshots = [recount(p, maps) for p in sorted(RAW.glob(c["name"] + "-smoke-*.txt"))]
        log = RAW / (c["name"] + "-smoke.log")
        saved_moves = operations(log, maps)
        require(not (RAW / (c["name"] + "-smoke.err")).read_bytes(), "saved sanitizer diagnostics")
        prefix = OWN / c["name"]
        argv = [
            str(OWN / "search-sanitize"),
            str(ROOT / c["catalog_path"]),
            str(seed),
            str(c["seed"]),
            "0.1",
            str(prefix),
        ]
        p = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
        require(p.returncode in [0, 1] and not p.stderr, "fresh sanitizer failure")
        own_log = prefix.with_suffix(".log")
        own_log.write_text(p.stdout)
        fresh = [recount(f, maps) for f in sorted(OWN.glob(c["name"] + "-*.txt"))]
        moves = operations(own_log, maps)
        last = json.loads(p.stdout.splitlines()[-1])
        require(last["event"] == "finished", "fresh run incomplete")
        require(
            recount(OWN / (c["name"] + "-best.txt"), maps)["holes"] == last["best_holes"],
            "fresh best claim differs",
        )
        require(
            {e["mode"] for e in moves if e["role"] == "forced_apply"} == {0, 1, 2, 3}
            or last["best_holes"] == 0,
            "move controls incomplete",
        )
        reports.append(
            {
                "case": c["name"],
                "seed": state,
                "catalog_sha256": c["catalog_sha256"],
                "templates_per_group": len(maps[0]),
                "saved_states": snapshots,
                "saved_operations": saved_moves,
                "fresh_command": argv,
                "fresh_exit": p.returncode,
                "fresh_states": fresh,
                "fresh_operations": moves,
                "fresh_final": last,
            }
        )
    result = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "source_sha256": SOURCE_SHA,
        "constructor_sha256": sha(INPUT / "prepare.py"),
        "seeds_sha256": sha(INPUT / "seeds.json"),
        "encoding_audit_sha256": sha(ENCODING / "independent-audit.json"),
        "ordinary_family": 1200,
        "seed_orbits": 100,
        "build_command": build,
        "binary_sha256": sha(OWN / "search-sanitize"),
        "cases": reports,
        "scope": "Independent native construction gate only. No move-connectivity proof, "
        "exact exclusion, unrestricted bound or cover claim.",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": True,
                "saved_states": sum(len(r["saved_states"]) for r in reports),
                "saved_operations": sum(len(r["saved_operations"]) for r in reports),
                "fresh_states": sum(len(r["fresh_states"]) for r in reports),
            }
        )
    )


if __name__ == "__main__":
    main()
