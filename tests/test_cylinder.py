import json
import tempfile
import unittest
from pathlib import Path

import rhino3dm as r3d

from sodam_rhino_mcp.model import build_model
from sodam_rhino_mcp.render import render_model


class CylinderTests(unittest.TestCase):
    def _spec(self, **changes):
        component = {"kind": "cylinder", "name": "column_A", "layer": "Columns",
                     "origin": [1, 2, 0.25], "size": [0.6, 0.6, 3.2],
                     "segments": 48, "evidence": "given"}
        component.update(changes)
        return {"units": "meters", "components": [component]}

    def test_column_roundtrip_closed_and_rendered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "column.json", root / "column.3dm"
            source.write_text(json.dumps(self._spec()), encoding="utf-8")
            summary = build_model(source, output)
            self.assertEqual(summary["objects"], 1)
            self.assertIn("Columns", summary["layers"])
            self.assertAlmostEqual(summary["bbox"]["min"][0], 1.0, places=5)
            self.assertAlmostEqual(summary["bbox"]["max"][2], 3.45, places=5)
            model = r3d.File3dm.Read(str(output))
            mesh = next(iter(model.Objects)).Geometry
            self.assertEqual(len(mesh.Vertices), 98)
            self.assertEqual(len(mesh.Faces), 144)
            edge_counts = {}
            for face in mesh.Faces:
                points = list(face)
                if points[-1] == points[-2]:
                    points.pop()
                for start, end in zip(points, points[1:] + points[:1]):
                    edge = tuple(sorted((start, end)))
                    edge_counts[edge] = edge_counts.get(edge, 0) + 1
            self.assertTrue(all(count == 2 for count in edge_counts.values()))
            self.assertGreater(render_model(output, root / "column.png")["faces"], 0)

    def test_segment_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for count in (12, 256):
                with self.subTest(segments=count):
                    source, output = root / f"column_{count}.json", root / f"column_{count}.3dm"
                    source.write_text(json.dumps(self._spec(segments=count)), encoding="utf-8")
                    build_model(source, output)
                    mesh = next(iter(r3d.File3dm.Read(str(output)).Objects)).Geometry
                    self.assertEqual(len(mesh.Faces), 3 * count)

    def test_bad_column_rejected_without_output(self):
        invalid = [
            {"size": [0.6, 0.8, 3.2]},
            {"size": [0, 0, 3.2]},
            {"segments": True},
            {"segments": 11},
            {"segments": 257},
            {"segments": 48.5},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, change in enumerate(invalid):
                with self.subTest(change=change):
                    source, output = root / f"bad{index}.json", root / f"bad{index}.3dm"
                    source.write_text(json.dumps(self._spec(**change)), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        build_model(source, output)
                    self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
