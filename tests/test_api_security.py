"""P1 #7 API authorization, anti-CSRF, filesystem and XSS abuse tests."""
import http.client
from io import BytesIO
from types import SimpleNamespace
import base64
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import time
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlencode, quote

from hass_configurator import configurator as cfg
from hass_configurator.api_security import ApiPolicy, ConfinedFS


class PolicyTests(unittest.TestCase):
    def test_no_remote_client_or_proxy_header_can_self_authenticate(self):
        class Handler:
            headers = {"X-CSRF-Token": ""}
            client_address = ("203.0.113.4", 12345)
            server = type("Server", (), {"server_address": ("0.0.0.0", 3218)})()

        policy = ApiPolicy()
        h = Handler()
        for method, path in (("GET", "/"), ("GET", "/api/file"),
                             ("POST", "/api/save")):
            with self.subTest(method=method, path=path):
                self.assertEqual(policy.authorize(h, method, path).status, 403)
        h.headers = {
            "X-CSRF-Token": policy.csrf_token,
            "X-Ingress-Path": "/api/hassio_ingress/private",
            "X-Forwarded-For": "127.0.0.1",
            "X-Forwarded-Proto": "https",
        }
        self.assertEqual(policy.authorize(h, "POST", "/api/save").status, 403)
        h.client_address = ("127.0.0.1", 12345)
        # A backend bound to 0.0.0.0 must not trust remote-proxy loopback.
        self.assertEqual(policy.authorize(h, "POST", "/api/save").status, 403)
        h._authenticated_basic = True
        self.assertIsNone(policy.authorize(h, "POST", "/api/save"))
        h.headers["X-CSRF-Token"] = "invalid"
        self.assertEqual(policy.authorize(h, "POST", "/api/save").status, 403)

    def test_loopback_access_rejects_dns_rebinding_host(self):
        class Handler:
            headers = {"Host": "evil.example"}
            client_address = ("127.0.0.1", 12345)
            server = type("Server", (), {"server_address": ("127.0.0.1", 3218)})()

        policy = ApiPolicy()
        h = Handler()
        for host in ("evil.example", "127.0.0.1.evil.example", "localhost.evil.example",
                     "evil@localhost:3218", "localhost:3218/anything",
                     "localhost:notaport", "localhost:3218 ", "localhost\\\\evil"):
            h.headers = {"Host": host}
            with self.subTest(host=host):
                self.assertEqual(policy.authorize(h, "GET", "/").status, 403)
        for host in ("localhost:3218", "127.0.0.1:3218", "[::1]:3218"):
            h.headers = {"Host": host}
            with self.subTest(host=host):
                self.assertIsNone(policy.authorize(h, "GET", "/"))

    def test_privileged_flags_require_literal_boolean_true(self):
        class Handler:
            headers = {"Host": "127.0.0.1:3218"}
            client_address = ("127.0.0.1", 12345)
            server = type("Server", (), {"server_address": ("127.0.0.1", 3218)})()

        policy = ApiPolicy()
        h = Handler()
        h.headers = {"Host": "127.0.0.1:3218", "X-CSRF-Token": policy.csrf_token}
        for endpoint, arg in (
            ("/api/exec_command", {"allow_shell": "false"}),
            ("/api/push", {"allow_git": "false"}),
            ("/api/allowed_networks", {"allow_network": "false"}),
            ("/api/restart", {"allow_ha_control": "false"}),
        ):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(policy.authorize(h, "POST", endpoint, **arg).status, 403)
        for name in ("ALLOW_SHELL_COMMANDS", "ALLOW_GIT_OPERATIONS",
                     "ALLOW_NETWORK_ADMIN", "ALLOW_HA_CONTROL"):
            with self.subTest(name=name):
                self.assertFalse(cfg._secure_flag({name: False}, name, False))
                self.assertTrue(cfg._secure_flag({name: True}, name, False))
                for invalid in ("false", "true", 0, 1, None, []):
                    with self.assertRaises(ValueError):
                        cfg._secure_flag({name: invalid}, name, False)

    def test_privileged_operations_disabled_even_with_valid_csrf(self):
        class Handler:
            headers = {}
            client_address = ("127.0.0.1", 12345)
            server = type("Server", (), {"server_address": ("127.0.0.1", 3218)})()

        policy = ApiPolicy()
        h = Handler()
        h.headers = {"X-CSRF-Token": policy.csrf_token,
                     "Host": "127.0.0.1:3218"}
        for method, path in (
            ("POST", "/api/exec_command"),
            ("POST", "/api/push"),
            ("POST", "/api/allowed_networks"),
            ("POST", "/api/restart"),
        ):
            with self.subTest(method=method, path=path):
                self.assertEqual(policy.authorize(h, method, path).status, 403)
        self.assertEqual(
            policy.authorize(h, "POST", "/api/restart", allow_ha_control=True),
            None,
        )
        h.headers = {}
        self.assertEqual(
            policy.authorize(h, "POST", "/api/restart", allow_ha_control=True).status,
            403,
        )



