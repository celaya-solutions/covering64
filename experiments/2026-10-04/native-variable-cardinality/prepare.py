# Document:    Variable Cardinality Pilot Preparation
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      e83bf832cf984eda9ef0bc29aecd081c78d9fed22545fee4d0aea588b781f7aa
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Build and exercise deterministic controls only. Never launch optimization."""

import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from run import BUDGET, HERE, RAW, ROOT, checked, dump, sha


def header(title, prefix):
    return (
        "\n".join(
            prefix + line
            for line in [
                f"Document:    {title}",
                "Version:     v1.0.0",
                "Author:      Celaya Solutions",
                "Contact:     hello@celayasolutions.com",
                "Date:        2026-10-04",
                "SHA256:      [pending]",
                "Chain:       n/a",
                "Tx:          [not anchored]",
                "License:     All Rights Reserved / Celaya Solutions",
            ]
        )
        + "\n"
    )


def freeze_header(path):
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    import hashlib

    digest = hashlib.sha256("".join(lines[9:]).encode()).hexdigest()
    lines[5] = re.sub(r"SHA256:      .*", "SHA256:      " + digest, lines[5])
    path.write_text("".join(lines))


def main():
    assert not (HERE / "manifest.json").exists(), "already frozen"
    RAW.mkdir(parents=True, exist_ok=True)
    origin = ROOT / "experiments/2026-10-04/native-pair-two-penalty/manifest.json"
    core_rows = json.loads(origin.read_text())["core_rows"]
    assert len(core_rows) == 4 and all(len(c) == len(set(c)) == 60 for c in core_rows)
    core_header = HERE / "cores.hpp"
    core_header.write_text(
        header("Four Diagnostic Core Rows", "// ")
        + "#pragma once\n#include <array>\nnamespace vc {\n"
        + "inline constexpr std::array<std::array<int,60>,4> core_rows={{\n"
        + ",\n".join("{{" + ",".join(map(str, row)) + "}}" for row in core_rows)
        + "\n}};\n}\n"
    )
    for path in HERE.iterdir():
        if path.suffix in (".hpp", ".cpp", ".py"):
            freeze_header(path)
    compiler = Path("/usr/bin/clang++")
    builds = []
    for source, name, flags in [
        ("search.cpp", "search", ["-O3", "-DNDEBUG"]),
        (
            "control.cpp",
            "control",
            ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"],
        ),
    ]:
        command = [
            str(compiler),
            "-std=c++20",
            *flags,
            "-Wall",
            "-Wextra",
            "-pedantic",
            str(HERE / source),
            "-o",
            str(RAW / name),
        ]
        p = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        (RAW / f"build-{name}.stdout").write_text(p.stdout)
        (RAW / f"build-{name}.stderr").write_text(p.stderr)
        assert p.returncode == 0, p.stderr
        builds.append(
            {"command": command, "returncode": p.returncode, "binary_sha256": sha(RAW / name)}
        )
    start = ROOT / "data/baselines/belic-1997.txt"
    initial = checked(start, core_rows)
    assert initial["metrics"]["cardinality"] == 65 and initial["metrics"]["holes"] == 0
    command = [str(RAW / "control"), str(start), str(RAW / "control")]
    p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False, timeout=30)
    (RAW / "controls.stdout.jsonl").write_text(p.stdout)
    (RAW / "controls.stderr.txt").write_text(p.stderr)
    assert p.returncode == 0 and not p.stderr, p.stderr
    events = [json.loads(line) for line in p.stdout.splitlines()]
    assert events[-1]["event"] == "controls_passed"
    families = [checked(path, core_rows) for path in sorted(RAW.glob("control-*.txt"))]
    # Malformed control families must fail both implementations' validity checks.
    from covering64.core import read_blocks, verify_cover

    malformed = []
    for name, content in {
        "duplicate": start.read_text() + start.read_text().splitlines()[0] + "\n",
        "label": "1 2 3 4 17\n",
        "damaged": "1 2 3 4\n",
    }.items():
        path = RAW / f"invalid-{name}.txt"
        path.write_text(content)
        try:
            package_rejected = not verify_cover(read_blocks(path))["valid"]
        except (ValueError, TypeError, IndexError):
            package_rejected = True
        p = subprocess.run(
            [sys.executable, "scripts/check_cover.py", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert package_rejected and p.returncode == 2
        malformed.append(
            {
                "name": name,
                "path": str(path.relative_to(ROOT)),
                "sha256": sha(path),
                "package_rejected": True,
                "standalone_returncode": p.returncode,
                "standalone_stdout": p.stdout,
            }
        )
    dump(
        HERE / "controls.json",
        {
            "passed": True,
            "command": command,
            "events": events,
            "families": families,
            "invalid_families": malformed,
            "initial": initial,
            "sanitizers": ["address", "undefined"],
            "optimization_launched": False,
            "synthetic_stop_predicate_is_not_a_witness": True,
        },
    )
    sources = [p for p in HERE.iterdir() if p.suffix in (".hpp", ".cpp", ".py")]
    source_map = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    raw_map = {str(p.relative_to(ROOT)): sha(p) for p in RAW.iterdir() if p.is_file()}
    input_paths = [
        start,
        origin,
        HERE / "controls.json",
        ROOT / "scripts/check_cover.py",
        ROOT / "src/covering64/core.py",
        ROOT / "uv.lock",
        ROOT / "experiments/2026-10-04/post-d2-literature/README.md",
        ROOT / "experiments/2026-10-04/post-d2-literature/sources.json",
    ]
    dump(
        HERE / "manifest.json",
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "budget": BUDGET,
            "source_revision": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "source_files": source_map,
            "input_files": {str(p.relative_to(ROOT)): sha(p) for p in input_paths},
            "raw_files": raw_map,
            "core_rows": core_rows,
            "core_origin_sha256": sha(origin),
            "start_path": str(start.relative_to(ROOT)),
            "binary_path": str((RAW / "search").relative_to(ROOT)),
            "binary_sha256": sha(RAW / "search"),
            "compiler_path": str(compiler),
            "compiler_sha256": sha(compiler),
            "compiler_version": subprocess.check_output([str(compiler), "--version"], text=True),
            "python_version": sys.version,
            "platform": platform.platform(),
            "builds": builds,
            "controls_sha256": sha(HERE / "controls.json"),
            "all_blocks": 4368,
            "triples": 560,
            "labels": "1-based",
            "block_order": "lexicographic",
            "cost": 1,
            "ranking": [
                "5*score+pscore descending",
                "pscore descending",
                "oldest flip",
                "smallest lex ID",
            ],
            "tabu_tenure": 4,
            "novelty_residue_threshold": "draw in 0..99 <11 (effective probability11/100)",
            "no_eligible_fallback": "first lex carrier, bypass CC/tabu",
            "decay": None,
            "core_policy": (
                "diagnostic only; no cap filtering in trajectory; "
                "admissible64 requires overlaps<=55"
            ),
            "trajectory_incumbent65": "64 -> 62 -> 63 -> 64, plus swaps",
            "records": [
                "best_complete",
                "best_raw_exact64",
                "best_four_core_cap_admissible_exact64",
                "actual_final",
            ],
            "source_algorithm": (
                "NuSC, DOI10.1109/TCYB.2022.3199147; independently written implementation"
            ),
            "upstream_revision": "fdacd80d92e7143b4fe305bddce471a1e8982e90",
            "adaptations": [
                "fixed verified Belic65 start replaces greedy construction",
                "deterministic lex final tie break",
                "mt19937_64 with uniform draws",
                "direct exact scores instead of cached updates",
                "stop immediately after every mutation yielding complete<=64",
                "diagnostic records and audits",
            ],
            "optimization_launched": False,
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "manifest_sha256": sha(HERE / "manifest.json"),
                "controls_sha256": sha(HERE / "controls.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
