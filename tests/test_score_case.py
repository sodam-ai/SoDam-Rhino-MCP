"""Validate frozen case scoring and failure isolation."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import rhino3dm as r3d
from PIL import Image

from scripts.score_case import score_case


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_case(folder: Path, *, units: r3d.UnitSystem = r3d.UnitSystem.Meters) -> dict:
    model = r3d.File3dm()
    model.Settings.ModelUnitSystem = units
    mesh = r3d.Mesh()
    for vertex in ((1, 2, 0), (3, 2, 0), (1, 4, 0)):
        mesh.Vertices.Add(*vertex)
    mesh.Faces.AddFace(0, 1, 2)
    attributes = r3d.ObjectAttributes()
    attributes.Name = "mass"
    model.Objects.AddMesh(mesh, attributes)
    model_path = folder / "model.3dm"
    if not model.Write(str(model_path), 8):
        raise OSError("test model write failed")
    image_path = folder / "photo.png"
    Image.new("RGB", (8, 8), "white").save(image_path)
    manifest = {
        "schema_version": 1, "case_type": "synthetic",
        "model": {"file": model_path.name, "sha256": digest(model_path)},
        "references": [{"file": image_path.name, "sha256": digest(image_path)}],
        "measurements": [
            {"name": "width", "object": "mass", "axis": "x", "quantity": "extent",
             "truth_m": 2, "tolerance_m": 0.01, "visibility": "given",
             "truth_source": "independent test fixture"},
            {"name": "left_offset", "object": "mass", "axis": "x", "quantity": "min",
             "relative_to": "mass", "relative_edge": "max", "truth_m": -2,
             "tolerance_m": 0.01, "visibility": "hidden",
             "truth_source": "independent test fixture"},
        ],
    }
    (folder / "case_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


class CaseScoringTests(unittest.TestCase):
    def test_pass_and_failed_tolerance_are_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            manifest = make_case(folder)
            passed = score_case(folder / "case_manifest.json")
            self.assertEqual(passed["measurements_within_tolerance"], 2)
            self.assertEqual(passed["comparison"][1]["relative_edge"], "max")
            self.assertFalse(passed["photo_shape_match_verified"])
            self.assertFalse(passed["independent_3dm_reader_verified"])
            manifest["measurements"][0]["truth_m"] = 2.5
            (folder / "case_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            failed = score_case(folder / "case_manifest.json")
            self.assertEqual(failed["measurements_within_tolerance"], 1)
            self.assertFalse(failed["all_measured_dimensions_within_tolerance"])

    def test_hashes_and_invalid_images_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            manifest = make_case(folder)
            (folder / "photo.png").write_bytes(b"not a PNG")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                score_case(folder / "case_manifest.json")
            manifest["references"][0]["sha256"] = digest(folder / "photo.png")
            (folder / "case_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unreadable reference image"):
                score_case(folder / "case_manifest.json")

    def test_truncated_jpeg_and_excessive_pixel_count_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            manifest = make_case(folder)
            jpg = folder / "photo.jpg"
            Image.new("RGB", (100, 100), "white").save(jpg)
            jpg.write_bytes(jpg.read_bytes()[:-20])
            manifest["references"] = [{"file": "photo.jpg", "sha256": digest(jpg)}]
            (folder / "case_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unreadable reference image"):
                score_case(folder / "case_manifest.json")
            manifest["references"] = [{"file": "photo.png", "sha256": digest(folder / "photo.png")}]
            (folder / "case_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with (patch.object(Image, "MAX_IMAGE_PIXELS", 16),
                  self.assertRaisesRegex(ValueError, "unreadable reference image")):
                score_case(folder / "case_manifest.json")

    def test_invalid_and_boundary_inputs_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            original = make_case(folder)
            variants = []
            for key, value in [("schema_version", True), ("case_type", "unknown")]:
                case = json.loads(json.dumps(original))
                case[key] = value
                variants.append(case)
            for value in [-0.01, float("nan"), 10**1000]:
                case = json.loads(json.dumps(original))
                case["measurements"][0]["tolerance_m"] = value
                variants.append(case)
            for name in ["../model.3dm", "C:/model.3dm"]:
                case = json.loads(json.dumps(original))
                case["model"]["file"] = name
                variants.append(case)
            case = json.loads(json.dumps(original))
            case["measurements"][1]["name"] = "width"
            variants.append(case)
            for field, value in [("object", []), ("axis", []), ("relative_to", [])]:
                case = json.loads(json.dumps(original))
                case["measurements"][1][field] = value
                variants.append(case)
            for case in variants:
                (folder / "case_manifest.json").write_text(json.dumps(case), encoding="utf-8")
                with self.assertRaises((ValueError, TypeError)):
                    score_case(folder / "case_manifest.json")

    def test_wrong_units_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            make_case(folder, units=r3d.UnitSystem.Millimeters)
            with self.assertRaisesRegex(ValueError, "meters"):
                score_case(folder / "case_manifest.json")
            make_case(folder)
            command = [sys.executable, "-m", "scripts.score_case", str(folder)]
            first = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(first.returncode, 0, first.stderr)
            score = folder / "case_score.json"
            initial = score.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(score.read_bytes(), initial)
            self.assertFalse(list(folder.glob(".case_score_*.tmp")))


if __name__ == "__main__":
    unittest.main()
