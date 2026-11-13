"""Validate relative access redirect compatibility with opaque Ingress prefixes."""
import http.client
import threading
import unittest
from urllib.parse import urljoin

from hass_configurator import configurator


class SesameRedirectTests(unittest.TestCase):
    def test_redirect_is_relative_to_external_ingress_document(self):
        before_token = configurator.SESAME
        before_hass_api = configurator.HASS_API
        before_allow = list(configurator.ALLOWED_NETWORKS)
        before_banned = list(configurator.BANNED_IPS)
        server = None
        thread = None
        try:
            configurator.SESAME = "safe-e2e-redirect-token"
            configurator.HASS_API = None
            server = configurator.SimpleServer(
                ("127.0.0.1", 0), configurator.RequestHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_address[1], timeout=5)
            try:
                connection.request("GET", "/safe-e2e-redirect-token")
                response = connection.getresponse()
                self.assertEqual(response.status, 302)
                self.assertEqual(response.getheader("Location"), "./")
                self.assertEqual(response.getheader("Cache-Control"), "no-store")
                self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
                headers = response.getheaders()
                self.assertEqual(sum(name.lower() == "cache-control"
                                     for name, _ in headers), 1)
                response.read()
            finally:
                connection.close()

            # An external path is stripped by the Supervisor. Its browser
            # resolves the redirect relative to the original prefixed URL.
            external = ("https://ha.example.invalid/api/hassio_ingress/"
                        "opaque-session/safe-e2e-redirect-token")
            self.assertEqual(urljoin(external, "./"),
                             "https://ha.example.invalid/api/hassio_ingress/"
                             "opaque-session/")
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            if thread is not None:
                thread.join(timeout=5)
            configurator.SESAME = before_token
            configurator.HASS_API = before_hass_api
            configurator.ALLOWED_NETWORKS[:] = before_allow
            configurator.BANNED_IPS[:] = before_banned


    def test_totp_access_redirect_is_non_cacheable_before_router(self):
        class FakeTOTP:
            @staticmethod
            def verify(value):
                return value == "local-test-code"

        before_sesame = configurator.SESAME
        before_totp = configurator.TOTP
        before_hass_api = configurator.HASS_API
        before_allow = list(configurator.ALLOWED_NETWORKS)
        before_banned = list(configurator.BANNED_IPS)
        server = None
        thread = None
        try:
            configurator.SESAME = None
            configurator.TOTP = FakeTOTP()
            configurator.HASS_API = None
            server = configurator.SimpleServer(
                ("127.0.0.1", 0), configurator.RequestHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_address[1], timeout=5)
            try:
                connection.request("GET", "/local-test-code")
                response = connection.getresponse()
                self.assertEqual(response.status, 302)
                self.assertEqual(response.getheader("Location"), "./")
                self.assertEqual(response.getheader("Cache-Control"), "no-store")
                self.assertEqual(response.getheader("X-Content-Type-Options"), "nosniff")
                headers = response.getheaders()
                self.assertEqual(sum(name.lower() == "cache-control"
                                     for name, _ in headers), 1)
                response.read()
            finally:
                connection.close()
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            if thread is not None:
                thread.join(timeout=5)
            configurator.SESAME = before_sesame
            configurator.TOTP = before_totp
            configurator.HASS_API = before_hass_api
            configurator.ALLOWED_NETWORKS[:] = before_allow
            configurator.BANNED_IPS[:] = before_banned


if __name__ == "__main__":
    unittest.main()
