#!/usr/bin/python3
# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines
"""
Configurator for Home Assistant.
https://github.com/danielperna84/hass-configurator
"""
import os
import sys
import argparse
import json
import ssl
import socket
import socketserver
import threading
import base64
import binascii
import ipaddress
import signal
import cgi
import shlex
import subprocess
import logging
import fnmatch
import hashlib
import hmac
import html as html_escape
import mimetypes
from string import Template
from http.server import BaseHTTPRequestHandler
from hass_configurator.http_routing import Router, Response, error_response, send_response as write_http_response
from hass_configurator._version import VERSION
from hass_configurator.api_security import ConfinedFS, FileReadLimitExceeded, run_bounded_command
import urllib.request
from urllib.parse import urlparse, parse_qs, unquote, quote

### Some options for you to change
LISTENIP = "0.0.0.0"
PORT = 3218
# Set BASEPATH to something like "/home/hass/.homeassistant/" if you're not
# running the configurator from that path
BASEPATH = None
# Set ENFORCE_BASEPATH to True to lock the configurator into the basepath and
# thereby prevent it from opening files outside of the BASEPATH
ENFORCE_BASEPATH = True
# Privileged capabilities are disabled unless explicitly opted into.
ALLOW_SHELL_COMMANDS = False
EXEC_ALLOWED_BINARIES = []  # absolute reviewed executable paths, empty = deny
ALLOW_GIT_OPERATIONS = False
ALLOW_NETWORK_ADMIN = False
ALLOW_HA_CONTROL = False
# Set the paths to a certificate and the key if you're using SSL,
# e.g "/etc/ssl/certs/mycert.pem"
SSL_CERTIFICATE = None
SSL_KEY = None
# Set the destination where the HASS API is reachable
HASS_API = "http://127.0.0.1:8123/api/"
# Set the destination where the websocket API is reachable (if different
# from HASS_API, e.g. wss://hass.example.com/api/websocket)
HASS_WS_API = None
# If a password is required to access the API, set it in the form of "password"
# if you have HA ignoring SSL locally this is not needed if on same machine.
HASS_API_PASSWORD = None
# Using the CREDENTIALS variable is deprecated.
# It will still work though if USERNAME and PASSWORD are not set.
CREDENTIALS = None
# Set the username used for basic authentication.
USERNAME = None
# Set the password used for basic authentication.
PASSWORD = None
# Limit access to the configurator by adding allowed IP addresses / networks to
# the list, e.g ALLOWED_NETWORKS = ["192.168.0.0/24", "172.16.47.23"]
ALLOWED_NETWORKS = []
# Serializes allowlist and banlist mutations across threaded HTTP requests.
NETWORK_ADMIN_LOCK = threading.RLock()
# Allow access to the configurator to client IP addesses which match the result
# of DNS lookups for the specified domains.
ALLOWED_DOMAINS = []
# List of statically banned IP addresses, e.g. ["1.1.1.1", "2.2.2.2"]
BANNED_IPS = []
# Ban IPs after n failed login attempts. Restart service to reset banning.
# The default of `0` disables this feature.
BANLIMIT = 0
# Enable git integration.
# GitPython (https://gitpython.readthedocs.io/en/stable/) has to be installed.
GIT = False
# Files to ignore in the UI.  A good example list that cleans up the UI is
# [".*", "*.log", "deps", "icloud", "*.conf", "*.json", "certs", "__pycache__"]
IGNORE_PATTERN = []
# if DIRSFIRST is set to `true`, directories will be displayed at the top
DIRSFIRST = False
# Don't display hidden files (starting with .)
HIDEHIDDEN = False
# Sesame token. Browse to the configurator URL + /secrettoken to unban your
# client IP and add it to the list of allowed IPs.
SESAME = None
# Instead of a static SESAME token you may also use a TOTP based token that
# changes every 30 seconds. The value needs to be a base 32 encoded string.
SESAME_TOTP_SECRET = None
# Verify the hostname used in the request. Block access if it doesn't match
# this value
VERIFY_HOSTNAME = None
# Prefix for environment variables
ENV_PREFIX = "HC_"
# Ignore SSL errors when connecting to the HASS API
IGNORE_SSL = False
# Notification service like `notify.mytelegram`. Default is `persistent_notification.create`
NOTIFY_SERVICE_DEFAULT = "persistent_notification.create"
NOTIFY_SERVICE = NOTIFY_SERVICE_DEFAULT
### End of options

LOGLEVEL_MAPPING = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG
}
DEFAULT_LOGLEVEL = "info"
LOGLEVEL = LOGLEVEL_MAPPING.get(os.environ.get("HC_LOGLEVEL", DEFAULT_LOGLEVEL))
LOG = logging.getLogger(__name__)
LOG.setLevel(LOGLEVEL)
SO = logging.StreamHandler(sys.stdout)
SO.setLevel(LOGLEVEL)
SO.setFormatter(
    logging.Formatter('%(levelname)s:%(asctime)s:%(name)s:%(message)s'))
LOG.addHandler(SO)
HTTP_ROUTER = Router()
BASEDIR = "."
DEV = False
LISTENPORT = None
TOTP = None
HTTPD = None
FAIL2BAN_IPS = {}
AUTH_FAILURE_LOCK = threading.Lock()
REPO = None
PREFS_FILENAME = ".hass_configurator_prefs.json"
# Bound in-memory editor/download responses; aligned with upload ceiling.
MAX_FILE_READ_BYTES = 100 * 1024 * 1024
DEFAULT_PREFS = {"ui_theme": "auto"}

def get_prefs_path():
    """Return the path for the preferences file (in BASEPATH or BASEDIR)."""
    base = BASEPATH if BASEPATH else BASEDIR
    return os.path.join(base, PREFS_FILENAME)

def load_prefs():
    """Load UI preferences from disk, return defaults on any error."""
    try:
        # Preferences are controlled by the same workspace boundary as editor
        # files. Never follow an attacker-created prefs symlink out of root.
        data = json.loads(_fs().read_bytes(get_prefs_path()).decode("utf-8"))
        # Ensure all default keys exist.
        for k, v in DEFAULT_PREFS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return dict(DEFAULT_PREFS)

def save_prefs(prefs):
    """Persist UI preferences to disk."""
    try:
        _fs().write_bytes(get_prefs_path(), json.dumps(prefs).encode("utf-8"))
        return True
    except Exception as err:
        LOG.warning("Could not save preferences: %s", err)
        return False

ERROR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1.0" />
    <title>HASS Configurator - Error</title>
