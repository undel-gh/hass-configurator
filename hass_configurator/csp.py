"""CSP construction for the authenticated editor document.

Only server configuration supplies additional connect destinations.
Request Host/forwarded headers and browser inputs are not policy inputs.
"""
import re
import secrets
from urllib.parse import urlsplit

_NONCE = re.compile(r"[A-Za-z0-9_-]{32,}")
_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")
_PATH = re.compile(r"/[A-Za-z0-9._~/-]+")


def new_nonce():
    """A fresh 192-bit nonce per no-store editor response."""
    return secrets.token_urlsafe(24)


def _endpoint(value, schemes):
    """Parse an explicit header-safe endpoint or reject it.

    Restrict host syntax to DNS/IPv4 forms understood by CSP host sources.
    IPv6 literals and non-ASCII/escaped paths need compatibility work.
    """
    if not isinstance(value, str) or not value or any(
            ord(ch) < 33 or ord(ch) > 126 for ch in value):
        return None
    if any(ch in value for ch in (";", "'", '"', "*", "\\", "%", "?", "#")):
        return None
    try:
        parts = urlsplit(value)
        host, port = parts.hostname, parts.port
    except ValueError:
        return None
    if (parts.scheme not in schemes or not host or parts.username is not None
            or parts.password is not None or len(host) > 253
            or not all(_LABEL.fullmatch(label) for label in host.split("."))
            or (port is not None and not 1 <= port <= 65535)):
        return None
    path = parts.path or "/"
    if (path != "/" and not _PATH.fullmatch(path)) or any(
            segment in (".", "..") for segment in path.split("/")):
        return None
    if "//" in path:
        return None
    authority = host + (":%d" % port if port is not None else "")
    if parts.netloc.lower() != authority:
        return None
    return parts.scheme, authority, path


def configured_websocket(hass_api, hass_ws_api):
    """Return the operator-configured WS URL; malformed override fails closed."""
    if hass_ws_api is not None:
        parsed = _endpoint(hass_ws_api, ("ws", "wss"))
        if not parsed:
            return ""
        scheme, authority, path = parsed
    else:
        parsed = _endpoint(hass_api, ("http", "https"))
        if not parsed:
            return ""
        scheme, authority, path = parsed
        scheme = "wss" if scheme == "https" else "ws"
        path = path.rstrip("/") + "/websocket"
    # A trailing slash in CSP matches a path prefix, not an endpoint.
    if path.endswith("/"):
        return ""
    return "%s://%s%s" % (scheme, authority, path)


def page_headers(nonce, websocket):
    """Enforce script/network/object/framing controls; observe stricter styles."""
    if not isinstance(nonce, str) or not _NONCE.fullmatch(nonce):
        raise ValueError("Invalid CSP nonce")
    if websocket and configured_websocket(None, websocket) != websocket:
        raise ValueError("Invalid CSP WebSocket endpoint")
    connect = "'self'" + (" " + websocket if websocket else "")
    directives = (
        "default-src 'none'",
        "script-src 'self' 'nonce-%s'" % nonce,
        "script-src-attr 'none'",
        "style-src 'self' 'unsafe-inline'",
        "font-src 'self'",
        "img-src 'self' data: blob:",
        "worker-src 'self' blob:",
        "connect-src " + connect,
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'self'",
        "form-action 'self'",
        "frame-src 'none'",
    )
    enforced = "; ".join(directives) + ";"
    report = "; ".join(
        "style-src 'self'" if item.startswith("style-src ") else item
        for item in directives
    ) + ";"
    # No report-uri/report-to: violations observed only in local browser tests.
    return (("Content-Security-Policy", enforced),
            ("Content-Security-Policy-Report-Only", report))


# Editable SVG/image files are not trusted editor documents.
UNTRUSTED_FILE_POLICY = "sandbox; default-src 'none'; base-uri 'none'; form-action 'none';"
