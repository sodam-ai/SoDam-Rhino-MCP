"""The agent can select a real renderer from reported workspace capabilities."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sodam_rhino_mcp.server import get_architectural_workspace


class WorkspaceCapabilityTests(unittest.TestCase):
    def test_reports_configured_blender_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            blender = Path(directory) / "blender.exe"
            blender.write_bytes(b"fixture")
            with patch.dict(os.environ, {"SODAM_BLENDER_EXE": str(blender)}):
                self.assertTrue(get_architectural_workspace()["blender_executable_configured"])

    def test_missing_blender_is_reported_without_claiming_render_support(self):
        with patch.dict(os.environ, {"SODAM_BLENDER_EXE": "C:/not-installed/blender.exe"}):
            self.assertFalse(get_architectural_workspace()["blender_executable_configured"])
