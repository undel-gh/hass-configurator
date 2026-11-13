"""Permanent HTTP routing and package-asset boundary.

The old API implementations remain in configurator.py until their P1 migration.
They MUST pass through this exact-path, method-aware dispatcher first.
"""
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
import re


# Explicitly enumerate the existing public routes; suffix matching is forbidden.
GET_API = frozenset((
    "/api/file", "/api/download", "/api/listdir", "/api/abspath",
    "/api/parent", "/api/prefs", "/api/version", "/api/netstat", "/api/restart",
    "/api/check_config", "/api/reload_automations", "/api/reload_scripts",
    "/api/reload_groups", "/api/reload_core",
))
POST_API = frozenset((
    "/api/save", "/api/upload", "/api/rename", "/api/delete",
    "/api/exec_command", "/api/gitadd", "/api/gitdiff", "/api/commit",
    "/api/checkout", "/api/newbranch", "/api/init", "/api/push",
    "/api/stash", "/api/newfolder", "/api/newfile",
    "/api/allowed_networks", "/api/banned_ips", "/api/prefs",
))
# Transitional aliases remain revalidated for existing clients. New HTML uses
# versioned paths and no permanent redirect is necessary.
PACKAGE_ASSETS = {
    "jquery-3.6.0.min.js": "text/javascript; charset=utf-8",
    "js-yaml.min.js": "text/javascript; charset=utf-8",
    "materialize.min.js": "text/javascript; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "material-icons.fallback.css": "text/css; charset=utf-8",
    "flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2": "font/woff2",
}
IMMUTABLE_CACHE = "private, max-age=31536000, immutable"
REVALIDATE_CACHE = "no-cache, must-revalidate"
NO_STORE = "no-store"
_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_.-]+$")
_VERSION_PATTERN = re.compile(r"^v[0-9a-f]{16}$")


@dataclass(frozen=True)
class Response:
    """An HTTP response emitted once by the transport adapter."""
    status: int
    body: bytes = b""
    content_type: str = "text/plain; charset=utf-8"
    headers: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class Match:
    """Dispatch result; legacy API/page dispatch happens only after matching."""
    kind: str
    path: str = ""
    asset: str = ""
    immutable: bool = False
    allow: str = ""


class Assets:
    """Small allowlisted package resource store. No arbitrary path reads."""

    def __init__(self, root=None):
        # Unit fixtures can supply a minimal isolated resource root. The real
        # installed application MUST have the complete vendored manifest.
        production_root = root is None
        self.root = Path(root) if root is not None else Path(__file__).parent
        self.root = self.root.resolve(strict=True)
        self.mime = dict(PACKAGE_ASSETS)
        self._vendor_hashes = {}
        manifest_path = self.root / "vendor" / "manifest.json"
        if production_root and not manifest_path.is_file():
            raise RuntimeError("Missing vendored assets manifest in installed package")
        if manifest_path.is_file():
            if manifest_path.is_symlink():
                raise RuntimeError("Unsafe vendor manifest symlink")
            manifest = json.loads(manifest_path.read_text(encoding="utf8"))
            if manifest.get("schema") != 1 or not isinstance(manifest.get("resources"), dict):
                raise RuntimeError("Invalid vendored assets manifest")
            for name, expected_hash in manifest["resources"].items():
                parts = PurePosixPath(name).parts
                if (not name.startswith("vendor/") or
                        not parts or any(not _SAFE_SEGMENT.fullmatch(p) for p in parts) or
                        not isinstance(expected_hash, str) or
                        len(expected_hash) != 64 or
                        any(c not in "0123456789abcdef" for c in expected_hash)):
                    raise RuntimeError("Invalid vendor resource entry: " + name)
                self._vendor_hashes[name] = expected_hash
                self.mime[name] = self._guess_mime(name)
        hashes = []
        self._snapshot = {}
        for name in sorted(self.mime):
            resource = self._resource_path(name)
            try:
                content = resource.read_bytes()
            except OSError as exc:
                raise RuntimeError("Missing packaged static asset: " + name) from exc
            hashed = sha256(content).hexdigest()
            if name in self._vendor_hashes and self._vendor_hashes[name] != hashed:
                raise RuntimeError("Vendored asset digest mismatch: " + name)
            self._snapshot[name] = content
            hashes.append(name.encode("ascii") + b"\x00" + hashed.encode("ascii"))
        self.version = sha256(b"\n".join(hashes)).hexdigest()[:16]

    @staticmethod
    def _guess_mime(name):
        return {
            ".js": "text/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".woff2": "font/woff2", ".woff": "font/woff",
            ".ttf": "font/ttf", ".eot": "application/vnd.ms-fontobject",
            ".svg": "image/svg+xml", ".json": "application/json",
            ".png": "image/png", ".gif": "image/gif",
            ".jpg": "image/jpeg",
            ".html": "text/html; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
        }.get(PurePosixPath(name).suffix.lower(), "application/octet-stream")

    def _resource_path(self, name):
        if name not in self.mime:
            raise FileNotFoundError(name)
        resource = self.root / name
        # Never follow a symlink in an allowlisted package path.
        component = self.root
        for part in resource.relative_to(self.root).parts:
            component = component / part
            if component.is_symlink():
                raise FileNotFoundError(name)
        try:
            resource.resolve(strict=False).relative_to(self.root)
        except ValueError as exc:
            raise FileNotFoundError(name) from exc
        return resource

    def read(self, name):
        # Immutable URL must yield immutable bytes during this process.
        # Recheck symlink safety if a package path changes after startup.
        self._resource_path(name)
        return self._snapshot[name]

    def response(self, match):
        try:
            payload = self.read(match.asset)
        except (FileNotFoundError, OSError):
            return error_response(404)
        return Response(200, payload, self.mime[match.asset], (
            ("Cache-Control", IMMUTABLE_CACHE if match.immutable else REVALIDATE_CACHE),
        ))


