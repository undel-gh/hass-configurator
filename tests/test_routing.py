"""Unit and loopback contract tests for the permanent routing boundary."""
import contextlib
import http.client
import os
from pathlib import Path
import tempfile
import threading
import unittest

from hass_configurator.http_routing import (
    Assets, Router, PACKAGE_ASSETS, IMMUTABLE_CACHE, NO_STORE,
)


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        for name in PACKAGE_ASSETS:
            (root / name).write_bytes(("file:" + name).encode())
        self.assets = Assets(root)
        self.router = Router(self.assets)

    def test_exact_api_routes_and_methods(self):
        self.assertEqual(self.router.match("GET", "/api/prefs").kind, "legacy_api")
        self.assertEqual(self.router.match("POST", "/api/prefs").kind, "legacy_api")
        self.assertEqual(self.router.match("POST", "/api/save").kind, "legacy_api")
        self.assertEqual(self.router.match("GET", "/api/save").kind, "method_not_allowed")
        self.assertEqual(self.router.match("GET", "/evil/api/prefs").kind, "not_found")
        self.assertEqual(self.router.match("POST", "/evil/api/save").kind, "not_found")
        self.assertEqual(self.router.match("GET", "/subpath/").kind, "not_found")
        self.assertEqual(self.router.match("GET", "/").kind, "legacy_page")
        self.assertEqual(self.router.match("POST", "/").kind, "method_not_allowed")

    def test_encoded_and_ambiguous_paths_rejected(self):
        for path in ("/assets/%2e%2e/x", "/assets/%2fapi", "/api/%70refs",
                     "/assets/../api/prefs", "//api/save", "/api/\\prefs"):
            with self.subTest(path=path):
                kind = self.router.match("GET", path).kind
                self.assertIn(kind, ("bad_request", "not_found"))

    def test_asset_version_and_cache_policies(self):
        filename = "style.css"
        path = "/assets/v%s/%s" % (self.assets.version, filename)
        match = self.router.match("GET", path)
        self.assertEqual(match.kind, "asset")
        response = self.assets.response(match)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.body, b"file:style.css")
        self.assertIn(("Cache-Control", IMMUTABLE_CACHE), response.headers)
        self.assertEqual(response.content_type, "text/css; charset=utf-8")
        alias = self.router.match("GET", "/style.css")
        self.assertEqual(alias.kind, "asset")
        self.assertIn(("Cache-Control", "no-cache, must-revalidate"),
                      self.assets.response(alias).headers)
        self.assertEqual(self.router.match("POST", path).allow, "GET")
        self.assertEqual(self.router.match("GET", path.replace("v" + self.assets.version, "v" + "0"*16)).kind, "not_found")
        self.assertEqual(self.router.match("GET", path + "/more").kind, "not_found")

    def test_content_change_changes_version(self):
        initial = self.assets.version
        (Path(self.tmp.name) / "style.css").write_bytes(b"changed")
        self.assertNotEqual(initial, Assets(self.tmp.name).version)

    def test_symlink_not_served(self):
        filename = "style.css"
        resource = Path(self.tmp.name) / filename
        resource.unlink()
        try:
            resource.symlink_to(Path(self.tmp.name) / "other.css")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        with self.assertRaises(FileNotFoundError):
            self.assets.read(filename)


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from hass_configurator import configurator
        cls.configurator = configurator
        cls.previous_api = configurator.HASS_API
        configurator.HASS_API = None
        cls.server = configurator.SimpleServer(("127.0.0.1", 0),
                                               configurator.RequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.configurator.HASS_API = cls.previous_api

    def request(self, method, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1",
                                              self.server.server_address[1], timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            data = response.read()
            return response, data
        finally:
            connection.close()

    def test_html_and_fingerprinted_static(self):
        result, html = self.request("GET", "/")
        self.assertEqual(result.status, 200)
        self.assertEqual(result.getheader("Cache-Control"), NO_STORE)
        version = self.configurator.HTTP_ROUTER.assets.version
        self.assertIn(("assets/v%s/jquery-3.6.0.min.js" % version).encode(), html)
        static, data = self.request("GET", "/assets/v%s/style.css" % version)
        self.assertEqual(static.status, 200)
        self.assertEqual(static.getheader("Cache-Control"), IMMUTABLE_CACHE)
        self.assertEqual(static.getheader("X-Content-Type-Options"), "nosniff")
        self.assertEqual(static.getheader("Content-Type"), "text/css; charset=utf-8")
        self.assertGreater(len(data), 10)

    def test_legacy_api_is_exact_and_not_cached(self):
        ok, content = self.request("GET", "/api/prefs")
        self.assertEqual(ok.status, 200)
        self.assertIn(b"ui_theme", content)
        self.assertEqual(ok.getheader("Cache-Control"), NO_STORE)
        bad, _ = self.request("GET", "/spoof/api/prefs")
        self.assertEqual(bad.status, 404)
        mismatch, _ = self.request("GET", "/api/save")
        self.assertEqual(mismatch.status, 405)
        self.assertEqual(mismatch.getheader("Allow"), "POST")

    def test_missing_assets_wrong_methods_and_spoofed_ingress_header(self):
        missing, _ = self.request("GET", "/assets/v0000000000000000/style.css")
        self.assertEqual(missing.status, 404)
        no_post, _ = self.request("POST", "/style.css", headers={"Content-Length": "0"})
        self.assertEqual(no_post.status, 405)
        bad, _ = self.request("GET", "/%2e%2e/api/prefs")
        self.assertEqual(bad.status, 400)
        spoof, body = self.request("GET", "/", headers={
            "X-Ingress-Path": "/attacker-controlled/",
        })
        self.assertEqual(spoof.status, 200)
        self.assertNotIn(b"attacker-controlled", body)


if __name__ == "__main__":
    unittest.main()
