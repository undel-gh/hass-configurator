"""Synthetic checks for the read-only selective rebuild evidence tool."""
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from scripts.rebuild_retained_ace import materialize, relation


class RetainedRebuildTests(unittest.TestCase):
    def archive(self, extra=None):
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            for name, raw in (("package/package.json", b'{"name":"fixture","version":"1.0.0"}'),
                              ("package/index.js", b"module.exports = 1;")):
                member = tarfile.TarInfo(name)
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
            if extra:
                archive.addfile(extra)
        return buffer.getvalue()

    def test_exact_materialization_and_byte_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "pkg"
            raw = self.archive()
            self.assertEqual(set(materialize(raw, dest, "fixture", "1.0.0")),
                             {"package.json", "index.js"})
            self.assertTrue(relation((dest / "index.js").read_bytes(), b"module.exports = 1;")["equal"])
            self.assertEqual(relation(b"abc", b"abx")["first_difference"], 2)
            self.assertEqual(relation(b"abc", b"abc\n")["first_difference"], 3)

    def test_reject_duplicate_link_and_traversal(self):
        link = tarfile.TarInfo("package/link")
        link.type = tarfile.SYMTYPE
        link.linkname = "../outside"
        for extra in (link, tarfile.TarInfo("package/index.js"), tarfile.TarInfo("package/../escape")):
            with self.subTest(member=extra.name), tempfile.TemporaryDirectory() as tmp:
                with self.assertRaisesRegex(ValueError, "Unsafe or duplicate"):
                    materialize(self.archive(extra), Path(tmp) / "pkg", "fixture", "1.0.0")
