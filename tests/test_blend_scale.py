"""Check Blender unit conversion before a 3DM file is written."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sodam_rhino_mcp.blend_import import import_blend


class BlendScaleTests(unittest.TestCase):
    def test_normal_scale_roundtrip_and_overflow_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "scene.blend"
            blender = root / "blender.exe"
            source.write_bytes(b"fixture")
            blender.write_bytes(b"fixture")
            payload = {"parts": [{
                "name": "column", "layer": "Columns", "material": "red",
                "color": [240, 20, 10], "vertices": [[4, 0, 0], [5, 0, 0], [4, 1, 0]],
                "faces": [[0, 1, 2]],
            }], "source_units": "METRIC", "scene_scale_length": 1.0}

            def fake_blender(command, **_kwargs):
                Path(command[-1]).write_text(json.dumps(payload), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("sodam_rhino_mcp.blend_import.subprocess.run", side_effect=fake_blender):
                normal = import_blend(source, root / "normal.3dm", blender)
                self.assertEqual(normal["layers"], ["Columns"])
                self.assertEqual(normal["bbox"]["max"][0], 5.0)
                self.assertEqual(normal["unit_source"], "Blender scene unit scale")
                for scale in (1e39, 1e308):
                    with self.subTest(scale=scale):
                        overflow_target = root / f"overflow_{scale}.3dm"
                        with self.assertRaises(ValueError):
                            import_blend(source, overflow_target, blender, scale)
                        self.assertFalse(overflow_target.exists())
                payload["parts"][0]["vertices"] = [[0, 0, 0], [1e-46, 0, 0], [0, 1, 0]]
                tiny_target = root / "tiny.3dm"
                with self.assertRaises(ValueError):
                    import_blend(source, tiny_target, blender)
                self.assertFalse(tiny_target.exists())


if __name__ == "__main__":
    unittest.main()
