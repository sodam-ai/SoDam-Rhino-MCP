import tempfile
import unittest
from pathlib import Path

from sodam_rhino_mcp.blend_import import import_blend


class BlendImportTests(unittest.TestCase):
    def test_invalid_inputs_do_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sample.blend"
            source.write_bytes(b"placeholder")
            output = root / "sample.3dm"
            for scale in (0, -1, float("nan"), float("inf")):
                with self.subTest(scale=scale), self.assertRaises(ValueError):
                    import_blend(source, output, root / "blender.exe", scale)
            self.assertFalse(output.exists())
            with self.assertRaises(FileNotFoundError):
                import_blend(source, output, root / "blender.exe")
            self.assertFalse(output.exists())

    def test_overwrite_is_refused_before_blender_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.blend").write_bytes(b"placeholder")
            output = root / "sample.3dm"
            output.write_bytes(b"original")
            with self.assertRaises(FileExistsError):
                import_blend(root / "sample.blend", output)
            self.assertEqual(output.read_bytes(), b"original")


if __name__ == "__main__":
    unittest.main()
