import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from sodam_rhino_mcp.evidence import (
    draft_evidence_spec,
    prepare_reference_case,
    validate_reference_case,
)


class PacketInputTests(unittest.TestCase):
    def test_interrupted_reference_write_leaves_no_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "view.png"
            Image.new("RGB", (16, 16)).save(image)
            packet = root / "packet.json"
            original_open = Path.open

            class FailingWriter:
                def __init__(self, mode, args, kwargs):
                    self.mode, self.args, self.kwargs = mode, args, kwargs

                def __enter__(self):
                    self.stream = original_open(packet, self.mode, *self.args, **self.kwargs)
                    return self

                def write(self, content):
                    self.stream.write(content[:10])
                    self.stream.flush()
                    raise OSError("simulated reference write failure")

                def __exit__(self, *_args):
                    self.stream.close()

            def open_file(path, mode="r", *args, **kwargs):
                if path == packet and mode in ("w", "x"):
                    return FailingWriter(mode, args, kwargs)
                return original_open(path, mode, *args, **kwargs)

            with (patch.object(Path, "open", open_file),
                  self.assertRaisesRegex(OSError, "reference write failure")):
                prepare_reference_case([image], {"width": 8}, packet)
            self.assertFalse(packet.exists())

    def test_modified_invalid_known_dimension_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "view.png"
            Image.new("RGB", (16, 16)).save(image)
            packet = root / "packet.json"
            prepare_reference_case([image], {"width": 8}, packet)
            spec = root / "spec.json"
            spec.write_text(json.dumps({"units": "meters", "components": [{
                "kind": "box", "name": "volume", "layer": "massing",
                "origin": [0, 0, 0], "size": [8, 5, 3]
            }]}), encoding="utf-8")
            draft = root / "draft.json"
            draft_evidence_spec(spec, packet, draft)
            data = json.loads(packet.read_text(encoding="utf-8"))
            data["known_dimensions"]["width"] = float("nan")
            packet.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "known dimensions"):
                validate_reference_case(draft, packet)


if __name__ == "__main__":
    unittest.main()
