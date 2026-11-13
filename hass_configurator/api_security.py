"""Server-side authorization, CSRF and directory-fd confined file operations.

Do not infer an authenticated user from X-Forwarded-*, X-Ingress-Path, Host,
or an Origin header. Actual Supervisor identity/trusted proxy semantics are
separately gated by real HA OS testing (#8).
"""
import hmac
import ipaddress
import os
from pathlib import Path
import secrets
from contextlib import contextmanager
from urllib.parse import urlsplit

from hass_configurator.http_routing import Response


# Legacy HA control actions perform outbound service POSTs; they must be
# routed as POST, with the same CSRF and capability checks as other mutations.
HA_CONTROL = frozenset({
    "/api/restart", "/api/check_config", "/api/reload_automations",
    "/api/reload_scripts", "/api/reload_groups", "/api/reload_core",
})
SHELL = frozenset({"/api/exec_command"})
GIT = frozenset({
    "/api/gitadd", "/api/gitdiff", "/api/commit", "/api/checkout",
    "/api/newbranch", "/api/init", "/api/push", "/api/stash",
})
NETWORK = frozenset({"/api/allowed_networks", "/api/banned_ips"})


class ApiPolicy:
    """One request-admission policy shared by all Router legacy API entries."""

    def __init__(self):
        self._token = secrets.token_urlsafe(32)

    @property
    def csrf_token(self):
        return self._token

    @staticmethod
    def _loopback_bound(handler):
        """Not the client IP alone: 0.0.0.0 bound servers are not trusted."""
        try:
            server = ipaddress.ip_address(handler.server.server_address[0])
            client = ipaddress.ip_address(handler.client_address[0])
            return server.is_loopback and client.is_loopback
        except (ValueError, IndexError, TypeError):
            return False

    @staticmethod
    def _local_host_only(handler):
        """Deny DNS rebinding against an unauthenticated loopback-only UI."""
        raw = handler.headers.get("Host", "")
        if (not isinstance(raw, str) or raw != raw.strip()
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in raw)
                or any(ch in raw for ch in "@/?#\\\\")):
            return False
        try:
            parsed = urlsplit("//" + raw)
            # Accessing port also rejects malformed numeric ports.
            _ = parsed.port
            return (not parsed.path and not parsed.query and not parsed.fragment
                    and (parsed.hostname or "").lower() in {"localhost", "127.0.0.1", "::1"})
        except ValueError:
            return False

    def authorize(self, handler, method, path, *, allow_shell=False,
                  allow_git=False, allow_network=False, allow_ha_control=False):
        # The Basic handler must successfully authenticate this REQUEST, not
        # just present a proxy forwarding header or stale handler instance.
        authenticated = bool(getattr(handler, "_authenticated_basic", False))
        local_peer_and_listener = self._loopback_bound(handler)
        if not (authenticated or local_peer_and_listener):
            return self._deny(403, "Authentication required (Basic Auth or loopback-only binding)")
        if not authenticated and not self._local_host_only(handler):
            return self._deny(403, "Untrusted Host on loopback-only editor")
        if method == "POST" and path in HA_CONTROL and allow_ha_control is not True:
            return self._deny(403, "HA control is disabled")
        if method == "POST":
            if path in SHELL and allow_shell is not True:
                return self._deny(403, "Command execution is disabled")
            if path in GIT and allow_git is not True:
                return self._deny(403, "Git operations are disabled")
            if path in NETWORK and allow_network is not True:
                return self._deny(403, "Network administration is disabled")

        if method == "POST":
            # Browsers cannot send a custom header from a foreign origin
            # without CORS preflight. Also reject same-site cookie CSRF;
            # request Origin/Referer are not sufficient authorization.
            received = handler.headers.get("X-CSRF-Token", "")
            if not hmac.compare_digest(received, self._token):
                return self._deny(403, "Missing or invalid CSRF token")
        return None

    @staticmethod
    def _deny(status, message):
        return Response(status, message.encode("utf8"),
                        headers=(("Cache-Control", "no-store"),))


