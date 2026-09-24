"""Failure after file writing must not leave a deliverable behind."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sodam_rhino_mcp.blend_import import import_blend
from sodam_rhino_mcp.model import build_model


class OutputCommitTests(unittest.TestCase):
    def test_build_reopen_failure_leaves_no_3dm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Path(__file__).parents[1] / "examples" / "small_house.json"
            output = root / "house.3dm"
            with (patch("sodam_rhino_mcp.model.inspect_model", side_effect=ValueError("reopen failed")),
                  self.assertRaisesRegex(ValueError, "reopen failed")):
                build_model(source, output)
            self.assertFalse(output.exists())

    def test_blend_import_reopen_failure_leaves_no_3dm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "house.blend"
            source.write_bytes(b"fixture")
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")
            output = root / "house.3dm"
            payload = {
                "parts": [{
                    "name": "wall", "layer": "Walls", "material": "White",
                    "color": [200, 200, 200],
                    "vertices": [[0, 0, 0], [2, 0, 0], [0, 2, 0]],
                    "faces": [[0, 1, 2]],
                }],
                "source_units": "METRIC", "scene_scale_length": 1.0,
            }

            def fake_blender(command, **_kwargs):
                Path(command[-1]).write_text(json.dumps(payload), encoding="utf-8")
                return subprocess.CompletedProcess(command, 0, "", "")

            with (patch("sodam_rhino_mcp.blend_import.subprocess.run", side_effect=fake_blender),
                  patch("sodam_rhino_mcp.blend_import.inspect_model", side_effect=ValueError("reopen failed")),
                  self.assertRaisesRegex(ValueError, "reopen failed")):
                import_blend(source, output, blender)
            self.assertFalse(output.exists())
