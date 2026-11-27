"""Fail-closed checks for the disposable #33 rehearsal input."""
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from contextlib import contextmanager, ExitStack
from unittest.mock import patch

from scripts import prepare_ace_migration as migration


class MigrationRehearsalTests(unittest.TestCase):
    def make_archive(self, path, version="4.3.2", duplicate=False, link=False):
        license_bytes = b"fixture license"
        members = [("package/package.json", json.dumps({
            "name": "js-yaml", "version": version, "license": "MIT"
        }).encode()), ("package/LICENSE", license_bytes),
            ("package/dist/js-yaml.min.js", b"fixture payload\n")]
        if duplicate:
            members.append(members[-1])
        with tarfile.open(path, "w:gz") as archive:
            for name, raw in members:
                info = tarfile.TarInfo(name)
                if link and name.endswith(".min.js"):
                    info.type = tarfile.SYMTYPE
                    info.linkname = "package/LICENSE"
                    archive.addfile(info)
                else:
                    info.size = len(raw)
                    archive.addfile(info, io.BytesIO(raw))
        return {"dist.tarball": migration.YAML_URL,
                "dist.integrity": migration.sri(path.read_bytes())}, license_bytes

    @contextmanager
    def pinned_fixture(self, archive, license_bytes):
        raw = archive.read_bytes()
        with patch.multiple(migration, YAML_LICENSE_BLOB=migration.git_blob_sha1(license_bytes),
                            YAML_SHA256=migration.sha(raw), YAML_SRI=migration.sri(raw),
                            YAML_MEMBER_SHA256=migration.sha(b"fixture payload\n"),
                            YAML_LICENSE_SHA256=migration.sha(license_bytes)):
            yield

    def test_exact_yaml_member_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            registry, license_bytes = self.make_archive(archive)
            with self.pinned_fixture(archive, license_bytes):
                report, payload, notice = migration.inspect_yaml(archive, registry)
            self.assertEqual(payload, b"fixture payload\n")
            self.assertEqual(notice, license_bytes)
            self.assertEqual(report["member_sha256"], migration.sha(payload))
            self.assertEqual(report["archive_sha256"], migration.sha(archive.read_bytes()))
            self.assertFalse(report["independent_archive_pin_pending"])

    def test_reject_wrong_registry_source_integrity_and_license(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            registry, license_bytes = self.make_archive(archive)
            for key, value in (("dist.tarball", "https://example.invalid/archive"),
                               ("dist.integrity", "sha512-invalid")):
                with self.subTest(key=key), self.assertRaisesRegex(ValueError, "registry integrity/source"):
                    migration.inspect_yaml(archive, {**registry, key: value})
            with self.pinned_fixture(archive, license_bytes):
                with patch.object(migration, "YAML_LICENSE_BLOB", "bad"):
                    with self.assertRaisesRegex(ValueError, "license differs"):
                        migration.inspect_yaml(archive, registry)

    def test_reject_wrong_identity_duplicate_and_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            for kwargs, message in (({"version": "4.1.0"}, "package identity"),
                                    ({"duplicate": True}, "duplicate or non-regular"),
                                    ({"link": True}, "duplicate or non-regular")):
                registry, license_bytes = self.make_archive(archive, **kwargs)
                with self.pinned_fixture(archive, license_bytes):
                    with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, message):
                        migration.inspect_yaml(archive, registry)

    def test_destination_must_be_new_and_outside_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = parent / "repo"
            root.mkdir()
            with patch.object(migration, "ROOT", root):
                for path in (root, root / "new", parent):
                    with self.subTest(path=path), self.assertRaisesRegex(ValueError, "new and outside"):
                        migration.outside_new_checkout(path)
                self.assertEqual(migration.outside_new_checkout(parent / "new"), parent / "new")

    def test_registry_consistent_but_unpinned_archive_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            registry, _ = self.make_archive(archive)
            with self.assertRaisesRegex(ValueError, "reviewed rehearsal archive"):
                migration.inspect_yaml(archive, registry)

    def test_pinned_archive_member_and_license_hashes_are_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.tgz"
            registry, license_bytes = self.make_archive(archive)
            with self.pinned_fixture(archive, license_bytes):
                for key in ("YAML_MEMBER_SHA256", "YAML_LICENSE_SHA256"):
                    with self.subTest(key=key), patch.object(migration, key, "bad"):
                        with self.assertRaisesRegex(ValueError, "member/license differs"):
                            migration.inspect_yaml(archive, registry)

    @contextmanager
    def main_fixture(self, parent, family_files=495, missing=None, advisories=None):
        bootstrap = (migration.ROOT / "hass_configurator/ace-bootstrap.js").read_bytes()
        profile = migration.read_profile(migration.ROOT / "hass_configurator/ace-bootstrap.js")
        root = parent / "repo"
        (root / "docs").mkdir(parents=True)
        workers = profile["infrastructure"] + profile["excluded"] + [
            row["file"] for row in profile["languages"].values()]
        family = {name: ("fixture:" + name).encode()
                  for name in workers + profile["excluded_themes"]}
        family.update({"mode-fixture-%d.js" % i: str(i).encode()
                       for i in range(495 - len(family))})
        runtime_lock = {"version": profile["ace_version"], "worker_files": workers,
                        "files_sha256": {n: migration.sha(b) for n, b in family.items()}}
        pkg = root / "hass_configurator"
        (pkg / "vendor/ace").mkdir(parents=True)
        (pkg / "vendor/licenses").mkdir()
        (pkg / "third_party/licenses").mkdir(parents=True)
        (pkg / "ace-bootstrap.js").write_bytes(bootstrap)
        (pkg / "vendor/manifest.json").write_text(json.dumps({
            "schema": 1, "resources": {}, "provenance": {}}), encoding="utf-8")
        for name, value in (
            ("ace-candidate-1.45.2.json", {"tarball": "fixture"}),
            ("ace-builds-1.45.2-lock.json", runtime_lock),
            ("ace-builds-1.9.6-lock.json", {"files_sha256": {}}),
            ("runtime-dependencies.json", {"ace": {}}),
        ):
            (root / "docs" / name).write_text(json.dumps(value), encoding="utf-8")
        archive = parent / "ace.tgz"
        license_bytes = b"ace fixture license"
        with tarfile.open(archive, "w:gz") as tar:
            info = tarfile.TarInfo("package/LICENSE")
            info.size = len(license_bytes)
            tar.addfile(info, io.BytesIO(license_bytes))
        registry = parent / "registry.json"
        registry.write_text("{}", encoding="utf-8")
        dest = parent / "overlay"
        report = parent / "evidence" / "verified-input.json"
        argv = ["prepare_ace_migration.py", "--ace", str(archive),
                "--ace-registry", str(registry), "--yaml", str(archive),
                "--yaml-registry", str(registry), "--dest", str(dest),
                "--report", str(report)]
        ace = {"family_files": family_files, "missing_ui_files": missing or [],
               "source_checkout": "fixture"}
        with ExitStack() as stack:
            stack.enter_context(patch.multiple(migration, ROOT=root,
                ACE_SHA256=migration.sha(archive.read_bytes()),
                ACE_SRI=migration.sri(archive.read_bytes()),
                ACE_LICENSE_SHA256=migration.sha(license_bytes)))
            stack.enter_context(patch("sys.argv", argv))
            stack.enter_context(patch.object(migration, "inspect_candidate", return_value=(ace, family)))
            yaml = stack.enter_context(patch.object(migration, "inspect_yaml",
                return_value=({"member_sha256": migration.sha(b"yaml"),
                               "license_sha256": migration.sha(b"license")}, b"yaml", b"license")))
            osv = stack.enter_context(patch.object(migration, "query_osv",
                return_value=[{"advisories": advisories or []}, {"advisories": []}]))
            yield dest, report, yaml, osv

    def test_main_rejects_incomplete_ace_family_before_osv_or_overlay(self):
        for family_files, missing in ((494, []), (495, ["mode-yaml.js"])):
            with self.subTest(family_files=family_files, missing=missing):
                with tempfile.TemporaryDirectory() as tmp:
                    with self.main_fixture(Path(tmp), family_files, missing) as (dest, report, yaml, osv):
                        with self.assertRaisesRegex(ValueError, "Unexpected Ace migration family"):
                            migration.main()
                        self.assertFalse(dest.exists())
                        self.assertFalse(report.exists())
                        yaml.assert_not_called()
                        osv.assert_not_called()

    def test_main_osv_match_preserves_report_but_prevents_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.main_fixture(Path(tmp), advisories=[{"id": "TEST-ADVISORY"}]) as (dest, report, yaml, osv):
                with self.assertRaisesRegex(ValueError, "Candidate package/version has OSV matches"):
                    migration.main()
                self.assertFalse(dest.exists())
                self.assertEqual(json.loads(report.read_text())["osv"][0]["advisories"],
                                 [{"id": "TEST-ADVISORY"}])
                osv.assert_called_once()

    def test_overlay_verifies_exact_inventory_and_rejects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp)
            vendor = pkg / "vendor"
            vendor.mkdir()
            (pkg / "third_party/licenses").mkdir(parents=True)
            payload = vendor / "asset.js"
            payload.write_bytes(b"asset")
            (pkg / "js-yaml.min.js").write_bytes(b"yaml")
            (pkg / "third_party/licenses/js-yaml.txt").write_bytes(b"license")
            expected = {"resources": {"vendor/asset.js": migration.sha(b"asset")}}
            manifest = vendor / "manifest.json"
            manifest.write_text(json.dumps(expected))
            yaml = {"member_sha256": migration.sha(b"yaml"),
                    "license_sha256": migration.sha(b"license")}
            self.assertEqual(migration.verify_overlay(pkg, expected, yaml),
                             {"vendor_resources_verified": 1, "js_yaml_files_verified": 2})
            payload.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "resource digest mismatch"):
                migration.verify_overlay(pkg, expected, yaml)
            payload.unlink()
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                migration.verify_overlay(pkg, expected, yaml)
            payload.write_bytes(b"asset")
            extra = vendor / "extra.js"
            extra.touch()
            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                migration.verify_overlay(pkg, expected, yaml)
            extra.unlink()
            (pkg / "js-yaml.min.js").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "js-yaml digest mismatch"):
                migration.verify_overlay(pkg, expected, yaml)
            (pkg / "js-yaml.min.js").write_bytes(b"yaml")
            manifest.write_text("{}")
            with self.assertRaisesRegex(ValueError, "manifest differs"):
                migration.verify_overlay(pkg, expected, yaml)

    def test_main_calls_overlay_verification_and_records_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.main_fixture(Path(tmp)) as (dest, report, _, __):
                with patch.object(migration, "verify_overlay", wraps=migration.verify_overlay) as verify:
                    migration.main()
                verify.assert_called_once()
                self.assertEqual(verify.call_args.args[0], dest / "hass_configurator")
                result = json.loads(report.read_text("utf-8"))
                self.assertEqual(result["curated_family_files"], 489)
                self.assertEqual(result["overlay_verification"], {
                    "vendor_resources_verified": 490, "js_yaml_files_verified": 2})
                self.assertEqual(len(result["excluded_workers"]), 5)
                self.assertEqual(result["excluded_themes"], ["theme-kr_theme.js"])
                for name in result["excluded_workers"] + result["excluded_themes"]:
                    self.assertFalse((dest / "hass_configurator/vendor/ace" / name).exists())

    def test_main_propagates_overlay_verification_failure(self):
        # Simulate an actual post-write extra file, not a mocked success.
        real_verify = migration.verify_overlay

        def tamper_and_verify(pkg, manifest, yaml):
            (pkg / "vendor/ace/worker-xml.js").write_bytes(b"unexpected worker")
            return real_verify(pkg, manifest, yaml)

        with tempfile.TemporaryDirectory() as tmp:
            with self.main_fixture(Path(tmp)) as (dest, report, _, __):
                with patch.object(migration, "verify_overlay", side_effect=tamper_and_verify) as verify:
                    with self.assertRaisesRegex(ValueError, "Overlay vendor inventory mismatch"):
                        migration.main()
                verify.assert_called_once()
                self.assertTrue(dest.exists())
                self.assertNotIn("overlay_verification", json.loads(report.read_text("utf-8")))
