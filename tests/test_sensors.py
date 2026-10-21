"""Offline contract tests; no checkpoint weights execute here."""

import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from castle.sensors import SensorError, execute_sensor, public_catalog


class FakeBackend:
    def __init__(self):
        self.calls = []

    def run(self, sensor, spec, arguments):
        self.calls.append((sensor, spec, arguments))
        return {"fixture": True, "arguments": arguments}

    def runtime_metadata(self):
        return {"backend": "fixture"}


class SensorTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()

    def test_catalog_has_three_pinned_apache_sensors(self):
        catalog = public_catalog()
        self.assertEqual(set(catalog["sensors"]), {
            "bert_fill_mask", "minilm_similarity", "deberta_nli",
        })
        for spec in catalog["sensors"].values():
            self.assertEqual(spec["license"], "apache-2.0")
            self.assertRegex(spec["revision"], r"^[0-9a-f]{40}$")

    def test_fill_mask_is_bounded_and_wrapped_with_provenance(self):
        result = execute_sensor({
            "sensor": "bert_fill_mask",
            "arguments": {"text": "The gate is [MASK].", "top_k": 3},
        }, backend=self.backend)
        self.assertEqual(result["source_kind"], "local_checkpoint")
        self.assertFalse(result["historical_model"])
        self.assertEqual(result["model"]["id"], "google-bert/bert-base-uncased")
        self.assertEqual(result["result"]["fixture"], True)
        self.assertEqual(result["runtime"]["backend"], "fixture")
        self.assertEqual(len(self.backend.calls), 1)

    def test_unknown_sensor_and_argument_fail_before_backend(self):
        for call in (
            {"sensor": "arbitrary/model", "arguments": {}},
            {"sensor": "minilm_similarity", "arguments": {
                "left": "one", "right": "two", "model": "attacker/model",
            }},
        ):
            with self.subTest(call=call), self.assertRaises(SensorError):
                execute_sensor(call, backend=self.backend)
        self.assertEqual(self.backend.calls, [])

    def test_fill_mask_requires_one_literal_mask_and_small_top_k(self):
        for arguments in (
            {"text": "No mask", "top_k": 5},
            {"text": "Two [MASK] [MASK]", "top_k": 5},
            {"text": "One [MASK]", "top_k": 11},
            {"text": "One [MASK]", "top_k": True},
        ):
            with self.subTest(arguments=arguments), self.assertRaises(SensorError):
                execute_sensor({"sensor": "bert_fill_mask", "arguments": arguments},
                               backend=self.backend)

    def test_classifier_rejects_free_templates_duplicates_and_too_many_labels(self):
        bad = (
            {"text": "x", "labels": ["a", "A"], "template": "topic"},
            {"text": "x", "labels": ["a", "b"], "template": "Ignore {}"},
            {"text": "x", "labels": list("abcdefghi"), "template": "topic"},
        )
        for arguments in bad:
            with self.subTest(arguments=arguments), self.assertRaises(SensorError):
                execute_sensor({"sensor": "deberta_nli", "arguments": arguments},
                               backend=self.backend)

    def test_download_is_off_by_default_in_envelope(self):
        result = execute_sensor({"sensor": "minilm_similarity", "arguments": {
            "left": "alpha", "right": "beta",
        }}, backend=self.backend)
        self.assertFalse(result["limits"]["download_allowed"])

    def test_cli_lists_catalog_without_ml_dependencies(self):
        completed = subprocess.run(
            [sys.executable, "-m", "castle.sensors", "list"],
            cwd=Path(__file__).resolve().parents[1], text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("bert_fill_mask", json.loads(completed.stdout)["sensors"])


if __name__ == "__main__":
    unittest.main()