class SettingsBooleanSemanticsTests(unittest.TestCase):
    """Issue #23: legacy bools, settings precedence and opt-in semantics."""

    _MUTATED = (
        "LISTENIP", "LISTENPORT", "BASEPATH", "SSL_CERTIFICATE", "SSL_KEY",
        "HASS_API", "HASS_API_PASSWORD", "CREDENTIALS", "ALLOWED_NETWORKS",
        "BANNED_IPS", "BANLIMIT", "DEV", "IGNORE_PATTERN", "DIRSFIRST",
        "SESAME", "VERIFY_HOSTNAME", "ENFORCE_BASEPATH", "ENV_PREFIX",
        "NOTIFY_SERVICE", "USERNAME", "PASSWORD", "SESAME_TOTP_SECRET",
        "TOTP", "GIT", "REPO", "PORT", "IGNORE_SSL", "HASS_WS_API",
        "ALLOWED_DOMAINS", "HIDEHIDDEN", "ALLOW_SHELL_COMMANDS",
        "EXEC_ALLOWED_BINARIES", "ALLOW_GIT_OPERATIONS",
        "ALLOW_NETWORK_ADMIN", "ALLOW_HA_CONTROL",
    )

    def setUp(self):
        original = {name: getattr(cfg, name) for name in self._MUTATED}
        self.state = patch.multiple(cfg, **original)
        self.state.start()
        self.addCleanup(self.state.stop)

    def _load(self, settings, env=None, *, cli_git=False):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "settings.json"
            path.write_text(json.dumps(settings), encoding="utf-8")
            args = SimpleNamespace(
                settings=str(path), git=cli_git, listen=None, port=None,
                basepath=None, enforce=False, standalone=True, dev=False,
                dirsfirst=False, hidehidden=False, username=None,
                password=None,
            )
            with patch.dict(os.environ, env or {}, clear=True):
                cfg.load_settings(args)

    def test_json_env_cli_precedence_and_git_ui_flags(self):
        with patch.object(cfg, "GIT", False), patch.object(cfg, "REPO", None), \
             patch.object(cfg, "ALLOW_GIT_OPERATIONS", False):
            self._load({"GIT": True, "DIRSFIRST": True, "HIDEHIDDEN": True},
                       {"HC_GIT": "false", "HC_DIRSFIRST": "false",
                        "HC_HIDEHIDDEN": "false"})
            self.assertIs(cfg.GIT, False)
            self.assertIs(cfg.DIRSFIRST, False)
            self.assertIs(cfg.HIDEHIDDEN, False)
            self.assertIs(cfg.ALLOW_GIT_OPERATIONS, False)
            self.assertIsNone(cfg.REPO)

            self._load({"GIT": False}, {"HC_GIT": "true"})
            self.assertIs(cfg.GIT, True)
            self.assertIs(cfg.ALLOW_GIT_OPERATIONS, False)
            self.assertIsNotNone(cfg.REPO)

            self._load({"GIT": True}, {"HC_GIT": "false"}, cli_git=True)
            self.assertIs(cfg.GIT, True)
            self.assertIs(cfg.ALLOW_GIT_OPERATIONS, False)

            self._load({"GIT": False}, {"HC_GIT": "false"})
            self.assertIs(cfg.GIT, False)
            self.assertIsNone(cfg.REPO)

    def test_malformed_legacy_boolean_inputs_rejected(self):
        for settings, env in (
            ({"GIT": "false"}, {}),
            ({"DIRSFIRST": 1}, {}),
            ({"HIDEHIDDEN": None}, {}),
            ({}, {"HC_GIT": "1"}),
            ({}, {"HC_GIT": "yes"}),
            ({}, {"HC_DIRSFIRST": "off"}),
            ({}, {"HC_HIDEHIDDEN": ""}),
            ({}, {"HC_IGNORE_SSL": "no"}),
            ({}, {"HC_ENFORCE_BASEPATH": "0"}),
        ):
            with self.subTest(settings=settings, env=env):
                with self.assertRaises(ValueError):
                    self._load(settings, env)

    def test_enforce_basepath_false_warns_for_json_and_environment(self):
        for settings, env in (
            ({"ENFORCE_BASEPATH": False}, {}),
            ({}, {"HC_ENFORCE_BASEPATH": "false"}),
        ):
            with self.subTest(settings=settings, env=env):
                with patch.object(cfg.LOG, "warning") as warning:
                    self._load(settings, env)
                self.assertIs(cfg.ENFORCE_BASEPATH, True)
                self.assertTrue(any(
                    "ENFORCE_BASEPATH=false ignored" in str(call)
                    for call in warning.call_args_list
                ))

    def test_boolean_looking_password_remains_string_and_git_gate_is_strict(self):
        with patch.object(cfg, "ALLOW_GIT_OPERATIONS", False):
            self._load({"GIT": False}, {"HC_PASSWORD": "false",
                                       "HC_ALLOW_GIT_OPERATIONS": "false"})
            self.assertEqual(cfg.PASSWORD, "false")
            self.assertIs(cfg.ALLOW_GIT_OPERATIONS, False)
            with self.assertRaises(ValueError):
                self._load({}, {"HC_ALLOW_GIT_OPERATIONS": "1"})


class HostHeaderTests(unittest.TestCase):
    def test_host_must_match_exact_name_not_substring_or_userinfo(self):
        with patch.object(cfg, "VERIFY_HOSTNAME", "trusted.example"):
            for valid in ("trusted.example", "TRUSTED.EXAMPLE", "trusted.example:3218"):
                self.assertTrue(cfg.verify_hostname(valid))
            for invalid in ("attacker-trusted.example", "trusted.example.evil",
                            "trusted.example@evil.example", "trusted.example/path",
                            "trusted.example\\r\\nX-Evil: 1"):
                self.assertFalse(cfg.verify_hostname(invalid))

    def test_configured_host_port_must_match(self):
        with patch.object(cfg, "VERIFY_HOSTNAME", "trusted.example:443"):
            self.assertTrue(cfg.verify_hostname("trusted.example:443"))
            self.assertFalse(cfg.verify_hostname("trusted.example:444"))
            self.assertFalse(cfg.verify_hostname("trusted.example"))


class BasicAuthConcurrencyTests(unittest.TestCase):
    def test_parallel_bad_credentials_reach_ban_threshold_without_lost_updates(self):
        previous = dict(cfg.FAIL2BAN_IPS)
        cfg.FAIL2BAN_IPS.clear()
        bad_basic = "Basic " + base64.b64encode(b"admin:wrong").decode("ascii")
        server = None
        worker = None
        try:
            with patch.object(cfg, "USERNAME", "admin"), \
                 patch.object(cfg, "PASSWORD", "correct"), \
                 patch.object(cfg, "BANLIMIT", 3):
                server = cfg.SimpleServer(("127.0.0.1", 0), cfg.AuthHandler)
                worker = threading.Thread(target=server.serve_forever, daemon=True)
                worker.start()
                results = []
                failures = []
                ready = threading.Barrier(9)

                def wrong_login():
                    try:
                        ready.wait(timeout=5)
                        code, _, _ = http_request(
                            server, "GET", "/", headers={"Authorization": bad_basic})
                        results.append(code)
                    except Exception as exc:
                        failures.append(exc)

                callers = [threading.Thread(target=wrong_login) for _ in range(8)]
                for caller in callers:
                    caller.start()
                ready.wait(timeout=5)
                for caller in callers:
                    caller.join(timeout=5)
                self.assertFalse(any(caller.is_alive() for caller in callers))
                self.assertFalse(failures)
                self.assertEqual(len(results), 8)
                self.assertEqual(results.count(401), 2)
                self.assertEqual(results.count(420), 6)
        finally:
            if server is not None:
                server.shutdown()
                server.server_close()
            if worker is not None:
                worker.join(timeout=5)
            cfg.FAIL2BAN_IPS.clear()
            cfg.FAIL2BAN_IPS.update(previous)


class BoundedFileReadTests(unittest.TestCase):
    def test_descriptor_bound_read_rejects_file_larger_than_limit(self):
        from hass_configurator.api_security import FileReadLimitExceeded
        with tempfile.TemporaryDirectory() as workspace:
            target = Path(workspace) / "large.yaml"
            target.write_bytes(b"Z" * 256)
            fs = ConfinedFS(workspace)
            with self.assertRaises(FileReadLimitExceeded):
                fs.read_bytes(target, max_bytes=64)
            self.assertEqual(fs.read_bytes(target, max_bytes=256), b"Z" * 256)


