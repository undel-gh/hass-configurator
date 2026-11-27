"""Guardrail checks for the generated disposable HA OS Ingress test app."""
from pathlib import Path
import re
import tempfile
import unittest

from scripts.prepare_haos_ingress_fixture import build

ROOT = Path(__file__).resolve().parents[1]


# Every nginx location that forwards to the loopback editor must independently
# drop secrets. A global assertIn() would still pass if just one location
# forwarded Authorization or X-Remote-User-Id (review #1, PR #22).
STRIPPED_BACKEND_HEADERS = (
    "X-Ingress-Path", "X-Forwarded-For", "X-Forwarded-Host",
    "X-Forwarded-Proto", "X-Remote-User-Id", "X-Remote-User-Name",
    "X-Remote-User-Display-Name", "X-Remote-User-Groups",
    "Forwarded", "X-Real-IP", "Cookie", "Authorization",
    "X-Supervisor-Token",
)
BACKEND_PROXY_LOCATIONS = ("/__haos_probe", "/")


def nginx_locations(source):
    """Return exact location blocks without confusing adjacent locations.

    This fixture uses simple location blocks and no nested location directives.
    Only parse as much nginx syntax as the fixture uses; a malformed or nested
    block fails closed instead of silently relying on another location.
    """
    found = {}
    location_start = re.compile(
        r"(?m)^[ \t]*location[ \t]+(?:=[ \t]+)?(?P<route>[^ \t{]+)[ \t]*\{")
    for match in location_start.finditer(source):
        route = match.group("route")
        if route in found:
            raise AssertionError("Duplicate nginx location: " + route)
        start = match.end()
        depth, end = 1, start
        while depth and end < len(source):
            if source[end] == "{":
                depth += 1
            elif source[end] == "}":
                depth -= 1
            end += 1
        if depth:
            raise AssertionError("Unclosed nginx location: " + route)
        block = source[start:end - 1]
        if re.search(r"(?m)^[ \t]*location[ \t]+", block):
            raise AssertionError("Nested nginx location not supported: " + route)
        found[route] = block
    return found


def assert_backend_secrets_stripped(source):
    """Enforce *every* proxying location, not one global header occurrence."""
    blocks = nginx_locations(source)
    proxy_blocks = {
        route: block for route, block in blocks.items()
        if re.search(r"(?m)^[ \t]*proxy_pass[ \t]+", block)
    }
    assert set(proxy_blocks) == set(BACKEND_PROXY_LOCATIONS), (
        "Unexpected set of editor proxy locations: " + repr(sorted(proxy_blocks))
    )
    for route, block in proxy_blocks.items():
        headers = {}
        for name, value in re.findall(
                r"(?mi)^[ \t]*proxy_set_header[ \t]+"
                r"([A-Z0-9-]+)[ \t]+([^;]+);", block):
            headers.setdefault(name.lower(), []).append(value.strip())
        assert headers.get("host") == ["127.0.0.1:3218"], (
            route + ": must set only trusted loopback Host"
        )
        for name in STRIPPED_BACKEND_HEADERS:
            assert headers.get(name.lower()) == ['""'], (
                route + ": must strip " + name + " exactly once; found "
                + repr(headers.get(name.lower()))
            )
        assert re.findall(r"(?m)^[ \t]*proxy_pass[ \t]+([^;]+);", block) == [
            "http://127.0.0.1:3218" +
            ("/api/version" if route == "/__haos_probe" else "")
        ], route + ": unexpected backend destination"


