"""P0 closeout contract: runnable scope, dependency evidence, and P1 boundaries.

These tests intentionally verify *current* P0 contracts. They do not execute
privileged legacy operations, claim real Supervisor Ingress, or inspect repo
branch-protection settings (which are maintainer-controlled outside git).
"""
import io
import json
from pathlib import Path
import unittest

from hass_configurator.http_routing import (
    Assets, Router, error_response, send_response, NO_STORE,
)
from scripts.audit_runtime_assets import extract


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "runtime-dependencies.json"
ACE_LOCK = ROOT / "docs" / "ace-builds-1.9.6-lock.json"
VENDOR_LOCK = ROOT / "hass_configurator" / "vendor" / "manifest.json"


class _FakeTransport:
    """Capture the status/header/end operations of the shared P0 writer."""

    def __init__(self):
        self.statuses = []
        self.headers = []
        self.ends = 0
        self.wfile = io.BytesIO()

    def send_response(self, status):
        self.statuses.append(status)

    def send_header(self, name, value):
        self.headers.append((name, value))

    def end_headers(self):
        self.ends += 1


class P0CloseoutTests(unittest.TestCase):
    def test_runtime_inventory_matches_html_and_has_no_auto_public_origin(self):
        data = json.loads(INVENTORY.read_text("utf8"))
        html = (ROOT / "hass_configurator" / "dev.html").read_text("utf8")
        scanned = extract(html)
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["required_runtime_origins"], [])
        self.assertEqual(data["required_external_files"], [])
        self.assertEqual(data["auto_loaded_external_images"], [])
        self.assertEqual(scanned["cdn"], [])
        self.assertEqual(scanned["avatars"], [])
        self.assertEqual(scanned["other_remote"], [])
        self.assertEqual(scanned["modes"], sorted(data["ace"]["language_modes_offered"]))
        self.assertEqual(scanned["themes"], sorted(data["ace"]["themes_offered"]))
        self.assertEqual(data["ace"]["missing_ui_modes"], [])
        self.assertTrue(data["optional_documentation_links"])

    def test_ace_selection_uses_same_locked_family_and_required_workers(self):
        inventory = json.loads(INVENTORY.read_text("utf8"))
        lock = json.loads(ACE_LOCK.read_text("utf8"))
        vendor = json.loads(VENDOR_LOCK.read_text("utf8"))
        self.assertEqual(lock["name"], "ace-builds")
        self.assertEqual(lock["version"], "1.9.6")
        self.assertEqual(lock["family"], "src-min-noconflict")
        self.assertEqual(lock["family_files"], 440)
        self.assertEqual(len(lock["files_sha256"]), 440)
        self.assertEqual(vendor["provenance"]["ace"]["npm_integrity"],
                         lock["npm_integrity"])
        self.assertEqual(vendor["provenance"]["ace"]["sha256"], lock["sha256"])
        self.assertEqual(inventory["ace"]["archive_sha256"], lock["sha256"])
        self.assertEqual(inventory["ace"]["selected_build_family"], lock["family"])
        for component in ("ace", "materialize", "mdi"):
            with self.subTest(component=component):
                source = vendor["provenance"][component]
                self.assertTrue(source["tarball"].startswith("https://registry.npmjs.org/"))
                self.assertTrue(source["npm_integrity"].startswith("sha512-"))
                self.assertEqual(len(source["sha256"]), 64)
                self.assertTrue(source["license_path_in_archive"])
        for kind, names in (
            ("mode", inventory["ace"]["language_modes_offered"]),
            ("theme", inventory["ace"]["themes_offered"]),
        ):
            for name in names:
                self.assertIn("%s-%s.js" % (kind, name), lock["files_sha256"])
        for name in lock["worker_files"]:
            with self.subTest(worker=name):
                self.assertIn(name, lock["files_sha256"])
                self.assertEqual(
                    vendor["resources"]["vendor/ace/" + name],
                    lock["files_sha256"][name],
                )

    def test_all_legacy_api_paths_remain_behind_exact_p0_router(self):
        router = Router(Assets())
        expected = (
            ("GET", "/api/prefs", "legacy_api"),
            ("POST", "/api/prefs", "legacy_api"),
            ("POST", "/api/save", "legacy_api"),
            ("GET", "/api/save", "method_not_allowed"),
            ("POST", "/api/version", "method_not_allowed"),
            ("GET", "/evil/api/prefs", "not_found"),
            ("POST", "/evil/api/save", "not_found"),
            ("GET", "/api/ws", "not_found"),
            ("GET", "/assets/%2e%2e/api/prefs", "bad_request"),
        )
        for method, url, kind in expected:
            with self.subTest(method=method, url=url):
                self.assertEqual(router.match(method, url).kind, kind)

    def test_router_owned_responses_have_single_status_and_header_block(self):
        for status, allow in ((400, ""), (404, ""), (405, "POST")):
            with self.subTest(status=status):
                fake = _FakeTransport()
                response = error_response(status, allow=allow)
                send_response(fake, response)
                self.assertEqual(fake.statuses, [status])
                self.assertEqual(fake.ends, 1)
                self.assertEqual(fake.wfile.getvalue(), response.body)
                self.assertEqual(fake.headers.count(("Cache-Control", NO_STORE)), 1)
                self.assertEqual(fake.headers.count(
                    ("X-Content-Type-Options", "nosniff")), 1)
                self.assertEqual(fake.headers.count(
                    ("Content-Length", str(len(response.body)))), 1)
                if allow:
                    self.assertEqual(fake.headers.count(("Allow", allow)), 1)

    def test_p0_release_probes_remain_in_ci(self):
        workflow = (ROOT / ".github/workflows/offline-foundation.yml").read_text("utf8")
        failure_fixtures = (ROOT / "tests" / "test_p0_failure_gates.py").read_text(
            "utf8")
        offline_smoke = (ROOT / "e2e" / "offline-smoke.spec.cjs").read_text("utf8")
        for required in (
            "Routing and loopback HTTP tests",
            "Full browser E2E matrix",
            "Browser gate against installed wheel and installed sdist",
            "Build fork Docker image, verify identity offline",
        ):
            self.assertIn(required, workflow)
        for case in (
            "test_injected_public_fetch_fails_inventory_gate",
            "test_missing_first_party_asset_fails_at_startup",
            "test_missing_declared_vendor_asset_fails_at_startup",
        ):
            self.assertIn(case, failure_fixtures)
        self.assertIn("network interceptor sees even a blocked external request",
                      offline_smoke)
        self.assertIn("runtime-attempts.json", offline_smoke)
        for filename in (
            "e2e/ingress-operations.spec.cjs",
            "e2e/cache-upgrade.spec.cjs",
            "e2e/ha-outage.spec.cjs",
            "e2e/release-matrix.spec.cjs",
        ):
            self.assertTrue((ROOT / filename).is_file(), filename)

    def test_closeout_matrix_excludes_real_ingress_and_privileged_security(self):
        closeout = (ROOT / "docs" / "P0_CLOSEOUT.md").read_text("utf8")
        trace = (ROOT / "docs" / "TRACEABILITY.md").read_text("utf8")
        for number in (1, 2, 6, 14):
            self.assertIn("#%d" % number, closeout)
        # Every required safe P0 acceptance scenario must retain an explicit
        # test/evidence row. This is documentation coverage, not a substitute
        # for CI executing the referenced browser and Python test suites.
        for number in range(1, 11):
            self.assertEqual(
                closeout.count("| AT-%02d |" % number), 1,
                "Missing/duplicate AT-%02d closeout row" % number,
            )
        self.assertIn("| AT-04 |", closeout)
        self.assertIn("privileged confirmations intentionally excluded (#7)",
                      closeout)
        for number in (7, 8, 9, 13):
            self.assertIn("#%d" % number, closeout)
        self.assertIn("NOT VERIFIED", closeout)
        self.assertIn("exact-HEAD", closeout)
        self.assertNotIn("all runtime requirements are PENDING", trace)
        self.assertIn("P0 automated", trace)
        self.assertIn("P1", trace)


if __name__ == "__main__":
    unittest.main()
