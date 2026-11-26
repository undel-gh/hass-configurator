"""Supply-chain evidence must fail closed on drift and incomplete scans."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.audit_supply_chain import (
    PACKAGE, NOTICE, source_inventory, sbom, query_osv, scan_queries, verify_legacy_relation,
    read_file,
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
        self.assertEqual(len(vendor["resources"]), 460)
        bom = sbom(inv, vendor)
        self.assertEqual(bom["bomFormat"], "CycloneDX")
        self.assertEqual(len(bom["components"]), 12)
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
                       "version": "4.1.0"}, queries)
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
