"""P1 #7 API authorization, anti-CSRF, filesystem and XSS abuse tests."""
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlencode, quote

from hass_configurator import configurator as cfg
from hass_configurator.api_security import ApiPolicy, ConfinedFS


class PolicyTests(unittest.TestCase):
    def test_no_remote_client_or_proxy_header_can_self_authenticate(self):
        class Handler:
            headers = {"X-CSRF-Token": ""}
            client_address = ("203.0.113.4", 12345)
            server = type("Server", (), {"server_address": ("0.0.0.0", 3218)})()

        policy = ApiPolicy()
        h = Handler()
        for method, path in (("GET", "/"), ("GET", "/api/file"),
                             ("POST", "/api/save")):
            with self.subTest(method=method, path=path):
                self.assertEqual(policy.authorize(h, method, path).status, 403)
        h.headers = {
            "X-CSRF-Token": policy.csrf_token,
            "X-Ingress-Path": "/api/hassio_ingress/private",
            "X-Forwarded-For": "127.0.0.1",
            "X-Forwarded-Proto": "https",
        }
        self.assertEqual(policy.authorize(h, "POST", "/api/save").status, 403)
        h.client_address = ("127.0.0.1", 12345)
        # A backend bound to 0.0.0.0 must not trust remote-proxy loopback.
        self.assertEqual(policy.authorize(h, "POST", "/api/save").status, 403)
        h._authenticated_basic = True
        self.assertIsNone(policy.authorize(h, "POST", "/api/save"))
        h.headers["X-CSRF-Token"] = "invalid"
        self.assertEqual(policy.authorize(h, "POST", "/api/save").status, 403)

    def test_privileged_operations_disabled_even_with_valid_csrf(self):
        class Handler:
            headers = {}
            client_address = ("127.0.0.1", 12345)
            server = type("Server", (), {"server_address": ("127.0.0.1", 3218)})()

        policy = ApiPolicy()
        h = Handler()
        h.headers = {"X-CSRF-Token": policy.csrf_token}
        for method, path in (
            ("POST", "/api/exec_command"),
            ("POST", "/api/push"),
            ("POST", "/api/allowed_networks"),
            ("POST", "/api/restart"),
        ):
            with self.subTest(method=method, path=path):
                self.assertEqual(policy.authorize(h, method, path).status, 403)
        self.assertEqual(
            policy.authorize(h, "POST", "/api/restart", allow_ha_control=True),
            None,
        )
        h.headers = {}
        self.assertEqual(
            policy.authorize(h, "POST", "/api/restart", allow_ha_control=True).status,
            403,
        )


class HostHeaderTests(unittest.TestCase):
    def test_host_must_match_exact_name_not_substring_or_userinfo(self):
        with patch.object(cfg, "VERIFY_HOSTNAME", "trusted.example"):
            for valid in ("trusted.example", "TRUSTED.EXAMPLE", "trusted.example:3218"):
                self.assertTrue(cfg.verify_hostname(valid))
            for invalid in ("attacker-trusted.example", "trusted.example.evil",
                            "trusted.example@evil.example", "trusted.example/path",
                            "trusted.example\\r\\nX-Evil: 1"):
                self.assertFalse(cfg.verify_hostname(invalid))

    def test_configured_host_port_must_match(self):
        with patch.object(cfg, "VERIFY_HOSTNAME", "trusted.example:443"):
            self.assertTrue(cfg.verify_hostname("trusted.example:443"))
            self.assertFalse(cfg.verify_hostname("trusted.example:444"))
            self.assertFalse(cfg.verify_hostname("trusted.example"))


