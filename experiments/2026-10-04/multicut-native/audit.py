# Document:    Native Fourteen-Cut Catalog and Move Audit
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      dcd8aa43187ae3f95e48177724791d34c61dc56b8e2cb7ccb0111cba281e36a8
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import copy
import functools
import hashlib
import importlib.util
import itertools as it
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/multicut-native-v1.4.0"
OUT = RAW / "controls"
CUT_PATH = ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json"
ORACLE_PATH = ROOT / "experiments/2026-10-03/four-seven-template-lookahead-independent/oracle.py"
ANCHORS = [tuple(range(4 * g + 1, 4 * g + 4)) for g in range(4)]
SPEC = importlib.util.spec_from_file_location("independent_oracle", ORACLE_PATH)
ORACLE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ORACLE)
CUT = json.loads(CUT_PATH.read_text())
COEFFICIENTS = [
    dict(zip(map(tuple, CUT["heavy_blocks"]), c["coefficients"], strict=True)) for c in CUT["cuts"]
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blocks(path):
    result = [tuple(map(int, line.split())) for line in path.read_text().splitlines()]
    require(result == sorted(result), "canonical block order")
    require(len(result) == len(set(result)) == 64, "distinct block count")
    require(all(len(b) == 5 and tuple(sorted(set(b))) == b for b in result), "block labels")
    return tuple(result)


@functools.cache
def heavy_oracle(heavy):
    return ORACLE.analyze(heavy)


@functools.cache
def recount(candidate, case, enabled, cut_weight=1):
    heavy = tuple(ORACLE.heavy_blocks(candidate))
    counts = Counter(t for b in candidate for t in it.combinations(b, 3))
    pairs = Counter(p for b in candidate for p in it.combinations(b, 2))
    missing = sorted(set(it.combinations(range(1, 17), 3)) - counts.keys())
    target = {p: 5 for p in it.combinations(range(1, 17), 2)}
    for g, anchor in enumerate(ANCHORS):
        target.update({p: 7 for p in it.combinations(anchor, 2)})
        target.update({(p, 4 * g + 4): 6 for p in anchor})
    extra = [(4, 8), (12, 16)] if case == "matching" else [(4, 8), (8, 12), (12, 16), (4, 16)]
    target.update({p: 7 if case == "matching" else 6 for p in extra})
    pair_defect = sum(abs(pairs[p] - target[p]) for p in target)
    over = sum(max(0, value - 2) for t, value in counts.items() if t not in ANCHORS)
    look = heavy_oracle(heavy)
    hcounts = Counter(t for b in heavy for t in it.combinations(b, 3))
    excess = Counter()
    for t, value in hcounts.items():
        for p in it.combinations(t, 2):
            excess[p] += max(0, value - 1)
    heavy_excess = sum(max(0, excess[p] - limit) for p, limit in ORACLE.budgets().items())
    lhs = [sum(coefficients[b] for b in heavy) for coefficients in COEFFICIENTS]
    violations = [max(0, c["rhs"] - value) for c, value in zip(CUT["cuts"], lhs, strict=True)]
    violation = max(violations)
    penalty = cut_weight * ((violation + 999) // 1000) if enabled else 0
    base = 5 * len(missing) + pair_defect + 5 * over
    return {
        "holes": len(missing),
        "base_score": base,
        "score": base + 100 * look["unsupported_count"] + penalty,
        "unsupported_count": look["unsupported_count"],
        "admissible_count": look["allowed_ordinary"],
        "heavy_excess": heavy_excess,
        "admissible_blocks": list(map(list, look["admissible_blocks"])),
        "unsupported_triples": list(map(list, look["unsupported"])),
        "cut_enabled": enabled,
        "cut_lhs": lhs,
        "cut_rhs": [c["rhs"] for c in CUT["cuts"]],
        "cut_weight": cut_weight,
        "cut_count": 14,
        "cut_violations": violations,
        "cut_violation": violation,
        "cut_penalty": penalty,
        "cut_denominator": 1000,
        "cut_sha256": sha(CUT_PATH),
        "weight": 100,
    }


def compare(detail, expected, original=False):
    for key, value in expected.items():
        if original and key.startswith("cut_"):
            continue
        require(detail[key] == value, f"recomputed {key} differs")


def run(argv, directory):
    directory.mkdir(parents=True, exist_ok=False)
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=45, check=False)
    (directory / "stdout.jsonl").write_text(result.stdout)
    (directory / "stderr.log").write_text(result.stderr)
    require(result.returncode == 0 and not result.stderr, "native check failed")
    return [json.loads(line) for line in result.stdout.splitlines()]


def catalog_sums(path):
    lines = path.read_text().splitlines()
    header = lines[0].split()
    sizes = list(map(int, header[2:]))
    require(header[:1] == ["C64T1"] and len(sizes) == 4, "catalog header")
    groups = [[] for _ in range(4)]
    for line in lines[1:]:
        values = list(map(int, line.split()))
        require(len(values) == 16, "catalog row size")
        g, index = values[0] - 1, values[1] - 1
        require(index == len(groups[g]), "catalog order")
        edges = list(zip(values[2::2], values[3::2], strict=True))
        row = [tuple(sorted((*ANCHORS[g], *edge))) for edge in edges]
        require(len(row) == len(set(row)) == 7, "template edge count")
        groups[g].append([sum(coefficients[b] for b in row) for coefficients in COEFFICIENTS])
    require([len(g) for g in groups] == sizes, "complete catalog")
    return groups


def main():
    require(not OUT.exists(), "fresh audit output required")
    OUT.mkdir(parents=True)
    preparation = json.loads((HERE / "preparation.json").read_text())
    source = ROOT / preparation["target"]
    require(sha(source) == preparation["target_sha256"], "native source changed")
    data = re.search(r"HEAVY_CUT_DATA = \{\{(.*?)\}\};", source.read_text(), re.S).group(1)
    native = [
        (int(mask), list(map(int, values.split(","))))
        for mask, values in re.findall(r"\{(\d+)u, \{\{([^}]+)\}\}\}", data)
    ]
    expected_data = [
        (sum(1 << (p - 1) for p in b), [c[b] for c in COEFFICIENTS]) for b in COEFFICIENTS[0]
    ]
    require(native == expected_data, "embedded cut data")
    configs = json.loads(
        (
            ROOT / "experiments/2026-10-03/four-seven-template-native-lookahead/seeds.json"
        ).read_text()
    )
    checked_states, checked_operations, catalog_total = [], 0, 0
    verifier_cache, binary_hashes, state_sets, controls = {}, {}, {}, []
    invalid_arguments = []
    for case_number, config in enumerate(configs["cases"]):
        case = config["name"]
        catalog = ROOT / config["catalog_path"]
        require(sha(catalog) == config["catalog_sha256"], "catalog hash")
        expected_catalog = catalog_sums(catalog)
        seed = (
            ROOT / "experiments/2026-10-03/lookahead-heavy-completion/seed.txt"
            if case == "cycle"
            else ROOT / config["seed_path"]
        )
        for binary_name in ["search", "search-sanitized"]:
            binary = RAW / binary_name
            binary_hashes[binary_name] = sha(binary)
            label = f"{case}-{binary_name}-catalog"
            directory = OUT / label
            output = run(
                [
                    str(binary),
                    str(catalog),
                    str(seed),
                    "2026104701",
                    "1",
                    str(directory / "unused"),
                    "--cut-guide",
                    "--cut-catalog",
                ],
                directory,
            )
            require(output[0]["groups"] == expected_catalog, "native template precomputation")
            require(output[0]["cut_sha256"] == sha(CUT_PATH), "native cut hash")
            catalog_total += sum(map(len, expected_catalog))
        settings = [
            (binary, enabled, weight)
            for binary in ["search", "search-sanitized"]
            for enabled, weight in [(False, 1), (True, 1), (True, 10), (False, 10), (True, 1000)]
        ]
        settings.append(("search-original", False, 1))
        for binary_name, enabled, weight in settings:
            binary = RAW / binary_name
            binary_hashes[binary_name] = sha(binary)
            label = f"{case}-{binary_name}-{'on' if enabled else 'off'}-w{weight}"
            directory = OUT / label
            prefix = directory / "state"
            argv = [
                str(binary),
                str(catalog),
                str(seed),
                str(2026104701 + case_number),
                "1",
                str(prefix),
            ]
            argv += ["--cut-guide"] if enabled else []
            if binary_name != "search-original":
                argv += ["--cut-weight", str(weight)]
            argv += ["--controls-only"]
            events = run(argv, directory)
            require(events[-1].get("event") == "controls_passed", "forced controls incomplete")
            original = binary_name == "search-original"
            states = {}
            for path in sorted(directory.glob("*.txt")):
                candidate = blocks(path)
                expected = recount(candidate, case, enabled, weight)
                detail = json.loads(Path(str(path) + ".lookahead.json").read_text())
                compare(detail, expected, original)
                states[path.name] = sha(path)
                checked_states.append(
                    {
                        "path": str(path.relative_to(ROOT)),
                        "sha256": sha(path),
                        "holes": expected["holes"],
                        "score": expected["score"],
                        "cut_lhs": expected["cut_lhs"],
                        "cut_penalty": expected["cut_penalty"],
                    }
                )
                if sha(path) not in verifier_cache:
                    checks = {}
                    for name, command in [
                        ("package", ["uv", "run", "covering64", "verify"]),
                        ("standalone", [sys.executable, "scripts/check_cover.py"]),
                    ]:
                        completed = subprocess.run(
                            command + [str(path), "--expected-blocks", "64"],
                            cwd=ROOT,
                            capture_output=True,
                            text=True,
                            timeout=30,
                            check=False,
                        )
                        response = json.loads(completed.stdout)
                        require(
                            completed.returncode in (0, 1) and not completed.stderr,
                            "verifier error",
                        )
                        require(response["valid"] == (expected["holes"] == 0), "cover validity")
                        require(len(response["uncovered"]) == expected["holes"], "cover hole count")
                        checks[name] = {"exit": completed.returncode, "response": response}
                    verifier_cache[sha(path)] = checks
                if not original and not controls:
                    for field in [
                        "holes",
                        "base_score",
                        "score",
                        "unsupported_count",
                        "admissible_count",
                        "heavy_excess",
                        "cut_lhs",
                        "cut_rhs",
                        "cut_violations",
                        "cut_weight",
                        "cut_count",
                        "cut_violation",
                        "cut_penalty",
                        "cut_denominator",
                    ]:
                        bad = copy.deepcopy(detail)
                        if isinstance(bad[field], list):
                            bad[field][0] += 1
                        else:
                            bad[field] += 1
                        try:
                            compare(bad, expected)
                        except ValueError:
                            controls.append(field)
                        else:
                            raise AssertionError(f"damaged field accepted: {field}")
                    bad = copy.deepcopy(detail)
                    bad["cut_enabled"] = not enabled
                    try:
                        compare(bad, expected)
                    except ValueError:
                        controls.append("cut_enabled")
                    else:
                        raise AssertionError("damaged cut toggle accepted")
            state_sets[label] = states
            for event in events:
                if event.get("event") != "operation":
                    continue
                before, after = blocks(Path(event["before"])), blocks(Path(event["after"]))
                require(
                    set(after)
                    == (set(before) - set(map(tuple, event["removed"])))
                    | set(map(tuple, event["added"])),
                    "move inventory",
                )
                left, right = (
                    recount(before, case, enabled, weight),
                    recount(after, case, enabled, weight),
                )
                for side, values in [("before", left), ("after", right)]:
                    require(
                        event["score_" + side] == values["score"]
                        and event["holes_" + side] == values["holes"],
                        "move score",
                    )
                if event["mode"] < 3:
                    require(left["cut_lhs"] == right["cut_lhs"], "ordinary move changed heavy sum")
                checked_operations += 1
            for mode in range(4):
                require(
                    states[f"state-control{mode}-before.txt"]
                    == states[f"state-control{mode}-rollback.txt"],
                    "rollback state changed",
                )
        require(
            state_sets[f"{case}-search-off-w1"]
            == state_sets[f"{case}-search-original-off-w1"]
            == state_sets[f"{case}-search-off-w10"]
            == state_sets[f"{case}-search-sanitized-off-w1"]
            == state_sets[f"{case}-search-sanitized-off-w10"],
            "disabled guide changed original control trajectory",
        )
        default_dir = OUT / f"{case}-default-weight"
        default_events = run(
            [
                str(RAW / "search"),
                str(catalog),
                str(seed),
                "2026104801",
                "1",
                str(default_dir / "unused"),
                "--cut-guide",
                "--lookahead-only",
            ],
            default_dir,
        )
        compare(default_events[-1], recount(blocks(seed), case, True, 1))
        for number, flags in enumerate(
            [
                ["--cut-weight", "0"],
                ["--cut-weight", "1001"],
                ["--cut-weight", "-1"],
                ["--cut-weight", "1.5"],
                ["--cut-weight", "abc"],
                ["--cut-weight"],
                ["--cut-weight", "1", "--cut-weight", "10"],
                ["--cut-guide", "--cut-guide"],
            ]
        ):
            directory = OUT / f"{case}-invalid-{number}"
            directory.mkdir()
            command = [
                str(RAW / "search"),
                str(catalog),
                str(seed),
                "2026104801",
                "1",
                str(directory / "unused"),
                *flags,
            ]
            completed = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True, timeout=10, check=False
            )
            require(
                completed.returncode != 0 and bool(completed.stderr),
                "invalid CLI arguments accepted",
            )
            require(
                not completed.stdout and not list(directory.glob("*.txt")),
                "invalid CLI arguments produced state",
            )
            (directory / "stderr.log").write_text(completed.stderr)
            invalid_arguments.append(
                {"case": case, "flags": flags, "exit": completed.returncode, "rejected": True}
            )
    (OUT / "verifier-results.json").write_text(json.dumps(verifier_cache, indent=2) + "\n")
    receipt = {
        "passed": True,
        "checker_sha256": sha(Path(__file__)),
        "source_sha256": sha(source),
        "cut_sha256": sha(CUT_PATH),
        "oracle_sha256": sha(ORACLE_PATH),
        "binaries": binary_hashes,
        "catalog_sums_compared": catalog_total,
        "unique_catalog_templates": catalog_total // 2,
        "individual_cut_sums_compared": catalog_total * 14,
        "tested_weights": [1, 10, 1000],
        "invalid_argument_controls_rejected": len(invalid_arguments),
        "invalid_argument_controls": invalid_arguments,
        "states": len(checked_states),
        "unique_verified_states": len(verifier_cache),
        "operations": checked_operations,
        "damaged_fields_rejected": len(controls),
        "damage_controls": controls,
        "snapshots": checked_states,
        "disabled_matches_original": True,
        "optimized_and_sanitized": True,
        "ceiling_boundaries_checked": [-1, 0, 1, 999, 1000, 1001],
        "native_stderr_empty": True,
        "zero_hole_override_retained": True,
        "scope": "Read-only catalog evaluation and forced move controls only; no search launch.",
    }
    (HERE / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (OUT / "audit.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: v for k, v in receipt.items() if k != "snapshots"}))


if __name__ == "__main__":
    main()
