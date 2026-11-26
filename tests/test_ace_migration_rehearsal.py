"""Fail-closed checks for the disposable #33 rehearsal input."""
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from scripts import prepare_ace_migration as migration


class MigrationRehearsalTests(unittest.TestCase):
    def make_archive(self, path, version="4.3.2", duplicate=False, link=False):
        license_bytes = b"fixture license"
        members = [("package/package.json", json.dumps({
            "name": "js-yaml", "version": version, "license": "MIT"
        }).encode()), ("package/LICENSE", license_bytes),
            ("package/dist/js-yaml.min.js", b"fixture payload\n")]
        if duplicate:
            members.append(members[-1])
        with tarfile.open(path, "w:gz") as archive:
            for name, raw in members:
                info = tarfile.TarInfo(name)
                if link and name.endswith(".min.js"):
                    info.type = tarfile.SYMTYPE
                    info.linkname = "package/LICENSE"
                    archive.addfile(info)
                else:
                    info.size = len(raw)
                    archive.addfile(info, io.BytesIO(raw))
        return {"dist.tarball": migration.YAML_URL,
                "dist.integrity": migration.sri(path.read_bytes())}, license_bytes

    def test_exact_yaml_member_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            registry, license_bytes = self.make_archive(archive)
            with patch.object(migration, "YAML_LICENSE_BLOB",
                              migration.git_blob_sha1(license_bytes)):
                report, payload, notice = migration.inspect_yaml(archive, registry)
            self.assertEqual(payload, b"fixture payload\n")
            self.assertEqual(notice, license_bytes)
            self.assertEqual(report["member_sha256"], migration.sha(payload))
            self.assertEqual(report["archive_sha256"], migration.sha(archive.read_bytes()))
            self.assertTrue(report["independent_archive_pin_pending"])

    def test_reject_wrong_registry_source_integrity_and_license(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            registry, _ = self.make_archive(archive)
            for key, value in (("dist.tarball", "https://example.invalid/archive"),
                               ("dist.integrity", "sha512-invalid")):
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, "registry integrity/source"):
                    migration.inspect_yaml(archive, {**registry, key: value})
            with self.assertRaisesRegex(ValueError, "license differs"):
                migration.inspect_yaml(archive, registry)

    def test_reject_wrong_identity_duplicate_and_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            for kwargs, message in (({"version": "4.1.0"}, "package identity"),
                                    ({"duplicate": True}, "duplicate or non-regular"),
                                    ({"link": True}, "duplicate or non-regular")):
                registry, license_bytes = self.make_archive(archive, **kwargs)
                with patch.object(migration, "YAML_LICENSE_BLOB",
                                  migration.git_blob_sha1(license_bytes)):
                    with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, message):
                        migration.inspect_yaml(archive, registry)

    def test_destination_must_be_new_and_outside_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "repo"
            root.mkdir()
            with patch.object(migration, "ROOT", root):
                for path in (root, root / "new", parent):
                    with self.subTest(path=path), self.assertRaisesRegex(ValueError, "new and outside"):
                        migration.outside_new_checkout(path)
                self.assertEqual(migration.outside_new_checkout(parent / "new"), parent / "new")
