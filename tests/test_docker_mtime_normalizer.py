"""Source epoch normalization is stable and doesn't require network access."""
import os
from pathlib import Path
import tempfile
import unittest

from requirements.normalize_mtimes import normalize_tree, main


class MtimeNormalizerTests(unittest.TestCase):
    def test_tree_epoch_stabilizes_nested_files_and_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "wheelhouse"
            directory = root / "nested"
            directory.mkdir(parents=True)
            a = directory / "file.whl"
            a.write_bytes(b"fixed wheel bytes")
            epoch = 1794500000
            normalize_tree(root, epoch)
            for item in (a, directory, root):
                self.assertEqual(item.stat().st_mtime_ns, epoch * 10**9)
            normalize_tree(root, epoch)
            self.assertEqual(a.read_bytes(), b"fixed wheel bytes")
            self.assertEqual(a.stat().st_mtime_ns, epoch * 10**9)

    def test_retained_runtime_lock_is_epoch_normalized(self):
        from scripts.check_docker_runtime_lock import REPO

        dockerfile = (REPO / "Dockerfile").read_text("utf8")
        final_stage = dockerfile.split("FROM ${PYTHON_BASE}")[-1]
        self.assertIn('touch -d "@$SOURCE_DATE_EPOCH"', final_stage)
        self.assertIn("/usr/local/share/hass-configurator/runtime.lock", final_stage)
        # The retained lock must be in the normalization command, not
        # merely mentioned as the pip install -r input.
        normalize = final_stage.split('&& touch -d "@$SOURCE_DATE_EPOCH"')[-1]
        self.assertIn("/usr/local/share/hass-configurator/runtime.lock",
                      normalize.split("EXPOSE 3218")[0])

    def test_missing_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "Missing reproducible"):
                normalize_tree(Path(folder) / "absent", 1794500000)


if __name__ == "__main__":
    unittest.main()
