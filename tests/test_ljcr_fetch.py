"""Offline controls for archive extraction and the checksum trust boundary."""

import hashlib
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fetch_ljcr", ROOT / "scripts/fetch_ljcr.py")
fetcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetcher)


def source_fragment():
    return (ROOT / "data/provenance/zenodo-c16-5-3.fragment.txt").read_bytes()


def test_pinned_extract_retains_every_block(tmp_path):
    fragment = source_fragment()
    prefix = b'{\n"C(4,3,2)": [[1,2,3]],\n'
    archive = tmp_path / "covers.json"
    archive.write_bytes(prefix + fragment + b'"next": []\n}\n')
    with patch.object(fetcher, "ENTRY_START", len(prefix)):
        assert fetcher.extract_entry(archive) == fragment
    blocks = fetcher.json.loads(b"{" + fragment.rstrip().rstrip(b",") + b"}")[fetcher.KEY]
    assert fetcher.validate(blocks)["covered_triples"] == 560


def test_mutated_fragment_fails_checksum(tmp_path):
    prefix = b"{\n"
    archive = tmp_path / "covers.json"
    fragment = source_fragment().replace(b"[1,2,3,4,6]", b"[1,2,3,4,7]")
    archive.write_bytes(prefix + fragment + b"}\n")
    with patch.object(fetcher, "ENTRY_START", len(prefix)):
        with pytest.raises(ValueError, match="fragment SHA-256 mismatch"):
            fetcher.extract_entry(archive)


def test_verified_cache_needs_no_network(tmp_path):
    payload = b'{"fixture": true}\n'
    cached = tmp_path / "coverdata.json"
    cached.write_bytes(payload)
    item = {
        "key": cached.name,
        "size": len(payload),
        "checksum": "md5:" + hashlib.md5(payload).hexdigest(),
        "links": {"self": "https://example.invalid/never-requested"},
    }
    with patch.object(fetcher.urllib.request, "urlopen", side_effect=AssertionError("network")):
        path, hashes = fetcher.fetch_file(item, tmp_path, timeout=1)
    assert path == cached
    assert hashes["sha256"] == hashlib.sha256(payload).hexdigest()


def test_server_ignoring_range_is_rejected(tmp_path):
    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

    item = {"size": 4_191_522_340, "links": {"self": "https://example.invalid/covers.json"}}
    with patch.object(fetcher.urllib.request, "urlopen", return_value=Response()):
        with pytest.raises(ValueError, match="did not honor"):
            fetcher.fetch_entry(item, tmp_path)
