"""Worker attribution must distinguish archive equality and lock candidates."""
import io
import json
import tarfile
import unittest
from unittest.mock import patch

from scripts import attribute_ace_workers as audit


def archive(files):
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w") as tar:
        for name, raw in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(raw)
            tar.addfile(member, io.BytesIO(raw))
    data.seek(0)
    return tarfile.open(fileobj=data, mode="r:")


class WorkerAttributionTests(unittest.TestCase):
    def test_workspace_specific_lock_path(self):
        lock = {"node_modules/yaml": {"version": "2.7.1"},
                "packages/ace-legacy-linters/node_modules/yaml": {"version": "2.8.3"}}
        found = audit.sources(b"  // node_modules/yaml/browser/index.js\n", lock)
        self.assertEqual(found[0]["source_lock_version"], "2.8.3")
        self.assertEqual(found[0]["lock_path"], "packages/ace-legacy-linters/node_modules/yaml")
        self.assertIn("not byte proof", found[0]["identity_basis"])

    def test_root_nested_scoped_and_unresolved_lock_paths(self):
        lock = {"node_modules/@babel/parser": {"version": "7.29.2"},
                "node_modules/esrecurse/node_modules/estraverse": {"version": "5.3.0"}}
        found = audit.sources(b" // ../../node_modules/@babel/parser/lib/index.js\n"
                              b" // ../../node_modules/esrecurse/node_modules/estraverse/estraverse.js\n"
                              b" // node_modules/unknown/index.js\n", lock)
        self.assertEqual({r["name"]: r["source_lock_version"] for r in found},
                         {"@babel/parser": "7.29.2", "estraverse": "5.3.0", "unknown": None})
        with self.assertRaisesRegex(ValueError, "escapes"):
            audit.resolve_comment("../../../node_modules/yaml/index.js", lock)

    def test_exact_worker_equality_requires_both_forms(self):
        worker = "worker-yaml.js"
        min_name = "src-min-noconflict/" + worker
        plain_name = "src-noconflict/" + worker
        plain = b"// node_modules/yaml/index.js\n"
        for candidate_plain, exact in ((plain, True), (b"other", False)):
            with archive({"package/" + min_name: b"min", "package/" + plain_name: plain}) as ace:
                with archive({"package/build/" + min_name: b"min",
                              "package/build/" + plain_name: candidate_plain}) as linters:
                    row = audit.compare_worker(ace, linters, worker, b"min", {})
                    self.assertEqual(row["status"] == "exact-linter-build-match", exact)
                    self.assertEqual(bool(row["source_lock_candidates"]), exact)
                    with self.assertRaisesRegex(ValueError, "Shipped worker differs"):
                        audit.compare_worker(ace, linters, worker, b"modified", {})

    def test_native_worker_not_inferred_from_linter_package(self):
        name = "worker-coffee.js"
        with archive({"package/src-min-noconflict/" + name: b"min",
                      "package/src-noconflict/" + name: b"plain"}) as ace:
            with archive({}) as linters:
                row = audit.compare_worker(ace, linters, name, b"min", {})
                self.assertEqual(row["status"], "native-worker-separate-source-audit")
                self.assertEqual(row["source_lock_candidates"], [])

    def test_notice_source_lock_sri_mismatch_fails(self):
        name, version = "yaml", "2.8.3"
        url = "https://registry.npmjs.org/yaml/-/yaml-2.8.3.tgz"
        raw = b"fixture"
        meta = {"name": name, "version": version,
                "dist": {"tarball": url, "integrity": audit.sri(raw)}}
        def fetch(url_):
            return raw if url_ == url else json.dumps(meta).encode()
        with self.assertRaisesRegex(ValueError, "source-lock SRI mismatch"):
            audit.notices_for(name, version, {"sha512-not-the-lock"}, fetch)

    def test_linter_notice_accepts_only_pinned_crlf_to_lf(self):
        shipped = b"license\n" * 21
        upstream = shipped.replace(b"\n", b"\r\n")
        with patch.multiple(audit, LINTER_ARCHIVE_LICENSE_SHA256=audit.sha(upstream),
                            LINTER_ARCHIVE_LICENSE_BLOB=audit.git_blob_sha1(upstream),
                            LINTER_LICENSE_BLOB=audit.git_blob_sha1(shipped)):
            self.assertEqual(audit.linter_license_relation(upstream, shipped), "crlf-to-lf-exact")
            self.assertEqual(audit.linter_license_relation(upstream + b" ", shipped), "mismatch")
            self.assertEqual(audit.linter_license_relation(upstream, shipped + b" "), "mismatch")
            self.assertEqual(audit.linter_license_relation(shipped, shipped), "mismatch")
        mixed = upstream.replace(b"\r\n", b"\n", 1)
        with patch.multiple(audit, LINTER_ARCHIVE_LICENSE_SHA256=audit.sha(mixed),
                            LINTER_ARCHIVE_LICENSE_BLOB=audit.git_blob_sha1(mixed),
                            LINTER_LICENSE_BLOB=audit.git_blob_sha1(shipped)):
            self.assertEqual(audit.linter_license_relation(mixed, shipped), "mismatch")
