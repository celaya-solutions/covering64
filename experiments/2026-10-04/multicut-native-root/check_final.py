# Document:    Independent Final-State Native Multicut Coefficient Check
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      [pending]
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    source = (ROOT / "scripts/four_seven_template_multicut_final_heuristic.cpp").read_bytes()
    bundle = (ROOT / "experiments/2026-10-03/cut-survivor-lp-screen/cut-bundle.json").read_bytes()
    gate = json.loads((HERE.parent / "cut-bundle-independent/audit.json").read_bytes())
    sha = lambda data: hashlib.sha256(data).hexdigest()  # noqa: E731
    assert gate["passed"] and sha(bundle) == gate["bundle_sha256"]
    data, text = json.loads(bundle), source.decode()
    part = text[text.index("HEAVY_CUT_DATA"):text.index("static std::array<CutValues, 65536>")]
    entries = re.findall(r"\{(\d+)u, \{\{([-0-9, ]+)\}\}\}", part)
    assert len(entries) == 276
    for index, (mask, coefficients) in enumerate(entries):
        assert int(mask) == sum(1 << (p - 1) for p in data["heavy_blocks"][index])
        assert list(map(int, coefficients.split(","))) == [
            cut["coefficients"][index] for cut in data["cuts"]]
    rhs_text = re.search(r"HEAVY_CUT_RHS = \{\{([^}]+)\}\}", text).group(1)
    assert list(map(int, rhs_text.split(","))) == [cut["rhs"] for cut in data["cuts"]]
    assert f'HEAVY_CUT_SHA256 = "{sha(bundle)}"' in text
    assert "HEAVY_CUT_COUNT = 14;" in text and "HEAVY_CUT_DENOMINATOR = 1000;" in text
    result = {"passed": True, "heavy_masks": 276, "embedded_coefficients": 3864,
              "right_hand_sides": 14, "source_sha256": sha(source),
              "bundle_sha256": sha(bundle), "checker_sha256": sha(Path(__file__).read_bytes()),
              "scope": "Embedded integer data only; runtime move audit is separate."}
    output = HERE / "audit-v1.4.1.json"
    assert not output.exists(), "Preserve completed evidence"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
