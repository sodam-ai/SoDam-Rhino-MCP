import json
import tempfile
import unittest
from pathlib import Path

import rhino3dm as r3d

from sodam_rhino_mcp.model import build_model
from sodam_rhino_mcp.revision import revise_spec


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "v1.json"
        original = Path(__file__).parents[1] / "examples" / "small_house.json"
        self.source.write_bytes(original.read_bytes())
        self.spec = json.loads(self.source.read_text(encoding="utf-8"))
        self.target = self.root / "v2.json"
        self.part = next(p for p in self.spec["components"] if p["name"] == "roof")

    def test_revision_preserves_other_parts_and_generates_reopenable_model(self):
        original_bytes = self.source.read_bytes()
        replacement = {**self.part, "ridge_height": 2.2}
        result = revise_spec(self.source, "roof", json.dumps(replacement), self.target)
        revised = json.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(result["revised_component"], "roof")
        self.assertEqual(self.source.read_bytes(), original_bytes)
        self.assertEqual(revised["components"][:-1], self.spec["components"][:-1])
        self.assertEqual(revised["components"][-1]["ridge_height"], 2.2)
        first = self.root / "v1.3dm"
        second = self.root / "v2.3dm"
        before = build_model(self.source, first)
        after = build_model(self.target, second)
        self.assertEqual(before["objects"], after["objects"])
        self.assertAlmostEqual(after["bbox"]["max"][2] - before["bbox"]["max"][2], 0.3, places=5)
        model = r3d.File3dm.Read(str(second))
        self.assertIsNotNone(model)
        self.assertTrue(any(o.Attributes.GetUserString("source_component") == "roof"
                            and json.loads(o.Attributes.GetUserString("control_json"))["ridge_height"] == 2.2
                            for o in model.Objects))

    def test_failure_cases_do_not_create_output(self):
        variants = [
            ("missing", json.dumps(self.part), ValueError),
            ("roof", json.dumps({**self.part, "name": "other"}), ValueError),
            ("roof", json.dumps({**self.part, "ridge_height": -1}), ValueError),
            ("roof", "{", ValueError),
            ("roof", json.dumps({**self.part, "ridge_height": float("nan")}), ValueError),
            ("roof", json.dumps({**self.part, "field_evidence": {}}), ValueError),
            ("roof", " " * 2_000_001, ValueError),
        ]
        for index, (name, content, error) in enumerate(variants):
            with self.subTest(index=index):
                output = self.root / f"bad_{index}.json"
                with self.assertRaises(error):
                    revise_spec(self.source, name, content, output)
                self.assertFalse(output.exists())
        with self.assertRaises(FileExistsError):
            revise_spec(self.source, "roof", json.dumps(self.part), self.source)
        self.assertFalse(self.target.exists())

    def test_refuses_stale_photo_evidence(self):
        self.spec["reference_packet"] = "references.json"
        self.source.write_text(json.dumps(self.spec), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "evidence review"):
            revise_spec(self.source, "roof", json.dumps(self.part), self.target)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
