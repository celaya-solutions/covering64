"""Fresh negative-control tests for the rebuilt independent checker."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_cover.py"
SPEC = importlib.util.spec_from_file_location("independent_check_cover", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class IndependentCheckerTests(unittest.TestCase):
    def test_exhaustive_multiplicities(self):
        result = checker.verify_cover([[1, 2], [1, 3]], v=3, k=2, t=1)
        self.assertTrue(result["valid"])
        self.assertEqual(result["coverage_multiplicities"], {1: 2, 2: 1})
        self.assertEqual(result["total_subset_incidences"], 4)
        self.assertEqual(result["required_subsets"], 3)

    def test_missing_subset_is_failure(self):
        result = checker.verify_cover([[1, 2]], v=3, k=2, t=1)
        self.assertFalse(result["valid"])
        self.assertEqual(result["uncovered"], [[3]])
        self.assertEqual(result["coverage_multiplicities"], {0: 1, 1: 2})

    def test_rejects_duplicate_permuted_blocks_and_labels(self):
        for blocks in ([[1, 2], [2, 1]], [[1, 1]], [[0, 1]], [[1, 4]], [[1]]):
            with self.subTest(blocks=blocks):
                with self.assertRaises(checker.InvalidWitness):
                    checker.verify_cover(blocks, v=3, k=2, t=1)

    def test_json_labels_are_not_coerced(self):
        for label in (True, False, 1.0, "1", None):
            with self.subTest(label=label):
                blocks = checker.parse_witness(json.dumps([[label, 2]]))
                with self.assertRaises(checker.InvalidWitness):
                    checker.verify_cover(blocks, v=3, k=2, t=1)

    def test_canonical_hash_ignores_order_but_preserves_labels(self):
        one = checker.verify_cover([[1, 2], [1, 3]], v=3, k=2, t=1)
        two = checker.verify_cover([[3, 1], [2, 1]], v=3, k=2, t=1)
        three = checker.verify_cover([[1, 2], [2, 3]], v=3, k=2, t=1)
        self.assertEqual(one["canonical_sha256"], two["canonical_sha256"])
        self.assertNotEqual(one["canonical_sha256"], three["canonical_sha256"])

    def test_cli_cardinality_and_source_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            witness = Path(directory) / "cover.txt"
            witness.write_text("1 2\n1 3\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(witness), "--v", "3", "--k", "2",
                 "--t", "1", "--expected-blocks", "1"],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertTrue(report["covers_all_subsets"])
        self.assertFalse(report["cardinality_matches"])
        self.assertEqual(len(report["source_sha256"]), 64)

    def test_cli_malformed_json_emits_error(self):
        with tempfile.TemporaryDirectory() as directory:
            witness = Path(directory) / "cover.json"
            witness.write_text('[[true, 2]]', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(witness), "--v", "3", "--k", "2",
                 "--t", "1"], capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("integer", json.loads(result.stdout)["error"])


if __name__ == "__main__":
    unittest.main()
