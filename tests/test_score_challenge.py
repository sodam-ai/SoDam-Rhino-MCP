"""Behavioral checks for geometry-based challenge scoring."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

import rhino3dm as r3d

from scripts.score_challenge import score
from sodam_rhino_mcp.model import build_model

TRUTH = {
    "units": "meters", "reference_mode": "single_perspective_with_occlusion",
    "width": 10.0, "depth": 8.0, "wall_height": 3.0, "roof_height": 1.5,
    "door_left": 3.5, "door_width": 1.5,
    "wing": {"x": 1.0, "width": 4.0, "projection": 2.0, "height": 2.5},
}

COMPONENTS = [
    {"kind": "box", "name": "main_volume", "layer": "massing",
     "origin": [0, 0, 0.25], "size": [10, 8, 3]},
    {"kind": "gable_roof", "name": "main_roof", "layer": "roof",
     "origin": [-0.3, -0.3, 3.25], "size": [10.6, 8.6, 0.1],
     "ridge_height": 1.5},
    {"kind": "box", "name": "front_wing", "layer": "massing",
     "origin": [1, -2, 0.25], "size": [4, 2, 2.5]},
    {"kind": "box", "name": "front_door", "layer": "openings",
     "origin": [3.5, -0.05, 0.25], "size": [1.5, 0.05, 2.2]},
]


class ChallengeScoringTests(unittest.TestCase):
    def test_score_reads_saved_geometry_not_changed_spec(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "reconstruction.json"
            model = root / "reconstruction.3dm"
            spec = {"units": "meters", "components": copy.deepcopy(COMPONENTS)}
            source.write_text(json.dumps(spec), encoding="utf-8")
            build_model(source, model)
            before = score(TRUTH, model)
            self.assertEqual(before["measurement_source"], "saved_3dm_mesh_vertices")
            self.assertEqual(before["inferred_mean_absolute_error_m"], 0)
            spec["components"][0]["size"][0] = 1000
            source.write_text(json.dumps(spec), encoding="utf-8")
            self.assertEqual(score(TRUTH, model), before)

            altered = root / "altered.3dm"
            build_model(source, altered)
            self.assertEqual(score(TRUTH, altered)["known_width_error_m"], 990)

    def test_duplicate_mesh_name_cannot_be_scored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "spec.json"
            model = root / "model.3dm"
            duplicate = root / "duplicate.3dm"
            source.write_text(json.dumps({"units": "meters", "components": COMPONENTS}),
                              encoding="utf-8")
            build_model(source, model)
            archive = r3d.File3dm.Read(str(model))
            item = next(iter(archive.Objects))
            archive.Objects.AddMesh(item.Geometry, item.Attributes)
            self.assertTrue(archive.Write(str(duplicate), 8))
            with self.assertRaisesRegex(ValueError, "duplicate object names"):
                score(TRUTH, duplicate)

    def test_missing_component_cannot_be_scored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "incomplete.json"
            model = root / "incomplete.3dm"
            source.write_text(json.dumps({
                "units": "meters", "components": [COMPONENTS[0]]
            }), encoding="utf-8")
            build_model(source, model)
            with self.assertRaisesRegex(ValueError, "missing objects"):
                score(TRUTH, model)


if __name__ == "__main__":
    unittest.main()