class ConfinedFileTests(unittest.TestCase):
    def setUp(self):
        self.parent = tempfile.TemporaryDirectory()
        self.addCleanup(self.parent.cleanup)
        self.root = Path(self.parent.name) / "workspace"
        self.root.mkdir()
        self.sibling = Path(self.parent.name) / "workspace-neighbor"
        self.sibling.mkdir()
        self.fs = ConfinedFS(self.root)

    def test_prefix_sibling_parent_escape_and_control_bytes_rejected(self):
        outside = self.sibling / "secret.txt"
        outside.write_text("secret", encoding="utf8")
        for name in (str(outside), str(self.root / ".." / "workspace-neighbor" / "secret.txt"),
                     str(self.root / "../workspace-neighbor/secret.txt"),
                     str(self.root / "evil\x00file")):
            with self.subTest(name=name), self.assertRaises((PermissionError, ValueError)):
                self.fs.read_bytes(name)

    def test_symlinks_and_intermediate_symlinks_rejected(self):
        outside = self.sibling / "secret.txt"
        outside.write_bytes(b"do not read or overwrite")
        link = self.root / "link.txt"
        link.symlink_to(outside)
        folder = self.root / "link-dir"
        folder.symlink_to(self.sibling, target_is_directory=True)
        for operation in (
            lambda: self.fs.read_bytes(link),
            lambda: self.fs.write_bytes(link, b"overwrite"),
            lambda: self.fs.write_bytes(folder / "secret.txt", b"overwrite"),
            lambda: self.fs.resolve_for_read(link),
        ):
            with self.assertRaises(OSError):
                operation()
        self.assertEqual(outside.read_bytes(), b"do not read or overwrite")

    def test_workspace_hardlink_cannot_overwrite_external_inode(self):
        victim = self.sibling / "sensitive.yaml"
        victim.write_bytes(b"outside: unchanged")
        linked = self.root / "hardlink.yaml"
        os.link(victim, linked)
        with self.assertRaises(PermissionError):
            self.fs.write_bytes(linked, b"outside: changed")
        self.assertEqual(victim.read_bytes(), b"outside: unchanged")
        self.assertEqual(linked.read_bytes(), b"outside: unchanged")

    def test_fd_confined_write_read_rename_create_and_remove(self):
        folder = self.root / "dir"
        self.fs.mkdir(folder)
        first = folder / "first.yaml"
        self.fs.write_bytes(first, b"old: true")
        self.assertEqual(self.fs.read_bytes(first), b"old: true")
        self.fs.write_bytes(first, b"new: true")
        self.assertEqual(self.fs.read_bytes(first), b"new: true")
        with self.assertRaises(FileExistsError):
            self.fs.write_bytes(first, b"cannot clobber", exclusive=True)
        second = folder / "second.yaml"
        self.fs.rename(first, second)
        self.assertFalse(first.exists())
        self.assertEqual(self.fs.read_bytes(second), b"new: true")
        self.fs.remove(second)
        self.fs.remove(folder, is_dir=True)
        self.assertFalse(folder.exists())

    def test_directory_scan_uses_descriptor_and_omits_symlink_entries(self):
        nested = self.root / "nested"
        self.fs.mkdir(nested)
        self.fs.write_bytes(nested / "real.yaml", b"a: 1")
        (nested / "outside").symlink_to(self.sibling, target_is_directory=True)
        names = {item["name"] for item in self.fs.scan_dir(nested)}
        self.assertIn("real.yaml", names)
        self.assertNotIn("outside", names)
        if hasattr(os, "mkfifo"):
            fifo = nested / "named-pipe"
            os.mkfifo(fifo)
            names = {item["name"] for item in self.fs.scan_dir(nested)}
            self.assertNotIn("named-pipe", names)
            with self.assertRaises(PermissionError):
                self.fs.read_bytes(fifo)
            with self.assertRaises(PermissionError):
                self.fs.write_bytes(fifo, b"unexpected")
        with self.assertRaises(OSError):
            self.fs.scan_dir(nested / "outside")

    def test_no_root_removal(self):
        with self.assertRaises(PermissionError):
            self.fs.remove(self.root)



