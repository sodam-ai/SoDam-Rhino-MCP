import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from sodam_rhino_mcp.evidence import (
    build_verified_model,
    draft_evidence_spec,
    prepare_reference_case,
    validate_reference_case,
)


class EvidenceTests(unittest.TestCase):
    def test_reference_to_verified_3dm_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "front.png"
            Image.new("RGB", (640, 480), (210, 220, 230)).save(image)
            packet = root / "reference.json"
            prepare_reference_case([image], {"facade_width": 8.0}, packet)
            source = root / "spec.json"
            source.write_text(json.dumps({"units": "meters", "components": [{
                "kind": "box", "name": "volume", "layer": "massing",
                "origin": [0, 0, 0], "size": [8, 5, 3],
            }]}), encoding="utf-8")
            draft = root / "draft.json"
            result = draft_evidence_spec(source, packet, draft)
            self.assertEqual(result["fields_to_review"], 6)
            spec = json.loads(draft.read_text(encoding="utf-8"))
            spec["components"][0]["field_evidence"]["size.0"] = {
                "status": "given", "source": "facade_width"}
            spec["components"][0]["field_evidence"]["size.2"] = {
                "status": "measured", "source": "front.png"}
            draft.write_text(json.dumps(spec), encoding="utf-8")
            audit = validate_reference_case(draft, packet)
            self.assertEqual(audit["fields"], {"given": 1, "measured": 1, "inferred": 4})
            self.assertFalse(audit["accuracy_verified"])
            self.assertEqual(len(audit["review_required"]), 5)
            self.assertIn("calibration", next(entry["reason"] for entry in audit["review_required"]
                                              if entry["field"] == "volume.size.2"))
            output = root / "verified.3dm"
            self.assertEqual(build_verified_model(draft, packet, output)["evidence_audit"], audit)
            self.assertTrue(output.exists())
            spec["components"][0]["field_evidence"]["size.0"]["source"] = "front.png"
            draft.write_text(json.dumps(spec), encoding="utf-8")
            with self.assertRaises(ValueError):
                build_verified_model(draft, packet, root / "invalid.3dm")
            self.assertFalse((root / "invalid.3dm").exists())
            Image.new("RGB", (640, 480), (0, 0, 0)).save(image)
            with self.assertRaises(ValueError):
                validate_reference_case(draft, packet)

    def test_given_dimension_must_match_value_and_units(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "view.png"
            Image.new("RGB", (50, 50)).save(image)
            packet = root / "packet.json"
            prepare_reference_case([image], {"width": 9}, packet)
            spec = root / "spec.json"
            spec.write_text(json.dumps({"units": "feet", "components": [{
                "kind": "box", "name": "x", "layer": "l", "origin": [0, 0, 0],
                "size": [8, 5, 3]}]}), encoding="utf-8")
            draft = root / "draft.json"
            draft_evidence_spec(spec, packet, draft)
            with self.assertRaisesRegex(ValueError, "units differ"):
                validate_reference_case(draft, packet)
            data = json.loads(draft.read_text(encoding="utf-8"))
            data["units"] = "meters"
            data["components"][0]["field_evidence"]["size.0"] = {"status": "given", "source": "width"}
            draft.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "does not match"):
                validate_reference_case(draft, packet)


if __name__ == "__main__":
    unittest.main()
