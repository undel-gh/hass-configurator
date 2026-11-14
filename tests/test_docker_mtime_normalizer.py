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
        # The final image now includes a SECOND touch for non-root account
        # metadata. Only the first touch normalizes the installed lock.
        final_stage = "\nFROM " + dockerfile.rsplit("\nFROM ", 1)[-1]
        pre_account_stage, account_stage = final_stage.split("\nRUN groupadd", 1)
        self.assertIn('touch -d "@$SOURCE_DATE_EPOCH"', pre_account_stage)
        self.assertIn("/usr/local/share/hass-configurator/runtime.lock", pre_account_stage)
        # Verify the lock is passed to touch, not merely pip install -r.
        normalize = pre_account_stage.rsplit('&& touch -d "@$SOURCE_DATE_EPOCH"', 1)[-1]
        self.assertIn("/usr/local/share/hass-configurator/runtime.lock", normalize)
        # Reproducible non-root Docker user creation requires a separate touch.
        self.assertIn('touch -d "@$SOURCE_DATE_EPOCH"', account_stage)
        self.assertIn("/etc/passwd", account_stage)
        self.assertIn("/config", account_stage)

    def test_missing_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "Missing reproducible"):
                normalize_tree(Path(folder) / "absent", 1794500000)


if __name__ == "__main__":
    unittest.main()