</head>
<body>
<h1>Error loading html. Please check the logs.</h1>
</body>
</html>"""

# pylint: disable=unused-argument
def signal_handler(sig, frame):
    """Handle signal to shut down server."""
    global HTTPD
    LOG.info("Got signal: %s. Shutting down server", str(sig))
    HTTPD.server_close()
    sys.exit(0)

def _redacted_settings(settings):
    """Never log credential values, even at debug verbosity."""
    return {
        key: ("<redacted>" if any(
            marker in key.lower() for marker in
            ("password", "secret", "token", "credential", "private_key", "sesame")
        ) else "<redacted-url>" if key.upper() in ("HASS_API", "HASS_WS_API")
               and value else value)
        for key, value in settings.items()
    }


def load_settings(args):
    """Load settings from file and environment."""
    global LISTENIP, LISTENPORT, BASEPATH, SSL_CERTIFICATE, SSL_KEY, HASS_API, \
    HASS_API_PASSWORD, CREDENTIALS, ALLOWED_NETWORKS, BANNED_IPS, BANLIMIT, \
    DEV, IGNORE_PATTERN, DIRSFIRST, SESAME, VERIFY_HOSTNAME, ENFORCE_BASEPATH, \
    ENV_PREFIX, NOTIFY_SERVICE, USERNAME, PASSWORD, SESAME_TOTP_SECRET, TOTP, \
    GIT, REPO, PORT, IGNORE_SSL, HASS_WS_API, ALLOWED_DOMAINS, HIDEHIDDEN, \
    ALLOW_SHELL_COMMANDS, EXEC_ALLOWED_BINARIES, ALLOW_GIT_OPERATIONS, ALLOW_NETWORK_ADMIN, ALLOW_HA_CONTROL
    settings = {}
    settingsfile = args.settings
    if settingsfile:
        try:
            if os.path.isfile(settingsfile):
                settings = json.loads(load_file(settingsfile).decode("utf-8"))
                LOG.debug("Settings from file:")
                LOG.debug(_redacted_settings(settings))
            else:
                LOG.warning("File not found: %s", settingsfile)
        except Exception as err:
            LOG.warning(err)
            LOG.warning("Not loading settings from file")
    ENV_PREFIX = settings.get('ENV_PREFIX', ENV_PREFIX)
    for key, value in os.environ.items():
        if key.startswith(ENV_PREFIX):
            # Convert booleans
            if value in ['true', 'false', 'True', 'False']:
                value = value in ['true', 'True']
            # Convert None / null
            elif value in ['none', 'None', 'null']:
                value = None
            # Convert plain numbers
            elif value.isnumeric():
                value = int(value)
            # Make lists out of comma separated values for list-settings
            elif key[len(ENV_PREFIX):] in ["ALLOWED_NETWORKS", "BANNED_IPS", "IGNORE_PATTERN", "EXEC_ALLOWED_BINARIES"]:
                value = value.split(',')
            settings[key[len(ENV_PREFIX):]] = value
    LOG.debug("Settings after looking at environment:")
    LOG.debug(_redacted_settings(settings))
    if args.git:
        GIT = args.git
    else:
        GIT = settings.get("GIT", GIT)
    if GIT:
        try:
            # pylint: disable=redefined-outer-name,import-outside-toplevel
            from git import Repo as REPO
        except ImportError:
            LOG.warning("Unable to import Git module")
    if args.listen:
        LISTENIP = args.listen
    else:
        LISTENIP = settings.get("LISTENIP", LISTENIP)
    if args.port is not None:
        PORT = args.port
    else:
        LISTENPORT = settings.get("LISTENPORT", None)
    PORT = settings.get("PORT", PORT)
    if LISTENPORT is not None:
        PORT = LISTENPORT
    if args.basepath:
        BASEPATH = args.basepath
    else:
        BASEPATH = settings.get("BASEPATH", BASEPATH)
    if args.enforce:
        ENFORCE_BASEPATH = True
    else:
        ENFORCE_BASEPATH = True
    if settings.get("ENFORCE_BASEPATH") is False:
        LOG.warning("ENFORCE_BASEPATH=false ignored: P1 confinement is mandatory")
    ALLOW_SHELL_COMMANDS = _secure_flag(settings, "ALLOW_SHELL_COMMANDS", ALLOW_SHELL_COMMANDS)
    EXEC_ALLOWED_BINARIES = settings.get("EXEC_ALLOWED_BINARIES", EXEC_ALLOWED_BINARIES)
    if not isinstance(EXEC_ALLOWED_BINARIES, list) or any(
            not isinstance(name, str) or not os.path.isabs(name)
            for name in EXEC_ALLOWED_BINARIES):
        raise ValueError("EXEC_ALLOWED_BINARIES must be a list of absolute paths")
    ALLOW_GIT_OPERATIONS = _secure_flag(settings, "ALLOW_GIT_OPERATIONS", ALLOW_GIT_OPERATIONS)
    ALLOW_NETWORK_ADMIN = _secure_flag(settings, "ALLOW_NETWORK_ADMIN", ALLOW_NETWORK_ADMIN)
    ALLOW_HA_CONTROL = _secure_flag(settings, "ALLOW_HA_CONTROL", ALLOW_HA_CONTROL)
    SSL_CERTIFICATE = settings.get("SSL_CERTIFICATE", SSL_CERTIFICATE)
    SSL_KEY = settings.get("SSL_KEY", SSL_KEY)
    if args.standalone:
        HASS_API = None
    else:
        HASS_API = settings.get("HASS_API", HASS_API)
    HASS_WS_API = settings.get("HASS_WS_API", HASS_WS_API)
    HASS_API_PASSWORD = settings.get("HASS_API_PASSWORD", HASS_API_PASSWORD)
    CREDENTIALS = settings.get("CREDENTIALS", CREDENTIALS)
    ALLOWED_NETWORKS = settings.get("ALLOWED_NETWORKS", ALLOWED_NETWORKS)
    if ALLOWED_NETWORKS and not all(ALLOWED_NETWORKS):
        LOG.warning("Invalid value for ALLOWED_NETWORKS. Using empty list.")
        ALLOWED_NETWORKS = []
    for net in ALLOWED_NETWORKS:
        try:
            ipaddress.ip_network(net)
        except Exception:
            LOG.warning("Invalid network in ALLOWED_NETWORKS: %s", net)
            ALLOWED_NETWORKS.remove(net)
    ALLOWED_DOMAINS = settings.get("ALLOWED_DOMAINS", ALLOWED_DOMAINS)
    if ALLOWED_DOMAINS and not all(ALLOWED_DOMAINS):
        LOG.warning("Invalid value for ALLOWED_DOMAINS. Using empty list.")
        ALLOWED_DOMAINS = []
    BANNED_IPS = settings.get("BANNED_IPS", BANNED_IPS)
    if BANNED_IPS and not all(BANNED_IPS):
        LOG.warning("Invalid value for BANNED_IPS. Using empty list.")
        BANNED_IPS = []
    for banned_ip in BANNED_IPS:
        try:
            ipaddress.ip_address(banned_ip)
        except Exception:
            LOG.warning("Invalid IP address in BANNED_IPS: %s", banned_ip)
            BANNED_IPS.remove(banned_ip)
    BANLIMIT = settings.get("BANLIMIT", BANLIMIT)
    if args.dev:
        DEV = True
    else:
        DEV = settings.get("DEV", DEV)
    IGNORE_PATTERN = settings.get("IGNORE_PATTERN", IGNORE_PATTERN)
    if IGNORE_PATTERN and not all(IGNORE_PATTERN):
        LOG.warning("Invalid value for IGNORE_PATTERN. Using empty list.")
        IGNORE_PATTERN = []
    if args.dirsfirst:
        DIRSFIRST = args.dirsfirst
    else:
        DIRSFIRST = settings.get("DIRSFIRST", DIRSFIRST)
    if args.hidehidden:
        HIDEHIDDEN = args.hidehidden
    else:
        HIDEHIDDEN = settings.get("HIDEHIDDEN", HIDEHIDDEN)
    SESAME = settings.get("SESAME", SESAME)
    SESAME_TOTP_SECRET = settings.get("SESAME_TOTP_SECRET", SESAME_TOTP_SECRET)
    VERIFY_HOSTNAME = settings.get("VERIFY_HOSTNAME", VERIFY_HOSTNAME)
    NOTIFY_SERVICE = settings.get("NOTIFY_SERVICE", NOTIFY_SERVICE_DEFAULT)
    IGNORE_SSL = settings.get("IGNORE_SSL", IGNORE_SSL)
    if IGNORE_SSL:
        # pylint: disable=protected-access
        ssl._create_default_https_context = ssl._create_unverified_context
    if args.username and args.password:
        USERNAME = args.username
        PASSWORD = args.password
    else:
        USERNAME = settings.get("USERNAME", USERNAME)
        PASSWORD = settings.get("PASSWORD", PASSWORD)
        PASSWORD = str(PASSWORD) if PASSWORD else None
    if CREDENTIALS and (USERNAME is None or PASSWORD is None):
        USERNAME = CREDENTIALS.split(":")[0]
        PASSWORD = ":".join(CREDENTIALS.split(":")[1:])
    if PASSWORD and PASSWORD.startswith("{sha256}"):
        PASSWORD = PASSWORD.lower()
    if SESAME_TOTP_SECRET:
        try:
            #pylint: disable=import-outside-toplevel
            import pyotp
            TOTP = pyotp.TOTP(SESAME_TOTP_SECRET)
        except ImportError:
            LOG.warning("Unable to import pyotp module")
        except Exception as err:
            LOG.warning("Unable to create TOTP object: %s", err)

def is_jwt(token):
    """Perform basic check if token is a JWT token."""
    return len(token.split('.')) == 3


def _js_safe(value):
    """Escape HTML/script terminators inside a JSON expression."""
    return (value.replace("<", r"\u003c").replace(">", r"\u003e")
            .replace("&", r"\u0026")
            .replace("\u2028", r"\u2028").replace("\u2029", r"\u2029"))

def _secure_flag(settings, name, default):
    """Privileged capabilities require an actual JSON/env boolean, not a truthy string."""
    value = settings.get(name, default)
    if type(value) is not bool:
        raise ValueError("%s must be a boolean (true or false)" % name)
    return value


def _fs():
    """Resolve the currently configured workspace for every request."""
    return ConfinedFS(BASEPATH or BASEDIR)


def is_safe_path(basedir, path, follow_symlinks=True):
    """Legacy compatibility check using component boundaries, no symlinks."""
    try:
        ConfinedFS(basedir or BASEDIR).resolve_for_read(path)
        return True
    except (OSError, ValueError, TypeError):
        return False


def validated_repo(path, **kwargs):
    """Never let search_parent_directories escape the workspace root."""
    if REPO is None:
        raise PermissionError("Git integration is disabled")
    checked = _fs().resolve_for_read(
        path, directory=os.path.isdir(path))
    repo = REPO(checked, **kwargs)
    root = _fs()
    try:
        root.resolve_for_read(repo.working_dir, directory=True)
    except OSError as err:
        raise PermissionError("Git worktree outside configured root") from err
    return repo

def get_dircontent(path, repo=None):
    """Get content of directory."""
    dircontent = []
    if repo:
        untracked = [
            "%s%s%s"%(repo.working_dir, os.sep, e) for e in \
            ["%s"%os.sep.join(f.split('/')) for f in repo.untracked_files]
        ]
        staged = {}
        unstaged = {}
        try:
            for element in repo.index.diff("HEAD"):
                staged["%s%s%s" % (repo.working_dir,
                                   os.sep,
                                   "%s"%os.sep.join(
                                       element.b_path.split('/')))] = element.change_type
        except Exception as err:
            LOG.warning("Exception: %s", str(err))
        for element in repo.index.diff(None):
            unstaged["%s%s%s" % (repo.working_dir,
                                 os.sep,
                                 "%s"%os.sep.join(
                                     element.b_path.split('/')))] = element.change_type
    else:
        untracked = []
        staged = {}
        unstaged = {}

    # Listing and metadata come from one pinned directory descriptor:
    # no os.listdir(path) / os.stat(path) race and no symlink follow.
    entries = _fs().scan_dir(path)
    if HIDEHIDDEN:
        entries = [item for item in entries if not item["name"].startswith('.')]
    entries.sort(key=lambda item: (
        0 if DIRSFIRST and item["type"] == "dir" else 1,
        item["name"].lower(),
    ))

    for entry in entries:
        edata = dict(entry)
        edata['dir'] = path
        edata['fullpath'] = os.path.abspath(os.path.join(path, entry["name"]))
        edata['changetype'] = None
        edata['gitstatus'] = bool(repo)
        edata['gittracked'] = 'untracked' if edata['fullpath'] in untracked else 'tracked'
        if edata['fullpath'] in unstaged:
            edata['gitstatus'] = 'unstaged'
            edata['changetype'] = unstaged.get(edata['name'], None)
        elif edata['fullpath'] in staged:
            edata['gitstatus'] = 'staged'
            edata['changetype'] = staged.get(edata['name'], None)

        hidden = False
        if IGNORE_PATTERN is not None:
            for file_pattern in IGNORE_PATTERN:
                if fnmatch.fnmatch(edata['name'], file_pattern):
                    hidden = True

        if not hidden:
            dircontent.append(edata)

    return dircontent

def load_file(filename, static=False):
    """Load files. If static is True, set to path of configurator."""
    if static:
        filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)
    try:
        with open(filename, 'rb') as fptr:
            content = fptr.read()
            return content
    except Exception as err:
        LOG.critical(err)
        return None

def password_problems(password, name="UNKNOWN"):
    """Rudimentary checks for password strength."""
    problems = 0
    password = str(password)
    if password is None:
        return problems
    if len(password) < 8:
        LOG.warning("Password %s is too short", name)
        problems += 1
    if password.isalpha():
        LOG.warning("Password %s does not contain digits", name)
        problems += 2
    if password.isdigit():
        LOG.warning("Password %s does not contain alphabetic characters", name)
        problems += 4
    quota = len(set(password)) / len(password)
    exp = len(password) ** len(set(password))
    score = exp / quota / 8
    if score < 65536:
        LOG.warning("Password %s does not contain enough unique characters (%i)",
                    name, len(set(password)))
        problems += 8
    return problems

def check_access(clientip):
    """Check if IP is allowed to access the configurator / API."""
    global BANNED_IPS
    with NETWORK_ADMIN_LOCK:
        banned = clientip in BANNED_IPS
        allowed_networks = tuple(ALLOWED_NETWORKS)
    if banned:
        LOG.warning("Client IP banned.")
        return False
    if not allowed_networks:
        return True
    for net in allowed_networks:
        ipobject = ipaddress.ip_address(clientip)
        if ipobject in ipaddress.ip_network(net):
            return True
    LOG.warning("Client IP not within allowed networks.")
    if ALLOWED_DOMAINS:
        for domain in ALLOWED_DOMAINS:
            try:
                domain_data = socket.getaddrinfo(domain, None)
            except Exception as err:
                LOG.warning("Unable to lookup domain data: %s", err)
                continue
            for res in domain_data:
                if res[0] in [socket.AF_INET, socket.AF_INET6]:
                    if res[4][0] == clientip:
                        return True
        LOG.warning("Client IP not within allowed domains.")
    with NETWORK_ADMIN_LOCK:
        if clientip not in BANNED_IPS:
            BANNED_IPS.append(clientip)
    return False

def verify_hostname(request_hostname):
    """Check the exact canonical Host, never a substring or forwarded value."""
    if not isinstance(request_hostname, str) or any(
            ord(ch) < 32 or ord(ch) == 127 for ch in request_hostname):
        return False
    if not VERIFY_HOSTNAME:
        return True
    try:
        if any(ch in request_hostname for ch in "@/?#\\"):
            return False
        actual = urlparse("//" + request_hostname)
        expected = urlparse("//" + VERIFY_HOSTNAME)
        if not actual.hostname or not expected.hostname:
            return False
        # A configured port is mandatory when specified; otherwise Host may
        # include the ordinary listener port used for this instance.
        if expected.port is not None and actual.port != expected.port:
            return False
        return hmac.compare_digest(
            actual.hostname.casefold(), expected.hostname.casefold())
    except ValueError:
        return False

class RequestHandler(BaseHTTPRequestHandler):
    """Request handler."""
    # pylint: disable=redefined-builtin
    def log_message(self, format, *args):
        LOG.info("%s - %s", self.client_address[0], format % args)

    def log_request(self, code="-", size="-"):
        """Do not log raw request targets: SESAME/TOTP and query args are secrets."""
        LOG.info("%s - %s %s", self.client_address[0], self.command, code)

    def _dispatch_route(self, method):
        """Shared exact-route boundary for static and transitional legacy API."""
        match = HTTP_ROUTER.match(method, self.path)
        self._legacy_route = match.kind in ("legacy_api", "legacy_page")
        if self._legacy_route:
            denied = HTTP_ROUTER.security.authorize(
                self, method, match.path,
                allow_shell=(ALLOW_SHELL_COMMANDS is True) and bool(EXEC_ALLOWED_BINARIES),
                allow_git=(ALLOW_GIT_OPERATIONS is True) and bool(GIT),
                allow_network=(ALLOW_NETWORK_ADMIN is True),
                allow_ha_control=(ALLOW_HA_CONTROL is True),
            )
            if denied is not None:
                # Central responses own their own headers. Legacy end_headers
                # injects no-store/nosniff only for direct legacy emitters.
                self._legacy_route = False
                write_http_response(self, denied)
                return False
            return True
        if match.kind == "asset":
            response = HTTP_ROUTER.assets.response(match)
        elif match.kind == "bad_request":
            response = error_response(400)
        elif match.kind == "method_not_allowed":
            response = error_response(405, allow=match.allow)
        else:
            response = error_response(404)
        write_http_response(self, response)
        return False

    def end_headers(self):
        """Legacy HTML and API outputs must never enter shared caches."""
        if getattr(self, "_legacy_route", False):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    # pylint: disable=invalid-name
    def _send_block(self, status=420, reason="Policy not fulfilled"):
        """Reject a pre-router request without permitting shared caching."""
        self.send_response(status)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(bytes(reason, "utf8"))

    def _serve_file(self, route, query):
        """Bounded, descriptor-confined response for editor and downloads."""
        filename = query.get("filename", [None])[0]
        if not filename:
            response = Response(400, b"Missing filename",
                                headers=(("Cache-Control", "no-store"),))
        else:
            try:
                payload = _fs().read_bytes(filename, max_bytes=MAX_FILE_READ_BYTES)
                if route == "/api/file":
                    guessed, _ = mimetypes.guess_type(filename)
                    content_type = (guessed if guessed and guessed.startswith("image/")
                                    else "text/plain; charset=utf-8")
                    if not (guessed and guessed.startswith("image/")):
                        payload.decode("utf-8")  # Preserve text-editor UTF-8 contract.
                    headers = (("Cache-Control", "no-store"),)
                else:
                    safe_name = quote(os.path.basename(filename), safe="")
                    content_type = "application/octet-stream"
                    headers = (
                        ("Cache-Control", "no-store"),
                        ("Content-Disposition",
                         "attachment; filename*=UTF-8''%s" % safe_name),
                    )
                response = Response(200, payload, content_type=content_type, headers=headers)
            except FileReadLimitExceeded:
                response = Response(413, b"File exceeds read limit",
                                    headers=(("Cache-Control", "no-store"),))
            except FileNotFoundError:
                response = Response(404, b"File not found",
                                    headers=(("Cache-Control", "no-store"),))
            except PermissionError:
                response = Response(403, b"Access denied",
                                    headers=(("Cache-Control", "no-store"),))
            except (UnicodeError, ValueError):
                response = Response(400, b"Invalid file encoding or filename",
                                    headers=(("Cache-Control", "no-store"),))
            except OSError:
                response = Response(400, b"Unable to read file",
                                    headers=(("Cache-Control", "no-store"),))
        # Router-owned file reply: legacy header injection would duplicate
        # the no-store/nosniff pair already owned by this response writer.
        self._legacy_route = False
        write_http_response(self, response)

    # pylint: disable=invalid-name
    def do_GET(self):
        """Customized do_GET method."""
        if not verify_hostname(self.headers.get('Host', '')):
            self._send_block(403, "Forbidden")
            return
        req = urlparse(self.path)
        if SESAME or TOTP:
            chunk = req.path.split("/")[-1]
            if SESAME and chunk == SESAME:
                with NETWORK_ADMIN_LOCK:
                    if self.client_address[0] not in ALLOWED_NETWORKS:
                        ALLOWED_NETWORKS.append(self.client_address[0])
                    if self.client_address[0] in BANNED_IPS:
                        BANNED_IPS.remove(self.client_address[0])
                self.send_response(302)
                self.send_header('Location', './')
                # Access-token redirects execute before the shared router.
                # They must still be explicitly non-cacheable, including
                # behind a prefix-stripping proxy.
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                data = {
                    "title": "HASS Configurator - SESAME access",
                    "message": "Your SESAME token has been used to whitelist " \
                    "the IP address %s." % self.client_address[0]
                }
                notify(**data)
                return
            if TOTP and TOTP.verify(chunk):
                with NETWORK_ADMIN_LOCK:
                    if self.client_address[0] not in ALLOWED_NETWORKS:
                        ALLOWED_NETWORKS.append(self.client_address[0])
                    if self.client_address[0] in BANNED_IPS:
                        BANNED_IPS.remove(self.client_address[0])
                self.send_response(302)
                self.send_header('Location', './')
                # Access-token redirects execute before the shared router.
                # They must still be explicitly non-cacheable, including
                # behind a prefix-stripping proxy.
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                data = {
                    "title": "HASS Configurator - SESAME access",
                    "message": "Your SESAME token has been used to whitelist " \
                    "the IP address %s." % self.client_address[0]
                }
                notify(**data)
                return
        if not check_access(self.client_address[0]):
            self._send_block()
            return
        if not self._dispatch_route("GET"):
            return
        query = parse_qs(req.query)
        if req.path in ("/api/file", "/api/download"):
            self._serve_file(req.path, query)
            return
        self.send_response(200)
        # pylint: disable=no-else-return
        if req.path == '/api/version':
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({'version': VERSION}).encode('utf-8'))
            return
        elif req.path == '/api/listdir':
            content = {'error': None}
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            dirpath = query.get('path', None)
            try:
                if dirpath:
                    dirpath = unquote(dirpath[0]).encode('utf-8')
                    dirpath = _fs().resolve_for_read(dirpath, directory=True).encode('utf-8')
                    if os.path.isdir(dirpath):
                        repo = None
                        activebranch = None
                        dirty = False
                        branches = []
                        if REPO and ALLOW_GIT_OPERATIONS:
                            try:
                                # pylint: disable=not-callable
                                repo = validated_repo(dirpath.decode('utf-8'),
                                            search_parent_directories=True)
                                activebranch = repo.active_branch.name
                                dirty = repo.is_dirty()
                                for branch in repo.branches:
                                    branches.append(branch.name)
                            except Exception as err:
                                LOG.debug("Exception (no repo): %s", str(err))
                        dircontent = get_dircontent(dirpath.decode('utf-8'), repo)
                        filedata = {
                            'content': dircontent,
                            'abspath': os.path.abspath(dirpath).decode('utf-8'),
                            'parent': os.path.dirname(os.path.abspath(dirpath)).decode('utf-8'),
                            'branches': branches,
                            'activebranch': activebranch,
                            'dirty': dirty,
                            'error': None
                        }
                        self.wfile.write(bytes(json.dumps(filedata), "utf8"))
            except Exception as err:
                LOG.warning(err)
                content['error'] = str(err)
                self.wfile.write(bytes(json.dumps(content), "utf8"))
            return
        elif req.path == '/api/abspath':
            content = ""
            self.send_header('Content-type', 'text/text')
            self.end_headers()
            dirpath = query.get('path', None)
            if dirpath:
                dirpath = unquote(dirpath[0]).encode('utf-8')
                try:
                    absp = _fs().resolve_for_read(dirpath, directory=True).encode('utf-8')
                except OSError:
                    return
                if os.path.isdir(absp):
                    self.wfile.write(absp)
            return
        elif req.path == '/api/parent':
            content = ""
            self.send_header('Content-type', 'text/text')
            self.end_headers()
            dirpath = query.get('path', None)
            if dirpath:
                dirpath = unquote(dirpath[0]).encode('utf-8')
                try:
                    absp = _fs().resolve_for_read(dirpath, directory=True).encode('utf-8')
                except OSError:
                    return
                if os.path.isdir(absp):
                    self.wfile.write(
                        absp if absp == os.fsencode(_fs().root)
                        else _fs().resolve_for_read(
                            os.path.dirname(absp), directory=True).encode('utf-8'))
            return
        elif req.path == '/api/prefs':
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            self.wfile.write(bytes(json.dumps(load_prefs()), "utf8"))
            return
        elif req.path == '/api/netstat':
            content = ""
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            res = {
                "allowed_networks": ALLOWED_NETWORKS,
                "banned_ips": BANNED_IPS
            }
            self.wfile.write(bytes(json.dumps(res), "utf8"))
            return
        elif req.path.endswith('/'):
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            loadfile = query.get('loadfile', [None])[0]
            # Query-supplied file names must never become raw JS source.
            loadfile = _js_safe(json.dumps(loadfile, ensure_ascii=True))
            services = "[]"
            events = "[]"
            states = "[]"
            try:
                if HASS_API:
                    headers = {
                        "Content-Type": "application/json"
                    }
                    if HASS_API_PASSWORD:
                        if is_jwt(HASS_API_PASSWORD):
                            headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
                        else:
                            headers["x-ha-access"] = HASS_API_PASSWORD

                    req = urllib.request.Request("%sservices" % HASS_API,
                                                 headers=headers, method='GET')
                    with urllib.request.urlopen(req) as response:
                        services = response.read().decode('utf-8')

                    req = urllib.request.Request("%sevents" % HASS_API,
                                                 headers=headers, method='GET')
                    with urllib.request.urlopen(req) as response:
                        events = response.read().decode('utf-8')

                    req = urllib.request.Request("%sstates" % HASS_API,
                                                 headers=headers, method='GET')
                    with urllib.request.urlopen(req) as response:
                        states_clean = []
                        for state in json.loads(response.read().decode('utf-8')):
                            states_clean.append(
                                {
                                    "entity_id": state.get("entity_id", ""),
                                    "attributes":
                                    {"friendly_name": state.get("attributes", {}).get(
                                        "friendly_name", state.get("entity_id", ""))}
                                }
                            )
                        states = json.dumps(states_clean)

            except Exception as err:
                LOG.warning("Exception getting bootstrap")
                LOG.warning(err)

            color = ""
            ws_api = ""
            if HASS_API:
                protocol, uri = HASS_API.split("//")
                ws_api = "%s://%swebsocket" % (
                    "wss" if protocol == 'https' else 'ws', uri
                )
            if HASS_WS_API:
                ws_api = HASS_WS_API
            standalone = ""
            if not HASS_API:
                standalone = "toggle_hass_panels();"
            try:
                html = Template(load_file("dev.html", static=True).decode('utf-8'))
                html = html.safe_substitute(
                    services=_js_safe(services),
                    events=_js_safe(events),
                    states=_js_safe(states),
                    loadfile=loadfile,
                    current=VERSION,
                    versionclass=color,
                    githidden="" if GIT and ALLOW_GIT_OPERATIONS else "hiddendiv",
                    # pylint: disable=anomalous-backslash-in-string
                    separator="\%s" % os.sep if os.sep == "\\" else os.sep,
                    your_address=html_escape.escape(self.client_address[0], quote=True),
                    listening_address=html_escape.escape("%s://%s:%i" % (
                        'https' if SSL_CERTIFICATE else 'http', LISTENIP, PORT), quote=True),
                    hass_api_address=html_escape.escape("%s" % (HASS_API, ), quote=True),
                    hass_ws_address=html_escape.escape(ws_api, quote=True),
                    # Never embed server-held HA credentials into HTML/DOM.
                    api_password="",
                    csrf_token=HTTP_ROUTER.security.csrf_token,
                    standalone=standalone,
                    ui_theme=(load_prefs().get('ui_theme', 'auto')
                              if load_prefs().get('ui_theme', 'auto')
                              in ('light', 'dark', 'auto') else 'auto'),
                    asset_version=HTTP_ROUTER.assets.version)
            except Exception as err:
                LOG.warning("Error getting html: %s", err)
                html = ERROR_HTML
            self.wfile.write(bytes(html, "utf8"))
            return
    # pylint: disable=invalid-name
    def do_POST(self):
        """Customized do_POST method."""
        global ALLOWED_NETWORKS, BANNED_IPS
        if not verify_hostname(self.headers.get('Host', '')):
            self._send_block(403, "Forbidden")
            return
        if not check_access(self.client_address[0]):
            self._send_block()
            return
        req = urlparse(self.path)
        if not self._dispatch_route("POST"):
            return

        response = {
            "error": True,
            "message": "Generic failure"
        }

        try:
            length = int(self.headers.get('Content-Length', ''))
            limit = 104857600 if req.path == '/api/upload' else 1048576
            if length < 0 or length > limit:
                raise ValueError("Invalid request size")
        except (ValueError, TypeError):
            self._legacy_route = False  # Router-owned 413 already supplies headers.
            write_http_response(self, error_response(413))
            return
        if req.path == '/api/save':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'filename' in postvars.keys() and 'text' in postvars.keys():
                if postvars['filename'] and postvars['text']:
                    try:
                        filename = unquote(postvars['filename'][0])
                        response['file'] = filename
                        _fs().write_bytes(filename, postvars['text'][0].encode("utf-8"))
                        self.send_response(200)
                        self.send_header('Content-type', 'text/json')
                        self.end_headers()
                        response['error'] = False
                        response['message'] = "File saved successfully"
                        self.wfile.write(bytes(json.dumps(response), "utf8"))
                        return
                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing filename or text"
        elif req.path == '/api/upload':
            if length > 104857600: #100 MB for now
                read = 0
                while read < length:
                    read += len(self.rfile.read(min(66556, length - read)))
                self.send_response(200)
                self.send_header('Content-type', 'text/json')
                self.end_headers()
                response['error'] = True
                response['message'] = "File too big: %i" % read
                self.wfile.write(bytes(json.dumps(response), "utf8"))
                return
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': self.headers['Content-Type'],
                })
            try:
                filename = form['file'].filename
                filepath = form['path'].file.read()
                if isinstance(filepath, bytes):
                    filepath = filepath.decode("utf-8")
                if (not filename or os.path.basename(filename) != filename
                        or filename in (".", "..")):
                    raise PermissionError("Invalid upload filename")
                data = form['file'].file.read()
                _fs().write_bytes(os.path.join(filepath, filename), data)
            except (KeyError, AttributeError, OSError, ValueError, TypeError) as err:
                LOG.warning("Upload rejected: %s", err)
                response['message'] = "Invalid or disallowed upload"
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            response['error'] = False
            response['message'] = "Upload successful"
            self.wfile.write(bytes(json.dumps(response), "utf8"))
            return
        elif req.path == '/api/rename':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'src' in postvars.keys() and 'dstfilename' in postvars.keys():
                if postvars['src'] and postvars['dstfilename']:
                    try:
                        src = unquote(postvars['src'][0])
                        dstfilename = unquote(postvars['dstfilename'][0])
                        if (not dstfilename or os.path.basename(dstfilename) != dstfilename
                                or dstfilename in (".", "..")):
                            raise PermissionError("Invalid destination name")
                        renamepath = os.path.join(os.path.dirname(src), dstfilename)
                        response['path'] = renamepath
                        try:
                            _fs().rename(src, renamepath)
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            response['error'] = False
                            response['message'] = "Rename successful"
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            LOG.warning(err)
                            response['error'] = True
                            response['message'] = str(err)

                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing filename or text"
        elif req.path == '/api/delete':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys():
                if postvars['path']:
                    try:
                        delpath = unquote(postvars['path'][0])
                        response['path'] = delpath
                        try:
                            if os.path.isdir(delpath):
                                _fs().remove(delpath, is_dir=True)
                            else:
                                _fs().remove(delpath)
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            response['error'] = False
                            response['message'] = "Deletion successful"
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            LOG.warning(err)
                            response['error'] = True
                            response['message'] = str(err)

                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing filename or text"
        elif req.path == '/api/exec_command':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'command' in postvars.keys():
                if postvars['command']:
                    try:
                        command = shlex.split(postvars['command'][0])
                        if not command or not os.path.isabs(command[0]):
                            raise PermissionError("Executable not in approved command allowlist")
                        # Validate and EXECUTE the same resolved absolute path.
                        # Otherwise an attacker could swap an allowlisted
                        # symlink between the check and subprocess.Popen().
                        resolved_binary = os.path.realpath(command[0])
                        if resolved_binary not in {
                                os.path.realpath(p) for p in EXEC_ALLOWED_BINARIES}:
                            raise PermissionError("Executable not in approved command allowlist")
                        command[0] = resolved_binary
                        timeout = 15
                        if 'timeout' in postvars.keys():
                            if postvars['timeout']:
                                timeout = int(postvars['timeout'][0])
                        if timeout < 1 or timeout > 30:
                            raise ValueError("Command timeout must be between 1 and 30 seconds")
                        try:
                            returncode, stdout, stderr = run_bounded_command(
                                command, timeout=timeout, cwd=str(_fs().root),
                                env={"PATH": "/usr/bin:/bin", "HOME": str(_fs().root)})
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            response['error'] = False
                            response['message'] = "Command executed: %s" % postvars['command'][0]
                            response['returncode'] = returncode
                            try:
                                response['stdout'] = stdout.decode(sys.getdefaultencoding())
                            except Exception as err:
                                LOG.warning(err)
                                response['stdout'] = stdout.decode("utf-8", errors="replace")
                            try:
                                response['stderr'] = stderr.decode(sys.getdefaultencoding())
                            except Exception as err:
                                LOG.warning(err)
                                response['stderr'] = stderr.decode("utf-8", errors="replace")
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            LOG.warning(err)
                            response['error'] = True
                            response['message'] = str(err)

                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing command"
        elif req.path == '/api/gitadd':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys():
                if postvars['path']:
                    try:
                        addpath = unquote(postvars['path'][0])
                        # pylint: disable=not-callable
                        repo = validated_repo(addpath,
                                    search_parent_directories=True)
                        filepath = "/".join(
                            addpath.split(os.sep)[len(repo.working_dir.split(os.sep)):])
                        response['path'] = filepath
                        try:
                            repo.index.add([filepath])
                            response['error'] = False
                            response['message'] = "Added file to index"
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            LOG.warning(err)
                            response['error'] = True
                            response['message'] = str(err)

                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing filename"
        elif req.path == '/api/gitdiff':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys():
                if postvars['path']:
                    try:
                        diffpath = unquote(postvars['path'][0])
                        # pylint: disable=not-callable
                        repo = validated_repo(diffpath,
                                    search_parent_directories=True)
                        filepath = "/".join(
                            diffpath.split(os.sep)[len(repo.working_dir.split(os.sep)):])
                        response['path'] = filepath
                        try:
                            diff = repo.index.diff(None,
                                                   create_patch=True,
                                                   paths=filepath)[0].diff.decode("utf-8")
                            response['error'] = False
                            response['message'] = diff
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            LOG.warning(err)
                            response['error'] = True
                            response['message'] = "Unable to load diff: %s" % str(err)

                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing filename"
        elif req.path == '/api/commit':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys() and 'message' in postvars.keys():
                if postvars['path'] and postvars['message']:
                    try:
                        commitpath = unquote(postvars['path'][0])
                        response['path'] = commitpath
                        message = unquote(postvars['message'][0])
                        # pylint: disable=not-callable
                        repo = validated_repo(commitpath,
                                    search_parent_directories=True)
                        try:
                            repo.index.commit(message)
                            response['error'] = False
                            response['message'] = "Changes commited"
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            response['error'] = True
                            response['message'] = str(err)
                            LOG.debug(response)

                    except Exception as err:
                        response['message'] = "Not a git repository: %s" % (str(err))
                        LOG.warning("Exception (no repo): %s", str(err))
            else:
                response['message'] = "Missing path"
        elif req.path == '/api/checkout':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys() and 'branch' in postvars.keys():
                if postvars['path'] and postvars['branch']:
                    try:
                        branchpath = unquote(postvars['path'][0])
                        response['path'] = branchpath
                        branch = unquote(postvars['branch'][0])
                        # pylint: disable=not-callable
                        repo = validated_repo(branchpath,
                                    search_parent_directories=True)
                        try:
                            head = [h for h in repo.heads if h.name == branch][0]
                            head.checkout()
                            response['error'] = False
                            response['message'] = "Checked out %s" % branch
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            response['error'] = True
                            response['message'] = str(err)
                            LOG.warning(response)

                    except Exception as err:
                        response['message'] = "Not a git repository: %s" % (str(err))
                        LOG.warning("Exception (no repo): %s", str(err))
            else:
                response['message'] = "Missing path or branch"
        elif req.path == '/api/newbranch':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys() and 'branch' in postvars.keys():
                if postvars['path'] and postvars['branch']:
                    try:
                        branchpath = unquote(postvars['path'][0])
                        response['path'] = branchpath
                        branch = unquote(postvars['branch'][0])
                        # pylint: disable=not-callable
                        repo = validated_repo(branchpath,
                                    search_parent_directories=True)
                        try:
                            repo.git.checkout("HEAD", b=branch)
                            response['error'] = False
                            response['message'] = "Created and checked out %s" % branch
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            response['error'] = True
                            response['message'] = str(err)
                            LOG.warning(response)

                    except Exception as err:
                        response['message'] = "Not a git repository: %s" % (str(err))
                        LOG.warning("Exception (no repo): %s", str(err))
            else:
                response['message'] = "Missing path or branch"
        elif req.path == '/api/init':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys():
                if postvars['path']:
                    try:
                        repopath = unquote(postvars['path'][0])
                        response['path'] = repopath
                        try:
                            repo = REPO.init(_fs().resolve_for_read(repopath, directory=True))
                            response['error'] = False
                            response['message'] = "Initialized repository in %s" % repopath
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            response['error'] = True
                            response['message'] = str(err)
                            LOG.warning(response)

                    except Exception as err:
                        response['message'] = "Not a git repository: %s" % (str(err))
                        LOG.warning("Exception (no repo): %s", str(err))
            else:
                response['message'] = "Missing path or branch"
        elif req.path == '/api/push':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys():
                if postvars['path']:
                    try:
                        repopath = unquote(postvars['path'][0])
                        response['path'] = repopath
                        try:
                            # pylint: disable=not-callable
                            repo = validated_repo(repopath)
                            urls = []
                            if repo.remotes:
                                for url in repo.remotes.origin.urls:
                                    urls.append(url)
                            if not urls:
                                response['error'] = True
                                response['message'] = "No remotes configured for %s" % repopath
                            else:
                                repo.remotes.origin.push()
                                response['error'] = False
                                response['message'] = "Pushed to %s" % urls[0]
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            response['error'] = True
                            response['message'] = str(err)
                            LOG.warning(response)

                    except Exception as err:
                        response['message'] = "Not a git repository: %s" % (str(err))
                        LOG.warning("Exception (no repo): %s", str(err))
            else:
                response['message'] = "Missing path or branch"
        elif req.path == '/api/stash':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys():
                if postvars['path']:
                    try:
                        repopath = unquote(postvars['path'][0])
                        response['path'] = repopath
                        try:
                            # pylint: disable=not-callable
                            repo = validated_repo(repopath)
                            returnvalue = repo.git.stash()
                            response['error'] = False
                            response['message'] = "%s\n%s" % (returnvalue, repopath)
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            response['error'] = True
                            response['message'] = str(err)
                            LOG.warning(response)

                    except Exception as err:
                        response['message'] = "Not a git repository: %s" % (str(err))
                        LOG.warning("Exception (no repo): %s", str(err))
            else:
                response['message'] = "Missing path or branch"
        elif req.path == '/api/newfolder':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys() and 'name' in postvars.keys():
                if postvars['path'] and postvars['name']:
                    try:
                        basepath = unquote(postvars['path'][0])
                        name = unquote(postvars['name'][0])
                        response['path'] = os.path.join(basepath, name)
                        try:
                            _fs().mkdir(response['path'])
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            response['error'] = False
                            response['message'] = "Folder created"
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            LOG.warning(err)
                            response['error'] = True
                            response['message'] = str(err)
                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
        elif req.path == '/api/newfile':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'path' in postvars.keys() and 'name' in postvars.keys():
                if postvars['path'] and postvars['name']:
                    try:
                        basepath = unquote(postvars['path'][0])
                        name = unquote(postvars['name'][0])
                        response['path'] = os.path.join(basepath, name)
                        try:
                            _fs().write_bytes(response['path'], b"", exclusive=True)
                            self.send_response(200)
                            self.send_header('Content-type', 'text/json')
                            self.end_headers()
                            response['error'] = False
                            response['message'] = "File created"
                            self.wfile.write(bytes(json.dumps(response), "utf8"))
                            return
                        except Exception as err:
                            LOG.warning(err)
                            response['error'] = True
                            response['message'] = str(err)
                    except Exception as err:
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing filename or text"
        elif req.path == '/api/allowed_networks':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'network' in postvars.keys() and 'method' in postvars.keys():
                if postvars['network'] and postvars['method']:
                    try:
                        network = unquote(postvars['network'][0])
                        method = unquote(postvars['method'][0])
                        if method == 'remove':
                            with NETWORK_ADMIN_LOCK:
                                if network in ALLOWED_NETWORKS:
                                    # Empty allowlist means allow-all: check
                                    # and removal must be one atomic action.
                                    if len(ALLOWED_NETWORKS) == 1:
                                        raise PermissionError("Cannot remove final allowed network")
                                    ALLOWED_NETWORKS.remove(network)
                            response['error'] = False
                        elif method == 'add':
                            ipaddress.ip_network(network)
                            with NETWORK_ADMIN_LOCK:
                                if network not in ALLOWED_NETWORKS:
                                    ALLOWED_NETWORKS.append(network)
                            response['error'] = False
                        else:
                            raise ValueError("Invalid network administration method")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/json')
                        self.end_headers()
                        response['error'] = False
                        response['message'] = "ALLOWED_NETWORKS (%s): %s" % (method, network)
                        self.wfile.write(bytes(json.dumps(response), "utf8"))
                        return
                    except Exception as err:
                        response['error'] = True
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing network"
        elif req.path == '/api/banned_ips':
            try:
                postvars = parse_qs(self.rfile.read(length).decode('utf-8'),
                                    keep_blank_values=1)
            except Exception as err:
                LOG.warning(err)
                response['message'] = "%s" % (str(err))
                postvars = {}
            if 'ip' in postvars.keys() and 'method' in postvars.keys():
                if postvars['ip'] and postvars['method']:
                    try:
                        ip_address = unquote(postvars['ip'][0])
                        method = unquote(postvars['method'][0])
                        if method == 'unban':
                            with NETWORK_ADMIN_LOCK:
                                if ip_address in BANNED_IPS:
                                    BANNED_IPS.remove(ip_address)
                            response['error'] = False
                        elif method == 'ban':
                            # The access check compares exact IP addresses;
                            # accepting a CIDR here would silently fail to ban.
                            ipaddress.ip_address(ip_address)
                            with NETWORK_ADMIN_LOCK:
                                if ip_address not in BANNED_IPS:
                                    BANNED_IPS.append(ip_address)
                        else:
                            raise ValueError("Invalid ban administration method")
                        self.send_response(200)
                        self.send_header('Content-type', 'text/json')
                        self.end_headers()
                        response['error'] = False
                        response['message'] = "BANNED_IPS (%s): %s" % (method, ip_address)
                        self.wfile.write(bytes(json.dumps(response), "utf8"))
                        return
                    except Exception as err:
                        response['error'] = True
                        response['message'] = "%s" % (str(err))
                        LOG.warning(err)
            else:
                response['message'] = "Missing IP"
        elif req.path == '/api/restart':
            LOG.info("/api/restart")
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            res = {"restart": False}
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                if HASS_API_PASSWORD:
                    if is_jwt(HASS_API_PASSWORD):
                        headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
                    else:
                        headers["x-ha-access"] = HASS_API_PASSWORD
                req = urllib.request.Request(
                    "%sservices/homeassistant/restart" % HASS_API,
                    headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    LOG.debug(res)
            except Exception as err:
                LOG.warning(err)
                res['restart'] = str(err)
            self.wfile.write(bytes(json.dumps(res), "utf8"))
            return
        elif req.path == '/api/check_config':
            LOG.info("/api/check_config")
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            res = {"check_config": False}
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                if HASS_API_PASSWORD:
                    if is_jwt(HASS_API_PASSWORD):
                        headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
                    else:
                        headers["x-ha-access"] = HASS_API_PASSWORD
                req = urllib.request.Request(
                    "%sconfig/core/check_config" % HASS_API,
                    headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    LOG.debug(res)
            except Exception as err:
                LOG.warning(err)
                res['errors'] = str(err)
            self.wfile.write(bytes(json.dumps(res), "utf8"))
            return
        elif req.path == '/api/reload_automations':
            LOG.info("/api/reload_automations")
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            res = {"reload_automations": False}
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                if HASS_API_PASSWORD:
                    if is_jwt(HASS_API_PASSWORD):
                        headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
                    else:
                        headers["x-ha-access"] = HASS_API_PASSWORD
                req = urllib.request.Request(
                    "%sservices/automation/reload" % HASS_API,
                    headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    LOG.debug(json.loads(response.read().decode('utf-8')))
                    res['service'] = "called successfully"
            except Exception as err:
                LOG.warning(err)
                res['restart'] = str(err)
            self.wfile.write(bytes(json.dumps(res), "utf8"))
            return
        elif req.path == '/api/reload_scripts':
            LOG.info("/api/reload_scripts")
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            res = {"reload_scripts": False}
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                if HASS_API_PASSWORD:
                    if is_jwt(HASS_API_PASSWORD):
                        headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
                    else:
                        headers["x-ha-access"] = HASS_API_PASSWORD
                req = urllib.request.Request(
                    "%sservices/script/reload" % HASS_API,
                    headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    LOG.debug(json.loads(response.read().decode('utf-8')))
                    res['service'] = "called successfully"
            except Exception as err:
                LOG.warning(err)
                res['restart'] = str(err)
            self.wfile.write(bytes(json.dumps(res), "utf8"))
            return
        elif req.path == '/api/reload_groups':
            LOG.info("/api/reload_groups")
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            res = {"reload_groups": False}
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                if HASS_API_PASSWORD:
                    if is_jwt(HASS_API_PASSWORD):
                        headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
                    else:
                        headers["x-ha-access"] = HASS_API_PASSWORD
                req = urllib.request.Request(
                    "%sservices/group/reload" % HASS_API,
                    headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    LOG.debug(json.loads(response.read().decode('utf-8')))
                    res['service'] = "called successfully"
            except Exception as err:
                LOG.warning(err)
                res['restart'] = str(err)
            self.wfile.write(bytes(json.dumps(res), "utf8"))
            return
        elif req.path == '/api/reload_core':
            LOG.info("/api/reload_core")
            self.send_response(200)
            self.send_header('Content-type', 'text/json')
            self.end_headers()
            res = {"reload_core": False}
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                if HASS_API_PASSWORD:
                    if is_jwt(HASS_API_PASSWORD):
                        headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
                    else:
                        headers["x-ha-access"] = HASS_API_PASSWORD
                req = urllib.request.Request(
                    "%sservices/homeassistant/reload_core_config" % HASS_API,
                    headers=headers, method='POST')
                with urllib.request.urlopen(req) as response:
                    LOG.debug(json.loads(response.read().decode('utf-8')))
                    res['service'] = "called successfully"
            except Exception as err:
                LOG.warning(err)
                res['restart'] = str(err)
            self.wfile.write(bytes(json.dumps(res), "utf8"))
            return
        elif req.path == '/api/prefs':
            try:
                body = self.rfile.read(length).decode('utf-8')
                new_prefs = json.loads(body)
            except Exception as err:
                LOG.warning(err)
                new_prefs = {}
            if 'ui_theme' in new_prefs:
                theme = new_prefs['ui_theme']
                if theme in ('light', 'dark', 'auto'):
                    prefs = load_prefs()
                    prefs['ui_theme'] = theme
                    ok = save_prefs(prefs)
                    self.send_response(200)
                    self.send_header('Content-type', 'text/json')
                    self.end_headers()
                    response['error'] = not ok
                    response['message'] = "Preferences saved" if ok else "Could not write prefs file"
                    self.wfile.write(bytes(json.dumps(response), "utf8"))
                    return
                else:
                    response['message'] = "Invalid theme value"
            else:
                response['message'] = "Missing ui_theme"
        else:
            response['message'] = "Invalid method"
        self.send_response(200)
        self.send_header('Content-type', 'text/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps(response), "utf8"))
        return

def _clear_auth_failures(clientip):
    """A successful Basic login clears the shared failure counter atomically."""
    if BANLIMIT:
        with AUTH_FAILURE_LOCK:
            FAIL2BAN_IPS.pop(clientip, None)


def _reject_failed_basic(clientip):
    """Increment failed Basic attempts atomically across HTTP worker threads."""
    if not BANLIMIT:
        return False
    with AUTH_FAILURE_LOCK:
        attempts = FAIL2BAN_IPS.get(clientip, 1)
        if attempts >= BANLIMIT:
            return True
        FAIL2BAN_IPS[clientip] = attempts + 1
        return False


class AuthHandler(RequestHandler):
    """Handler to verify auth header."""
    def _send_block(self, status=420, reason="Policy not fulfilled"):
        # Reuse the same pre-router denial policy as RequestHandler.
        return super()._send_block(status, reason)

    # pylint: disable=invalid-name
    def _send_auth_challenge(self):
        """Request authorization."""
        LOG.info("Requesting authorization")
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm=\"HASS Configurator\"')
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()

    def _valid_basic(self, header):
        """Malformed Authorization must be a challenge, never a 500 or crash."""
        if not header or len(header) > 8192:
            return False
        try:
            scheme, token = header.split(" ", 1)
            if scheme.lower() != "basic":
                return False
            decoded = base64.b64decode(token, validate=True).decode("utf-8")
            username, password = decoded.split(":", 1)
            if not USERNAME or not PASSWORD:
                return False
            if PASSWORD.startswith("{sha256}"):
                password = "{sha256}%s" % hashlib.sha256(
                    password.encode("utf-8")).hexdigest()
            return (hmac.compare_digest(username.encode("utf-8"), USERNAME.encode("utf-8"))
                    and hmac.compare_digest(password.encode("utf-8"), PASSWORD.encode("utf-8")))
        except (ValueError, UnicodeError, binascii.Error, AttributeError, TypeError):
            return False

    def do_GET(self):
        if not verify_hostname(self.headers.get('Host', '')):
            self._send_block(403, "Forbidden")
            return
        header = self.headers.get('Authorization', None)
        if header is None:
            self._send_auth_challenge()
            self.wfile.write(bytes('no auth header received', 'utf-8'))
        else:
            if self._valid_basic(header):
                    _clear_auth_failures(self.client_address[0])
                    self._authenticated_basic = True
                    super().do_GET()
                    return
            if _reject_failed_basic(self.client_address[0]):
                LOG.warning("Blocking access from %s", self.client_address[0])
                self._send_block()
                return
            self._send_auth_challenge()
            self.wfile.write(bytes('Authentication required', 'utf-8'))

    def do_POST(self):
        if not verify_hostname(self.headers.get('Host', '')):
            self._send_block(403, "Forbidden")
            return
        header = self.headers.get('Authorization', None)
        if header is None:
            self._send_auth_challenge()
            self.wfile.write(bytes('no auth header received', 'utf-8'))
        else:
            if self._valid_basic(header):
                    _clear_auth_failures(self.client_address[0])
                    self._authenticated_basic = True
                    super().do_POST()
                    return
            if _reject_failed_basic(self.client_address[0]):
                LOG.warning("Blocking access from %s", self.client_address[0])
                self._send_block()
                return
            self._send_auth_challenge()
            self.wfile.write(bytes('Authentication required', 'utf-8'))

class SimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Server class."""
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)