class GitMetadataConfinementTests(unittest.TestCase):
    """Git metadata must not escape even if the worktree is inside BASEPATH."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.workspace = base / "workspace"
        self.workspace.mkdir()
        self.repo_dir = self.workspace / "project"
        self.repo_dir.mkdir()
        self.outside = base / "outside"
        self.outside.mkdir()

    def test_normal_git_repository_and_nested_file_are_accepted(self):
        from git import Repo
        with patch.object(cfg, "BASEPATH", str(self.workspace)), \
             patch.object(cfg, "REPO", Repo):
            initialized = cfg.safe_init_repo(str(self.repo_dir))
            self.assertEqual(Path(initialized.working_dir), self.repo_dir)
            nested = self.repo_dir / "configs"
            nested.mkdir()
            target = nested / "test.yaml"
            target.write_text("key: true\n", encoding="utf-8")
            found = cfg.validated_repo(str(target),
                                       search_parent_directories=True)
            self.assertEqual(Path(found.working_dir), self.repo_dir)
            self.assertEqual(Path(found.git_dir), self.repo_dir / ".git")

    def test_repository_at_workspace_root_is_accepted(self):
        # Protect the cursor == fs.root order: inspect .git before rejecting
        # a search past the workspace boundary.
        from git import Repo
        with patch.object(cfg, "BASEPATH", str(self.workspace)), \
             patch.object(cfg, "REPO", Repo):
            initialized = cfg.safe_init_repo(str(self.workspace))
            self.assertEqual(Path(initialized.working_dir), self.workspace)
            root_repo = cfg.validated_repo(str(self.workspace),
                                           search_parent_directories=True)
            self.assertEqual(Path(root_repo.working_dir), self.workspace)
            target = self.workspace / "at-root.yaml"
            target.write_text("inside: true\n", encoding="utf-8")
            found = cfg.validated_repo(str(target),
                                       search_parent_directories=True)
            self.assertEqual(Path(found.working_dir), self.workspace)
            self.assertEqual(Path(found.common_dir), self.workspace / ".git")

    def test_gitdir_pointer_and_symlink_are_rejected_before_gitpython(self):
        for mode in ("pointer", "symlink"):
            with self.subTest(mode=mode):
                control = self.repo_dir / ".git"
                if mode == "pointer":
                    control.write_text("gitdir: " +
                                       str(self.outside / ".git") + "\n",
                                       encoding="utf-8")
                else:
                    control.symlink_to(self.outside, target_is_directory=True)
                try:
                    with patch.object(cfg, "BASEPATH", str(self.workspace)), \
                         patch.object(cfg, "REPO") as repo_class:
                        with self.assertRaises(PermissionError):
                            cfg.validated_repo(str(self.repo_dir),
                                               search_parent_directories=True)
                        repo_class.assert_not_called()
                        with self.assertRaises(PermissionError):
                            cfg.safe_init_repo(str(self.repo_dir))
                        repo_class.init.assert_not_called()
                finally:
                    control.unlink()

    def test_git_commondir_pointer_refused_before_gitpython(self):
        control = self.repo_dir / ".git"
        control.mkdir()
        (control / "commondir").write_text(str(self.outside) + "\n",
                                           encoding="utf-8")
        with patch.object(cfg, "BASEPATH", str(self.workspace)), \
             patch.object(cfg, "REPO") as repo_class:
            with self.assertRaises(PermissionError):
                cfg.validated_repo(str(self.repo_dir))
            repo_class.assert_not_called()
            with self.assertRaises(PermissionError):
                cfg.safe_init_repo(str(self.repo_dir))
            repo_class.init.assert_not_called()

    def test_gitpython_metadata_redirect_is_rejected_after_discovery(self):
        from types import SimpleNamespace
        control = self.repo_dir / ".git"
        control.mkdir()
        # Test each metadata location independently; rejecting git_dir alone
        # must not hide a missing common_dir safety check.
        for field in ("git_dir", "common_dir"):
            false_repo = SimpleNamespace(working_dir=str(self.repo_dir),
                                         git_dir=str(control),
                                         common_dir=str(control))
            setattr(false_repo, field, str(self.outside))
            with self.subTest(field=field), \
                 patch.object(cfg, "BASEPATH", str(self.workspace)), \
                 patch.object(cfg, "REPO", return_value=false_repo) as factory:
                with self.assertRaises(PermissionError):
                    cfg.validated_repo(str(self.repo_dir))
                factory.assert_called_once()



def http_request(server, method, path, data=None, headers=None):
    conn = http.client.HTTPConnection(
        "127.0.0.1", server.server_address[1], timeout=5)
    try:
        conn.request(method, path, body=data,
                     headers=headers or {})
        resp = conn.getresponse()
        return resp.status, dict(resp.getheaders()), resp.read()
    finally:
        conn.close()


def http_raw_headers(server, method, path, data=None, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
    try:
        conn.request(method, path, body=data, headers=headers or {})
        response = conn.getresponse()
        result = response.status, list(response.getheaders())
        response.read()
        return result
    finally:
        conn.close()



def raw_post_with_headers(server, path, header_pairs):
    """Send raw HTTP/1.1 request headers without http.client adding length."""
    conn = http.client.HTTPConnection("127.0.0.1",
                                      server.server_address[1], timeout=5)
    try:
        conn.putrequest("POST", path)
        for name, value in header_pairs:
            conn.putheader(name, value)
        conn.endheaders()
        reply = conn.getresponse()
        return reply.status, list(reply.getheaders()), reply.read()
    finally:
        conn.close()


class SecurityLoopbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory()
        cls.old = (cfg.BASEPATH, cfg.HASS_API, cfg.ALLOW_SHELL_COMMANDS,
                   cfg.ALLOW_GIT_OPERATIONS, cfg.ALLOW_NETWORK_ADMIN,
                   cfg.ALLOW_HA_CONTROL, cfg.USERNAME, cfg.PASSWORD)
        cfg.BASEPATH = cls.workspace.name
        cfg.HASS_API = None
        cfg.ALLOW_SHELL_COMMANDS = False
        cfg.ALLOW_GIT_OPERATIONS = False
        cfg.ALLOW_NETWORK_ADMIN = False
        cfg.ALLOW_HA_CONTROL = False
        cfg.USERNAME = None
        cfg.PASSWORD = None
        cls.server = cfg.SimpleServer(("127.0.0.1", 0), cfg.RequestHandler)
        cls.thread = threading.Thread(
            target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        (cfg.BASEPATH, cfg.HASS_API, cfg.ALLOW_SHELL_COMMANDS,
         cfg.ALLOW_GIT_OPERATIONS, cfg.ALLOW_NETWORK_ADMIN,
         cfg.ALLOW_HA_CONTROL, cfg.USERNAME, cfg.PASSWORD) = cls.old
        cls.workspace.cleanup()

    def test_post_length_errors_are_distinct_and_close_connection(self):
        csrf = ("X-CSRF-Token", cfg.HTTP_ROUTER.security.csrf_token)
        cases = (
            ("missing", [], 411),
            ("invalid-text", [("Content-Length", "bogus")], 400),
            ("negative", [("Content-Length", "-1")], 400),
            ("signed", [("Content-Length", "+1")], 400),
            ("fraction", [("Content-Length", "1.5")], 400),
            ("duplicate", [("Content-Length", "0"),
                           ("Content-Length", "0")], 400),
            ("chunked", [("Transfer-Encoding", "chunked")], 400),
            ("length-and-chunked", [("Content-Length", "0"),
                                   ("Transfer-Encoding", "chunked")], 400),
            ("oversize", [("Content-Length", str(1048576 + 1))], 413),
        )
        for case, headers, expected in cases:
            with self.subTest(case=case):
                status, pairs, payload = raw_post_with_headers(
                    self.server, "/api/save", [csrf] + headers)
                self.assertEqual(status, expected)
                self.assertEqual(payload, {411: b"Length required",
                                           400: b"Bad request",
                                           413: b"Payload too large"}[expected])
                self.assertEqual(
                    [v for k, v in pairs if k.lower() == "cache-control"],
                    ["no-store"])
                self.assertEqual(
                    [v for k, v in pairs if k.lower() == "x-content-type-options"],
                    ["nosniff"])
                self.assertEqual(
                    [v for k, v in pairs if k.lower() == "connection"],
                    ["close"])
        status, _, _ = raw_post_with_headers(
            self.server, "/api/upload",
            [csrf, ("Content-Length", str(100 * 1024 * 1024 + 1))])
        self.assertEqual(status, 413)

    def test_post_oversized_decimal_and_leading_zero_normalization(self):
        # Large syntactically valid decimal headers must not be misclassified
        # when Python int() has a decimal digit conversion limit.
        csrf = ("X-CSRF-Token", cfg.HTTP_ROUTER.security.csrf_token)
        for desc, value, expected in (
            ("five-thousand-nines", "9" * 5000, 413),
            ("over-limit-with-leading-zeros", "0" * 5000 + "1048577", 413),
            ("limit-with-leading-zeros", "0" * 5000 + "1048576", 200),
            ("five-thousand-zeros", "0" * 5000, 200),
        ):
            with self.subTest(desc=desc):
                if expected == 200 and value.lstrip("0"):
                    # Consume the exact declared body on the valid-limit case.
                    # A 1 MiB request is inexpensive and exercises real HTTP.
                    payload = b" " * 1048576
                    status, _, response = http_request(
                        self.server, "POST", "/api/save", payload,
                        {"X-CSRF-Token": csrf[1],
                         "Content-Length": value})
                else:
                    status, _, response = raw_post_with_headers(
                        self.server, "/api/save", [csrf, ("Content-Length", value)])
                self.assertEqual(status, expected)
                if status == 200:
                    self.assertTrue(json.loads(response)["error"])

    def test_exact_post_size_limit_is_accepted_on_both_routes(self):
        # The 1 MiB maximum is a real HTTP body; a 100 MiB synthetic multipart
        # body uses mocked FieldStorage to exercise admission without actually
        # buffering a 100 MiB fixture on shared CI runners.
        csrf = cfg.HTTP_ROUTER.security.csrf_token
        with tempfile.TemporaryDirectory(dir=self.workspace.name) as folder:
            target = Path(folder) / "max-size.yaml"
            prefix = urlencode({"filename": str(target), "text": ""}).encode()
            payload = prefix + b"a" * (1048576 - len(prefix))
            self.assertEqual(len(payload), 1048576)
            status, _, response = http_request(
                self.server, "POST", "/api/save", payload,
                {"X-CSRF-Token": csrf,
                 "Content-Type": "application/x-www-form-urlencoded"})
            self.assertEqual(status, 200)
            self.assertFalse(json.loads(response)["error"])
            self.assertEqual(target.stat().st_size, 1048576 - len(prefix))

            from types import SimpleNamespace
            form = {
                "file": SimpleNamespace(filename="boundary.yaml",
                                        file=BytesIO(b"safe: true")),
                "path": SimpleNamespace(file=BytesIO(folder.encode("utf-8"))),
            }
            with patch.object(cfg.cgi, "FieldStorage", return_value=form):
                status, _, response = raw_post_with_headers(
                    self.server, "/api/upload",
                    [("X-CSRF-Token", csrf),
                     ("Content-Length", str(100 * 1024 * 1024)),
                     ("Content-Type", "multipart/form-data; boundary=test")])
            self.assertEqual(status, 200)
            self.assertFalse(json.loads(response)["error"])
            self.assertEqual((Path(folder) / "boundary.yaml").read_bytes(),
                             b"safe: true")

    def test_post_zero_length_valid_and_security_gate_precedes_size(self):
        csrf = ("X-CSRF-Token", cfg.HTTP_ROUTER.security.csrf_token)
        status, _, payload = raw_post_with_headers(
            self.server, "/api/save", [csrf, ("Content-Length", "0")])
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(payload)["error"])
        # Even malformed body framing never bypasses authorization or CSRF.
        status, _, _ = raw_post_with_headers(self.server, "/api/save", [])
        self.assertEqual(status, 403)
        with patch.object(cfg.HTTP_ROUTER.security, "_loopback_bound",
                          return_value=False):
            status, _, _ = raw_post_with_headers(
                self.server, "/api/save", [csrf, ("Content-Length", "bogus")])
            self.assertEqual(status, 403)

    def test_every_registered_legacy_api_has_auth_and_csrf_admission(self):
        from hass_configurator.http_routing import GET_API, POST_API
        from hass_configurator.api_security import GIT, SHELL, NETWORK, HA_CONTROL
        self.assertEqual(
            GIT | SHELL | NETWORK | HA_CONTROL,
            GIT.union(SHELL, NETWORK, HA_CONTROL) & POST_API)
        with patch.object(cfg.HTTP_ROUTER.security, "_loopback_bound",
                          return_value=False):
            for path in sorted(GET_API | {"/"}):
                with self.subTest(method="GET", path=path):
                    status, _, _ = http_request(self.server, "GET", path)
                    self.assertEqual(status, 403)
            for path in sorted(POST_API):
                with self.subTest(method="POST", path=path):
                    status, _, _ = http_request(self.server, "POST", path, b"")
                    self.assertEqual(status, 403)
        # Basic/local access never exempts ordinary mutations from CSRF.
        for path in sorted(POST_API):
            with self.subTest(no_csrf=path):
                status, _, _ = http_request(self.server, "POST", path, b"")
                self.assertEqual(status, 403)
        token = cfg.HTTP_ROUTER.security.csrf_token
        for path in sorted(GIT | SHELL | NETWORK | HA_CONTROL):
            with self.subTest(disabled_privilege=path):
                status, _, _ = http_request(
                    self.server, "POST", path, b"",
                    {"X-CSRF-Token": token})
                self.assertEqual(status, 403)

    def test_router_owned_denials_emit_single_security_header_pair(self):
        token = cfg.HTTP_ROUTER.security.csrf_token
        for path, method, headers, unauthorized in (
            ("/api/save", "POST", {}, False),
            ("/api/exec_command", "POST", {"X-CSRF-Token": token}, False),
            ("/", "GET", {}, True),
        ):
            with self.subTest(path=path, method=method, unauthorized=unauthorized):
                with patch.object(cfg.HTTP_ROUTER.security, "_loopback_bound", return_value=False) if unauthorized else patch.object(cfg, "ALLOW_SHELL_COMMANDS", False):
                    status, raw_headers = http_raw_headers(
                        self.server, method, path, b"" if method == "POST" else None,
                        headers)
                self.assertEqual(status, 403)
                for name, expected in (("cache-control", "no-store"),
                                       ("x-content-type-options", "nosniff")):
                    matches = [v for k, v in raw_headers if k.lower() == name]
                    self.assertEqual(matches, [expected],
                                     "Duplicate or missing %s in %s" % (name, path))

    def test_missing_wrong_or_spoofed_csrf_never_writes_file(self):
        target = Path(self.workspace.name) / "csrf-target.yaml"
        body = urlencode({"filename": str(target), "text": "safe: true"}).encode()
        for token in (None, "bad-token"):
            hdrs = {"Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "http://evil.invalid",
                    "X-Ingress-Path": "/injected/path"}
            if token is not None:
                hdrs["X-CSRF-Token"] = token
            status, headers, _ = http_request(
                self.server, "POST", "/api/save", body, hdrs)
            self.assertEqual(status, 403)
            self.assertEqual(headers.get("Cache-Control"), "no-store")
            self.assertFalse(target.exists())
        token = cfg.HTTP_ROUTER.security.csrf_token
        status, _, raw = http_request(
            self.server, "POST", "/api/save", body,
            {"Content-Type": "application/x-www-form-urlencoded",
             "X-CSRF-Token": token})
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(raw)["error"])
        self.assertEqual(target.read_text(), "safe: true")

    def test_ha_control_requires_post_csrf_and_capability(self):
        with patch("urllib.request.urlopen") as urlopen:
            status, headers, _ = http_request(self.server, "GET", "/api/restart")
            self.assertEqual(status, 405)
            self.assertEqual(headers.get("Allow"), "POST")
            status, _, _ = http_request(self.server, "POST", "/api/restart", b"")
            self.assertEqual(status, 403)
            status, _, _ = http_request(
                self.server, "POST", "/api/restart", b"",
                headers={"X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
            self.assertEqual(status, 403)
            urlopen.assert_not_called()

    def test_string_valued_privileged_flags_never_enable_http_routes(self):
        # JSON configuration strings such as "false" must not be treated as opt-in.
        headers = {"X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token,
                   "Content-Type": "application/x-www-form-urlencoded"}
        with patch.object(cfg, "ALLOW_SHELL_COMMANDS", "false"), \
             patch.object(cfg, "EXEC_ALLOWED_BINARIES", ["/usr/bin/true"]), \
             patch.object(cfg, "ALLOW_GIT_OPERATIONS", "false"), \
             patch.object(cfg, "GIT", True), \
             patch.object(cfg, "ALLOW_NETWORK_ADMIN", "false"), \
             patch.object(cfg, "ALLOW_HA_CONTROL", "false"), \
             patch("urllib.request.urlopen") as opener:
            for route in ("/api/exec_command", "/api/push",
                          "/api/allowed_networks", "/api/restart"):
                with self.subTest(route=route):
                    status, _, _ = http_request(
                        self.server, "POST", route, b"path=/&command=id", headers)
                    self.assertEqual(status, 403)
            opener.assert_not_called()

    def test_shell_executes_resolved_allowlisted_path_not_client_symlink(self):
        command_link = Path(self.workspace.name) / "shell-allowlisted-symlink"
        command_link.symlink_to("/usr/bin/true")
        with patch.object(cfg, "ALLOW_SHELL_COMMANDS", True), \
             patch.object(cfg, "EXEC_ALLOWED_BINARIES", ["/usr/bin/true"]), \
             patch.object(cfg, "run_bounded_command",
                          return_value=(0, b"", b"")) as runner:
            body = urlencode({"command": str(command_link)}).encode()
            status, _, raw = http_request(
                self.server, "POST", "/api/exec_command", body,
                {"Content-Type": "application/x-www-form-urlencoded",
                 "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
            self.assertEqual(status, 200)
            self.assertFalse(json.loads(raw)["error"])
            self.assertEqual(runner.call_args.args[0][0],
                             os.path.realpath("/usr/bin/true"))
            self.assertNotEqual(runner.call_args.args[0][0], str(command_link))

    def test_http_shell_timeout_kills_inherited_pipe_descendants(self):
        # The subprocess deliberately starts a child that inherits stdout
        # and stderr. A naive proc.kill(); proc.communicate() blocks until
        # the child exits rather than respecting the HTTP timeout.
        command = "/bin/sh -c 'sleep 8 & wait'"
        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token}
        with patch.object(cfg, "ALLOW_SHELL_COMMANDS", True), \
             patch.object(cfg, "EXEC_ALLOWED_BINARIES", ["/bin/sh"]):
            import time
            started = time.monotonic()
            status, _, raw = http_request(
                self.server, "POST", "/api/exec_command",
                urlencode({"command": command, "timeout": 1}).encode(), headers)
            elapsed = time.monotonic() - started
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)["error"])
        self.assertIn("timed out", json.loads(raw)["message"])
        self.assertLess(elapsed, 3.0, "Inherited pipes delayed timeout handling")

    @unittest.skipUnless(os.name == "posix", "Process groups require POSIX")
    def test_shell_timeout_prevents_descendant_post_deadline_write(self):
        # Unlike the inherited-pipes latency test, this fails if killpg is
        # deliberately disabled OR weakened to SIGTERM: the child ignores
        # TERM/INT and writes a marker AFTER the reply unless SIGKILL works.
        # Keep the marker inside the disposable, isolated HTTP test workspace.
        with tempfile.TemporaryDirectory(dir=self.workspace.name) as scratch:
            marker = Path(scratch) / "orphan-wrote-after-timeout"
            # An ignored SIGTERM/INT makes the test fail if process-group
            # termination is weakened from SIGKILL to a catchable signal.
            descendant = ("trap '' TERM INT; sleep 2; printf survived > "
                          + shlex.quote(str(marker)))
            command = "/bin/sh -c " + shlex.quote("(" + descendant + ") & wait")
            headers = {"Content-Type": "application/x-www-form-urlencoded",
                       "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token}
            with patch.object(cfg, "ALLOW_SHELL_COMMANDS", True), \
                 patch.object(cfg, "EXEC_ALLOWED_BINARIES", ["/bin/sh"]):
                started = time.monotonic()
                status, _, raw = http_request(
                    self.server, "POST", "/api/exec_command",
                    urlencode({"command": command, "timeout": 1}).encode(), headers)
                elapsed = time.monotonic() - started
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(raw)["error"])
            self.assertIn("timed out", json.loads(raw)["message"])
            self.assertLess(elapsed, 3.0)
            # The still-live descendant would write 2s after its start.
            # Waiting after the 1s deadline detects a lost group kill.
            time.sleep(1.7)
            self.assertFalse(marker.exists(),
                             "Timed-out command left a live descendant")

    def test_http_shell_oversized_output_is_terminated(self):
        # yes floods stdout; the server must not buffer it into worker RAM.
        command = "/bin/sh -c 'yes x'"
        with patch.object(cfg, "ALLOW_SHELL_COMMANDS", True), \
             patch.object(cfg, "EXEC_ALLOWED_BINARIES", ["/bin/sh"]):
            status, _, raw = http_request(
                self.server, "POST", "/api/exec_command",
                urlencode({"command": command, "timeout": 3}).encode(),
                {"Content-Type": "application/x-www-form-urlencoded",
                 "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(raw)["error"])
        self.assertIn("output exceeds", json.loads(raw)["message"])

    def test_shell_git_and_network_mutations_denied_before_body(self):
        headers = {"X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token,
                   "Content-Type": "application/x-www-form-urlencoded"}
        for route in ("/api/exec_command", "/api/push", "/api/allowed_networks"):
            with self.subTest(route=route):
                status, _, _ = http_request(
                    self.server, "POST", route, b"path=/&command=id", headers)
                self.assertEqual(status, 403)

    def test_download_and_read_path_escape_and_symlink(self):
        outside = Path(self.workspace.name).parent / "outside-sensitive.txt"
        # Avoid creating outside files: symlink to a harmless in-repo fixture.
        try:
            link = Path(self.workspace.name) / "escape"
            link.symlink_to(Path(__file__).resolve())
            for target in (link, Path(self.workspace.name) / "../not-inside-file"):
                path = "/api/download?filename=" + quote(str(target), safe="")
                status, _, content = http_request(self.server, "GET", path)
                self.assertNotIn(b"\"\"\"P1 #7 API authorization", content)
        finally:
            if link.is_symlink():
                link.unlink()

    def test_file_and_download_limit_return_413_without_file_contents(self):
        target = Path(self.workspace.name) / "large-read-target.yaml"
        target.write_bytes(b"SENSITIVE_CONTENT" * 10)
        try:
            with patch.object(cfg, "MAX_FILE_READ_BYTES", 64):
                for route in ("/api/file", "/api/download"):
                    with self.subTest(route=route):
                        status, headers, payload = http_request(
                            self.server, "GET",
                            route + "?filename=" + quote(str(target), safe=""))
                        self.assertEqual(status, 413)
                        self.assertEqual(headers["Cache-Control"], "no-store")
                        self.assertNotIn(b"SENSITIVE_CONTENT", payload)
            status, _, payload = http_request(
                self.server, "GET", "/api/download?filename=" +
                quote(str(target), safe=""))
            self.assertEqual(status, 200)
            self.assertEqual(payload, target.read_bytes())
        finally:
            target.unlink(missing_ok=True)

    def test_nonce_page_treats_ha_bootstrap_as_json_only(self):
        # An upstream response embedded in a nonce-bearing script must not
        # become arbitrary JavaScript merely because it lacks HTML tags.
        responses = [BytesIO(b"[]; window.hc_attacked = true;"),
                     BytesIO(b'[{"event":"</script><script>window.hc_attacked=2</script>"}]'),
                     BytesIO(b"[]")]
        with patch.object(cfg, "HASS_API", "http://127.0.0.1:8123/api/"), \
             patch.object(cfg, "HASS_WS_API", "ws://127.0.0.1:8123/api/websocket"), \
             patch.object(cfg, "HASS_API_PASSWORD", None), \
             patch("urllib.request.urlopen", side_effect=responses):
            status, headers, html = http_request(
                self.server, "GET", "/", headers={"X-Forwarded-Host": "evil.invalid"})
        self.assertEqual(status, 200)
        self.assertIn("connect-src 'self' ws://127.0.0.1:8123/api/websocket;",
                      headers["Content-Security-Policy"])
        self.assertNotIn("evil.invalid", headers["Content-Security-Policy"])
        self.assertIn(b'var services_list = [];', html)
        self.assertIn(b'\\u003c/script\\u003e', html)
        self.assertNotIn(b'[]; window.hc_attacked = true;', html)
        self.assertNotIn(b'</script><script>window.hc_attacked', html)

    def test_nonce_page_rejects_non_list_ha_bootstrap_json(self):
        # Valid JSON is not necessarily a list. Pin the type check separately
        # from the rejection of malformed JSON/JavaScript.
        for value in ({"services": []}, "not a list", 1, True, None):
            with self.subTest(value=value):
                self.assertEqual(cfg._safe_json_list(json.dumps(value)), "[]")
        self.assertEqual(json.loads(cfg._safe_json_list('[{"domain":"light"}]')),
                         [{"domain": "light"}])

        responses = [BytesIO(b'{"services":[]}'),
                     BytesIO(b'{"events":[]}'),
                     BytesIO(b"[]")]
        with patch.object(cfg, "HASS_API", "http://127.0.0.1:8123/api/"), \
             patch.object(cfg, "HASS_WS_API", None), \
             patch.object(cfg, "HASS_API_PASSWORD", None), \
             patch("urllib.request.urlopen", side_effect=responses):
            status, _, html = http_request(self.server, "GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"var services_list = [];", html)
        self.assertIn(b"var events_list = [];", html)
        self.assertNotIn(b'var services_list = {', html)
        self.assertNotIn(b'var events_list = {', html)

    def test_editable_svg_cannot_be_an_executable_same_origin_document(self):
        target = Path(self.workspace.name) / "active.svg"
        target.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>window.hc_attacked=1</script></svg>')
        try:
            for route in ("/api/file", "/api/download"):
                with self.subTest(route=route):
                    status, headers, payload = http_request(
                        self.server, "GET", route + "?filename=" + quote(str(target), safe=""))
                    self.assertEqual(status, 200)
                    self.assertIn("sandbox;", headers["Content-Security-Policy"])
                    self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
                    self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                    self.assertEqual(payload, target.read_bytes())
        finally:
            target.unlink(missing_ok=True)

    def test_query_filename_must_not_generate_executable_inline_js(self):
        payload = "'</script><script>window.attacked=1</script>"
        status, headers, html = http_request(
            self.server, "GET", "/?loadfile=" + quote(payload, safe=""))
        self.assertEqual(status, 200)
        self.assertIn(b"hc-csrf-token", html)
        self.assertNotIn(b"</script><script>window.attacked", html)
        self.assertIn(b"\\u003c/script\\u003e", html)

    def test_loadfile_json_string_boundary_inside_nonce_script(self):
        # No HTML delimiters: _js_safe alone cannot turn these into JS data.
        # The first two inputs are executable statements if json.dumps is
        # removed; the others cover quote/backslash preservation.
        for payload in ("'';window.attacked=1;//",
                        '"";window.attacked=1;//',
                        '";window.attacked=1;//',
                        "';window.attacked=1;//",
                        'quote"\\path\nnext'):
            with self.subTest(payload=payload):
                status, headers, html = http_request(
                    self.server, "GET", "/?loadfile=" + quote(payload, safe=""))
                self.assertEqual(status, 200)
                self.assertIn("'nonce-", headers["Content-Security-Policy"])
                match = re.search(rb"(?m)^\s*var init_loadfile = (.*);$", html)
                self.assertIsNotNone(match)
                # Decode the complete literal, not a substring that might
                # also occur in a raw executable expression.
                self.assertEqual(json.loads(match.group(1).decode("utf-8")),
                                 payload)

    def test_shell_allowlist_denies_unlisted_executable_before_subprocess(self):
        payload = urlencode({"command": "/bin/sh -c whoami", "timeout": "1"}).encode()
        with patch.object(cfg, "ALLOW_SHELL_COMMANDS", True), \
             patch.object(cfg, "EXEC_ALLOWED_BINARIES", ["/usr/bin/true"]), \
             patch("subprocess.Popen") as popen:
            status, _, raw = http_request(
                self.server, "POST", "/api/exec_command", payload,
                {"Content-Type": "application/x-www-form-urlencoded",
                 "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(raw)["error"])
            popen.assert_not_called()

    def test_git_parent_search_cannot_escape_workspace(self):
        from types import SimpleNamespace
        root = Path(self.workspace.name)
        inside = root / "trusted-repo"
        inside.mkdir(exist_ok=True)
        with patch.object(cfg, "REPO", return_value=SimpleNamespace(
                working_dir=str(root.parent))):
            with self.assertRaises(PermissionError):
                cfg.validated_repo(str(inside), search_parent_directories=True)

    def test_opted_in_git_init_and_add_via_real_http(self):
        # Exercise the actual route/policy/CSRF path, not only the helper.
        from git import Repo
        with tempfile.TemporaryDirectory(dir=self.workspace.name) as scratch:
            worktree = Path(scratch) / "repo"
            worktree.mkdir()
            headers = {"Content-Type": "application/x-www-form-urlencoded",
                       "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token}
            with patch.object(cfg, "GIT", True), \
                 patch.object(cfg, "REPO", Repo), \
                 patch.object(cfg, "ALLOW_GIT_OPERATIONS", True):
                status, _, raw = http_request(
                    self.server, "POST", "/api/init",
                    urlencode({"path": str(worktree)}).encode(), headers)
                self.assertEqual(status, 200)
                self.assertFalse(json.loads(raw)["error"], raw)
                self.assertTrue((worktree / ".git").is_dir())
                example = worktree / "example.yaml"
                example.write_text("hello: world\n", encoding="utf-8")
                status, _, raw = http_request(
                    self.server, "POST", "/api/gitadd",
                    urlencode({"path": str(example)}).encode(), headers)
                self.assertEqual(status, 200)
                self.assertFalse(json.loads(raw)["error"], raw)
                self.assertIn("example.yaml",
                              Repo(worktree).git.diff("--cached", "--name-only"))

    def test_opted_in_git_init_denies_control_symlink_via_real_http(self):
        from git import Repo
        with tempfile.TemporaryDirectory(dir=self.workspace.name) as scratch, \
             tempfile.TemporaryDirectory() as outside:
            worktree = Path(scratch) / "repo"
            worktree.mkdir()
            (worktree / ".git").symlink_to(outside, target_is_directory=True)
            headers = {"Content-Type": "application/x-www-form-urlencoded",
                       "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token}
            with patch.object(cfg, "GIT", True), \
                 patch.object(cfg, "REPO", Repo), \
                 patch.object(cfg, "ALLOW_GIT_OPERATIONS", True):
                status, _, raw = http_request(
                    self.server, "POST", "/api/init",
                    urlencode({"path": str(worktree)}).encode(), headers)
            self.assertEqual(status, 200)
            self.assertTrue(json.loads(raw)["error"])
            self.assertTrue((worktree / ".git").is_symlink())
            self.assertEqual(list(Path(outside).iterdir()), [])


    def test_preferences_symlink_cannot_overwrite_file_outside_workspace(self):
        prefs = Path(self.workspace.name) / cfg.PREFS_FILENAME
        with tempfile.TemporaryDirectory() as external:
            victim = Path(external) / "unrelated.txt"
            victim.write_text("original secret", encoding="utf8")
            if prefs.exists() or prefs.is_symlink():
                self.skipTest("Unexpected existing preferences file")
            prefs.symlink_to(victim)
            try:
                body = json.dumps({"ui_theme": "dark"}).encode("utf8")
                status, _, raw = http_request(
                    self.server, "POST", "/api/prefs", body,
                    {"Content-Type": "application/json",
                     "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
                self.assertEqual(status, 200)
                self.assertTrue(json.loads(raw)["error"])
                self.assertEqual(victim.read_text(), "original secret")
                self.assertEqual(cfg.load_prefs()["ui_theme"], "auto")
            finally:
                prefs.unlink()

    def test_config_debug_settings_always_redact_secrets(self):
        cleaned = cfg._redacted_settings({
            "HASS_API_PASSWORD": "not-for-logs",
            "SESAME_TOTP_SECRET": "not-for-logs",
            "PASSWORD": "not-for-logs",
            "HASS_API": "http://bob:pass@localhost:8123/api/?token=secret",
            "HASS_WS_API": "ws://bob:pass@localhost:8123/api/websocket?token=secret",
            "SESAME": "secret-access-url-token",
        })
        for field in ("PASSWORD", "HASS_API_PASSWORD", "SESAME_TOTP_SECRET",
                      "SESAME"):
            self.assertEqual(cleaned[field], "<redacted>")
        self.assertEqual(cleaned["HASS_API"], "<redacted-url>")
        self.assertEqual(cleaned["HASS_WS_API"], "<redacted-url>")

    def test_loaded_secret_settings_do_not_reach_debug_logs(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as folder:
            settings_file = Path(folder) / "settings.json"
            secret = "sesame-bearer-keep-private"
            url_secret = "query-credential-keep-private"
            settings_file.write_text(json.dumps({
                "SESAME": secret,
                "HASS_API": "http://u:pass@localhost:8123/api/?access_token=" + url_secret,
                "HASS_WS_API": "ws://u:pass@localhost:8123/api/websocket?token=" + url_secret,
            }), encoding="utf-8")
            opts = SimpleNamespace(
                settings=str(settings_file), git=False, listen=None,
                port=None, basepath=None, enforce=False, standalone=False,
                dirsfirst=False, hidehidden=False, dev=False,
                username=None, password=None)
            with patch.object(cfg, "SESAME", None), \
                 patch.object(cfg, "HASS_API", None), \
                 patch.object(cfg, "HASS_WS_API", None), \
                 patch.object(cfg.LOG, "debug") as debug:
                cfg.load_settings(opts)
                logged = repr(debug.call_args_list)
            self.assertNotIn(secret, logged)
            self.assertNotIn(url_secret, logged)
            self.assertNotIn("u:pass", logged)
            self.assertIn("<redacted>", logged)
            self.assertIn("<redacted-url>", logged)

    def test_request_log_never_contains_query_tokens_or_sesame_path(self):
        secret = "not-for-request-logs"
        with patch.object(cfg.LOG, "info") as info:
            status, _, _ = http_request(
                self.server, "GET", "/api/version?access_token=" + secret)
        self.assertEqual(status, 200)
        self.assertNotIn(secret, repr(info.call_args_list))

    def test_sesame_bearer_url_is_not_recorded_by_request_logging(self):
        secret = "private-test-sesame-key-8f6a20"
        with patch.object(cfg, "SESAME", secret), \
             patch.object(cfg, "HASS_API", None), \
             patch.object(cfg, "ALLOWED_NETWORKS", []), \
             patch.object(cfg.LOG, "info") as info:
            status, _, _ = http_request(self.server, "GET", "/" + secret)
        self.assertEqual(status, 302)
        self.assertNotIn(secret, repr(info.call_args_list))

    def test_network_allowlist_cannot_be_cleared_by_admin(self):
        original = list(cfg.ALLOWED_NETWORKS)
        cfg.ALLOWED_NETWORKS[:] = ["127.0.0.1/32"]
        try:
            with patch.object(cfg, "ALLOW_NETWORK_ADMIN", True):
                payload = urlencode({"network": "127.0.0.1/32", "method": "remove"}).encode()
                status, _, data = http_request(
                    self.server, "POST", "/api/allowed_networks", payload,
                    {"Content-Type": "application/x-www-form-urlencoded",
                     "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
                self.assertEqual(status, 200)
                self.assertTrue(json.loads(data)["error"])
                self.assertEqual(cfg.ALLOWED_NETWORKS, ["127.0.0.1/32"])
        finally:
            cfg.ALLOWED_NETWORKS[:] = original

    def test_parallel_network_removals_never_clear_last_allowed_range(self):
        original = list(cfg.ALLOWED_NETWORKS)
        cfg.ALLOWED_NETWORKS[:] = ["127.0.0.0/8", "127.0.0.1/32"]
        try:
            results = []
            failures = []
            ready = threading.Barrier(3)
            def remove(network):
                try:
                    ready.wait(timeout=5)
                    body = urlencode({"network": network, "method": "remove"}).encode()
                    status, _, payload = http_request(
                        self.server, "POST", "/api/allowed_networks", body,
                        {"Content-Type": "application/x-www-form-urlencoded",
                         "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
                    results.append((status, json.loads(payload)))
                except Exception as exc:
                    failures.append(exc)

            with patch.object(cfg, "ALLOW_NETWORK_ADMIN", True):
                workers = [threading.Thread(target=remove, args=(network,))
                           for network in tuple(cfg.ALLOWED_NETWORKS)]
                for worker in workers:
                    worker.start()
                ready.wait(timeout=5)
                for worker in workers:
                    worker.join(timeout=5)
                self.assertFalse(any(worker.is_alive() for worker in workers))
                self.assertFalse(failures)
                self.assertEqual(len(results), 2)
                self.assertEqual(len(cfg.ALLOWED_NETWORKS), 1)
                self.assertEqual(sum(not result["error"] for _, result in results), 1)
        finally:
            cfg.ALLOWED_NETWORKS[:] = original

    def test_network_admin_rejects_invalid_method_and_cidr_ban(self):
        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token}
        original_allowed = list(cfg.ALLOWED_NETWORKS)
        original_banned = list(cfg.BANNED_IPS)
        try:
            with patch.object(cfg, "ALLOW_NETWORK_ADMIN", True):
                for route, payload in (
                    ("/api/allowed_networks", {"network": "127.0.0.1/32", "method": "nonsense"}),
                    ("/api/banned_ips", {"ip": "203.0.113.0/24", "method": "ban"}),
                    ("/api/banned_ips", {"ip": "203.0.113.1", "method": "nonsense"}),
                ):
                    with self.subTest(route=route, payload=payload):
                        status, _, raw = http_request(
                            self.server, "POST", route, urlencode(payload).encode(), headers)
                        self.assertEqual(status, 200)
                        self.assertTrue(json.loads(raw)["error"])
                self.assertEqual(cfg.ALLOWED_NETWORKS, original_allowed)
                self.assertEqual(cfg.BANNED_IPS, original_banned)
        finally:
            cfg.ALLOWED_NETWORKS[:] = original_allowed
            cfg.BANNED_IPS[:] = original_banned

    def test_ha_control_real_outbound_post_only_after_all_gates(self):
        class Reply:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return b"{}"

        with patch.object(cfg, "ALLOW_HA_CONTROL", True), \
             patch.object(cfg, "HASS_API", "http://127.0.0.1:8123/api/"), \
             patch("urllib.request.urlopen", return_value=Reply()) as opener:
            status, _, content = http_request(
                self.server, "POST", "/api/restart", b"",
                {"X-CSRF-Token": cfg.HTTP_ROUTER.security.csrf_token})
            self.assertEqual(status, 200)
            self.assertIn(b"{}", content)
            self.assertEqual(opener.call_count, 1)
            req = opener.call_args.args[0]
            self.assertEqual(req.get_method(), "POST")
            self.assertEqual(req.full_url,
                             "http://127.0.0.1:8123/api/services/homeassistant/restart")

    def test_unsupported_internal_http_verbs_are_501(self):
        for method in ("AUTHHEAD", "BLOCK"):
            status, _, _ = http_request(self.server, method, "/")
            self.assertEqual(status, 501)


if __name__ == "__main__":
    unittest.main()
