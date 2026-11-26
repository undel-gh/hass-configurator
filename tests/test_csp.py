"""Security policy source construction is strict and independent of HTTP input."""
import unittest
from html.parser import HTMLParser
from pathlib import Path
import re
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


    def test_template_has_no_executable_attributes_and_bindings_are_static(self):
        class Inventory(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.events = []
                self.script_attributes = []
                self.bindings = set()
                self.javascript_urls = []

            def handle_starttag(self, tag, attrs):
                data = dict(attrs)
                if tag == "script":
                    self.script_attributes.append(data)
                for name, value in attrs:
                    if name.startswith("on"):
                        self.events.append(name)
                    if name in ("href", "src", "action", "formaction") and value:
                        if value.strip().lower().startswith("javascript:"):
                            self.javascript_urls.append(name)
                    if name in ("data-hc-click", "data-hc-change"):
                        self.bindings.add((name[8:], value))

        root = Path(__file__).resolve().parents[1] / "hass_configurator"
        inventory = Inventory()
        inventory.feed((root / "dev.html").read_text(encoding="utf-8"))
        self.assertEqual(inventory.events, [])
        self.assertEqual(inventory.javascript_urls, [])
        inline = [item for item in inventory.script_attributes if "src" not in item]
        self.assertTrue(inline)
        self.assertTrue(all(item.get("nonce") == "$csp_nonce" for item in inline))
        handlers = (root / "ui-handlers.js").read_text(encoding="utf-8")
        static = set(re.findall(r"bind\('(click|change)', '(hc-\d+)', function", handlers))
        self.assertTrue(static)
        self.assertEqual(inventory.bindings, static)
        for name in ("ui-handlers.js", "ace-bootstrap.js"):
            self.assertTrue(any(item.get("src") == "assets/v$asset_version/" + name
                                for item in inventory.script_attributes))
        for source in ("dev.html", "ui-handlers.js", "ace-bootstrap.js"):
            code = (root / source).read_text(encoding="utf-8")
            self.assertNotRegex(code, r"\b(?:eval\s*\(|new\s+Function\s*\()")

if __name__ == "__main__":
    unittest.main()
