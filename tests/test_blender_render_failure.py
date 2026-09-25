import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from sodam_rhino_mcp.blender_render import render_blender_views
from sodam_rhino_mcp.model import build_model


class BlenderRenderFailureTests(unittest.TestCase):
    def test_failed_blender_leaves_no_partial_deliverable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "house.json"
            spec.write_text((Path(__file__).parents[1] / "examples" / "small_house.json").read_text(encoding="utf-8"), encoding="utf-8")
            model = root / "house.3dm"
            build_model(spec, model)
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")
            output = root / "render"

            def failed_run(command, **_kwargs):
                stage = Path(command[-1])
                stage.mkdir(parents=True, exist_ok=True)
                (stage / "front.png").write_bytes(b"incomplete")
                return subprocess.CompletedProcess(command, 1, "", "render failed")

            with patch("sodam_rhino_mcp.blender_render.subprocess.run", side_effect=failed_run), self.assertRaises(RuntimeError):
                render_blender_views(model, output, blender)
            self.assertFalse((output / "front.png").exists())
            self.assertFalse((output / "rear.png").exists())
            self.assertFalse((output / "scene.blend").exists())

    def test_blender_timeout_leaves_no_partial_deliverable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "house.json"
            spec.write_text(
                (Path(__file__).parents[1] / "examples" / "small_house.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            model = root / "house.3dm"
            build_model(spec, model)
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")
            output = root / "render"

            def timed_out(command, **_kwargs):
                (Path(command[-1]) / "front.png").write_bytes(b"incomplete")
                raise subprocess.TimeoutExpired(command, 90)

            with patch("sodam_rhino_mcp.blender_render.subprocess.run", side_effect=timed_out), self.assertRaises(subprocess.TimeoutExpired):
                render_blender_views(model, output, blender)
            self.assertFalse((output / "front.png").exists())
            self.assertFalse((output / "rear.png").exists())
            self.assertFalse((output / "scene.blend").exists())

    def test_invalid_cameras_leave_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "house.json"
            spec.write_text(
                (Path(__file__).parents[1] / "examples" / "small_house.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            model = root / "house.3dm"
            build_model(spec, model)
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")
            for camera_args in (
                {"front_azimuth": float("nan")},
                {"front_elevation": 90.1},
                {"rear_azimuth": True},
                {"front_azimuth": 315, "rear_azimuth": -45},
                {"front_azimuth": 10, "rear_azimuth": 10, "front_elevation": 20, "rear_elevation": 20},
                {"front_azimuth": 0, "rear_azimuth": 180, "front_elevation": 90, "rear_elevation": 90},
                {"front_azimuth": 10, "rear_azimuth": 15},
                {"front_azimuth": 10 ** 1000},
            ):
                with self.subTest(camera_args=camera_args):
                    with patch("sodam_rhino_mcp.blender_render.subprocess.run") as run:
                        with self.assertRaises(ValueError):
                            render_blender_views(model, root / "render", blender, **camera_args)
                        run.assert_not_called()
                    self.assertFalse((root / "render").exists())

    def test_custom_cameras_reach_blender_payload(self):
        import json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "house.json"
            spec.write_text(
                (Path(__file__).parents[1] / "examples" / "small_house.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            model = root / "house.3dm"
            build_model(spec, model)
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")
            captured = {}

            def successful_run(command, **_kwargs):
                stage = Path(command[-1])
                captured.update(json.loads((stage / "scene.json").read_text(encoding="utf-8"))["cameras"])
                for name in ("front.png", "rear.png"):
                    image = Image.new("RGB", (20, 20), "white")
                    image.paste("black", (0, 0, 10, 20))
                    image.save(stage / name)
                (stage / "scene.blend").write_bytes(b"generated")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("sodam_rhino_mcp.blender_render.subprocess.run", side_effect=successful_run):
                result = render_blender_views(
                    model, root / "render", blender,
                    front_azimuth=300, front_elevation=32,
                    rear_azimuth=120, rear_elevation=20,
                )
            expected = {
                "front": {"azimuth": 300, "elevation": 32},
                "rear": {"azimuth": 120, "elevation": 20},
            }
            self.assertEqual(captured, expected)
            self.assertEqual(result["cameras"], expected)
            for name in ("front.png", "rear.png"):
                self.assertTrue((root / "render" / name).is_file())
            self.assertEqual((root / "render" / "scene.blend").read_bytes(), b"generated")

    def test_visible_low_contrast_image_is_delivered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / "house.3dm"
            build_model(Path(__file__).parents[1] / "examples" / "small_house.json", model)
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")

            def low_contrast_run(command, **_kwargs):
                stage = Path(command[-1])
                for name in ("front.png", "rear.png"):
                    image = Image.new("RGB", (128, 128), (100, 100, 100))
                    image.paste((108, 108, 108), (32, 32, 96, 96))
                    image.save(stage / name)
                (stage / "scene.blend").write_bytes(b"generated")
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch("sodam_rhino_mcp.blender_render.subprocess.run", side_effect=low_contrast_run):
                result = render_blender_views(model, root / "render", blender)
            self.assertTrue(Path(result["front"]).is_file())
            self.assertTrue(Path(result["rear"]).is_file())

    def test_isolated_pixel_noise_does_not_count_as_visible_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            model = root / "house.3dm"
            build_model(Path(__file__).parents[1] / "examples" / "small_house.json", model)
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")

            def noisy_run(command, **_kwargs):
                stage = Path(command[-1])
                for name in ("front.png", "rear.png"):
                    image = Image.new("RGB", (256, 256), (100, 100, 100))
                    image.putpixel((128, 128), (255, 255, 255))
                    image.save(stage / name)
                (stage / "scene.blend").write_bytes(b"generated")
                return subprocess.CompletedProcess(command, 0, "", "")

            with (patch("sodam_rhino_mcp.blender_render.subprocess.run", side_effect=noisy_run),
                  self.assertRaisesRegex(RuntimeError, "blank image")):
                render_blender_views(model, root / "render", blender)
            self.assertFalse((root / "render").exists())

    def test_blank_blender_image_leaves_no_partial_deliverable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = root / "house.json"
            spec.write_text(
                (Path(__file__).parents[1] / "examples" / "small_house.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            model = root / "house.3dm"
            build_model(spec, model)
            blender = root / "blender.exe"
            blender.write_bytes(b"fixture")
            output = root / "render"

            def blank_run(command, **_kwargs):
                stage = Path(command[-1])
                Image.new("RGB", (20, 20), "gray").save(stage / "front.png")
                Image.new("RGB", (20, 20), "gray").save(stage / "rear.png")
                (stage / "scene.blend").write_bytes(b"generated")
                return subprocess.CompletedProcess(command, 0, "", "")

            with (patch("sodam_rhino_mcp.blender_render.subprocess.run", side_effect=blank_run),
                  self.assertRaisesRegex(RuntimeError, "blank image")):
                render_blender_views(model, output, blender)
            self.assertFalse(output.exists())
