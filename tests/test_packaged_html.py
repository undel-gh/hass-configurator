"""Negative tests proving wheel/sdist packaging checks cover the main HTML UI."""
import contextlib
import io
from pathlib import Path
import unittest

from hass_configurator.http_routing import PACKAGE_ASSETS
from scripts.check_offline_artifacts import MANIFEST, NOTICE_FILES, ROOT, verify


class MainHtmlPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = ROOT / "hass_configurator"
        included = (
            set(MANIFEST["resources"])
            | set(PACKAGE_ASSETS) | NOTICE_FILES
            | {"dev.html", "_version.py", "vendor/manifest.json"}
        )
        cls.files = {
            "hass_configurator/" + name: (package / name).read_bytes()
            for name in included
        }

    def check_files(self, files):
        with contextlib.redirect_stdout(io.StringIO()):
            verify(files, "test-archive")

    def test_complete_archive_accepts_html(self):
        self.check_files(dict(self.files))

    def test_missing_html_rejected(self):
        copied = dict(self.files)
        copied.pop("hass_configurator/dev.html")
        with self.assertRaisesRegex(RuntimeError, "missing=.*dev.html"):
            self.check_files(copied)

    def test_missing_notice_rejected(self):
        copied = dict(self.files)
        copied.pop("hass_configurator/third_party/licenses/roboto.txt")
        with self.assertRaisesRegex(RuntimeError, "missing=.*roboto.txt"):
            self.check_files(copied)

    def test_modified_notice_rejected(self):
        copied = dict(self.files)
        copied["hass_configurator/third_party/licenses/jquery.txt"] += b"tampered"
        with self.assertRaisesRegex(RuntimeError, "changed=.*jquery.txt"):
            self.check_files(copied)

    def test_modified_html_rejected(self):
        copied = dict(self.files)
        copied["hass_configurator/dev.html"] += b"\n<!-- unexpected edit -->\n"
        with self.assertRaisesRegex(RuntimeError, "changed=.*dev.html"):
            self.check_files(copied)


if __name__ == "__main__":
    unittest.main()