def notify(title="HASS Configurator",
           message="Notification by HASS Configurator",
           notification_id=None):
    """Helper function to send notifications via HASS."""
    if not HASS_API or not NOTIFY_SERVICE:
        return
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "message": message
    }
    if notification_id and NOTIFY_SERVICE == NOTIFY_SERVICE_DEFAULT:
        data["notification_id"] = notification_id
    if HASS_API_PASSWORD:
        if is_jwt(HASS_API_PASSWORD):
            headers["Authorization"] = "Bearer %s" % HASS_API_PASSWORD
        else:
            headers["x-ha-access"] = HASS_API_PASSWORD
    req = urllib.request.Request(
        "%sservices/%s" % (HASS_API, NOTIFY_SERVICE.replace('.', '/')),
        data=bytes(json.dumps(data).encode('utf-8')),
        headers=headers, method='POST')
    LOG.info("%s", data)
    try:
        with urllib.request.urlopen(req) as response:
            message = response.read().decode('utf-8')
            LOG.debug(message)
    except Exception as err:
        LOG.warning("Exception while creating notification: %s", err)

def main():
    """Main function, duh!"""
    global HTTPD
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(description="Visit " \
    "https://github.com/danielperna84/hass-configurator for more details " \
    "about the availble options.")
    parser.add_argument(
        'settings', nargs='?',
        help="Path to file with persistent settings.")
    parser.add_argument(
        '--listen', '-l', nargs='?',
        help="The IP address the service is listening on. Default: 0.0.0.0")
    parser.add_argument(
        '--port', '-p', nargs='?', type=int,
        help="The port the service is listening on. " \
        "0 allocates a dynamic port. Default: 3218")
    parser.add_argument(
        '--allowed_networks', '-a', nargs='?',
        help="Comma-separated list of allowed networks / IP addresses " \
        "from which access is allowed. Eg. 127.0.0.1,192.168.0.0/16. " \
        "By default access is allowed from anywhere.")
    parser.add_argument(
        '--username', '-U', nargs='?',
        help="Username required for access.")
    parser.add_argument(
        '--password', '-P', nargs='?',
        help="Password required for access.")
    parser.add_argument(
        '--sesame', '-S', nargs='?',
        help="SESAME token for whitelisting client IPs by accessing " \
        "a scret URL: http://1.2.3.4:3218/secret_sesame_token")
    parser.add_argument(
        '--basepath', '-b', nargs='?',
        help="Path to initially serve files from")
    parser.add_argument(
        '--enforce', '-e', action='store_true',
        help="Lock the configurator into the basepath.")
    parser.add_argument(
        '--standalone', '-s', action='store_true',
        help="Don't fetch data from HASS_API.")
    parser.add_argument(
        '--dirsfirst', '-d', action='store_true',
        help="Display directories first.")
    parser.add_argument(
        '--hidehidden', '-H', action='store_true',
        help="Don't display hidden files.")
    parser.add_argument(
        '--git', '-g', action='store_true',
        help="Enable GIT support.")
    parser.add_argument(
        '--dev', '-D', action='store_true',
        help="Enable Dev-Mode (serve dev.html instead of embedded HTML).")
    args = parser.parse_args()
    load_settings(args)
    LOG.info("Starting server")

    try:
        problems = None
        if HASS_API_PASSWORD:
            problems = password_problems(HASS_API_PASSWORD, "HASS_API_PASSWORD")
        if problems:
            data = {
                "title": "HASS Configurator - Password warning",
                "message": "Your Home Assistant API password seems insecure (%i). " \
                "Refer to the HASS Configurator logs for further information." % problems,
                "notification_id": "HC_HASS_API_PASSWORD"
            }
            notify(**data)

        problems = None
        if SESAME:
            problems = password_problems(SESAME, "SESAME")
        if problems:
            data = {
                "title": "HASS Configurator - Password warning",
                "message": "Your SESAME seems insecure (%i). " \
                "Refer to the HASS Configurator logs for further information." % problems,
                "notification_id": "HC_SESAME"
            }
            notify(**data)

        problems = None
        if PASSWORD:
            problems = password_problems(PASSWORD, "PASSWORD")
        if problems:
            data = {
                "title": "HASS Configurator - Password warning",
                "message": "Your PASSWORD seems insecure (%i). " \
                "Refer to the HASS Configurator logs for further information." % problems,
                "notification_id": "HC_PASSWORD"
            }
            notify(**data)
    except Exception as err:
        LOG.warning("Exception while checking passwords: %s", err)

    custom_server = SimpleServer
    if ':' in LISTENIP:
        custom_server.address_family = socket.AF_INET6
    server_address = (LISTENIP, PORT)
    if USERNAME and PASSWORD:
        handler = AuthHandler
    else:
        handler = RequestHandler
    HTTPD = custom_server(server_address, handler)
    if SSL_CERTIFICATE:
        HTTPD.socket = ssl.wrap_socket(HTTPD.socket,
                                       certfile=SSL_CERTIFICATE,
                                       keyfile=SSL_KEY,
                                       server_side=True)
    LOG.info('Listening on: %s://%s:%i',
             'https' if SSL_CERTIFICATE else 'http',
             HTTPD.server_address[0], HTTPD.server_address[1])
    if BASEPATH:
        os.chdir(BASEPATH)
    HTTPD.serve_forever()

if __name__ == "__main__":
    main()