def error_response(status, allow=""):
    labels = {400: "Bad request", 404: "Not found", 405: "Method not allowed"}
    hdrs = [("Cache-Control", NO_STORE)]
    if allow:
        hdrs.append(("Allow", allow))
    return Response(status, labels.get(status, "Request error").encode("utf-8"),
                    headers=tuple(hdrs))


def _clean_path(url):
    """Reject ambiguous encodings before exact-path matching."""
    parsed = urlsplit(url)
    path = parsed.path
    if not path.startswith("/") or "\\" in path or any(ord(ch) < 32 for ch in path):
        raise ValueError("Invalid path")
    if "%" in path:
        # Do not normalize encoded separators or dot paths into a valid route.
        raise ValueError("Encoded route path not supported")
    if any(part in (".", "..") for part in path.split("/")):
        raise ValueError("Traversal")
    return path


class Router:
    """Method/path dispatcher reused by all current and future controllers."""

    def __init__(self, assets=None):
        self.assets = assets if assets is not None else Assets()
        # Security admission is owned by the permanent router, not by
        # ad-hoc legacy handler conditions. Import after Response is defined.
        from hass_configurator.api_security import ApiPolicy
        self.security = ApiPolicy()

    def match(self, method, url):
        try:
            path = _clean_path(url)
        except ValueError:
            return Match("bad_request")

        if path == "/":
            return Match("legacy_page" if method == "GET" else "method_not_allowed",
                         path, allow="GET")

        if path in GET_API or path in POST_API:
            allowed = set()
            if path in GET_API:
                allowed.add("GET")
            if path in POST_API:
                allowed.add("POST")
            if method not in allowed:
                return Match("method_not_allowed", path, allow=", ".join(sorted(allowed)))
            return Match("legacy_api", path)

        # Exact alias and versioned asset matches are supported. All other
        # paths (including suffixes like /evil/api/save) are rejected.
        if path.count("/") == 1 and path[1:] in PACKAGE_ASSETS:
            if method != "GET":
                return Match("method_not_allowed", path, allow="GET")
            return Match("asset", path, asset=path[1:])

        if path.startswith("/assets/"):
            parts = path.split("/")
            name = "/".join(parts[3:])
            if (len(parts) < 4 or
                    not _VERSION_PATTERN.fullmatch(parts[2]) or
                    not name or
                    any(not _SAFE_SEGMENT.fullmatch(p) for p in parts[3:]) or
                    name not in self.assets.mime or
                    parts[2] != "v" + self.assets.version):
                return Match("not_found", path)
            if method != "GET":
                return Match("method_not_allowed", path, allow="GET")
            return Match("asset", path, asset=name, immutable=True)

        return Match("not_found", path)


def send_response(handler, response):
    """Write a response exactly once for dispatcher-owned paths."""
    handler.send_response(response.status)
    handler.send_header("Content-Type", response.content_type)
    handler.send_header("X-Content-Type-Options", "nosniff")
    for key, value in response.headers:
        handler.send_header(key, value)
    handler.send_header("Content-Length", str(len(response.body)))
    handler.end_headers()
    handler.wfile.write(response.body)
