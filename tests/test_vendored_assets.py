"""Verify committed third-party assets are complete and origin-free."""
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

from hass_configurator.http_routing import Assets, Router

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "hass_configurator"
MANIFEST = json.loads((PACKAGE / "vendor" / "manifest.json").read_text("utf8"))


class VendoredAssetsTests(unittest.TestCase):
    def test_hash_manifest_is_complete_and_matches_every_file(self):
        self.assertEqual(MANIFEST["schema"], 1)
        resources = MANIFEST["resources"]
        self.assertEqual(len([p for p in resources if p.startswith("vendor/ace/")]), 440)
        self.assertGreaterEqual(len(resources), 455)
        for name, checksum in resources.items():
            with self.subTest(name=name):
                source = PACKAGE / name
                self.assertTrue(source.is_file(), name)
                self.assertFalse(source.is_symlink(), name)
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), checksum)
        self.assertEqual({p.relative_to(PACKAGE).as_posix() for p in
                          (PACKAGE / "vendor").rglob("*") if p.is_file()} -
                         {"vendor/manifest.json"}, set(resources))

    def test_provenance_integrity_matches_pinned_ace_lock(self):
        original = json.loads((ROOT / "docs" / "ace-builds-1.9.6-lock.json")
                              .read_text("utf8"))
        ace = MANIFEST["provenance"]["ace"]
        self.assertEqual(ace["version"], "1.9.6")
        self.assertEqual(ace["npm_integrity"], original["npm_integrity"])
        self.assertEqual(ace["sha256"], original["sha256"])
        for filename, value in original["files_sha256"].items():
            self.assertEqual(MANIFEST["resources"]["vendor/ace/" + filename], value)

    def test_css_urls_resolve_to_exact_allowlisted_local_files(self):
        for css in ("vendor/materialize/css/materialize.min.css",
                    "vendor/mdi/css/materialdesignicons.min.css"):
            with self.subTest(css=css):
                stylesheet = (PACKAGE / css).read_text("utf8")
                refs = re.findall(r"url\(\s*['\"]?([^)'\"]+)", stylesheet, flags=re.I)
                for ref in refs:
                    if ref.startswith("data:"):
                        continue
                    self.assertFalse(ref.startswith(("http:", "https:", "//")), ref)
                    path = ref.split("?", 1)[0].split("#", 1)[0]
                    target = (PACKAGE / css).parent / path
                    name = target.resolve().relative_to(PACKAGE.resolve()).as_posix()
                    self.assertIn(name, MANIFEST["resources"],
                                  "%s references missing resource %s" % (css, ref))

    def test_router_handles_nested_static_routes_and_known_fonts(self):
        assets = Assets()
        router = Router(assets)
        for name, expected_mime in (
            ("vendor/ace/ace.js", "text/javascript"),
            ("vendor/ace/mode-yaml.js", "text/javascript"),
            ("vendor/ace/theme-monokai.js", "text/javascript"),
            ("vendor/ace/worker-yaml.js", "text/javascript"),
            ("vendor/mdi/css/materialdesignicons.min.css", "text/css"),
            ("vendor/mdi/fonts/materialdesignicons-webfont.woff2", "font/woff2"),
            ("vendor/materialize/css/materialize.min.css", "text/css"),
            ("vendor/materialize/fonts/roboto/Roboto-Regular.woff2", "font/woff2"),
        ):
            with self.subTest(name=name):
                route = "/assets/v%s/%s" % (assets.version, name)
                matched = router.match("GET", route)
                self.assertEqual(matched.kind, "asset")
                resp = assets.response(matched)
                self.assertEqual(resp.status, 200)
                self.assertTrue(resp.content_type.startswith(expected_mime))
                self.assertGreater(len(resp.body), 0)
                self.assertIn(("Cache-Control",
                               "private, max-age=31536000, immutable"),
                              resp.headers)
                self.assertEqual(router.match("GET", route + "/escape").kind,
                                 "not_found")

    def test_missing_or_tampered_vendored_file_fails_at_startup(self):
        # Copy only the baseline files and manifest with one tampered resource,
        # so a mismatch is discovered before the HTTP server starts.
        from hass_configurator.http_routing import PACKAGE_ASSETS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in PACKAGE_ASSETS:
                (root / name).write_bytes((PACKAGE / name).read_bytes())
            (root / "vendor").mkdir()
            fake = {"schema": 1, "resources": {"vendor/fake.js": hashlib.sha256(b"good").hexdigest()}}
            (root / "vendor" / "manifest.json").write_text(json.dumps(fake))
            (root / "vendor" / "fake.js").write_bytes(b"tampered")
            with self.assertRaisesRegex(RuntimeError, "digest mismatch"):
                Assets(root)


if __name__ == "__main__":
    unittest.main()