class ConfinedFileTests(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.TemporaryDirectory()
        self.addCleanup(self.parent.cleanup)
        self.root = Path(self.parent.name) / "workspace"
        self.root.mkdir()
        self.sibling = Path(self.parent.name) / "workspace-neighbor"
        self.sibling.mkdir()
        self.fs = ConfinedFS(self.root)

    def test_prefix_sibling_parent_escape_and_control_bytes_rejected(self):
        outside = self.sibling / "secret.txt"
        outside.write_text("secret", encoding="utf8")
        for name in (str(outside), str(self.root / ".." / "workspace-neighbor" / "secret.txt"),
                     str(self.root / "../workspace-neighbor/secret.txt"),
                     str(self.root / "evil\x00file")):
            with self.subTest(name=name), self.assertRaises((PermissionError, ValueError)):
                self.fs.read_bytes(name)

    def test_symlinks_and_intermediate_symlinks_rejected(self):
        outside = self.sibling / "secret.txt"
        outside.write_bytes(b"do not read or overwrite")
        link = self.root / "link.txt"
        link.symlink_to(outside)
        folder = self.root / "link-dir"
        folder.symlink_to(self.sibling, target_is_directory=True)
        for operation in (
            lambda: self.fs.read_bytes(link),
            lambda: self.fs.write_bytes(link, b"overwrite"),
            lambda: self.fs.write_bytes(folder / "secret.txt", b"overwrite"),
            lambda: self.fs.resolve_for_read(link),
        ):
            with self.assertRaises(OSError):
                operation()
        self.assertEqual(outside.read_bytes(), b"do not read or overwrite")

    def test_fd_confined_write_read_rename_create_and_remove(self):
        folder = self.root / "dir"
        self.fs.mkdir(folder)
        first = folder / "first.yaml"
        self.fs.write_bytes(first, b"old: true")
        self.assertEqual(self.fs.read_bytes(first), b"old: true")
        self.fs.write_bytes(first, b"new: true")
        self.assertEqual(self.fs.read_bytes(first), b"new: true")
        with self.assertRaises(FileExistsError):
            self.fs.write_bytes(first, b"cannot clobber", exclusive=True)
        second = folder / "second.yaml"
        self.fs.rename(first, second)
        self.assertFalse(first.exists())
        self.assertEqual(self.fs.read_bytes(second), b"new: true")
        self.fs.remove(second)
        self.fs.remove(folder, is_dir=True)
        self.assertFalse(folder.exists())

    def test_directory_scan_uses_descriptor_and_omits_symlink_entries(self):
        nested = self.root / "nested"
        self.fs.mkdir(nested)
        self.fs.write_bytes(nested / "real.yaml", b"a: 1")
        (nested / "outside").symlink_to(self.sibling, target_is_directory=True)
        names = {item["name"] for item in self.fs.scan_dir(nested)}
        self.assertIn("real.yaml", names)
        self.assertNotIn("outside", names)
        with self.assertRaises(OSError):
            self.fs.scan_dir(nested / "outside")

    def test_no_root_removal(self):
        with self.assertRaises(PermissionError):
            self.fs.remove(self.root)


def http_request(server, method, path, data=None, headers=None):
    conn = http.client.HTTPConnection(
        "127.0.0.1", server.server_address[1], timeout=5)
    try:
        conn.request(method, path, body=data,
                     headers=headers or {})
        resp = conn.getresponse()
        return resp.status, dict(resp.getheaders()), resp.read()
    finally:
        conn.close()


class SecurityLoopbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.old = (cfg.BASEPATH, cfg.HASS_API, cfg.ALLOW_SHELL_COMMANDS,
                   cfg.ALLOW_GIT_OPERATIONS, cfg.ALLOW_NETWORK_ADMIN,
                   cfg.ALLOW_HA_CONTROL, cfg.USERNAME, cfg.PASSWORD)
        cfg.BASEPATH = cls.workspace.name
        cfg.HASS_API = None
        cfg.ALLOW_SHELL_COMMANDS = False
        cfg.ALLOW_GIT_OPERATIONS = False
        cfg.ALLOW_NETWORK_ADMIN = False
        cfg.ALLOW_HA_CONTROL = False
        cfg.USERNAME = None
        cfg.PASSWORD = None
        cls.server = cfg.SimpleServer(("127.0.0.1", 0), cfg.RequestHandler)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        (cfg.BASEPATH, cfg.HASS_API, cfg.ALLOW_SHELL_COMMANDS,
         cfg.ALLOW_GIT_OPERATIONS, cfg.ALLOW_NETWORK_ADMIN,
         cfg.ALLOW_HA_CONTROL, cfg.USERNAME, cfg.PASSWORD) = cls.old
        cls.workspace.cleanup()

    def test_missing_wrong_or_spoofed_csrf_never_writes_file(self):
        target = Path(self.workspace.name) / "csrf-target.yaml"
        body = urlencode({"filename": str(target), "text": "safe: true"}).encode()
        for token in (None, "bad-token"):
            hdrs = {"Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "http://evil.invalid",
                    "X-Ingress-Path": "/injected/path"}
            if token is not None:
                hdrs["X-CSRF-Token"] = token
            status, headers, _ = http_request(
                self.server, "POST", "/api/save", body, hdrs)
            self.assertEqual(status, 403)
            self.assertEqual(headers.get("Cache-Control"), "no-store")
            self.assertFalse(target.exists())
        token = cfg.HTTP_ROUTER.security.csrf_token
        status, _, raw = http_request(
            self.server, "POST", "/api/save", body,
            {"Content-Type": "application/x-www-form-urlencoded",
             "X-CSRF-Token": token})
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(raw)["error"])
        self.assertEqual(target.read_text(), "safe: true")

    def test_ha_control_requires_post_csrf_and_capability(self):
        with patch("urllib.request.urlopen") as urlopen:
            status, headers, _ = http_request(self.server, "GET", "/api/restart")
            self.assertEqual(status, 405)
            self.assertEqual(headers.get("Allow"), "POST")
            status, _, _ = http_request(self.server, "POST", "/api/restart", b"")
            self.assertEqual(status, 403)
            status, _, _ = http_request(
                self.server, "POST", "/api/restart", b"",
                headers={"X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
            self.assertEqual(status, 403)
            urlopen.assert_not_called()

    def test_shell_git_and_network_mutations_denied_before_body(self):
        headers = {"X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token,
                   "Content-Type": "application/x-www-form-urlencoded"}
        for route in ("/api/exec_command", "/api/push", "/api/allowed_networks"):
            with self.subTest(route=route):
                status, _, _ = http_request(
                    self.server, "POST", route, b"path=/&command=id", headers)
                self.assertEqual(status, 403)

    def test_download_and_read_path_escape_and_symlink(self):
        outside = Path(self.workspace.name).parent / "outside-sensitive.txt"
        # Avoid creating outside files: symlink to a harmless in-repo fixture.
        try:
            link = Path(self.workspace.name) / "escape"
            link.symlink_to(Path(__file__).resolve())
            for target in (link, Path(self.workspace.name) / "../not-inside-file"):
                path = "/api/download?filename=" + quote(str(target), safe="")
                status, _, content = http_request(self.server, "GET", path)
                self.assertNotIn(b"\"\"\"P1 #7 API authorization", content)
        finally:
            if link.is_symlink():
                link.unlink()

    def test_query_filename_must_not_generate_executable_inline_js(self):
        payload = "'</script><script>window.attacked=1</script>"
        status, headers, html = http_request(
            self.server, "GET", "/?loadfile=" + quote(payload, safe=""))
        self.assertEqual(status, 200)
        self.assertIn(b"hc-csrf-token", html)
        self.assertNotIn(b"</script><script>window.attacked", html)
        self.assertIn(b"\\u003c/script\\u003e", html)

    def test_preferences_symlink_cannot_overwrite_file_outside_workspace(self):
        prefs = Path(self.workspace.name) / cfg.PREFS_FILENAME
        with tempfile.TemporaryDirectory() as external:
            victim = Path(external) / "unrelated.txt"
            victim.write_text("original secret", encoding="utf8")
            if prefs.exists() or prefs.is_symlink():
                self.skipTest("Unexpected existing preferences file")
            prefs.symlink_to(victim)
            try:
                body = json.dumps({"ui_theme": "dark"}).encode("utf8")
                status, _, raw = http_request(
                    self.server, "POST", "/api/prefs", body,
                    {"Content-Type": "application/json",
                     "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
                self.assertEqual(status, 200)
                self.assertTrue(json.loads(raw)["error"])
                self.assertEqual(victim.read_text(), "original secret")
                self.assertEqual(cfg.load_prefs()["ui_theme"], "auto")
            finally:
                prefs.unlink()

    def test_config_debug_settings_always_redact_secrets(self):
        cleaned = cfg._redacted_settings({
            "HASS_API_PASSWORD": "not-for-logs",
            "SESAME_TOTP_SECRET": "not-for-logs",
            "PASSWORD": "not-for-logs",
            "HASS_API": "http://localhost:8123/api/",
        })
        self.assertEqual(cleaned["PASSWORD"], "<redacted>")
        self.assertEqual(cleaned["HASS_API_PASSWORD"], "<redacted>")
        self.assertEqual(cleaned["SESAME_TOTP_SECRET"], "<redacted>")
        self.assertEqual(cleaned["HASS_API"], "http://localhost:8123/api/")

    def test_network_allowlist_cannot_be_cleared_by_admin(self):
        original = list(cfg.ALLOWED_NETWORKS)
        cfg.ALLOWED_NETWORKS[:] = ["127.0.0.1/32"]
        try:
            with patch.object(cfg, "ALLOW_NETWORK_ADMIN", True):
                payload = urlencode({"network": "127.0.0.1/32", "method": "remove"}).encode()
                status, _, data = http_request(
                    self.server, "POST", "/api/allowed_networks", payload,
                    {"Content-Type": "application/x-www-form-urlencoded",
                     "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
                self.assertEqual(status, 200)
                self.assertTrue(json.loads(data)["error"])
                self.assertEqual(cfg.ALLOWED_NETWORKS, ["127.0.0.1/32"])
        finally:
            cfg.ALLOWED_NETWORKS[:] = original

    def test_ha_control_real_outbound_post_only_after_all_gates(self):
        class Reply:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return b"{}"

        with patch.object(cfg, "ALLOW_HA_CONTROL", True), \
             patch.object(cfg, "HASS_API", "http://127.0.0.1:8123/api/"), \
             patch("urllib.request.urlopen", return_value=Reply()) as opener:
            status, _, content = http_request(
                self.server, "POST", "/api/restart", b"",
                {"X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
            self.assertEqual(status, 200)
            self.assertIn(b"{}", content)
            self.assertEqual(opener.call_count, 1)
            req = opener.call_args.args[0]
            self.assertEqual(req.get_method(), "POST")
            self.assertEqual(req.full_url,
                             "http://127.0.0.1:8123/api/services/homeassistant/restart")

    def test_unsupported_internal_http_verbs_are_501(self):
        for method in ("AUTHHEAD", "BLOCK"):
            status, _, _ = http_request(self.server, method, "/")
            self.assertEqual(status, 501)


if __name__ == "__main__":
    unittest.main()
