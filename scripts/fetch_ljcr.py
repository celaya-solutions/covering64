#!/usr/bin/env python3
"""Reproduce the immutable LJCR C(16,5,3) benchmark using the standard library.

Default mode verifies all of coverdata.json and requests the exact 1,070-byte
cover entry. It does not verify the 4.19 GB covers.json checksum. Optional
--full-archive downloads and verifies that entire payload before extraction.
This script was reconstructed after the original execution filesystem was lost.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path

RECORD_ID = 19735294
KEY = "C(16,5,3)"
ENTRY_START = 18_860_330
ENTRY_END = 18_861_399
ENTRY_SHA256 = "582ee63e54ba947af3155e03e6055027a92c55c1fda9b78ec021b5b693968d3c"
WITNESS_SHA256 = "89e4f68acba5d2cbee73e22d07dd1030e540b920fc7541619a065e998dc7d43f"
REPO = Path(__file__).resolve().parents[1]


def digests(path: Path) -> dict[str, str]:
    md5, sha256 = hashlib.md5(), hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return {"md5": md5.hexdigest(), "sha256": sha256.hexdigest()}


def fetch_file(item: dict, directory: Path, timeout: float) -> tuple[Path, dict]:
    destination = directory / item["key"]
    expected_md5 = item["checksum"].removeprefix("md5:")
    if destination.exists() and destination.stat().st_size == item["size"]:
        actual = digests(destination)
        if actual["md5"] == expected_md5:
            return destination, actual
    partial = destination.with_name(destination.name + ".part")
    started = last_notice = time.monotonic()
    downloaded = 0
    request = urllib.request.Request(item["links"]["self"])
    with urllib.request.urlopen(request, timeout=30) as response, partial.open("wb") as stream:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            if time.monotonic() - started > timeout:
                raise TimeoutError(f"{item['key']} exceeded {timeout:g}s download budget")
            stream.write(chunk)
            downloaded += len(chunk)
            if time.monotonic() - last_notice >= 30:
                print(f"{item['key']}: {downloaded:,}/{item['size']:,} bytes", file=sys.stderr)
                last_notice = time.monotonic()
    if partial.stat().st_size != item["size"]:
        raise ValueError(f"{item['key']}: wrong downloaded length")
    actual = digests(partial)
    if actual["md5"] != expected_md5:
        raise ValueError(f"{item['key']}: published MD5 mismatch")
    partial.replace(destination)
    return destination, actual


def fetch_entry(item: dict, directory: Path) -> tuple[bytes, dict]:
    request = urllib.request.Request(
        item["links"]["self"], headers={"Range": f"bytes={ENTRY_START}-{ENTRY_END}"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        expected_range = f"bytes {ENTRY_START}-{ENTRY_END}/{item['size']}"
        if response.status != 206 or response.headers.get("Content-Range") != expected_range:
            raise ValueError("Archive endpoint did not honor the exact HTTP byte range")
        raw = response.read(ENTRY_END - ENTRY_START + 2)
    if len(raw) != ENTRY_END - ENTRY_START + 1:
        raise ValueError("Truncated or oversized archive entry")
    if hashlib.sha256(raw).hexdigest() != ENTRY_SHA256:
        raise ValueError("Pinned archive fragment SHA-256 mismatch")
    (directory / "c16-5-3.fragment.txt").write_bytes(raw)
    return raw, {"http_status": 206, "content_range": expected_range}


def extract_entry(path: Path) -> bytes:
    """Scan the archive line by line, retaining only the requested small array."""
    marker = f'"{KEY}":'.encode()
    with path.open("rb") as stream:
        offset = 0
        for line in stream:
            if line.startswith(marker):
                if offset != ENTRY_START:
                    raise ValueError("Unexpected entry position in pinned archive")
                parts = [line]
                for line in stream:
                    parts.append(line)
                    if line.startswith(b"],"):
                        raw = b"".join(parts)
                        if hashlib.sha256(raw).hexdigest() != ENTRY_SHA256:
                            raise ValueError("Pinned archive fragment SHA-256 mismatch")
                        return raw
                raise ValueError("Archive ended inside the requested entry")
            offset += len(line)
    raise ValueError(f"{KEY} was not found")


def validate(blocks: list[list[int]]) -> dict:
    """Independent exhaustive check; do not import the construction engine."""
    if len(blocks) != 65 or len({tuple(sorted(block)) for block in blocks}) != 65:
        raise ValueError("Expected 65 distinct blocks")
    if any(
        len(block) != 5
        or len(set(block)) != 5
        or not all(type(p) is int and 1 <= p <= 16 for p in block)
        for block in blocks
    ):
        raise ValueError("Malformed block")
    block_sets = list(map(set, blocks))
    multiplicities = {
        triple: sum(set(triple) <= block for block in block_sets)
        for triple in combinations(range(1, 17), 3)
    }
    histogram = dict(sorted(Counter(multiplicities.values()).items()))
    if histogram != {1: 497, 2: 56, 3: 2, 7: 5}:
        raise ValueError(f"Unexpected coverage multiplicities: {histogram}")
    return {
        "blocks": len(blocks),
        "distinct_blocks": len(block_sets),
        "triples": len(multiplicities),
        "covered_triples": sum(value > 0 for value in multiplicities.values()),
        "triple_incidences": sum(multiplicities.values()),
        "multiplicity_histogram": histogram,
        "sevenfold_triples": [list(t) for t, value in multiplicities.items() if value == 7],
        "point_replications": {p: sum(p in b for b in block_sets) for p in range(1, 17)},
        "pair_multiplicity_histogram": dict(
            sorted(
                Counter(
                    sum(set(pair) <= block for block in block_sets)
                    for pair in combinations(range(1, 17), 2)
                ).items()
            )
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--full-archive",
        action="store_true",
        help="download all 4.19 GB and verify its published MD5",
    )
    parser.add_argument(
        "--cache-dir", type=Path, default=Path(tempfile.gettempdir()) / "covering64-ljcr"
    )
    parser.add_argument(
        "--download-timeout",
        type=float,
        default=7200,
        help="per-file wall time budget in seconds",
    )
    args = parser.parse_args()
    if args.cache_dir.resolve().is_relative_to(REPO):
        parser.error("--cache-dir must be outside the repository")
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    record_path = REPO / "data/provenance/zenodo-record-19735294.json"
    record = json.loads(record_path.read_text())
    if record.get("id") != RECORD_ID or record["metadata"].get("version") != "1.2":
        raise ValueError("Expected the pinned LJCR version 1.2 record")
    files = {item["key"]: item for item in record["files"]}
    metadata_path, metadata_hashes = fetch_file(
        files["coverdata.json"], args.cache_dir, args.download_timeout
    )
    metadata = json.loads(metadata_path.read_text())[KEY]
    if metadata["size"] != 65 or metadata["low_bd"] != 61:
        raise ValueError("Unexpected archival bounds")
    archive_hashes = range_response = None
    if args.full_archive:
        archive_path, archive_hashes = fetch_file(
            files["covers.json"], args.cache_dir, args.download_timeout
        )
        raw = extract_entry(archive_path)
        mode = "complete_archive_md5_verified"
    else:
        raw, range_response = fetch_entry(files["covers.json"], args.cache_dir)
        mode = "versioned_http_byte_range_full_archive_md5_unverified"
    blocks = json.loads(b"{" + raw.rstrip().rstrip(b",") + b"}")[KEY]
    result = validate(blocks)
    text = "".join(" ".join(map(str, block)) + "\n" for block in blocks)
    witness_sha256 = hashlib.sha256(text.encode()).hexdigest()
    if witness_sha256 != WITNESS_SHA256:
        raise ValueError("Witness does not match the retained discovery report SHA-256")
    baseline = REPO / "data/baselines/belic-1997.txt"
    baseline.parent.mkdir(parents=True, exist_ok=True)
    baseline.write_text(text)
    provenance = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "recovery": {
            "reconstructed_after_original_filesystem_loss": True,
            "original_research_logs_restored": False,
            "note": "Primary source bytes re-fetched and checks performed anew.",
        },
        "dataset": {
            "title": record["metadata"]["title"],
            "doi": record["metadata"]["doi"],
            "record_url": f"https://zenodo.org/records/{RECORD_ID}",
            "version": "1.2",
            "publication_date": record["metadata"]["publication_date"],
            "creator": record["metadata"]["creators"],
            "license": "CC-BY-4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/",
        },
        "record_metadata_sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
        "coverdata": {
            "url": files["coverdata.json"]["links"]["self"],
            "size": files["coverdata.json"]["size"],
            "published_md5": files["coverdata.json"]["checksum"],
            "actual_hashes": metadata_hashes,
            "published_md5_verified": True,
            "entry": metadata,
        },
        "covers": {
            "url": files["covers.json"]["links"]["self"],
            "size": files["covers.json"]["size"],
            "published_md5": files["covers.json"]["checksum"],
            "actual_full_file_hashes": archive_hashes,
            "published_md5_verified": archive_hashes is not None,
            "entry_byte_range_inclusive": [ENTRY_START, ENTRY_END],
            "fragment_sha256": ENTRY_SHA256,
            "http_range_response": range_response,
        },
        "construction": {"author": "Rade Belic", "date": "1997-08-06", "parameters": [16, 5, 3]},
        "serialization": (
            "archive block order; archive point labels; "
            "one space-separated block per line; trailing newline"
        ),
        "baseline_path": "data/baselines/belic-1997.txt",
        "baseline_sha256": witness_sha256,
        "discovery_report_sha256_matches": True,
        "verification": result,
        "limitations": []
        if archive_hashes
        else [
            "Only the versioned archive entry was fetched; full covers.json MD5 was not checked.",
            "Fragment and witness SHA-256 values are locally computed reproducibility checks.",
        ],
    }
    provenance_dir = REPO / "data/provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    (provenance_dir / "zenodo-c16-5-3.fragment.txt").write_bytes(raw)
    (provenance_dir / "ljcr-c16-5-3.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(
        json.dumps(
            {"mode": mode, "baseline_sha256": witness_sha256, "verification": result}, indent=2
        )
    )


if __name__ == "__main__":
    main()
