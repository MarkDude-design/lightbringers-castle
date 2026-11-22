"""Offline checks for the staged, scripted Peanut Gallery Castle door.

This is not a historical-checkpoint execution or a browser integration test.
"""
import csv
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PeanutGalleryStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.room = json.loads(
            (ROOT / "castle/rooms/peanut_gallery.json").read_text(encoding="utf-8")
        )
        cls.theater = (ROOT / "castle/scripts/theater.js").read_text(encoding="utf-8")
        with (ROOT / "registry/rooms.csv").open(encoding="utf-8", newline="") as handle:
            cls.registry = list(csv.DictReader(handle))

    def test_registry_matches_room_and_cast(self):
        matching = [row for row in self.registry if row["room_id"] == "peanut_gallery"]
        self.assertEqual(len(matching), 1)
        row = matching[0]
        self.assertEqual(row["description"], self.room["description"])
        self.assertEqual(int(row["bots_count"]), len(self.room["bots_present"]))
        self.assertEqual(row["status"], "active")
        self.assertEqual(len(self.room["bots_present"]), len(set(self.room["bots_present"])))
        for bot in self.room["bots_present"]:
            data = json.loads(
                (ROOT / "castle/bots" / (bot + ".json")).read_text(encoding="utf-8")
            )
            self.assertEqual(data["id"], bot)

    def test_browser_explicitly_lists_room_once(self):
        match = re.search(r"const rooms = \[(.*?)\];", self.theater, flags=re.DOTALL)
        self.assertIsNotNone(match)
        ids = re.findall(r"\{id: '([^']+)'", match.group(1))
        self.assertEqual(ids.count(self.room["id"]), 1)
        self.assertEqual(len(ids), len(set(ids)))

    def test_scripted_room_does_not_pretend_to_have_checkpoint_receipts(self):
        self.assertIn("scripted", self.room["description"].lower())
        self.assertIn("not arrived", self.room["description"].lower())
        self.assertTrue(
            any("SCRIPTED PERFORMANCE" in text for text in self.room["environment_gags"])
        )
        self.assertTrue(
            any("no live historical checkpoints" in text for text in self.room["interactions"])
        )


if __name__ == "__main__":
    unittest.main()
