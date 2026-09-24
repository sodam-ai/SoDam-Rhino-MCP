import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sodam_rhino_mcp.spec_store import write_spec


class SpecStoreTests(unittest.TestCase):
    def test_write_reopen_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(__file__).parents[1] / "examples" / "small_house.json"
            target = Path(directory) / "house.json"
            text = source.read_text(encoding="utf-8")
            result = write_spec(text, target)
            self.assertEqual(result["components"], len(json.loads(text)["components"]))
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), json.loads(text))
            before = target.read_bytes()
            with self.assertRaises(FileExistsError):
                write_spec(text, target)
            self.assertEqual(target.read_bytes(), before)

    def test_write_failure_leaves_no_partial_spec(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(__file__).parents[1] / "examples" / "small_house.json"
            content = source.read_text(encoding="utf-8")
            target = Path(directory) / "partial.json"
            original_open = Path.open

            class FailingWriter:
                def __enter__(self):
                    self.stream = original_open(target, "x", encoding="utf-8")
                    return self

                def write(self, content):
                    self.stream.write(content[:10])
                    self.stream.flush()
                    raise OSError("simulated disk write failure")

                def __exit__(self, *_args):
                    self.stream.close()

            with (patch.object(Path, "open", return_value=FailingWriter()),
                  self.assertRaisesRegex(OSError, "disk write failure")):
                write_spec(content, target)
            self.assertFalse(target.exists())

    def test_invalid_content_never_creates_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            good = (Path(__file__).parents[1] / "examples" / "small_house.json").read_text(encoding="utf-8")
            cases = ["{", "[]", good.replace('"meters"', '"unknown"', 1),
                     good.replace('"meters"', '"meters", "extra": NaN', 1), " " * 2_000_001]
            for index, content in enumerate(cases):
                with self.subTest(index=index):
                    target = root / f"bad_{index}.json"
                    with self.assertRaises((ValueError, json.JSONDecodeError)):
                        write_spec(content, target)
                    self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