class ConfinedFS:
    """Directory-descriptor path operations; reject symlinks in every component.

    The trusted root is opened by descriptor. Relative and absolute client
    paths are accepted only if they reside under that root, by COMPONENT,
    not string-prefix. Every intermediate component is opened O_NOFOLLOW.
    """

    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Filesystem root must be a directory")
        self._dirflags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)

    def _parts(self, value):
        if isinstance(value, os.PathLike):
            value = os.fspath(value)
        if isinstance(value, bytes):
            value = os.fsdecode(value)
        if not isinstance(value, str) or not value or "\x00" in value or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
            raise PermissionError("Invalid file path")
        path = Path(value)
        if not path.is_absolute():
            path = self.root / path
        # Do not resolve symlinks before taking the directory fd: we must
        # *reject*, not traverse, client-controlled symlinks.
        parts = path.parts
        root_parts = self.root.parts
        if parts[:len(root_parts)] != root_parts:
            raise PermissionError("Path is outside configured filesystem root")
        inside = parts[len(root_parts):]
        if any(component in ("", ".", "..") for component in inside):
            raise PermissionError("Unsafe file component")
        return inside

    @contextmanager
    def _parent(self, value):
        parts = self._parts(value)
        if not parts:
            raise PermissionError("Cannot modify filesystem root")
        fd = os.open(self.root, self._dirflags)
        try:
            for piece in parts[:-1]:
                next_fd = os.open(piece, self._dirflags, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            yield fd, parts[-1]
        finally:
            os.close(fd)

    def resolve_for_read(self, value, directory=False):
        """Compatibility with legacy listdir/Git code; component safety only.

        Use read_bytes() for a truly descriptor-confined read. Callers doing
        multi-step metadata queries cannot rely on this for TOCTOU safety.
        """
        pieces = self._parts(value)
        if not pieces:
            return str(self.root)
        with self._parent(value) as (fd, name):
            flags = (self._dirflags if directory else os.O_RDONLY
                     | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_NONBLOCK", 0))
            opened = os.open(name, flags, dir_fd=fd)
            try:
                import stat
                mode = os.fstat(opened).st_mode
                if not (stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)):
                    raise PermissionError("Only ordinary files and directories are allowed")
            finally:
                os.close(opened)
        return str(self.root.joinpath(*pieces))

    @contextmanager
    def _directory(self, value):
        """Hold the actual directory inode across scan/stat operations."""
        pieces = self._parts(value)
        if not pieces:
            fd = os.open(self.root, self._dirflags)
            try:
                yield fd
            finally:
                os.close(fd)
        else:
            with self._parent(value) as (parent, name):
                fd = os.open(name, self._dirflags, dir_fd=parent)
                try:
                    yield fd
                finally:
                    os.close(fd)

    def scan_dir(self, value):
        """Return metadata without following symlinks or reopening by path."""
        import stat
        items = []
        with self._directory(value) as fd:
            for name in os.listdir(fd):
                try:
                    meta = os.stat(name, dir_fd=fd, follow_symlinks=False)
                except (OSError, ValueError):
                    continue
                if stat.S_ISLNK(meta.st_mode):
                    # UI must not advertise symlinks it cannot safely open.
                    continue
                items.append({
                    "name": name,
                    "type": "dir" if stat.S_ISDIR(meta.st_mode) else "file",
                    "size": meta.st_size,
                    "modified": meta.st_mtime,
                    "created": meta.st_ctime,
                })
        return items

    def read_bytes(self, value):
        with self._parent(value) as (fd, name):
            flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
            opened = os.open(name, flags, dir_fd=fd)
            try:
                import stat
                if not stat.S_ISREG(os.fstat(opened).st_mode):
                    raise PermissionError("Only regular files may be read")
                with os.fdopen(opened, "rb") as stream:
                    opened = None
                    return stream.read()
            finally:
                if opened is not None:
                    os.close(opened)

    def write_bytes(self, value, payload, exclusive=False):
        with self._parent(value) as (fd, name):
            flags = (os.O_WRONLY | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_NONBLOCK", 0)
                     | (os.O_EXCL if exclusive else 0))
            # Check an existing target's type before opening with O_TRUNC:
            # a named pipe/device in the workspace must not be truncated.
            # O_NONBLOCK avoids waiting on a FIFO while denying it.
            import stat
            try:
                existing = os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                existing = None
            if existing is not None and not stat.S_ISREG(existing.st_mode):
                raise PermissionError("Only regular files may be written")
            out = os.open(name, flags, 0o600, dir_fd=fd)
            try:
                if not stat.S_ISREG(os.fstat(out).st_mode):
                    raise PermissionError("Only regular files may be written")
                # Validate the opened inode BEFORE truncating; a race that
                # replaces the name cannot redirect the write to a device.
                os.ftruncate(out, 0)
                with os.fdopen(out, "wb") as stream:
                    out = None
                    stream.write(payload)
            finally:
                if out is not None:
                    os.close(out)

    def mkdir(self, value):
        with self._parent(value) as (fd, name):
            os.mkdir(name, mode=0o700, dir_fd=fd)

    def remove(self, value, is_dir=False):
        with self._parent(value) as (fd, name):
            # Never recursively delete; symlinks may be unlinked but their
            # targets cannot be reached because parent descriptors are pinned.
            if is_dir:
                os.rmdir(name, dir_fd=fd)
            else:
                os.unlink(name, dir_fd=fd)

    def rename(self, source, target):
        with self._parent(source) as (src_fd, src_name):
            with self._parent(target) as (dst_fd, dst_name):
                os.rename(src_name, dst_name,
                          src_dir_fd=src_fd, dst_dir_fd=dst_fd)
