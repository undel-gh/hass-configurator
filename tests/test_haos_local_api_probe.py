"""Offline-only tests for the opt-in, read-only Supervisor API/WS probe."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from scripts import haos_local_api_probe as probe


class LocalAPIProbeTests(unittest.TestCase):
    def test_main_never_prints_credentials_configuration_or_events(self):
        token = "bearer-unit-test-confidential-value"
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "status.json"
            output = io.StringIO()
            with patch.object(probe, "STATUS_PATH", dest), \
                 patch.dict(os.environ, {"SUPERVISOR_TOKEN": token}), \
                 patch.object(probe, "rest_read", return_value=True) as rest, \
                 patch.object(probe, "ws_observer",
                              return_value=(True, True)) as ws, \
                 redirect_stdout(output):
                probe.main()
            rest.assert_called_once_with(token)
            ws.assert_called_once_with(token)
            logged = output.getvalue()
            status = json.loads(dest.read_text(encoding="utf8"))
            self.assertNotIn(token, logged)
            self.assertNotIn(token, dest.read_text(encoding="utf8"))
            self.assertEqual(status, {
                "schema": 1,
                "mode": "supervisor-readonly",
                "rest": "ok",
                "ws_auth": "ok",
                "ws_subscribe": "ok",
            })
            self.assertIn("REST=ok WS-auth=ok WS-subscribe=ok", logged)
            self.assertEqual(dest.stat().st_mode & 0o777, 0o644)

    def test_missing_token_fails_closed_without_network_use(self):
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "status.json"
            with patch.object(probe, "STATUS_PATH", dest), \
                 patch.dict(os.environ, {}, clear=True), \
                 patch.object(probe, "rest_read") as rest, \
                 patch.object(probe, "ws_observer") as ws, \
                 redirect_stdout(io.StringIO()):
                probe.main()
            rest.assert_not_called()
            ws.assert_not_called()
            result = json.loads(dest.read_text(encoding="utf8"))
            self.assertEqual(result["mode"], "missing-token")
            self.assertEqual(result["rest"], "failed")

    def test_rest_is_fixed_supervisor_read_only_get(self):
        class FakeResponse:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self, _size):
                return b'{"version":"2026.11.0"}'

        with patch.object(probe.urllib.request, "urlopen",
                          return_value=FakeResponse()) as urlopen:
            self.assertTrue(probe.rest_read("test-private-value"))
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://supervisor/core/api/config")
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("Bearer test-private-value",
                      list(request.header_items())[0][1])
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)

    def test_ws_server_frame_parser_rejects_masks_and_large_payloads(self):
        self.assertEqual(probe._read_frame(io.BytesIO(b"\x81\x03hey")),
                         (1, b"hey"))
        with self.assertRaises(ValueError):
            probe._read_frame(io.BytesIO(b"\x81\x83abcd"))
        oversized = b"\x81\x7e" + struct.pack("!H", probe.MAX_FRAME + 1)
        with self.assertRaises(ValueError):
            probe._read_frame(io.BytesIO(oversized))

    def test_ws_client_frames_are_masked(self):
        class FakeSocket:
            payload = None

            def sendall(self, value):
                self.payload = value

        sock = FakeSocket()
        probe._send_frame(sock, b'{"type":"auth"}')
        raw = sock.payload
        self.assertEqual(raw[0], 0x81)
        self.assertTrue(raw[1] & 0x80, "Clients must mask frames")
        size = raw[1] & 0x7f
        mask = raw[2:6]
        plain = bytes(value ^ mask[i % 4]
                      for i, value in enumerate(raw[6:]))
        self.assertEqual(size, len(plain))
        self.assertEqual(plain, b'{"type":"auth"}')


if __name__ == "__main__":
    unittest.main()
