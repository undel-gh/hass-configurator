"""Security policy source construction is strict and independent of HTTP input."""
import unittest
from hass_configurator.csp import configured_websocket, new_nonce, page_headers


class CSPTests(unittest.TestCase):
    def test_approved_endpoint_and_derivation(self):
        self.assertEqual(configured_websocket("http://127.0.0.1:8123/api/", None),
                         "ws://127.0.0.1:8123/api/websocket")
        self.assertEqual(configured_websocket("https://ha.example.test/api", None),
                         "wss://ha.example.test/api/websocket")
        self.assertEqual(configured_websocket(None, "wss://HA.example.test:8443/local/ws"),
                         "wss://ha.example.test:8443/local/ws")
        self.assertEqual(configured_websocket(None, None), "")

    def test_explicit_invalid_override_cannot_fall_back_or_inject_policy(self):
        for invalid in (
            "", "https://ha.example.test/ws", "ws://*/api/websocket",
            "ws://user:secret@ha.example.test/api/websocket",
            "ws://ha.example.test/api/websocket?token=secret",
            "ws://ha.example.test/api/websocket#fragment",
            "ws://ha.example.test/api/websocket;script-src *",
            "ws://ha.example.test/api/websocket\r\nX-Evil: yes",
            "ws://ha.example.test:0/api/websocket",
            "ws://ha.example.test:65536/api/websocket",
            "ws://ha.example.test:080/api/websocket",
            "ws://ha.example.test:/api/websocket",
            "ws://ha.example.test/api/%2e%2e/ws",
            "ws://ha.example.test/api/../ws",
            "ws://ha.example.test/api//ws",
            "ws://ha.example.test/api/",
            "ws://[::1]:8123/api/websocket",
            "ws://ha.example.test",
            True,
        ):
            with self.subTest(invalid=invalid):
                self.assertEqual(
                    configured_websocket("http://127.0.0.1:8123/api/", invalid), "")
        self.assertEqual(configured_websocket("http://ha.example.test/api/?token=x", None), "")
        self.assertEqual(configured_websocket("malformed", None), "")

    def test_header_does_not_accept_unsafe_inputs(self):
        nonce = new_nonce()
        self.assertNotEqual(nonce, new_nonce())
        for value in ("ws://ha.example.test/ws; script-src *", "ws://*.test/ws",
                      "ws://u:p@ha.example.test/ws", "wss://ha.example.test/ws?token=x"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                page_headers(nonce, value)
        with self.assertRaises(ValueError):
            page_headers("bad; nonce", "")
        policies = dict(page_headers(nonce, "wss://ha.example.test:8443/api/websocket"))
        for policy in policies.values():
            self.assertIn("connect-src 'self' wss://ha.example.test:8443/api/websocket;", policy)
            self.assertNotIn("unsafe-eval", policy)
            self.assertNotIn("report-uri", policy)
            self.assertNotIn("report-to", policy)


if __name__ == "__main__":
    unittest.main()
