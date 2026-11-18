#!/usr/bin/env python3
"""Read-only HAOS-11 Supervisor REST / event observer WebSocket probe.

This is run ONLY in an explicitly generated local test app with
homeassistant_api: true. It MUST NOT be imported into the editor, expose
SUPERVISOR_TOKEN to HTML, send a command to HA, or log URL/token/user data.
Uses the stdlib only; validates the actual Supervisor Core proxy endpoints.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import struct
import urllib.request

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
STATUS_PATH = Path("/tmp/hc-ha-probe-status.json")
MAX_FRAME = 16384


def rest_read(token):
    request = urllib.request.Request(
        "http://supervisor/core/api/config",
        headers={"Authorization": "Bearer " + token},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status != 200:
            return False
        # This result stays in memory. Never log HA configuration details.
        value = json.loads(response.read(MAX_FRAME + 1))
    return isinstance(value, dict) and "version" in value


def _exact(stream, size):
    out = stream.read(size)
    if len(out) != size:
        raise EOFError("Short WebSocket read")
    return out


def _read_frame(stream):
    first, second = _exact(stream, 2)
    if first & 0x70:
        raise ValueError("Unsupported WS reserved bits")
    opcode = first & 0x0F
    size = second & 0x7F
    if size == 126:
        size = struct.unpack("!H", _exact(stream, 2))[0]
    elif size == 127:
        size = struct.unpack("!Q", _exact(stream, 8))[0]
    if size > MAX_FRAME:
        raise ValueError("Oversized WS frame")
    # Server-to-client frames must be unmasked.
    if second & 0x80:
        raise ValueError("Masked server WS frame")
    return opcode, _exact(stream, size)


def _send_frame(sock, payload, opcode=1):
    if len(payload) > MAX_FRAME:
        raise ValueError("Oversized outbound WS frame")
    mask = os.urandom(4)
    length = len(payload)
    lead = bytes((0x80 | opcode, 0x80 | length)) if length < 126 else (
        bytes((0x80 | opcode, 0x80 | 126)) + struct.pack("!H", length))
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    sock.sendall(lead + mask + masked)


def _send_json(sock, value):
    _send_frame(sock, json.dumps(value, separators=(",", ":")).encode("utf8"))


def _recv_json(stream, sock):
    for _ in range(8):
        opcode, payload = _read_frame(stream)
        if opcode == 9:  # ping, answer with masked pong
            _send_frame(sock, payload, opcode=10)
            continue
        if opcode != 1:
            raise ValueError("Expected HA WS text frame")
        return json.loads(payload)
    raise ValueError("Too many WS control frames")


def ws_observer(token):
    """Return (authenticated, subscribed) without retaining event contents."""
    authenticated = False
    with socket.create_connection(("supervisor", 80), timeout=5) as sock:
        sock.settimeout(5)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake = (
            "GET /core/websocket HTTP/1.1\r\n"
            "Host: supervisor\r\n"
            "Connection: Upgrade\r\n"
            "Upgrade: websocket\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Sec-WebSocket-Key: " + key + "\r\n\r\n"
        )
        sock.sendall(handshake.encode("ascii"))
        with sock.makefile("rb") as stream:
            status = stream.readline(1024)
            if b" 101 " not in status:
                raise ValueError("Supervisor WS handshake refused")
            headers = {}
            for _ in range(40):
                line = stream.readline(2048)
                if line == b"\r\n":
                    break
                if b":" not in line:
                    raise ValueError("Invalid WS handshake headers")
                name, value = line.split(b":", 1)
                headers[name.strip().lower()] = value.strip()
            expected = base64.b64encode(
                hashlib.sha1((key + GUID).encode("ascii")).digest())
            if headers.get(b"sec-websocket-accept") != expected:
                raise ValueError("WS handshake accept mismatch")
            if _recv_json(stream, sock).get("type") != "auth_required":
                raise ValueError("Unexpected HA WS pre-auth frame")
            _send_json(sock, {"type": "auth", "access_token": token})
            authenticated = _recv_json(stream, sock).get("type") == "auth_ok"
            if not authenticated:
                return False, False
            _send_json(sock, {"id": 1, "type": "subscribe_events",
                              "event_type": "homeassistant_started"})
            result = _recv_json(stream, sock)
            subscribed = (result.get("type") == "result"
                          and result.get("id") == 1
                          and result.get("success") is True)
            if subscribed:
                _send_json(sock, {"id": 2, "type": "unsubscribe_events",
                                  "subscription": 1})
            return True, subscribed


def main():
    # Never include exception messages or network endpoints in logs.
    report = {"schema": 1, "mode": "supervisor-readonly",
              "rest": "failed", "ws_auth": "failed",
              "ws_subscribe": "failed"}
    token = os.environ.get("SUPERVISOR_TOKEN", "")
    if token:
        try:
            if rest_read(token):
                report["rest"] = "ok"
        except Exception:
            pass
        try:
            authenticated, subscribed = ws_observer(token)
            if authenticated:
                report["ws_auth"] = "ok"
            if subscribed:
                report["ws_subscribe"] = "ok"
        except Exception:
            pass
    else:
        report["mode"] = "missing-token"
    # Only literal, fixed-key status enums are ever written.
    STATUS_PATH.write_text(json.dumps(report, sort_keys=True) + "\n",
                           encoding="utf8")
    STATUS_PATH.chmod(0o644)
    print("HAOS-11 read-only probe: REST=%s WS-auth=%s WS-subscribe=%s" %
          (report["rest"], report["ws_auth"], report["ws_subscribe"]),
          flush=True)


if __name__ == "__main__":
    main()
