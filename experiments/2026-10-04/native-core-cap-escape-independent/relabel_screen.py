# Document:    Native Nine-Hole Relabeled Core Screen
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-04
# SHA256:      5e328b6753fe52a09916510cdbf7457e89222f2be5b20aac7da4547b5016ca9f
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions
"""Apply the previously audited complete necessary-condition screen."""

import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "experiments/2026-10-04/six-hole-strong-core-release-independent/relabels.py"
WITNESS = ROOT / (
    "experiments/2026-10-04/native-core-cap-escape-v2/seed-2026104201/search-h9.txt"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert sha(SOURCE) == "9cdcd511eb94954bb45c1cf209c5d51517b46c11e46b44a22ce7221d9309f74a"
assert sha(WITNESS) == "15db6bdbf8c6210c6754cbe52a1408dda6a279429bb5471cf03a1b68b24f0c46"
spec = importlib.util.spec_from_file_location("audited_relabel_screen", SOURCE)
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)
ids = [screen.RANK[tuple(map(int, line.split()))] for line in WITNESS.read_text().splitlines()]
result = screen.check(ids)
result.update(
    witness_path=str(WITNESS.relative_to(ROOT)),
    witness_sha256=sha(WITNESS),
    screen_source_sha256=sha(SOURCE),
    caller_sha256=sha(Path(__file__)),
    optimizer_calls=0,
    covering_verifier_receipt_sha256=sha(HERE / "postcheck.json"),
)
(HERE / "relabel-screen.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result))
