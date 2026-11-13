"""Guardrail checks for the generated disposable HA OS Ingress test app."""
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_haos_ingress_fixture import build

ROOT = Path(__file__).resolve().parents[1]


class HAOSIngressFixtureTests(unittest.TestCase):
    def test_generated_app_is_isolated_and_fork_based(self):
        with tempfile.TemporaryDirectory() as dirname:
            target = Path(dirname) / "hc_ingress_validation"
            result = build(target)
            self.assertTrue(result["fixture_only"])
            self.assertFalse(result["home_assistant_api"])
            self.assertFalse(result["external_host_ports"])
            self.assertGreaterEqual(result["vendor_resource_count"], 460)

            config = (target / "config.yaml").read_text(encoding="utf8")
            nginx = (target / "nginx.conf").read_text(encoding="utf8")
            runner = (target / "run.sh").read_text(encoding="utf8")
            dockerfile = (target / "Dockerfile").read_text(encoding="utf8")
            self.assertIn("ingress: true", config)
            self.assertIn("ingress_port: 8099", config)
            self.assertIn("ingress_stream: true", config)
            self.assertIn("map: []", config)
            self.assertIn("boot: manual", config)
            self.assertIn("allow 172.30.32.2;", nginx)
            self.assertIn("deny all;", nginx)
            self.assertIn("exec_command|gitadd", nginx)
            self.assertIn("setpriv --reuid=configurator-e2e", runner)
            self.assertIn('wait "$app_pid"', runner)
            self.assertIn("--standalone", runner)
            self.assertIn("--enforce", runner)
            self.assertIn("COPY app/", dockerfile)
            self.assertNotIn("pip install hass-configurator==", dockerfile)
            self.assertEqual((target / "app" / "hass_configurator" /
                              "vendor" / "manifest.json").read_bytes(),
                             (ROOT / "hass_configurator" / "vendor" /
                              "manifest.json").read_bytes())
            self.assertFalse((target / "app" / "hass_configurator" /
                              "config.json").exists())

    def test_refuses_overwriting_existing_app_directory(self):
        with tempfile.TemporaryDirectory() as dirname:
            dest = Path(dirname) / "hc_ingress_validation"
            dest.mkdir()
            marker = dest / "important.txt"
            marker.write_text("preserve", encoding="utf8")
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                build(dest)
            self.assertEqual(marker.read_text(encoding="utf8"), "preserve")


if __name__ == "__main__":
    unittest.main()
