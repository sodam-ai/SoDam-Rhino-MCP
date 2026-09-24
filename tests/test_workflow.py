import json
import tempfile
import unittest
from pathlib import Path

import rhino3dm as r3d

from sodam_rhino_mcp.model import build_model
from sodam_rhino_mcp.render import render_model


class WorkflowTests(unittest.TestCase):
    def test_round_trip_and_two_views(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "house.json"
            spec.write_text((Path(__file__).parents[1] / "examples" / "small_house.json").read_text(encoding="utf-8"), encoding="utf-8")
            output = root / "house.3dm"
            summary = build_model(spec, output)
            self.assertGreater(summary["objects"], 8)
            self.assertAlmostEqual(summary["bbox"]["max"][2], 5.35, places=5)
            self.assertIn("02_Walls", summary["layers"])
            opened = r3d.File3dm.Read(str(output))
            self.assertIsNotNone(opened)
            evidence = {o.Attributes.GetUserString("evidence") for o in opened.Objects}
            self.assertEqual(evidence, {"given", "inferred"})
            main = root / "main.png"
            secondary = root / "secondary.png"
            self.assertGreater(render_model(output, main)["faces"], 30)
            render_model(output, secondary, azimuth=215)
            self.assertNotEqual(main.read_bytes(), secondary.read_bytes())
            with self.assertRaises(FileExistsError):
                build_model(spec, output)

    def test_gable_roof_thickness_changes_closed_saved_mesh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            models = []
            for thickness in (0.1, 0.8):
                spec = root / f"roof_{thickness}.json"
                spec.write_text(json.dumps({"units": "meters", "components": [{
                    "kind": "gable_roof", "name": "roof", "layer": "roof",
                    "origin": [0, 0, 3], "size": [4, 6, thickness],
                    "ridge_height": 2,
                }]}), encoding="utf-8")
                output = root / f"roof_{thickness}.3dm"
                summary = build_model(spec, output)
                models.append(summary)
                mesh = next(iter(r3d.File3dm.Read(str(output)).Objects)).Geometry
                self.assertEqual(len(mesh.Vertices), 10)
                edge_counts = {}
                for face in mesh.Faces:
                    points = list(face)
                    if points[-1] == points[-2]:
                        points.pop()
                    for start, end in zip(points, points[1:] + points[:1]):
                        edge = tuple(sorted((start, end)))
                        edge_counts[edge] = edge_counts.get(edge, 0) + 1
                self.assertTrue(edge_counts)
                self.assertTrue(all(count == 2 for count in edge_counts.values()))
            self.assertAlmostEqual(models[0]["bbox"]["min"][2], 2.9, places=5)
            self.assertAlmostEqual(models[1]["bbox"]["min"][2], 2.2, places=5)
            self.assertAlmostEqual(models[0]["bbox"]["max"][2], models[1]["bbox"]["max"][2], places=5)

    def test_bad_opening_does_not_create_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "bad.json"
            spec.write_text(json.dumps({"units": "meters", "components": [{
                "kind": "wall_opening", "name": "wall", "layer": "walls", "origin": [0, 0, 0],
                "size": [4, 0.2, 3], "axis": "x", "opening": {
                    "start_bottom": [3.5, 0], "size": [1, 2]
                }
            }]}), encoding="utf-8")
            output = root / "bad.3dm"
            with self.assertRaises(ValueError):
                build_model(spec, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
