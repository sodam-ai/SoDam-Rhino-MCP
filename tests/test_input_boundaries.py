"""Regression checks for invalid geometry, render input, and saved colors."""

import json
import tempfile
import unittest
from pathlib import Path

import rhino3dm as r3d
from PIL import Image

from sodam_rhino_mcp.model import build_model
from sodam_rhino_mcp.render import render_model


class InputBoundaryTests(unittest.TestCase):
    def test_invalid_geometry_never_writes_3dm(self):
        roof = {"kind": "gable_roof", "name": "roof", "layer": "roof",
                "origin": [0, 0, 0], "size": [4, 3, 1], "ridge_height": 1}
        cases = {
            "zero_roof_depth": {**roof, "size": [4, 3, 0]},
            "unrepresentable_roof_thickness": {**roof, "size": [4, 3, 1e-46]},
            "tiny_box_width": {"kind": "box", "name": "box", "layer": "mass",
                               "origin": [0, 0, 0], "size": [1e-46, 1, 1]},
            "large_relative_width": {"kind": "box", "name": "box", "layer": "mass",
                                     "origin": [1e38, 0, 0], "size": [1, 1, 1]},
            "nan_ridge": {**roof, "ridge_height": float("nan")},
            "string_ridge": {**roof, "ridge_height": "2"},
            "float32_overflow": {"kind": "box", "name": "box", "layer": "mass",
                                 "origin": [1e39, 0, 0], "size": [1, 1, 1]},
            "overflow_vertex": {"kind": "box", "name": "box", "layer": "mass",
                                "origin": [1e308, 0, 0], "size": [1e308, 1, 1]},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, component in cases.items():
                with self.subTest(label=label):
                    spec = root / f"{label}.json"
                    output = root / f"{label}.3dm"
                    spec.write_text(json.dumps({"units": "meters", "components": [component]}), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        build_model(spec, output)
                    self.assertFalse(output.exists())

    def test_invalid_camera_never_writes_png(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "spec.json"
            source.write_text(json.dumps({"units": "meters", "components": [{
                "kind": "box", "name": "mass", "layer": "mass",
                "origin": [0, 0, 0], "size": [2, 2, 2]}]}), encoding="utf-8")
            model = root / "model.3dm"
            build_model(source, model)
            for label, options in {
                "nan": {"azimuth": float("nan")},
                "infinite": {"azimuth": float("inf")},
                "elevation": {"elevation": 91},
                "width_bool": {"width": True},
            }.items():
                with self.subTest(label=label):
                    target = root / f"{label}.png"
                    arguments = {"width": 320, "height": 240}
                    arguments.update(options)
                    with self.assertRaises(ValueError):
                        render_model(model, target, **arguments)
                    self.assertFalse(target.exists())

    def test_corrupt_3dm_mesh_is_rejected_on_inspection(self):
        from sodam_rhino_mcp.model import inspect_model
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = r3d.File3dm()
            mesh = r3d.Mesh()
            for vertex in ((1e39, 0, 0), (0, 1, 0), (0, 0, 1)):
                mesh.Vertices.Add(*vertex)
            mesh.Faces.AddFace(0, 1, 2)
            model.Objects.AddMesh(mesh)
            path = root / "corrupt.3dm"
            self.assertTrue(model.Write(str(path), 8))
            with self.assertRaisesRegex(ValueError, "non-finite mesh vertices"):
                inspect_model(path)
            with self.assertRaisesRegex(ValueError, "non-finite mesh vertices"):
                render_model(path, root / "corrupt.png", width=320, height=240)
            self.assertFalse((root / "corrupt.png").exists())
            from sodam_rhino_mcp.blender_render import export_scene
            with self.assertRaisesRegex(ValueError, "non-finite mesh vertices"):
                export_scene(path)
    def test_object_color_used_without_custom_color_string(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = r3d.File3dm()
            layer = r3d.Layer()
            layer.Name = "Colored"
            layer_index = model.Layers.Add(layer)
            mesh = r3d.Mesh()
            for vertex in ((0, 0, 0), (2, 0, 0), (0, 2, 0)):
                mesh.Vertices.Add(*vertex)
            mesh.Faces.AddFace(0, 1, 2)
            attributes = r3d.ObjectAttributes()
            attributes.Name = "red_triangle"
            attributes.LayerIndex = layer_index
            attributes.ObjectColor = (255, 0, 0, 255)
            attributes.ColorSource = r3d.ObjectColorSource.ColorFromObject
            model.Objects.AddMesh(mesh, attributes)
            source = root / "color.3dm"
            self.assertTrue(model.Write(str(source), 8))
            output = root / "color.png"
            render_model(source, output, azimuth=315, elevation=28, width=320, height=240)
            pixels = list(Image.open(output).convert("RGB").getdata())
            self.assertTrue(any(red > green * 1.4 and red > blue * 1.4
                                for red, green, blue in pixels))


if __name__ == "__main__":
    unittest.main()
