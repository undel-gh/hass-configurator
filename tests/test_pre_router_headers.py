"""Pre-router response headers: socket-level regression for #2 closeout.

Exercise RequestHandler and AuthHandler without any external HA connection or
sensitive actions. Authentication and access decisions are unchanged.
"""
import base64
import http.client
import threading
import unittest
from unittest.mock import patch

from hass_configurator import configurator as cfg


class PreRouterHeadersTests(unittest.TestCase):
    @staticmethod
    def request(server, method, headers=None):
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_address[1], timeout=5)
        try:
            connection.request(method, "/", body=b"" if method == "POST" else None,
                               headers=headers or {})
            response = connection.getresponse()
            return response.status, response.getheaders(), response.read()
        finally:
            connection.close()

    def assert_no_store(self, result, expected_status):
        status, headers, _ = result
        self.assertEqual(status, expected_status)
        for key, value in (
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        ):
            selected = [v for k, v in headers if k.lower() == key.lower()]
            self.assertEqual(selected, [value], "%s must appear exactly once" % key)

    def test_pre_router_host_denial_on_both_transports_and_methods(self):
        old_hostname = cfg.VERIFY_HOSTNAME
        cfg.VERIFY_HOSTNAME = "valid.example"
        try:
            for handler in (cfg.RequestHandler, cfg.AuthHandler):
                server = cfg.SimpleServer(("127.0.0.1", 0), handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    for method in ("GET", "POST"):
                        with self.subTest(handler=handler.__name__, method=method):
                            result = self.request(
                                server, method, {"Host": "evil.example"})
                            self.assert_no_store(result, 403)
                            self.assertEqual(result[2], b"Forbidden")
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)
        finally:
            cfg.VERIFY_HOSTNAME = old_hostname

    def test_pre_router_access_block_from_request_handler(self):
        server = cfg.SimpleServer(("127.0.0.1", 0), cfg.RequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.object(cfg, "verify_hostname", return_value=True), \
                 patch.object(cfg, "check_access", return_value=False):
                for method in ("GET", "POST"):
                    with self.subTest(method=method):
                        result = self.request(server, method)
                        self.assert_no_store(result, 420)
                        self.assertEqual(result[2], b"Policy not fulfilled")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_basic_challenge_and_ban_share_pre_router_header_policy(self):
        old_user, old_password, old_ban = cfg.USERNAME, cfg.PASSWORD, cfg.BANLIMIT
        before_banned = dict(cfg.FAIL2BAN_IPS)
        cfg.USERNAME = "header-review"
        cfg.PASSWORD = "header-review-secret"
        cfg.BANLIMIT = 0
        server = None
        thread = None
        try:
            server = cfg.SimpleServer(("127.0.0.1", 0), cfg.AuthHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            with patch.object(cfg, "verify_hostname", return_value=True):
                for method in ("GET", "POST"):
                    with self.subTest(kind="challenge", method=method):
                        result = self.request(server, method)
                        self.assert_no_store(result, 401)
                        headers = dict(result[1])
                        self.assertIn("Basic", headers.get("WWW-Authenticate", ""))
                        self.assertEqual(headers.get("Content-type"), "text/html")

                cfg.BANLIMIT = 1
                wrong = base64.b64encode(
                    b"not-the-header-review-user:wrong").decode("ascii")
                for method in ("GET", "POST"):
                    with self.subTest(kind="ban", method=method):
                        result = self.request(
                            server, method, {"Authorization": "Basic " + wrong})
                        self.assert_no_store(result, 420)
                        self.assertEqual(result[2], b"Policy not fulfilled")
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            if thread is not None:
                thread.join(timeout=5)
            cfg.USERNAME, cfg.PASSWORD, cfg.BANLIMIT = (
                old_user, old_password, old_ban)
            cfg.FAIL2BAN_IPS.clear()
            cfg.FAIL2BAN_IPS.update(before_banned)


if __name__ == "__main__":
    unittest.main()
