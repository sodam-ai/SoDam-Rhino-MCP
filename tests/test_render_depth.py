import json
import tempfile
import unittest
from pathlib import Path

from sodam_rhino_mcp.model import build_model
from sodam_rhino_mcp.render import render_model


class DepthRenderTests(unittest.TestCase):
    def test_overlapping_objects_render_independently_of_component_order(self):
        far = {"kind": "box", "name": "far", "layer": "a", "origin": [0, 0, 0],
               "size": [2, 2, 2], "color": [25, 75, 220]}
        near = {"kind": "box", "name": "near", "layer": "b", "origin": [0.3, 0.4, 0.5],
                "size": [2, 2, 2], "color": [220, 50, 25]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, components in enumerate(([far, near], [near, far])):
                spec = root / f"input_{index}.json"
                spec.write_text(json.dumps({"units": "meters", "components": components}), encoding="utf-8")
                model = root / f"model_{index}.3dm"
                output = root / f"view_{index}.png"
                build_model(spec, model)
                render_model(model, output, width=640, height=480, azimuth=45, elevation=30)
            self.assertEqual((root / "view_0.png").read_bytes(), (root / "view_1.png").read_bytes())


if __name__ == "__main__":
    unittest.main()
