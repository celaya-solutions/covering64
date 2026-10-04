# Document:    Independent H9 D23 Queue Delta Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      16fa3543d788f697b455c913f3de744e9ab609002e9b45befa5138c46827ee12
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Pure file, arithmetic, and abstract queue checks; never launch a shell."""

import ast
import copy
import hashlib
import importlib.util
import json
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P = HERE.parent / "weak-pair-h9-d23-neutral-queue"
OLD = HERE.parent / "weak-pair-neutral-queue-resume-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def family(path, universe):
    rows = [tuple(map(int, line.split())) for line in Path(path).read_text().splitlines()]
    assert rows == sorted(set(rows)) and len(rows) == 64
    assert all(len(row) == 5 and row == tuple(sorted(set(row))) for row in rows)
    return {universe[row] for row in rows}


def fake_state(tag, deficit=23, ordinal=0, holes=9):
    return {
        "sha256": tag,
        "ids": [ordinal],
        "metrics": {"holes": holes, "D2max": deficit},
    }


def answer(strict=(), neutral=(), passed=True, complete=True, covers=()):
    return {
        "passed": passed,
        "complete": complete,
        "observed_covers": list(covers),
        "best_ties": list(strict),
        "neutral_ties": list(neutral),
    }


def queue_checks(run):
    results = []
    for strict in [False, True]:
        seed = fake_state("seed", deficit=100)
        calls = []

        def execute(number, kind, center):
            calls.append((number, kind, center["sha256"]))
            next_state = fake_state(
                f"n{number}", deficit=100 - number if strict else 100, ordinal=number
            )
            if kind == "two":
                return answer()
            return answer(strict=[next_state]) if strict else answer(neutral=[next_state])

        result = run.queue_campaign(seed, {"old"}, execute, lambda row, _: row, [seed])
        assert len(calls) == 32 and result["centers_processed"] == 16
        assert result["stop_reason"] == "center_budget"
        assert len(result["visited_hashes"]) == 17
        assert result["unscanned_next"]["sha256"] == "n16"
        assert result["unscanned_frontier"] == [result["unscanned_next"]]
        assert not result["plateau_exhaustion_claim"]
        assert all(calls[2 * n][0] == n + 1 for n in range(16))
        results.append({"case": "strict bound" if strict else "neutral bound", "calls": 32})

    seed = fake_state("seed")
    for name, frontier, history in [
        ("empty frontier", [], set()),
        ("duplicate frontier", [seed, seed], set()),
        ("visited initial", [seed], {"seed"}),
        ("mixed rank", [seed, fake_state("bad", 24, 1)], set()),
        ("nonleast initial", [seed, fake_state("less", ordinal=-1)], set()),
    ]:
        calls = []

        def forbidden(*args):
            calls.append(args)
            raise AssertionError("unexpected shell callback")

        try:
            run.queue_campaign(seed, history, forbidden, lambda row, _: row, frontier)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted {name}")
        assert not calls
        results.append({"case": name, "calls": 0, "rejected": True})

    cases = [
        ("empty sampled frontier", [answer(), answer()], "sample_exhausted", 2),
        ("first incomplete", [answer(complete=False)], "incomplete", 1),
        ("second incomplete", [answer(), answer(passed=False)], "incomplete", 2),
        ("early cover", [answer(covers=[seed])], "cover_observed", 1),
    ]
    for name, replies, reason, count in cases:
        calls = []

        def execute(*args):
            calls.append(args)
            return replies[len(calls) - 1]

        result = run.queue_campaign(seed, set(), execute, lambda row, _: row, [seed])
        assert result["stop_reason"] == reason and len(calls) == count
        assert not result["plateau_exhaustion_claim"]
        results.append({"case": name, "calls": count})
    return results


def main():
    m = read(P / "manifest.json")
    assert (
        sha(P / "manifest.json")
        == "64d63c5bee05e8ba8c5ca7bbb4f98b3258a6f3d6192297e792a4b62b12835d87"
    )
    checked = {}
    for group in ["input_files", "sources", "files", "raw_files"]:
        for name, digest in m[group].items():
            assert sha(ROOT / name) == digest, name
            checked[name] = digest
    expected_budget = {
        "budget_transfer": False,
        "max_centers": 16,
        "max_shell_launches": 32,
        "relaunch": False,
        "seconds_per_shell": 120,
        "seed": None,
        "termination_grace_seconds": 5,
        "watchdog_seconds": 135,
    }
    assert m["budget"] == expected_budget
    assert len(m["core_rows"]) == 4 and m["neutral_cap_per_shell"] == 64
    old_manifest = read(OLD / "manifest.json")
    assert m["core_rows"] == old_manifest["core_rows"]
    assert m["shells"] == old_manifest["shells"]
    old_gate = read(OLD.parent / "weak-pair-neutral-queue-resume-01-independent/gate.json")
    assert old_gate["passed"] and old_gate["decision"] == "GO"
    assert old_gate["manifest_sha256"] == sha(OLD / "manifest.json")
    for kind in ["one", "two"]:
        assert m["shells"][kind]["binary_sha256"] == old_gate[f"{kind}_binary_sha256"]

    old_tree = ast.parse((OLD / "run.py").read_text())
    new_tree = ast.parse((P / "run.py").read_text())
    old_queue = next(
        n for n in old_tree.body if isinstance(n, ast.FunctionDef) and n.name == "queue_campaign"
    )
    new_queue = next(
        n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == "queue_campaign"
    )
    normalized = copy.deepcopy(new_queue)
    changes = []
    for node in ast.walk(normalized):
        if isinstance(node, ast.Constant) and type(node.value) is int and node.value in [16, 17]:
            changes.append(node.value)
            node.value = {16: 32, 17: 33}[node.value]
    assert sorted(changes) == [16, 17]
    assert ast.dump(normalized) == ast.dump(old_queue)
    for name in ["rank", "base_module", "execute_shell"]:
        a = next(n for n in old_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        b = next(n for n in new_tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        assert ast.dump(a) == ast.dump(b)

    universe = {b: i for i, b in enumerate(combinations(range(1, 17), 5))}
    ids = family(P / "initial.txt", universe)
    initial = m["initial"]
    assert sorted(ids) == initial["ids"] and sha(P / "initial.txt") == initial["sha256"]
    assert initial["metrics"] == {
        "D2max": 23,
        "D2sum": 29,
        "D3": 0,
        "D4": 0,
        "cardinality": 64,
        "core_overlaps": [1, 0, 1, 1],
        "holes": 9,
        "minimum_pair_count": 5,
    }
    native_path = HERE.parent / "native-five-core-record-runtime-independent/postcheck.json"
    native = read(native_path)
    assert native["passed"] and sha(native_path) == m["native_runtime_audit_sha256"]
    matching = [f for f in native["families"] if f["sha256"] == initial["sha256"]]
    assert len(matching) == 1
    f = matching[0]
    assert f["ids"] == initial["ids"] and f["weak_metrics"] == initial["metrics"]
    assert f["package"] == initial["verification"]["package"]
    assert f["standalone"] == initial["verification"]["standalone"]
    assert f["weak_qualified"] and f["five_caps_pass"]
    assert (
        not initial["cover_found"]
        and not initial["package_valid"]
        and not initial["standalone_valid"]
    )
    frontier = read(ROOT / m["resume_frontier_path"])["frontier"]
    assert frontier == [initial] and m["resume_frontier_count"] == 1

    h = read(ROOT / m["history_distance_path"])
    prior_result = read(OLD / "result.json")
    historical = set(m["historical_visited_hashes"])
    assert historical == set(prior_result["visited_hashes"])
    assert len(historical) == len(m["historical_visited_hashes"]) == 34
    assert initial["sha256"] not in historical
    assert {row["sha256"] for row in h["centers"]} == historical
    distances = []
    for row in h["centers"]:
        path = ROOT / row["path"]
        assert sha(path) == row["sha256"]
        distance = 64 - len(ids & family(path, universe))
        assert distance == row["one_swap_distance"] == 63
        distances.append(distance)
    assert h["maximum_center_radius"] == 2 * (16 - 1) == 30
    assert h["maximum_inspected_candidate_radius"] == 2 * 16 == 32
    assert min(distances) > h["maximum_inspected_candidate_radius"]
    fifth = m["observed_fifth_core"]
    assert fifth["diagnostic_only"] is True
    overlap = len(ids & set(fifth["ids"]))
    assert overlap == fifth["initial_overlap"] == 1
    assert fifth["maximum_candidate_radius"] == 32
    assert overlap + 32 == fifth["maximum_overlap_within_budget"] == 33
    assert 33 < fifth["threshold"] == 56
    fifth_body = {
        universe[tuple(map(int, line.split()))]
        for line in (ROOT / fifth["witness_path"]).read_text().splitlines()
    }
    assert fifth_body == set(fifth["ids"]) and len(fifth_body) == 62

    spec = importlib.util.spec_from_file_location("independent_h9_queue", P / "run.py")
    run = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(run)
    result = {
        "passed": True,
        "manifest_sha256": sha(P / "manifest.json"),
        "runner_sha256": sha(P / "run.py"),
        "source_sha256": sha(__file__),
        "unique_file_pins_checked": len(checked),
        "initial_sha256": initial["sha256"],
        "initial_metrics": initial["metrics"],
        "native_runtime_audit_sha256": sha(native_path),
        "unchanged_queue_except_16_center_budget": True,
        "unchanged_functions": ["rank", "base_module", "execute_shell"],
        "prior_manifest_sha256": sha(OLD / "manifest.json"),
        "historical_families": 34,
        "historical_distances": sorted(set(distances)),
        "maximum_center_radius": 30,
        "maximum_candidate_radius": 32,
        "fifth_core_maximum_overlap": 33,
        "fifth_core_threshold": 56,
        "fifth_core_diagnostic_only": True,
        "budget": expected_budget,
        "queue_controls": queue_checks(run),
        "optimizer_launches": 0,
        "shell_process_launches": 0,
        "scope": (
            "Focused delta review only. Previous native and adapter audits reused by hashes. "
            "Named history and fifth-core bounds apply to this 16-center pilot only."
        ),
    }
    (HERE / "checks.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "passed",
                    "unique_file_pins_checked",
                    "historical_families",
                    "optimizer_launches",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
