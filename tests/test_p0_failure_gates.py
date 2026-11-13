"""Prove P0 checks fail closed, including missing assets and outbound fetches."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hass_configurator.http_routing import Assets, PACKAGE_ASSETS
from scripts import audit_runtime_assets

ROOT = Path(__file__).resolve().parents[1]


class OfflineP0FailureFixtures(unittest.TestCase):
    def test_missing_first_party_asset_fails_at_startup(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in PACKAGE_ASSETS:
                if name != "style.css":
                    (root / name).write_bytes(b"test resource")
            with self.assertRaisesRegex(RuntimeError,
                                        "Missing packaged static asset: style.css"):
                Assets(root)

    def test_missing_declared_vendor_asset_fails_at_startup(self):
        import hashlib
        import json

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in PACKAGE_ASSETS:
                (root / name).write_bytes(b"test resource")
            (root / "vendor").mkdir()
            (root / "vendor" / "manifest.json").write_text(
                json.dumps({"schema": 1, "resources": {
                    "vendor/ace/mode-yaml.js":
                        hashlib.sha256(b"official file").hexdigest(),
                }}), encoding="utf8",
            )
            with self.assertRaisesRegex(RuntimeError,
                                        "Missing packaged static asset: vendor/ace/mode-yaml.js"):
                Assets(root)

    def test_injected_public_fetch_fails_inventory_gate(self):
        original = (ROOT / "hass_configurator" / "dev.html").read_text(
            encoding="utf8")
        self.assertEqual(audit_runtime_assets.extract(original)["other_remote"], [])
        injected = original.replace(
            "</head>",
            '<script src="https://example.invalid/test-unapproved.js"></script></head>',
            1,
        )
        self.assertIn(
            "https://example.invalid/test-unapproved.js",
            audit_runtime_assets.extract(injected)["other_remote"],
        )
        with tempfile.TemporaryDirectory() as directory:
            html = Path(directory) / "injected.html"
            html.write_text(injected, encoding="utf8")
            with (
                patch.object(audit_runtime_assets, "HTML", html),
                patch("sys.argv", ["audit_runtime_assets.py", "--strict-offline"]),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertNotEqual(audit_runtime_assets.main(), 0)

    def test_fork_docker_uses_local_wheel_not_pypi_upstream(self):
        docker = (ROOT / "Dockerfile").read_text(encoding="utf8")
        self.assertIn("COPY hass_configurator/ hass_configurator/", docker)
        self.assertIn("pip wheel --no-deps", docker)
        self.assertIn("COPY --from=wheel-builder", docker)
        self.assertIn("/wheelhouse/hass_configurator-*.whl", docker)
        self.assertNotIn("pip install --no-cache-dir hass-configurator\n",
                         docker)
        self.assertIn('ENTRYPOINT ["hass-configurator"]', docker)


if __name__ == "__main__":
    unittest.main()
