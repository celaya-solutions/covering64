# Document:    Six-Case Hub Count LP Campaign
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      2c3550e8adbf8df8115ca4d753bbbe95117487a798953f5b4e7c1a8a335fdc3b
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Run all six audited hub-count cases, with at most two LP processes at once."""

import argparse
import concurrent.futures
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path

from four_seven_hub_split import CASES

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--representatives", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or args.seconds <= 0:
        parser.error("positive finite seconds required")
    audit = json.loads(args.audit.read_text())
    helper = Path(__file__).with_name("four_seven_hub_split.py")
    if audit.get("passed") is not True or audit.get("helper_sha256") != sha(helper):
        parser.error("a passing independent audit of this exact hub helper is required")
    if args.output.exists():
        parser.error("output directory must be new")
    args.output.mkdir(parents=True)
    representatives = args.representatives.resolve()
    output = args.output.resolve()
    (output / "representatives.json").write_bytes(representatives.read_bytes())
    (output / "independent-hub-audit.json").write_bytes(args.audit.read_bytes())
    (output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    source_paths = [Path(__file__), *[ROOT / "scripts" / name for name in (
        "four_seven_link_lp.py", "four_seven_hub_split.py", "four_seven_blossom_cuts.py",
        "four_seven_feature_cuts.py", "four_seven_facet_cuts.py", "four_seven_double_cuts.py",
        "four_seven_search.py")]]
    metadata = {
        "cases": [list(case) for case in CASES], "maximum_parallel_processes": 2,
        "seconds_per_stage": args.seconds,
        "sources": {str(path.relative_to(ROOT)): sha(path) for path in source_paths},
        "representatives_sha256": sha(representatives), "audit_sha256": sha(args.audit),
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "scope": "Six exhaustive integer hub-count cases in each regular four-sevenfold "
                 "branch. Exclusion of an orbit requires checked certificates in all six.",
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")

    def run(case):
        m4, z = case
        name = f"m4-{m4}-z-{z}"
        command = ["uv", "run", "python", str(ROOT / "scripts/four_seven_link_lp.py"),
                   "--representatives", str(representatives), "--output", str(output / name),
                   "--seconds", str(args.seconds), "--feature-cuts", "--feature-proof",
                   "experiments/2026-10-03/four-seven-link-orbits/safe-linear-cuts.json",
                   "--facet-cuts", "--facet-proof",
                   "experiments/2026-10-03/four-seven-link-orbits/safe-feature-facets.json",
                   "--blossom-cuts", "--four-hub-blocks", str(m4),
                   "--double-hub-triples", str(z)]
        start = time.monotonic()
        with (output / f"{name}.log").open("w") as log:
            completed = subprocess.run(command, cwd=ROOT, stdout=log,
                                       stderr=subprocess.STDOUT, check=False)
        result = {"case": list(case), "command": command,
                  "returncode": completed.returncode, "seconds": time.monotonic() - start}
        (output / f"{name}-process.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({key: value for key, value in result.items() if key != "command"}),
              flush=True)
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, CASES))
    (output / "process-results.json").write_text(json.dumps(results, indent=2) + "\n")
    if any(result["returncode"] for result in results):
        raise SystemExit("one or more case screens failed; preserve logs and incomplete evidence")


if __name__ == "__main__":
    main()
