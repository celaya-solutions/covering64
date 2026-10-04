# Document:    Primary Covering Bound Refresh Readback
# Version:     v1.0.0
# Author:      Celaya Solutions
# Contact:     hello@celayasolutions.com
# Date:        2026-10-03
# SHA256:      a420d26d6652e8f2665cf77f3127688b5851aacdfa524fe406d79a2de15839ba
# Chain:       n/a
# Tx:          [not anchored]
# License:     All Rights Reserved / Celaya Solutions

"""Check saved response hashes and extract the freshly retrieved primary record."""

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT / "experiments/scratch/public-bound-refresh-20261003"


def inspect(sources, extracted):
    assert len(sources) == 9
    for source in sources:
        data = (RAW / source["artifact"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == source["sha256"]
        assert len(data) == source["bytes"]
    metadata = json.loads((RAW / "zenodo.json").read_text())
    assert metadata["id"] == 19735294 and metadata["conceptrecid"] == "10779736"
    assert metadata["metadata"]["version"] == "1.2"
    assert metadata["metadata"]["publication_date"] == "2026-04-24"
    for name in ("coverdata.json", "covering_code.py", "README.md"):
        entry = next(f for f in metadata["files"] if f["key"] == name)
        content = (RAW / name).read_bytes()
        assert len(content) == entry["size"]
        assert "md5:" + hashlib.md5(content).hexdigest() == entry["checksum"]
    data = json.loads((RAW / "coverdata.json").read_text())
    assert extracted == data["C(16,5,3)"]
    assert extracted["size"] == 65 and extracted["low_bd"] == 61
    assert extracted["imps"][0] == ["65", "", "Rade Belic", "1997-08-06 00:00:00"]
    assert not any(int(improvement[0]) <= 64 for improvement in extracted["imps"])


def main():
    sources = json.loads((HERE / "sources.json").read_text())
    entry = json.loads((RAW / "coverdata.json").read_text())["C(16,5,3)"]
    inspect(sources, entry)
    damaged = copy.deepcopy(sources)
    damaged[-1]["sha256"] = "0" * 64
    controls = [(damaged, entry), (sources[:-1], entry)]
    for key, value in (("size", 64), ("low_bd", 65)):
        bad_entry = copy.deepcopy(entry)
        bad_entry[key] = value
        controls.append((sources, bad_entry))
    for bad_sources, bad_entry in controls:
        try:
            inspect(bad_sources, bad_entry)
        except AssertionError:
            continue
        raise AssertionError("damaged source evidence accepted")
    report = {
        "passed": True,
        "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "metadata_sha256": hashlib.sha256((RAW / "coverdata.json").read_bytes()).hexdigest(),
        "entry": entry,
        "source_version": "1.2",
        "source_publication_date": "2026-04-24",
        "primary_record": "https://zenodo.org/records/19735294",
        "primary_database_frozen": "March 2026, per repository README",
        "current_coveringrepository_entry_freshly_verified": False,
        "current_entry_limitation": "HTTP403 browser challenge; "
        "in-app and Chrome browser surfaces unavailable",
        "witness_archive_downloaded": False,
        "damaged_controls_rejected": len(controls),
        "scope": "Fresh retrieval of a frozen primary database; "
        "not a proof of no later improvement.",
    }
    (HERE / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
