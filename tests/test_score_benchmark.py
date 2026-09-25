"""Reject ambiguous or incorrectly scaled 3DM benchmark submissions."""

import tempfile
import unittest
from pathlib import Path

import rhino3dm as r3d

from scripts.score_benchmark import mesh_bounds


def write_model(path: Path, *, units: r3d.UnitSystem = r3d.UnitSystem.Meters,
                duplicate: bool = False, point: bool = False) -> None:
    model = r3d.File3dm()
    model.Settings.ModelUnitSystem = units
    mesh = r3d.Mesh()
    for vertex in ((0, 0, 0), (1, 0, 0), (0, 1, 0)):
        mesh.Vertices.Add(*vertex)
    mesh.Faces.AddFace(0, 1, 2)
    attributes = r3d.ObjectAttributes()
    attributes.Name = "mass"
    model.Objects.AddMesh(mesh, attributes)
    if duplicate:
        model.Objects.AddMesh(mesh, attributes)
    if point:
        model.Objects.AddPoint(r3d.Point3d(0, 0, 0), attributes)
    if not model.Write(str(path), 8):
        raise OSError("failed to create test model")


class BenchmarkInputTests(unittest.TestCase):
    def test_meter_mesh_has_expected_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.3dm"
            write_model(path)
            self.assertEqual(mesh_bounds(path), {"mass": ([0.0] * 3, [1.0, 1.0, 0.0])})

    def test_non_meter_model_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.3dm"
            write_model(path, units=r3d.UnitSystem.Millimeters)
            with self.assertRaisesRegex(ValueError, "meters"):
                mesh_bounds(path)

    def test_duplicate_name_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.3dm"
            write_model(path, duplicate=True)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                mesh_bounds(path)

    def test_non_mesh_object_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.3dm"
            write_model(path, point=True)
            with self.assertRaisesRegex(TypeError, "mesh"):
                mesh_bounds(path)


if __name__ == "__main__":
    unittest.main()