class HAOSIngressFixtureTests(unittest.TestCase):
    def test_generated_app_is_isolated_and_fork_based(self):
        with tempfile.TemporaryDirectory() as dirname:
            target = Path(dirname) / "hc_ingress_validation"
            result = build(target)
            self.assertTrue(result["fixture_only"])
            self.assertFalse(result["home_assistant_api"])
            self.assertFalse(result["external_host_ports"])
            self.assertEqual(result["vendor_resource_count"], 515)

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
            self.assertIn("proxy_set_header Host 127.0.0.1:3218;", nginx)
            self.assertNotIn("proxy_set_header Host $http_host", nginx)
            self.assertNotIn("proxy_set_header X-Ingress-Path $http_", nginx)
            self.assertIn("location = /__haos_probe", nginx)
            self.assertIn("location = /__haos_api_probe", nginx)
            self.assertIn('X-HC-Fixture-Id "hc-ingress-validation-v1"', nginx)
            self.assertIn("proxy_pass http://127.0.0.1:3218/api/version", nginx)
            assert_backend_secrets_stripped(nginx)
            self.assertEqual((target / "ha-api-mode").read_text(), "disabled\n")
            self.assertNotIn("homeassistant_api: true", config)
            self.assertTrue((target / "haos_local_api_probe.py").exists())
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

    def test_every_proxy_location_rejects_unstripped_header_regressions(self):
        """Replacing one scrub directive must fail, even if other location is safe."""
        source = (ROOT / "haos-fixture" / "nginx.conf").read_text(encoding="utf8")
        blocks = nginx_locations(source)
        assert_backend_secrets_stripped(source)
        for location in BACKEND_PROXY_LOCATIONS:
            block = blocks[location]
            for name in STRIPPED_BACKEND_HEADERS:
                with self.subTest(location=location, forwarded_header=name):
                    scrub = 'proxy_set_header %s "";' % name
                    self.assertIn(scrub, block)
                    # Reproduce an accidental passthrough in precisely one
                    # location; the other location stays correctly scrubbed.
                    changed = block.replace(
                        scrub, 'proxy_set_header %s $http_untrusted;' % name, 1)
                    poisoned = source.replace(block, changed, 1)
                    with self.assertRaisesRegex(
                            AssertionError, r"must strip"):
                        assert_backend_secrets_stripped(poisoned)
            with self.subTest(location=location, change="duplicate secret"):
                poisoned = source.replace(
                    block, block + '\nproxy_set_header Authorization $http_authorization;',
                    1)
                with self.assertRaisesRegex(AssertionError, "must strip Authorization"):
                    assert_backend_secrets_stripped(poisoned)
            with self.subTest(location=location, change="untrusted Host"):
                original = "proxy_set_header Host 127.0.0.1:3218;"
                self.assertIn(original, block)
                poisoned_block = block.replace(
                    original, "proxy_set_header Host $http_host;", 1)
                poisoned = source.replace(block, poisoned_block, 1)
                with self.assertRaisesRegex(
                        AssertionError, "must set only trusted loopback Host"):
                    assert_backend_secrets_stripped(poisoned)
            with self.subTest(location=location, change="redirected proxy_pass"):
                original = ("proxy_pass http://127.0.0.1:3218" +
                            ("/api/version" if location == "/__haos_probe"
                             else "") + ";")
                self.assertIn(original, block)
                poisoned_block = block.replace(
                    original, "proxy_pass http://attacker.invalid:8080;", 1)
                poisoned = source.replace(block, poisoned_block, 1)
                with self.assertRaisesRegex(
                        AssertionError, "unexpected backend destination"):
                    assert_backend_secrets_stripped(poisoned)

    def test_new_proxy_location_cannot_omit_secret_stripping(self):
        source = (ROOT / "haos-fixture" / "nginx.conf").read_text(encoding="utf8")
        # If a future extra proxy route appears, the allowlisted security
        # boundary must be extended explicitly rather than silently skipped.
        added = ('\nlocation = /__future {\n'
                 '  proxy_pass http://127.0.0.1:3218;\n}\n')
        with self.assertRaisesRegex(AssertionError, "Unexpected set"):
            assert_backend_secrets_stripped(source + added)

    def test_ha_api_probe_requires_explicit_separate_fixture_opt_in(self):
        with tempfile.TemporaryDirectory() as dirname:
            target = Path(dirname) / "ha-api-test"
            metadata = build(target, with_ha_api_probe=True)
            self.assertTrue(metadata["home_assistant_api"])
            self.assertTrue(metadata["read_only_supervisor_probe"])
            self.assertTrue(metadata["fixture_only"])
            self.assertFalse(metadata["external_host_ports"])
            config = (target / "config.yaml").read_text(encoding="utf8")
            self.assertIn("homeassistant_api: true", config)
            self.assertIn("map: []", config)
            self.assertEqual((target / "ha-api-mode").read_text(), "enabled\n")
            runner = (target / "run.sh").read_text(encoding="utf8")
            self.assertIn("python /opt/hc-haos-local-api-probe.py", runner)
            self.assertIn("unset SUPERVISOR_TOKEN", runner)
            self.assertLess(runner.index("unset SUPERVISOR_TOKEN"),
                            runner.index("setpriv --reuid="))
            dockerfile = (target / "Dockerfile").read_text(encoding="utf8")
            self.assertIn("COPY haos_local_api_probe.py", dockerfile)

    def test_two_disposable_revisions_change_immutable_asset_digest(self):
        from hass_configurator.http_routing import Assets
        with tempfile.TemporaryDirectory() as root:
            source = (ROOT / "hass_configurator" / "style.css").read_bytes()
            a = Path(root) / "version-a"
            b = Path(root) / "version-b"
            first = build(a, fixture_version="0.0.1", cache_revision="A")
            second = build(b, fixture_version="0.0.2", cache_revision="B")
            self.assertEqual(first["test_cache_revision"], "A")
            self.assertEqual(second["test_cache_revision"], "B")
            self.assertIn('version: "0.0.2"',
                          (b / "config.yaml").read_text(encoding="utf8"))
            self.assertNotEqual(
                Assets(a / "app" / "hass_configurator").version,
                Assets(b / "app" / "hass_configurator").version)
            self.assertEqual(
                (ROOT / "hass_configurator" / "style.css").read_bytes(), source)

    def test_rejects_untrusted_test_revision_values_before_build(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "fixture"
            for value in ("../escape", "evil\nbody", "A'B"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    build(target, cache_revision=value)
                self.assertFalse(target.exists())
            with self.assertRaises(ValueError):
                build(target, fixture_version="1.2.3; echo unsafe")
            self.assertFalse(target.exists())

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
