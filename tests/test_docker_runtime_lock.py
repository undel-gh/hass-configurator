"""Fail-closed tests for the Docker release's byte-exact wheel dependency lock."""
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.check_docker_runtime_lock import (
    LOCK, direct_dependencies_from_setup, read_lock, validate_lock,
    verify_wheelhouse,
)

class DockerRuntimeLockTests(unittest.TestCase):
    def test_complete_lock_matches_setup_direct_requirements(self):
        locked = validate_lock()
        self.assertEqual(len(locked), 5)
        self.assertEqual(direct_dependencies_from_setup(),
                         {"pyotp", "gitpython", "legacy-cgi"})
        self.assertTrue(direct_dependencies_from_setup().issubset(locked))
        self.assertEqual(len({hash for _, hash in locked.values()}), 5)

    def test_rejects_unhashed_duplicate_and_unpinned_runtime_dependency(self):
        original = LOCK.read_text("utf8")
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "lock"
            for data in (
                original + "\ngitdb==4.0.12 --hash=sha256:" + "0" * 64 + "\n",
                original.replace("GitPython==3.2.1", "GitPython>=3.2.1"),
                original.replace("--only-binary=:all:", "--prefer-binary"),
                original.replace("--hash=sha256:", "--hash=sha512:", 1),
            ):
                p.write_text(data)
                with self.subTest(kind=data[-75:]):
                    with self.assertRaises(ValueError):
                        read_lock(p)

    def test_detects_missing_declared_direct_requirement(self):
        data = LOCK.read_text("utf8")
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "lock"
            data = "\n".join(
                line for line in data.splitlines()
                if not line.startswith("pyotp==")) + "\n"
            p.write_text(data)
            with self.assertRaisesRegex(ValueError,
                                        "Direct package dependencies missing"):
                validate_lock(p)

    def test_wheelhouse_rejects_injected_or_tampered_wheels(self):
        # Tiny local forged wheel validates exact hash/metadata/closure logic
        # without trusting an artifact from PyPI or using any network.
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "pkg-1.2.3-py3-none-any.whl"
            with zipfile.ZipFile(p, "w") as archive:
                archive.writestr("pkg-1.2.3.dist-info/METADATA",
                                 "Metadata-Version: 2.1\nName: pkg\nVersion: 1.2.3\n")
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(verify_wheelhouse(folder, {"pkg": ("1.2.3", digest)}),
                             {"pkg"})
            p.write_bytes(p.read_bytes() + b"tampered")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                verify_wheelhouse(folder, {"pkg": ("1.2.3", digest)})
            p.unlink()
            (Path(folder) / "surprise.tar.gz").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "non-wheel"):
                verify_wheelhouse(folder, {"pkg": ("1.2.3", digest)})


if __name__ == "__main__":
    unittest.main()
