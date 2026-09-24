"""Project-used rhino3dm API surface verified against 8.35.0 at runtime."""
from collections.abc import Iterator
from enum import Enum
from uuid import UUID

class UnitSystem(Enum):
    Meters = ...
    Millimeters = ...
    Centimeters = ...
    Feet = ...

class ObjectColorSource(Enum):
    ColorFromObject = ...

class ObjectMaterialSource(Enum):
    MaterialFromObject = ...

class Point3f:
    X: float
    Y: float
    Z: float

class MeshVertexList:
    def Add(self, x: float, y: float, z: float) -> int: ...
    def __iter__(self) -> Iterator[Point3f]: ...
    def __getitem__(self, index: int) -> Point3f: ...

class MeshFaceList:
    def AddFace(self, *indices: int) -> int: ...
    def __iter__(self) -> Iterator[tuple[int, ...]]: ...

class MeshNormalList:
    def ComputeNormals(self) -> bool: ...

class Mesh:
    Vertices: MeshVertexList
    Faces: MeshFaceList
    Normals: MeshNormalList

class Layer:
    Name: str

class Material:
    Name: str
    DiffuseColor: tuple[int, int, int, int]

class ObjectAttributes:
    Name: str
    LayerIndex: int
    ObjectColor: tuple[int, int, int, int]
    ColorSource: ObjectColorSource
    MaterialIndex: int
    MaterialSource: ObjectMaterialSource
    def SetUserString(self, key: str, value: str) -> bool: ...
    def GetUserString(self, key: str) -> str: ...

class File3dmSettings:
    ModelUnitSystem: UnitSystem

class File3dmObject:
    Geometry: object
    Attributes: ObjectAttributes

class File3dmLayerTable:
    def Add(self, layer: Layer) -> int: ...
    def __iter__(self) -> Iterator[Layer]: ...
    def __getitem__(self, index: int) -> Layer: ...

class File3dmMaterialTable:
    def Add(self, material: Material) -> int: ...

class File3dmObjectTable:
    def AddMesh(self, mesh: Mesh, attributes: ObjectAttributes) -> UUID: ...
    def __iter__(self) -> Iterator[File3dmObject]: ...

class File3dm:
    Settings: File3dmSettings
    Layers: File3dmLayerTable
    Materials: File3dmMaterialTable
    Objects: File3dmObjectTable
    @staticmethod
    def Read(path: str) -> File3dm | None: ...
    def Write(self, path: str, version: int) -> bool: ...
