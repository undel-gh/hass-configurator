"""Independent inventory of legacy routes and execution smoke tests.

The expected GET/POST lists are intentionally not imported from the Router:
deleting an endpoint from the implementation must fail this contract.
"""
import base64
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.parse import quote, urlencode

from hass_configurator import configurator as cfg
from hass_configurator.http_routing import Assets, GET_API, POST_API, Router

EXPECTED_GET = {
    "/api/file", "/api/download", "/api/listdir", "/api/abspath",
    "/api/parent", "/api/prefs", "/api/version", "/api/netstat", "/api/restart",
    "/api/check_config", "/api/reload_automations", "/api/reload_scripts",
    "/api/reload_groups", "/api/reload_core",
}
EXPECTED_POST = {
    "/api/save", "/api/upload", "/api/rename", "/api/delete",
    "/api/exec_command", "/api/gitadd", "/api/gitdiff", "/api/commit",
    "/api/checkout", "/api/newbranch", "/api/init", "/api/push",
    "/api/stash", "/api/newfolder", "/api/newfile",
    "/api/allowed_networks", "/api/banned_ips", "/api/prefs",
}


def make_request(server, method, route, body=None, headers=None):
    connection = http.client.HTTPConnection(
        "127.0.0.1", server.server_address[1], timeout=5)
    try:
        request_headers = dict(headers or {})
        # This helper models the first-party AJAX client. Negative CSRF and
        # forged-client cases are tested separately in test_api_security.py.
        if method == "POST":
            request_headers.setdefault(
                "X-CSRF-Token", cfg.HTTP_ROUTER.security.csrf_token)
        connection.request(method, route, body=body, headers=request_headers)
        response = connection.getresponse()
        result = (response.status, dict(response.getheaders()), response.read())
        return result
    finally:
        connection.close()


class LegacyRouteRegistryTests(unittest.TestCase):
    def test_all_legacy_api_paths_are_explicit_and_method_checked(self):
        self.assertEqual(GET_API, EXPECTED_GET)
        self.assertEqual(POST_API, EXPECTED_POST)
        router = Router(Assets())
        for path in sorted(EXPECTED_GET | EXPECTED_POST):
            for method, expected in (
                ("GET", "legacy_api" if path in EXPECTED_GET else "method_not_allowed"),
                ("POST", "legacy_api" if path in EXPECTED_POST else "method_not_allowed"),
            ):
                with self.subTest(path=path, method=method):
                    result = router.match(method, path)
                    self.assertEqual(result.kind, expected)
                    if result.kind == "method_not_allowed":
                        self.assertIn("GET" if method == "POST" else "POST", result.allow)

    def test_query_does_not_change_exact_route(self):
        router = Router(Assets())
        self.assertEqual(router.match(
            "GET", "/api/file?filename=%2Ftmp%2Ftest.yaml").kind, "legacy_api")
        self.assertEqual(router.match(
            "POST", "/api/prefs?source=ui").kind, "legacy_api")
        self.assertEqual(router.match(
            "POST", "/evil/api/save?ignored=1").kind, "not_found")


class LegacyLoopbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.old_hass_api = cfg.HASS_API
        cls.old_basepath = cfg.BASEPATH
        cfg.HASS_API = None
        cfg.BASEPATH = cls.workspace.name
        cls.server = cfg.SimpleServer(("127.0.0.1", 0), cfg.RequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cfg.HASS_API = cls.old_hass_api
        cfg.BASEPATH = cls.old_basepath
        cls.workspace.cleanup()

    def test_version_identity_matches_distribution_runtime_and_ui(self):
        from importlib.metadata import version as installed_version

        self.assertEqual(cfg.VERSION, installed_version("hass-configurator"))
        status, headers, raw = make_request(self.server, "GET", "/api/version")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertEqual(json.loads(raw), {"version": cfg.VERSION})
        status, headers, html = make_request(self.server, "GET", "/")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertIn((">" + cfg.VERSION + "</a>").encode("utf8"), html)
        status, headers, _ = make_request(self.server, "POST", "/api/version",
                                          b"", {"Content-Type": "application/json"})
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET")

    def test_post_prefs_json_and_get_round_trip(self):
        body = json.dumps({"ui_theme": "dark"}).encode("utf-8")
        status, headers, response = make_request(
            self.server, "POST", "/api/prefs?source=test",
            body, {"Content-Type": "application/json"})
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(response)["error"])
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        status, _, response = make_request(self.server, "GET", "/api/prefs")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(response)["ui_theme"], "dark")
        # Restore expected default without touching users' project files.
        body = json.dumps({"ui_theme": "auto"}).encode("utf-8")
        self.assertEqual(make_request(
            self.server, "POST", "/api/prefs", body,
            {"Content-Type": "application/json"})[0], 200)

    def test_post_save_and_file_query_round_trip(self):
        filename = Path(self.workspace.name) / "editor test.yaml"
        content = "test_key: value & another\nline: caf\u00e9\n"
        body = urlencode({"filename": str(filename), "text": content}).encode("utf-8")
        status, headers, response = make_request(
            self.server, "POST", "/api/save", body,
            {"Content-Type": "application/x-www-form-urlencoded"})
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertFalse(json.loads(response)["error"], response)
        self.assertEqual(filename.read_text(encoding="utf-8"), content)
        status, _, loaded = make_request(
            self.server, "GET",
            "/api/file?filename=" + quote(str(filename), safe=""))
        self.assertEqual(status, 200)
        self.assertEqual(loaded.decode("utf-8"), content)

    def test_unsupported_methods_are_not_dispatched_to_legacy_api(self):
        # Explicit choice: HEAD/PUT/DELETE are not implemented in this
        # transitional release. BaseHTTPRequestHandler emits path-agnostic 501,
        # avoiding future auth bypass and non-idempotent GET-as-HEAD behavior.
        for method in ("HEAD", "PUT", "DELETE"):
            with self.subTest(method=method):
                status, _, _ = make_request(
                    self.server, method, "/api/save")
                self.assertEqual(status, 501)


class AuthLoopbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_username, cls.old_password = cfg.USERNAME, cfg.PASSWORD
        cls.old_hass_api = cfg.HASS_API
        cls.old_basepath = cfg.BASEPATH
        cls.workspace = tempfile.TemporaryDirectory()
        cfg.USERNAME, cfg.PASSWORD = "review-user", "long-review-password"
        cfg.HASS_API = None
        cfg.BASEPATH = cls.workspace.name
        cls.server = cfg.SimpleServer(("127.0.0.1", 0), cfg.AuthHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        token = base64.b64encode(b"review-user:long-review-password").decode()
        cls.auth = {"Authorization": "Basic " + token}

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cfg.USERNAME, cfg.PASSWORD = cls.old_username, cls.old_password
        cfg.HASS_API = cls.old_hass_api
        cfg.BASEPATH = cls.old_basepath
        cls.workspace.cleanup()

    def test_authhandler_protects_get_and_post(self):
        status, headers, _ = make_request(
            self.server, "GET", "/api/prefs")
        self.assertEqual(status, 401)
        self.assertIn("Basic", headers.get("WWW-Authenticate", ""))
        status, _, _ = make_request(
            self.server, "GET", "/api/prefs", headers=self.auth)
        self.assertEqual(status, 200)

        data = json.dumps({"ui_theme": "auto"}).encode()
        status, _, _ = make_request(
            self.server, "POST", "/api/prefs", data,
            {"Content-Type": "application/json"})
        self.assertEqual(status, 401)
        authorized_headers = dict(self.auth)
        authorized_headers["Content-Type"] = "application/json"
        status, _, response = make_request(
            self.server, "POST", "/api/prefs", data, authorized_headers)
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(response)["error"])
        status, _, body = make_request(
            self.server, "GET", "/api/prefs", headers=self.auth)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["ui_theme"], "auto")

        version = cfg.HTTP_ROUTER.assets.version
        resource = "/assets/v%s/style.css" % version
        status, _, _ = make_request(self.server, "GET", resource)
        self.assertEqual(status, 401)
        status, headers, body = make_request(
            self.server, "GET", resource, headers=self.auth)
        self.assertEqual(status, 200)
        self.assertIn("immutable", headers.get("Cache-Control", ""))
        self.assertGreater(len(body), 10)

    def test_unsupported_methods_do_not_disclose_route_existence(self):
        for method in ("HEAD", "PUT", "DELETE"):
            with self.subTest(method=method):
                known = make_request(self.server, method, "/api/prefs")
                unknown = make_request(self.server, method, "/does-not-exist")
                self.assertEqual(known[0], 501)
                self.assertEqual(unknown[0], 501)


if __name__ == "__main__":
    unittest.main()
