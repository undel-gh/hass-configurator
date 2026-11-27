"""Supply-chain evidence must fail closed on drift and incomplete scans."""
import json
import base64
import hashlib
import io
import tarfile
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.audit_supply_chain import (
    PACKAGE, NOTICE, source_inventory, sbom, query_osv, scan_queries, verify_legacy_relation,
    read_file, EMBEDDED, immutable_raw_url, git_blob_sha1, embedded_upstream_evidence,
    check_npm_notice_pin, verify_npm_notice,
)


class SupplyChainTests(unittest.TestCase):
    def test_read_file_accepts_canonical_relative_regular_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "nested").mkdir()
            (root / "nested" / "data.txt").write_bytes(b"expected")
            self.assertEqual(read_file(root, "nested/data.txt"), b"expected")

    def test_read_file_rejects_noncanonical_or_escaping_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            root = parent / "package"
            root.mkdir()
            (root / "nested").mkdir()
            (root / "nested" / "data.txt").write_bytes(b"inside")
            outside = parent / "outside.txt"
            outside.write_bytes(b"outside")
            for name in (
                "../outside.txt", "nested/../../outside.txt",
                outside.as_posix(), "/absolute.txt",
                "nested/../nested/data.txt", "nested/./data.txt",
                "./nested/data.txt", "nested//data.txt", "nested/data.txt/",
                r"nested\data.txt", r"..\outside.txt", "", ".",
                "C:/outside.txt", "C:outside.txt", "nested/data.txt:stream",
            ):
                with self.subTest(name=name):
                    with self.assertRaisesRegex(ValueError, "Invalid inventory path"):
                        read_file(root, name)

    def test_read_file_rejects_missing_files_and_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "directory").mkdir()
            for name in ("missing.txt", "directory"):
                with self.subTest(name=name):
                    with self.assertRaisesRegex(ValueError, "Missing or unsafe inventory file"):
                        read_file(root, name)

    def test_read_file_rejects_file_and_parent_symlinks(self):
        with tempfile.TemporaryDirectory() as folder:
            parent = Path(folder)
            root = parent / "package"
            root.mkdir()
            inside = root / "inside"
            outside = parent / "outside"
            for directory in (inside, outside):
                directory.mkdir()
                (directory / "data.txt").write_bytes(b"existing")
            try:
                (root / "file-link").symlink_to(outside / "data.txt")
                (root / "dir-link").symlink_to(outside, target_is_directory=True)
                (root / "inner-link").symlink_to(inside, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest("Symlink creation not supported: " + str(exc))
            for name in ("file-link", "dir-link/data.txt", "inner-link/data.txt"):
                with self.subTest(name=name):
                    with self.assertRaisesRegex(ValueError, "Missing or unsafe inventory file"):
                        read_file(root, name)

    def test_source_inventory_and_bom(self):
        inv, vendor = source_inventory()
        self.assertEqual(len(inv["components"]), 7)
        self.assertEqual(len(vendor["resources"]), 510)
        bom = sbom(inv, vendor)
        self.assertEqual(bom["bomFormat"], "CycloneDX")
        self.assertEqual(next(c for c in bom["components"] if c["bom-ref"] == "asset:ace")["version"], "1.45.2")
        self.assertEqual(next(c for c in bom["components"] if c["bom-ref"] == "asset:js-yaml")["version"], "4.3.2")
        embedded = [c for c in bom["components"] if c["bom-ref"].startswith("embedded:")]
        self.assertNotIn("embedded:ace-jshint", {c["bom-ref"] for c in embedded})
        self.assertIn("embedded:ace-legacy-linters", next(d for d in bom["dependencies"]
                      if d["ref"] == "asset:ace")["dependsOn"])
        yaml = next(c for c in embedded if c["bom-ref"] == "embedded:ace-yaml-parser")
        self.assertEqual(yaml["name"], "yaml (Ace worker)")
        self.assertNotIn("version", yaml)
        self.assertNotIn("purl", yaml)
        self.assertEqual(inv["legacy_archive_locks"]["js-yaml.min.js"]["relation"], "exact")
        self.assertEqual(len(inv["embedded"]["worker_review"]), 6)
        historical = json.loads((PACKAGE.parent / "docs/history/ace-1.9.6-embedded.json").read_text("utf-8"))
        self.assertIn("ace-jshint", {c["id"] for c in historical["components"]})
        for retired in ("ace-coffee", "ace-luaparse", "ace-xml-lodash", "ace-xml-chevrotain"):
            self.assertNotIn("embedded:" + retired, {c["bom-ref"] for c in embedded})
        self.assertIn("embedded:ace-xqlint", {c["bom-ref"] for c in embedded})
        esrecurse = next(c for c in embedded if c["bom-ref"] == "embedded:ace-esrecurse")
        self.assertEqual(esrecurse["version"], "4.3.0")
        self.assertEqual(esrecurse["purl"], "pkg:npm/esrecurse@4.3.0")
        l10n = next(c for c in embedded if c["bom-ref"] == "embedded:ace-vscode-l10n")
        self.assertNotIn("version", l10n)
        self.assertNotIn("purl", l10n)
        refs = [c["bom-ref"] for c in bom["components"]]
        self.assertEqual(len(refs), len(set(refs)))
        self.assertEqual("2.136", next(c for c in bom["components"]
                                        if c["bom-ref"] == "asset:roboto")["version"])
        self.assertEqual(bom, sbom(inv, vendor))

    def mutate(self, action, message):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "package"
            shutil.copytree(PACKAGE, target)
            action(target)
            with self.assertRaisesRegex(ValueError, message):
                source_inventory(target)

    def mutate_embedded(self, edit, message):
        def action(root):
            path = root / EMBEDDED
            data = json.loads(path.read_text("utf-8"))
            edit(data)
            path.write_text(json.dumps(data), encoding="utf-8")
        self.mutate(action, message)

    def test_embedded_missing_notice_and_marker_rejected(self):
        def no_notice(doc):
            next(c for c in doc["components"] if c["id"] == "mat-hammer")["notices"] = []
        self.mutate_embedded(no_notice, "Missing embedded license notice")
        def wrong_marker(doc):
            doc["components"][0]["locations"][0]["marker"] = "never-present-marker-58ef5"
        self.mutate_embedded(wrong_marker, "Embedded marker missing")

    def test_embedded_parent_and_worker_coverage(self):
        def wrong_parent(doc):
            doc["components"][0]["parent"] = "jquery"
        self.mutate_embedded(wrong_parent, "Embedded container does not belong to parent")
        def missing_worker(doc):
            del doc["worker_review"]["vendor/ace/worker-yaml.js"]
        self.mutate_embedded(missing_worker, "Incomplete Ace worker review")
        def wrong_relationship(doc):
            doc["source_relationships"].append({"relation": "loosely-normalized"})
        self.mutate_embedded(wrong_relationship, "Unknown embedded source relationship")

    def test_embedded_notice_bytes_are_pinned(self):
        self.mutate(lambda root: (root / "third_party/licenses/embedded/ace-legacy-linters.txt")
                    .write_bytes(b"changed"), "SHA256 mismatch")

    def test_upstream_pin_is_immutable_and_mismatch_fails(self):
        url = "https://github.com/owner/repo/blob/" + "a" * 40 + "/LICENSE"
        self.assertEqual(immutable_raw_url(url),
                         "https://raw.githubusercontent.com/owner/repo/" + "a" * 40 + "/LICENSE")
        for invalid in (url.replace("a" * 40, "master"), url + "?raw=1",
                        url.replace("/LICENSE", "/../LICENSE"), "https://example.invalid/a"):
            with self.subTest(url=invalid), self.assertRaises(ValueError):
                immutable_raw_url(invalid)
        inv, _ = source_inventory()
        with self.assertRaisesRegex(ValueError, "Embedded upstream Git blob mismatch"):
            embedded_upstream_evidence(inv, fetch=lambda url: b"not the pinned source")
        self.assertEqual(git_blob_sha1(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")

    def test_npm_notice_exact_archive_and_member(self):
        local = b"original notice\r\n"

        def fixture(duplicate=False, link=False, wrong_identity=False):
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
                items = [("package/package.json", json.dumps({
                    "name": "wrong" if wrong_identity else "@scope/pkg",
                    "version": "1.2.3"}).encode()), ("package/LICENSE", local)]
                if duplicate:
                    items.append(items[-1])
                for name, payload in items:
                    info = tarfile.TarInfo(name)
                    if link and name.endswith("LICENSE"):
                        info.type = tarfile.SYMTYPE
                        info.linkname = "package/package.json"
                        archive.addfile(info)
                    else:
                        info.size = len(payload)
                        archive.addfile(info, io.BytesIO(payload))
            raw = buffer.getvalue()
            pin = {"name": "@scope/pkg", "version": "1.2.3", "member": "package/LICENSE",
                   "tarball": "https://registry.npmjs.org/@scope/pkg/-/pkg-1.2.3.tgz",
                   "archive_sha256": hashlib.sha256(raw).hexdigest(),
                   "npm_integrity": "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode(),
                   "sha256": hashlib.sha256(local).hexdigest()}
            return pin, raw

        pin, raw = fixture()
        self.assertEqual(verify_npm_notice(pin, raw, local)["relation"], "exact-archive-reference-member")
        for change in ({"tarball": "https://example.invalid/a"}, {"member": "package/../LICENSE"},
                       {"npm_integrity": "invalid"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                check_npm_notice_pin({**pin, **change})
        with self.assertRaisesRegex(ValueError, "archive mismatch"):
            verify_npm_notice(pin, raw + b"x", local)
        with self.assertRaisesRegex(ValueError, "bytes mismatch"):
            verify_npm_notice(pin, raw, local.replace(b"\r\n", b"\n"))
        for options, message in (({"duplicate": True}, "duplicate"),
                                 ({"link": True}, "duplicate"),
                                 ({"wrong_identity": True}, "identity mismatch")):
            altered, payload = fixture(**options)
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, message):
                verify_npm_notice(altered, payload, local)

    def test_legacy_bytes_and_notice_hashes(self):
        for name in ("js-yaml.min.js", "third_party/licenses/roboto.txt"):
            with self.subTest(name=name):
                self.mutate(lambda root: (root / name).write_bytes(b"changed"),
                            "SHA256 mismatch")

    def test_vendor_metadata_drift(self):
        self.mutate(lambda root: (root / "vendor/manifest.json").write_text("{}"),
                    "SHA256 mismatch")

    def test_unowned_component(self):
        def action(root):
            path = root / NOTICE
            data = json.loads(path.read_text())
            data["components"] = [c for c in data["components"] if c["id"] != "roboto"]
            path.write_text(json.dumps(data))
        self.mutate(action, "Incomplete third-party ownership")

    def test_legacy_relationship_is_exact(self):
        verify_legacy_relation(b"a\n", b"a", "missing-final-lf")
        verify_legacy_relation(b"a\xc2\xa0b\n", b"a b", "one-nbsp-to-space-and-missing-final-lf")
        verify_legacy_relation(b"npm", b"git", "exact-git-release-file-not-npm-member", b"git")
        for upstream, local, relation, git_raw in (
            (b"a\n", b"b", "missing-final-lf", None),
            (b"a\xc2\xa0b\xc2\xa0c\n", b"a b c", "one-nbsp-to-space-and-missing-final-lf", None),
            (b"npm", b"local", "exact-git-release-file-not-npm-member", b"other"),
        ):
            with self.subTest(relation=relation):
                with self.assertRaisesRegex(ValueError, "Unexpected legacy JS relationship"):
                    verify_legacy_relation(upstream, local, relation, git_raw)

    def test_scan_is_version_bound_and_deduplicated(self):
        inv, _ = source_inventory()
        report = {"distributions": [{"name": "gitpython", "version": "3.2.1"}],
                  "debian_packages": [{"source": "openssl", "source_version": "3.0.0"}]}
        queries = scan_queries(inv, [report, report])
        self.assertIn({"package": {"ecosystem": "npm", "name": "js-yaml"},
                       "version": "4.3.2"}, queries)
        self.assertIn({"package": {"ecosystem": "npm", "name": "ace-builds"},
                       "version": "1.45.2"}, queries)
        self.assertNotIn({"package": {"ecosystem": "npm", "name": "jshint"},
                          "version": "2.11.0"}, queries)
        self.assertIn({"package": {"ecosystem": "npm", "name": "esrecurse"},
                       "version": "4.3.0"}, queries)
        self.assertFalse(any(q["package"]["name"] == "@vscode/l10n" for q in queries))
        self.assertIn({"package": {"ecosystem": "npm", "name": "hammerjs"},
                       "version": "2.0.4"}, queries)
        self.assertFalse(any(q["package"]["name"] in {"Velocity.js", "js-yaml (Ace embedded parser)"}
                             for q in queries))
        self.assertIn({"package": {"ecosystem": "Debian:12", "name": "openssl"},
                       "version": "3.0.0"}, queries)
        self.assertEqual(len(queries), len({json.dumps(q, sort_keys=True) for q in queries}))

    def test_scan_result_correlation_and_pagination(self):
        query = {"package": {"ecosystem": "npm", "name": "x"}, "version": "1"}
        replies = iter([{"results": [{"vulns": [{"id": "A"}], "next_page_token": "n"}, {}]},
                        {"results": [{"vulns": [{"id": "B"}]}]}])
        result = query_osv([query, query], lambda batch: next(replies))
        self.assertEqual([v["id"] for v in result[0]["advisories"]], ["A", "B"])
        self.assertEqual(result[1]["advisories"], [])

    def test_incomplete_scan_is_not_clean(self):
        for response in ({}, {"results": []}, {"results": [{"error": "bad"}]}):
            with self.subTest(response=response):
                with self.assertRaises(ValueError):
                    query_osv([{}], lambda batch: response)


if __name__ == "__main__":
    unittest.main()
