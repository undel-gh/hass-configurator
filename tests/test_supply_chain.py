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
    check_npm_notice_pin, verify_npm_notice, embedded_source_relation,
    textmate_snippet_collection, textmate_collection_records, textmate_plist_entry,
    SQLSERVER_SHARED_BLOCKS, SQLSERVER_REFERENCE_PATHS, SQLSERVER_REFERENCE_REV,
    validate_vala_history, VALA_LICENSE_PATH, VALA_REDCAR, VALA_REDCAR_REV,
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

    def test_nord_and_one_dark_attribution(self):
        inv, vendor = source_inventory()
        for name, theme in (("nord", "nord_dark"), ("one-dark", "one_dark")):
            record = next(c for c in inv["embedded"]["components"]
                          if c["id"] == "ace-theme-" + name)
            self.assertEqual(record["status"], "partial")
            self.assertEqual(record["license"], "MIT")
            self.assertIsNone(record["version"])
            self.assertIsNone(record["ecosystem"])
            self.assertEqual([x["file"] for x in record["locations"]],
                             ["vendor/ace/theme-" + theme + ".js"])
            self.assertEqual(len(record["evidence"]), 5)
            self.assertEqual(len(record["notices"]), 1)
            self.assertEqual(inv["embedded"]["notices"][record["notices"][0]]["kind"],
                             "whole-file")

    def test_original_gruvbox_license_declaration_inventory(self):
        inv, vendor = source_inventory()
        record = next(c for c in inv["embedded"]["components"]
                      if c["id"] == "ace-theme-gruvbox-original")
        self.assertEqual(record["status"], "partial")
        self.assertEqual(record["license"], "MIT")
        self.assertIsNone(record["version"])
        self.assertIsNone(record["ecosystem"])
        self.assertEqual({x["file"] for x in record["locations"]}, {
            "vendor/ace/theme-gruvbox.js",
            "vendor/ace/theme-gruvbox_dark_hard.js",
            "vendor/ace/theme-gruvbox_light_hard.js",
        })
        self.assertEqual(len(record["evidence"]), 7)
        declaration, template = record["notices"]
        self.assertEqual(inv["embedded"]["notices"][declaration]["kind"], "source-excerpt")
        self.assertEqual(inv["embedded"]["notices"][template]["kind"], "whole-file")
        self.assertIn(b"[MIT/X11][]", read_file(PACKAGE, declaration))
        self.assertIn(b"<year> <copyright holders>", read_file(PACKAGE, template))
        component = next(c for c in sbom(inv, vendor)["components"]
                         if c["bom-ref"] == "embedded:ace-theme-gruvbox-original")
        self.assertNotIn("purl", component)
        self.assertNotIn("version", component)

    def test_source_inventory_and_bom(self):
        inv, vendor = source_inventory()
        self.assertEqual(len(inv["components"]), 7)
        self.assertEqual(len(vendor["resources"]), 493)
        bom = sbom(inv, vendor)
        self.assertEqual(bom["bomFormat"], "CycloneDX")
        self.assertEqual(next(c for c in bom["components"] if c["bom-ref"] == "asset:ace")["version"], "1.45.2")
        self.assertEqual(next(c for c in bom["components"] if c["bom-ref"] == "asset:js-yaml")["version"], "4.3.2")
        embedded = [c for c in bom["components"] if c["bom-ref"].startswith("embedded:")]
        self.assertNotIn("embedded:ace-jshint", {c["bom-ref"] for c in embedded})
        self.assertIn("embedded:ace-legacy-linters", next(d for d in bom["dependencies"]
                      if d["ref"] == "asset:ace")["dependsOn"])
        yaml = next(c for c in embedded if c["bom-ref"] == "embedded:ace-yaml-parser")
        self.assertEqual(yaml["name"], "yaml")
        self.assertEqual(yaml["version"], "2.8.3")
        self.assertEqual(yaml["purl"], "pkg:npm/yaml@2.8.3")
        self.assertEqual(inv["legacy_archive_locks"]["js-yaml.min.js"]["relation"], "exact")
        self.assertEqual(len(inv["embedded"]["worker_review"]), 6)
        for theme, count in (("tomorrow", 5), ("solarized", 2), ("gruvbox-hard", 2)):
            record = next(c for c in inv["embedded"]["components"] if c["id"] == "ace-theme-" + theme)
            self.assertEqual(record["status"], "partial")
            self.assertEqual(len(record["locations"]), count)
            self.assertIsNone(record["ecosystem"])
            self.assertEqual(record["license"], "MIT")
            self.assertEqual(len(record["notices"]), 1)
            self.assertEqual(inv["embedded"]["notices"][record["notices"][0]]["kind"], "whole-file")
        historical = json.loads((PACKAGE.parent / "docs/history/ace-1.9.6-embedded.json").read_text("utf-8"))
        self.assertIn("ace-jshint", {c["id"] for c in historical["components"]})
        for retired in ("ace-coffee", "ace-luaparse", "ace-xml-lodash", "ace-xml-chevrotain"):
            self.assertNotIn("embedded:" + retired, {c["bom-ref"] for c in embedded})
        self.assertIn("embedded:ace-xqlint", {c["bom-ref"] for c in embedded})
        esrecurse = next(c for c in embedded if c["bom-ref"] == "embedded:ace-esrecurse")
        self.assertEqual(esrecurse["version"], "4.3.0")
        self.assertEqual(esrecurse["purl"], "pkg:npm/esrecurse@4.3.0")
        l10n = next(c for c in embedded if c["bom-ref"] == "embedded:ace-vscode-l10n")
        self.assertEqual(l10n["version"], "0.0.18")
        self.assertEqual(l10n["purl"], "pkg:npm/%40vscode/l10n@0.0.18")
        expected_candidates = {
          "ace-babel-parser": [
                    "@babel/parser",
                    "7.29.2"
          ],
          "ace-code": [
                    "ace-code",
                    "1.43.6"
          ],
          "ace-eslint-scope": [
                    "eslint-scope",
                    "9.1.2"
          ],
          "ace-esrecurse": [
                    "esrecurse",
                    "4.3.0"
          ],
          "ace-estraverse": [
                    "estraverse",
                    "5.3.0"
          ],
          "ace-globals": [
                    "globals",
                    "14.0.0"
          ],
          "ace-yaml-parser": [
                    "yaml",
                    "2.8.3"
          ],
          "ace-htmlhint": [
                    "htmlhint",
                    "1.9.2"
          ],
          "ace-jsonc-parser": [
                    "jsonc-parser",
                    "3.3.1"
          ],
          "ace-vscode-css-languageservice": [
                    "vscode-css-languageservice",
                    "6.3.10"
          ],
          "ace-vscode-json-languageservice": [
                    "vscode-json-languageservice",
                    "5.7.2"
          ],
          "ace-vscode-languageserver-textdocument": [
                    "vscode-languageserver-textdocument",
                    "1.0.12"
          ],
          "ace-vscode-languageserver-types": [
                    "vscode-languageserver-types",
                    "3.17.5"
          ],
          "ace-vscode-uri": [
                    "vscode-uri",
                    "3.1.0"
          ],
          "ace-vscode-l10n": [
                    "@vscode/l10n",
                    "0.0.18"
          ]
}
        for cid, (name, version) in expected_candidates.items():
            record = next(c for c in embedded if c["bom-ref"] == "embedded:" + cid)
            self.assertEqual((record["name"], record["version"]), (name, version))
            self.assertEqual(record["purl"], "pkg:npm/" + name.replace("@", "%40") + "@" + version)
            self.assertTrue(record["licenses"])
        self.assertEqual(sum(n["kind"] == "npm-archive-member" for n in inv["embedded"]["notices"].values()), 15)
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

    def test_bounded_xqlint_and_browser_pack_relations(self):
        original = b"var A = require('./a');\nvar B = require('./b');"
        renamed = original.replace(b"require(", b"_dereq_(")
        self.assertTrue(embedded_source_relation(original, b"head\n" + renamed + b"\ntail",
                                                  "xqlint-two-require-renames"))
        self.assertFalse(embedded_source_relation(original, renamed.replace(b"./b", b"./c"),
                                                   "xqlint-two-require-renames"))
        with self.assertRaisesRegex(ValueError, "require count"):
            embedded_source_relation(original + b"\nrequire('c');", renamed, "xqlint-two-require-renames")
        prelude = b"// comment\n(function outer () {\n\n    return newRequire;\n})\n"
        adapted = b"(function outer () {\n    return newRequire(entry[0]);\n})"
        prefix = b"define(function(require, exports, module) {\nmodule.exports = "
        container = prefix + adapted + b"\n({})\n});"
        self.assertTrue(embedded_source_relation(prelude, container, "browser-pack-standalone-prelude"))
        for wrong in (b"prefix" + container, container.replace(b"entry[0]", b"entry[1]")):
            self.assertFalse(embedded_source_relation(prelude, wrong, "browser-pack-standalone-prelude"))
        with self.assertRaisesRegex(ValueError, "return count"):
            embedded_source_relation(prelude + b"return newRequire;", container,
                                     "browser-pack-standalone-prelude")

    def test_historical_theme_wrapper_relation(self):
        original = (b"/* ***** BEGIN LICENSE BLOCK *****\n"
                    b"Copyright 2011 Irakli Gozalishvili.\n"
                    b"***** END LICENSE BLOCK ***** */\n\n"
                    b"define(function(require, exports, module) {\n\n"
                    b'exports.isDark = true;\nexports.cssClass = "ace-gruvbox";\n'
                    b'exports.cssText = require("../requirejs/text!./gruvbox.css");\n\n'
                    b'var dom = require("../lib/dom");\n'
                    b"dom.importCssString(exports.cssText, exports.cssClass);\n\n});\n")
        current = (b'exports.isDark = true;\nexports.cssClass = "ace-gruvbox";\n'
                   b'exports.cssText = require("./gruvbox-css");\n\n'
                   b'var dom = require("../lib/dom");\n'
                   b"dom.importCssString(exports.cssText, exports.cssClass, false);\n")
        relation = "ace-theme-wrapper-amd-to-commonjs"
        self.assertTrue(embedded_source_relation(original, current, relation))
        for changed in (current + b"evil();", current.replace(b"true", b"false"),
                        current.replace(b"gruvbox-css", b"chaos-css")):
            self.assertFalse(embedded_source_relation(original, changed, relation))
        self.assertFalse(embedded_source_relation(original + b"evil();", current, relation))

    def test_historical_gruvbox_css_relation(self):
        old = b".ace-gruvbox { color: red; }"
        suffix = "\n\n.ace-gruvbox .ace_indent-guide-active {\n  background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAACCAYAAACZgbYnAAAAEklEQVQIW2PQ1dX9zzBz5sz/ABCcBFFentLlAAAAAElFTkSuQmCC) right repeat-y;\n}\n`;\n"
        current = b"module.exports = `" + old + suffix.encode("ascii")
        relation = "ace-gruvbox-css-indent-guide"
        self.assertTrue(embedded_source_relation(old, current, relation))
        self.assertFalse(embedded_source_relation(old, current + b"extra", relation))
        self.assertFalse(embedded_source_relation(old.replace(b"red", b"blue"), current, relation))

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
        for name, version in [["@babel/parser","7.29.2"],["ace-code","1.43.6"],["eslint-scope","9.1.2"],["esrecurse","4.3.0"],["estraverse","5.3.0"],["globals","14.0.0"],["yaml","2.8.3"],["htmlhint","1.9.2"],["jsonc-parser","3.3.1"],["vscode-css-languageservice","6.3.10"],["vscode-json-languageservice","5.7.2"],["vscode-languageserver-textdocument","1.0.12"],["vscode-languageserver-types","3.17.5"],["vscode-uri","3.1.0"],["@vscode/l10n","0.0.18"]]:
            self.assertIn({"package": {"ecosystem": "npm", "name": name},
                           "version": version}, queries)
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

    def test_github_light_default_primer_attribution(self):
        inv, vendor = source_inventory()
        record = next(c for c in inv["embedded"]["components"]
                      if c["id"] == "ace-theme-github-light-default")
        self.assertEqual(record["status"], "partial")
        self.assertEqual(record["license"], "MIT")
        self.assertIsNone(record["version"])
        self.assertIsNone(record["ecosystem"])
        self.assertEqual([loc["file"] for loc in record["locations"]],
                         ["vendor/ace/theme-github_light_default.js"])
        self.assertEqual(len(record["notices"]), 1)
        path = record["notices"][0]
        self.assertEqual(inv["embedded"]["notices"][path]["kind"], "whole-file")
        self.assertIn(b"Copyright (c) 2020 Primer", read_file(PACKAGE, path))
        component = next(c for c in sbom(inv, vendor)["components"]
                         if c["bom-ref"] == "embedded:ace-theme-github-light-default")
        self.assertNotIn("purl", component)
        self.assertNotIn("version", component)

    def test_snipmate_template_literal_exact_and_fail_closed(self):
        relation = "ace-snippet-template-literal"
        raw = b"snippet test\n\t\x24{1}\n"
        wrapped = b"module.exports = \x60snippet test\n\t\\\x24{1}\n\x60;\n"
        self.assertTrue(embedded_source_relation(raw, wrapped, relation))
        self.assertTrue(embedded_source_relation(
            b"require", b"module.exports = \x60requir\\x65\x60;\n", relation))
        self.assertTrue(embedded_source_relation(
            b"\x60\\", b"module.exports = \x60\\\x60\\\\\x60;\n", relation))
        for changed in (
            wrapped.replace(b"\\\x24{1}", b"\x24{1}"),
            wrapped.replace(b"test", b"other"),
            wrapped.replace(b"\\\x24{1}", b"\\u0024{1}"),
            wrapped.replace(b"\n", b"\r\n"),
            wrapped + b"run();",
            b"other();\n" + wrapped,
            wrapped.replace(b"\\\x24{1}", b"\\xZZ"),
        ):
            with self.subTest(changed=changed):
                self.assertFalse(embedded_source_relation(raw, changed, relation))
        self.assertFalse(embedded_source_relation(b"unrelated", wrapped, relation))

    def test_snipmate_derived_relations_fail_closed(self):
        old = b"## Access Modifiers\nsnippet po\n\tprotected\nsnippet pu\n\tpublic\nsnippet pr\n\tprivate\n"
        new = b"## Access Modifiers\nsnippet u\n\tUN\nsnippet un\n\tUNB\nsnippet pr\n\tprivate\n"
        relation = "ace-edifact-java-two-triggers"
        self.assertTrue(embedded_source_relation(old, new, relation))
        for changed in (new + b"x", new.replace(b"private", b"public"), new.replace(b"UNB", b"UN")):
            self.assertFalse(embedded_source_relation(old, changed, relation))
        self.assertFalse(embedded_source_relation(old + old, new + new, relation))
        self.assertFalse(embedded_source_relation(b"x" + old, b"x" + new, relation))
        html = b"# Some useful Unicode entities\nsnippet nbs\n\t&nbsp;\n"
        prefix = b"\n# liquid specific snippets\nsnippet ife\n\t{% if ${1:condition} %}\n\n\t{% else %}\n\n\t{% endif %}\nsnippet if\n\t{% if ${1:condition} %}\n\t\t\n\t{% endif %}\nsnippet for\n\t{% for in ${1:iterator} %}\n\n\t{% endfor %}\nsnippet capture\n\t{% capture ${1} %}\n\n\t{% endcapture %}\nsnippet comment\n\t{% comment %}\n\t  ${1:comment}\n\t{% endcomment %}\n\n# Include html.snippets\n"
        relation = "ace-liquid-html-prefix"
        self.assertTrue(embedded_source_relation(html, prefix + html, relation))
        for changed in (b"x" + prefix + html, prefix + html + b"x",
                        prefix.replace(b"snippet ife", b"snippet if") + html, prefix + html[:-1]):
            self.assertFalse(embedded_source_relation(html, changed, relation))
        self.assertFalse(embedded_source_relation(b"x" + html, prefix + b"x" + html, relation))

    def test_wollok_java_shared_material_is_bounded_and_ordered(self):
        # Synthetic distinct gaps: only the named retained fragments are compared.
        blocks = (
            b"##\n## Basic Java packages and import\nsnippet im\n\timport\n",
            b"snippet cl\n\tclass ${1:`Filename(\"\", \"untitled\")`} ${2}\n",
            b"##\n## Comments\nsnippet /*\n\t/*\n\t * ${1}\n\t */\n",
            b"##\n## Control Statements\n",
            b"snippet el\n\telse\n",
            b"snippet if\n\tif (${1}) ${2}\n",
            b"##\n## Create a Method\nsnippet m\n",
            b"snippet as\n",
            b"snippet ca\n",
            b"snippet thr\n\tthrow\n",
            b"snippet try\n\ttry {\n\t\t${3}\n",
            b"##\n## Javadocs\nsnippet /**\n\t/**\n\t * ${1}\n\t */\n",
            b"##\n## Print Methods\nsnippet print\n",
            b"##\n## Setter and Getter Methods\nsnippet set\n",
            b"snippet get\n",
            b"##\n## Terminate Methods or Loops\nsnippet re\n\treturn",
        )
        upstream = b"java-only\n".join(blocks) + b"\nmore Java\n"
        container = b"wollok-only\n".join(blocks)
        relation = "ace-wollok-java-retained-blocks"
        self.assertTrue(embedded_source_relation(upstream, container, relation))
        for changed in (container.replace(b"Basic Java packages", b"Other packages"),
                        container.replace(b"untitled", b"changed"),
                        b"wollok-only\n".join(blocks[:2][::-1] + blocks[2:]),
                        blocks[0] + container, container + b"\n",
                        container.replace(b"snippet get\n", b"snippet different\n")):
            self.assertFalse(embedded_source_relation(upstream, changed, relation))
        self.assertFalse(embedded_source_relation(upstream.replace(b"snippet thr\n", b"snippet other\n"),
                                                  container, relation))



    def test_sqlserver_microsoft_reference_scope_and_tamper(self):
        from urllib.parse import quote
        root = "https://github.com/microsoft/sql-server-samples/blob/" + SQLSERVER_REFERENCE_REV + "/"
        for path in SQLSERVER_REFERENCE_PATHS:
            url = root + quote(path, safe="/")
            self.assertEqual(immutable_raw_url(url), url.replace("github.com/", "raw.githubusercontent.com/").replace("/blob/", "/"))
            for bad in (url.replace("%20", "%2520", 1), url.replace("%28", "%28%2F", 1),
                        url.replace("%20", "%20%00", 1), url.replace("New%20Menu", "Other%20Menu"),
                        url.replace(SQLSERVER_REFERENCE_REV, "a" * 40), url + "#x",
                        url.replace("microsoft/", "other/"), url.replace("%28", "%28%2E%2E", 1)):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    immutable_raw_url(bad)
        proc = "ace-sqlserver-ms-procedure-shared"
        func = "ace-sqlserver-ms-function-shared"
        blocks = SQLSERVER_SHARED_BLOCKS
        source = lambda kind: b"upstream-only\n".join(a for a, _ in blocks[kind])
        section = lambda kind: b"ace-only\n".join(b for _, b in blocks[kind])
        raw = (b"# unrelated\nsnippet unrelated\n\tx\n# Create Procedure\nsnippet createproc\n"
               + section(proc) + b"# Create Scalar Function\nsnippet createfn\n" + section(func))
        for kind in (proc, func):
            self.assertTrue(embedded_source_relation(source(kind), raw, kind))
            self.assertFalse(embedded_source_relation(source(kind).replace(blocks[kind][0][0], b"changed"),
                                                      raw, kind))
            self.assertFalse(embedded_source_relation(source(kind), raw.replace(blocks[kind][0][1], b"changed", 1)
                                                      if kind == proc else raw.replace(blocks[kind][0][1], b"changed"), kind))
            self.assertFalse(embedded_source_relation(blocks[kind][0][0] + source(kind), raw, kind))
        self.assertFalse(embedded_source_relation(source(proc), raw.replace(b"snippet createproc", b"snippet other"), proc))
        self.assertFalse(embedded_source_relation(source(func), raw + b"\n", func))
        self.assertTrue(embedded_source_relation(source(proc), raw.replace(b"\tx\n", b"\ty\n"), proc))
        # Whole payload pins independently protect unshared material; partial comparator must not claim otherwise.

    def test_sqlserver_microsoft_partial_inventory(self):
        inv, vendor = source_inventory()
        embedded = inv["embedded"]
        record = next(c for c in embedded["components"] if c["id"] == "ace-sqlserver-microsoft-template-material")
        self.assertEqual((record["status"], record["license"], record["version"], record["ecosystem"]),
                         ("partial", "MIT", None, None))
        self.assertEqual(record["notices"], ["third_party/licenses/embedded/microsoft-ssms-templates-mit.txt"])
        self.assertEqual(git_blob_sha1(read_file(PACKAGE, record["notices"][0])),
                         "9d333bb098c152c0983042ca77f16ac0c8999441")
        for kind in SQLSERVER_SHARED_BLOCKS:
            rows = [r for r in embedded["source_relationships"] if r["relation"] == kind]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["container"]["git_blob"], "403bd6bc551a0fcb224e84fd5c996a0ca6c26984")
        component = next(c for c in sbom(inv, vendor)["components"] if c["bom-ref"] == "embedded:" + record["id"])
        self.assertNotIn("purl", component)
        self.assertNotIn("version", component)
        self.assertFalse(any(q["package"]["name"] == record["name"] for q in scan_queries(inv, [])))

    def test_lsl_historical_source_review_is_exact_not_a_library(self):
        inv, vendor = source_inventory()
        archive = json.loads((PACKAGE.parent / "docs/history/ace-snippet-exclusions.json").read_text("utf-8"))
        self.assertNotIn("vendor/ace/snippets/lsl.js", vendor["resources"])
        self.assertFalse(any(c["id"] == "ace-lsl-snippet-source-review" for c in inv["embedded"]["components"]))
        record = next(c for c in archive["components"] if c["id"] == "ace-lsl-snippet-source-review")
        self.assertEqual(record["kind"], "review")
        self.assertEqual(record["status"], "partial")
        self.assertIsNone(record["license"])
        self.assertIsNone(record["version"])
        self.assertIsNone(record["ecosystem"])
        self.assertEqual(record["notices"], [])
        self.assertEqual(record["locations"], [{"file": "vendor/ace/snippets/lsl.js",
                                               "marker": "ace/snippets/lsl"}])
        rels = archive["source_relationships"]
        matches = [r for r in rels if r["relation"] == "ace-lsl-identical-raw"]
        self.assertEqual(len(matches), 2)
        self.assertEqual({r["upstream"]["git_blob"] for r in matches}, {
            "bc0d2eb9d0286050bbb56efa09cc02aaec500dba", "352d26e7b4ed7389ddefb8365b4e2d985e63d037"})
        for row in matches:
            self.assertEqual(row["upstream"]["git_blob"], row["container"]["git_blob"])
        current = [r for r in rels if r["relation"] == "ace-snippet-template-literal"
                   and r["container"]["url"].endswith("/lsl.snippets.js")]
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["upstream"]["git_blob"], "352d26e7b4ed7389ddefb8365b4e2d985e63d037")
        self.assertEqual(current[0]["container"]["git_blob"], "7e33bdc2855b5f7e3ff0cb5d4f5f546dc809ccf5")
        self.assertNotIn("embedded:ace-lsl-snippet-source-review",
                         {c["bom-ref"] for c in sbom(inv, vendor)["components"]})
        sample = b"snippet CAMERA_ACTIVE\n\tvalue\n"
        self.assertTrue(embedded_source_relation(sample, sample, "ace-lsl-identical-raw"))
        self.assertFalse(embedded_source_relation(sample, sample + b"\n", "ace-lsl-identical-raw"))
        self.assertFalse(embedded_source_relation(b"other", b"other", "ace-lsl-identical-raw"))

    def test_snipmate_exact_and_modified_payload_attribution(self):
        inv, vendor = source_inventory()
        record = next(c for c in inv["embedded"]["components"]
                      if c["id"] == "ace-snipmate-snippets")
        self.assertEqual(record["status"], "partial")
        self.assertEqual(record["license"], "MIT")
        self.assertIsNone(record["version"])
        self.assertIsNone(record["ecosystem"])
        names = {"actionscript", "c_cpp", "clojure", "coffee", "css", "diff", "django", "erlang", "haml", "haskell", "java", "jsp", "lua", "makefile", "perl", "rst", "ruby", "snippets", "sql", "tcl", "tex", "textile"}
        exact_names = names.copy()
        modified = {"dart", "html", "javascript", "markdown", "php", "python", "r", "sh"}
        self.assertTrue(exact_names.isdisjoint(modified))
        derived = {"liquid"}
        self.assertTrue(derived.isdisjoint(exact_names | modified))
        names |= modified | derived
        self.assertEqual({loc["file"] for loc in record["locations"]},
                         {"vendor/ace/snippets/" + n + ".js" for n in names})
        self.assertEqual(len(record["locations"]), len(names))
        self.assertEqual(record["notices"], [
            "third_party/licenses/embedded/snipmate-snippets-mit.txt",
            "third_party/licenses/embedded/snipmate-snippets-authors.txt",
        ])
        for path, blob in zip(record["notices"], [
                "495ced27810b679dad1c75375e48db9ae9c9c9aa",
                "1261dc82ddfea218e2a61077fb4ed0d64b42c2bb"]):
            with self.subTest(path=path):
                self.assertEqual(inv["embedded"]["notices"][path]["kind"], "whole-file")
                self.assertEqual(git_blob_sha1(read_file(PACKAGE, path)), blob)
        relations = [r for r in inv["embedded"]["source_relationships"]
                     if r["relation"] == "ace-snippet-template-literal"
                     and r["container"]["url"].rsplit("/", 1)[1] in {n + ".snippets.js" for n in names}]
        self.assertEqual(len(relations), len(names))
        self.assertEqual({r["container"]["url"].rsplit("/", 1)[1] for r in relations},
                         {n + ".snippets.js" for n in names})
        # Distinguish original unchanged inputs from modified historical endpoints.
        by_name = {r["container"]["url"].rsplit("/", 1)[1].removesuffix(".snippets.js"): r
                   for r in relations}
        evidence = {item["url"]: item["git_blob"] for item in record["evidence"]}
        for n in exact_names:
            self.assertIn("https://github.com/honza/vim-snippets/blob/", by_name[n]["upstream"]["url"])
        modified_pins = {
            "dart": ("6f0b8ac5e5ba87851513a3f9dd2b808e2e70ad81",
                "93673bbe8b0a1e90a773aa3dd94fe8fa112f7af5", "14a1c3e5939d691de25aa390ff7f17c4e5b42a70",
                "fa6a8452fcd7faec4f7aa1a70d0a93fc47059f55"),
            "html": ("0f75efd08a2c7917bc9b880a7952de97479fb3ec",
                "96850288dca9b632aaa79b4f9bdf1305ae5d9694", "5f0e46b476083398e70a53e7d9630383bfb4fe99",
                "8fd5affd801799b79f14f645c7ddd3c95dc1a1da"),
            "javascript": ("fc845fa02198562dda841591126d2eb107fd2ae8",
                "2d0b980c65966e45260ba341e176b9cde0c57399", "83b15aab6f41fdf08692dd8e9167a5b95fc266c5",
                "6e4d29a4dbab301680f762d7bd0838059ebe0d55"),
            "markdown": ("e4efd3c2d014fe8a9b6ba92fd08e1483aea5d1c3",
                "3c6cd4d16f89de0531d7e8f06c5e791839ab9eb6", "a5110fc9a3d79f0aa98796237773393e4a836e97",
                "26ad61345a037c5197d28ef1798a252f585ae149"),
            "php": ("e861a5be96827edc8a2182d76d864b5b4a8a6b60",
                "f36ade1647e90d20480d93ac6da6169fc55e65e5", "12b6c358d6927bd245ac3a8e1f9a5fe47f8f4b2a",
                "987e34d04474aa6cb5ffa64a7bb31731f60d0f8d"),
            "python": ("dd2e8123dcc8db911c92a260a771f2116146ff57",
                "eac48f519040e8e2d17dd1a5b76c2818ecf58cd1", "347bbdebfd9d13e17cdd0131523eef30db186a26",
                "5d556cf6f7d6f54eb41d815b1b9862e9e80397e7"),
            "r": ("71186e35b47f2aa8d46071d89ab9ffcfc727a888",
                "f17c67cd01316d4fdbbd5625594d81e28c894083", "948542f5bbacc0de657e65d95dc2d54c52c0f13e",
                "dbac55301a26b64aedf8342d4b883a81ee44a4c9"),
            "sh": ("9a48eb514c5306d2fa7223a0e45703381d7b69bd",
                "b6463844b04758745f99b1553416f4cf4b8ad013", "305fb661ed25a75093d8e168f46deb012f662c07",
                "8c5e7f6c288d2078e4d4dfe9bc481ab536b3a7fe"),
        }
        self.assertEqual(set(modified_pins), modified)
        for n, (original, revision, endpoint, current) in modified_pins.items():
            with self.subTest(modified=n):
                relation = by_name[n]
                imported = "https://github.com/ajaxorg/ace/blob/d16daddc5ea91e578fafde6c9c17b41cdb036579/lib/ace/snippets/" + n + ".snippets"
                source = "https://github.com/honza/vim-snippets/blob/02593f7d57b4944bd857e0aeacfcd5410c0e81f2/snippets/" + n + ".snippets"
                historical = "https://github.com/ajaxorg/ace/blob/" + revision + "/lib/ace/snippets/" + n + ".snippets"
                self.assertEqual(evidence[imported], original)
                self.assertEqual(evidence[source], original)
                self.assertEqual(evidence[historical], endpoint)
                self.assertEqual(relation["upstream"]["url"], historical)
                self.assertEqual(relation["upstream"]["git_blob"], endpoint)
                self.assertEqual(relation["container"]["git_blob"], current)
                self.assertNotEqual(original, endpoint)
        derived_pins = {
            "liquid": ("ace-liquid-html-prefix",
                "https://github.com/ajaxorg/ace/blob/d9b38ac378d0dea6e1ca820c0e8294f04c46010a/lib/ace/snippets/html.snippets", "20a73d72e339c352216ce4803e6c5b842f7d7212",
                "58fcde32061df7d7f6ef38a6bfcf306b0f800f92", "b3e3c982cfa70d04544b74652bbe85e702f5ebf2", "7c72fe03a9fce8c65f6b486d83fbc88f618a97b5"),
        }
        self.assertEqual(set(derived_pins), derived)
        for n, (kind, original_url, original_blob, revision, endpoint, current) in derived_pins.items():
            with self.subTest(derived=n):
                historical = "https://github.com/ajaxorg/ace/blob/" + revision + "/lib/ace/snippets/" + n + ".snippets"
                self.assertEqual(evidence[original_url], original_blob)
                self.assertEqual(evidence[historical], endpoint)
                self.assertEqual(by_name[n]["upstream"]["url"], historical)
                self.assertEqual(by_name[n]["upstream"]["git_blob"], endpoint)
                self.assertEqual(by_name[n]["container"]["git_blob"], current)
                matches = [r for r in inv["embedded"]["source_relationships"] if r["relation"] == kind]
                self.assertEqual(len(matches), 1)
                self.assertEqual(matches[0]["upstream"]["url"], original_url)
                self.assertEqual(matches[0]["upstream"]["git_blob"], original_blob)
                self.assertEqual(matches[0]["container"]["url"], historical)
                self.assertEqual(matches[0]["container"]["git_blob"], endpoint)
        archive = json.loads((PACKAGE.parent / "docs/history/ace-snippet-exclusions.json").read_text("utf-8"))
        self.assertNotIn("vendor/ace/snippets/edifact.js", vendor["resources"])
        self.assertEqual(archive["former_snipmate_location"]["file"], "vendor/ace/snippets/edifact.js")
        edifact = [r for r in archive["source_relationships"] if r["relation"] == "ace-edifact-java-two-triggers"]
        self.assertEqual(len(edifact), 1)
        self.assertEqual(edifact[0]["upstream"]["git_blob"], "854f14ac22f148309d4f9ec450fda38244ede6ec")
        self.assertEqual(edifact[0]["container"]["git_blob"], "624b87ad3d9e135050ba3415237fff3e38241bbc")
        self.assertNotIn("vendor/ace/snippets/wollok.js", vendor["resources"])
        self.assertEqual(archive["former_wollok_snipmate_location"], {"file": "vendor/ace/snippets/wollok.js", "marker": "ace/snippets/wollok"})
        historical_wollok = {e["url"]: e["git_blob"] for e in archive["former_wollok_snipmate_evidence"]}
        self.assertEqual(historical_wollok, {"https://github.com/ajaxorg/ace/blob/4f9cd17910cfe36dc504b456ea5ef62c15189f2d/lib/ace/snippets/java.snippets":"854f14ac22f148309d4f9ec450fda38244ede6ec","https://github.com/ajaxorg/ace/blob/1693305c8974a5dd4f350bb0b9d48b134fca113c/lib/ace/snippets/wollok.snippets":"f98f8587908fefe10bc9dc3a9fa02443a60bb1aa"})
        self.assertFalse(set(historical_wollok) & set(evidence))
        wollok = [r for r in archive["source_relationships"] if r["relation"] == "ace-wollok-java-retained-blocks"]
        self.assertEqual(len(wollok), 1)
        self.assertEqual(wollok[0]["upstream"]["git_blob"], "854f14ac22f148309d4f9ec450fda38244ede6ec")
        self.assertEqual(wollok[0]["container"]["git_blob"], "f98f8587908fefe10bc9dc3a9fa02443a60bb1aa")
        mapped_wollok = [r for r in archive["source_relationships"] if r["container"]["url"].endswith("/wollok.snippets.js")]
        self.assertEqual(len(mapped_wollok), 1)
        self.assertEqual(mapped_wollok[0]["upstream"]["git_blob"], "f98f8587908fefe10bc9dc3a9fa02443a60bb1aa")
        self.assertEqual(mapped_wollok[0]["container"]["git_blob"], "04d3c58efa7c958cb98aa84e76bcbdcc0bb6dd8b")
        component = next(c for c in sbom(inv, vendor)["components"]
                         if c["bom-ref"] == "embedded:ace-snipmate-snippets")
        self.assertNotIn("version", component)
        self.assertNotIn("purl", component)
        self.assertFalse(any(q["package"]["name"] == record["name"]
                             for q in scan_queries(inv, [])))


    def test_textmate_encoded_paths_are_scoped_and_canonical(self):
        base = "https://github.com/textmate/io.tmbundle/blob/e8f7b3773544cfc14a7ede7344ed94683f7ed602/Snippets/"
        vala = "https://github.com/technosophos/Vala-TMBundle/blob/2fd9373f90bf74eef0b15f43c7240c28d55bebaa/Snippets/"
        for url in (base + "Indented%20return.plist",
                    vala + "try%3Acatch.tmSnippet",
                    vala + "Verbatim%20string%20%28%22%22%22%29.tmSnippet"):
            self.assertEqual(immutable_raw_url(url), url.replace("github.com/", "raw.githubusercontent.com/").replace("/blob/", "/"))
        for url in (base + "Indented return.plist", base + "Indented%2520return.plist",
                    base + "%2E%2E%2FLICENSE.plist", base + "a%2Fb.plist",
                    base + "a%5Cb.plist", base + "a%00b.plist", base + "a%0Ab.plist",
                    base + "a%3Fb.plist", base + "a%23b.plist", base + "%61.plist",
                    base + "a%20b.plist?raw=1", vala + "try%3acatch.tmSnippet",
                    base.replace("textmate/io.tmbundle", "other/repo") + "a%20b.plist",
                    base.replace("e8f7b3773544cfc14a7ede7344ed94683f7ed602", "a" * 40) + "a%20b.plist"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                immutable_raw_url(url)

    def test_textmate_collection_exact_and_tamper(self):
        def source(i):
            return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" '
                    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                    '<plist version="1.0"><dict>'
                    f'<key>name</key><string>n{i}</string>'
                    '<key>content</key><string>&lt;x&gt;\n\t</string>'
                    '<key>scope</key><string>source.io</string>'
                    '<key>uuid</key><string>12345678-1234-1234-1234-123456789abc</string>'
                    '</dict></plist>\n').encode()
        sources = [source(i) for i in range(10)]
        rows = [{"name": f"n{i}", "content": "<x>\n\t", "scope": "io"} for i in range(10)]
        def module(entries):
            return ('"use strict";\n\nexports.snippets = ' + json.dumps(entries)
                    + ';\nexports.scope = "io";\n').encode()
        good = module(rows)
        self.assertTrue(textmate_snippet_collection(sources, good, "io"))
        self.assertTrue(textmate_snippet_collection(sources, module(rows[::-1]), "io"))
        for inputs, output in (
            (sources[:-1], good), (sources + sources[:1], good),
            (sources[:-1] + sources[:1], good), (sources, module(rows[:-1])),
            (sources, module(rows[:-1] + rows[:1])), (sources, module(rows + rows[:1])),
            (sources, good.replace(b'"scope": "io"', b'"scope": "other"', 1)),
            (sources, good.replace(b'"name": "n0"', b'"name": "n0", "name": "n0"', 1)),
            (sources, good + b"run();"),
            ([sources[0].replace(b"<key>name</key>", b"<key>scope</key>")] + sources[1:], good),
            ([sources[0].replace(b"<dict>", b"<dict><!--ignored-->")] + sources[1:], good),
            ([sources[0].replace(b"<string>n0", b"<string><x/>n0")] + sources[1:], good),
            ([sources[0].replace(b"<dict>", b"<dict><key>other</key><string>x</string>")] + sources[1:], good),
            ([sources[0].replace(b"<!DOCTYPE plist PUBLIC", b"<!DOCTYPE evil PUBLIC")] + sources[1:], good),
        ):
            self.assertFalse(textmate_snippet_collection(inputs, output, "io"))
        self.assertFalse(textmate_snippet_collection(sources, good, "vala"))


    def test_textmate_io_historical_return_key_exact_cr(self):
        # Exact original XML bytes; this is the only observed literal CR.
        raw = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<!DOCTYPE plist PUBLIC \"-//Apple Computer//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">\n<plist version=\"1.0\">\n<dict>\n\t<key>content</key>\n\t<string>\n\t$0\n</string>\n\t<key>keyEquivalent</key>\n\t<string>\r</string>\n\t<key>name</key>\n\t<string>Special: Return Inside Empty Parenthesis</string>\n\t<key>scope</key>\n\t<string>source.io meta.empty-parenthesis.io, source.io meta.comma-parenthesis.io</string>\n\t<key>uuid</key>\n\t<string>0F687653-BF6D-4C2C-A75E-C9193E870BBC</string>\n</dict>\n</plist>\n").encode("utf-8")
        self.assertEqual(git_blob_sha1(raw), "97bfd34c245f79c304f9e3f6c2810477b1037958")
        parsed = textmate_plist_entry(raw)
        self.assertEqual(parsed["name"], "Special: Return Inside Empty Parenthesis")
        self.assertEqual(parsed["keyEquivalent"], "\r")
        self.assertEqual(parsed["content"], "\n\t$0\n")
        self.assertEqual(parsed["scope"], "io meta.empty-parenthesis.io, io meta.comma-parenthesis.io")
        self.assertEqual(textmate_plist_entry(raw.replace(b"\r", b"\n"))["keyEquivalent"], "\n")
        for changed in (raw + b"\n", raw.replace(b"\r", b"\r\r"),
                        raw.replace(b"<string>\r</string>", b"<string>\n</string>").replace(b"$0", b"$0\r")):
            with self.assertRaisesRegex(ValueError, "Unexpected literal CR"):
                textmate_plist_entry(changed)
        sources = [raw] + [
            (f'<plist version="1.0"><dict><key>name</key><string>n{i}</string>'
             '<key>content</key><string>x</string><key>scope</key><string>source.io</string>'
             '<key>uuid</key><string>12345678-1234-1234-1234-123456789abc</string>'
             '</dict></plist>').encode() for i in range(9)]
        rows = [parsed] + [{"name": f"n{i}", "content": "x", "scope": "io"} for i in range(9)]
        def module(entries):
            return ('"use strict";\n\nexports.snippets = ' + json.dumps(entries)
                    + ';\nexports.scope = "io";\n').encode()
        self.assertTrue(textmate_snippet_collection(sources, module(rows), "io"))
        rows[0] = {**parsed, "keyEquivalent": "\n"}
        self.assertFalse(textmate_snippet_collection(sources, module(rows), "io"))

    def test_textmate_collection_inventory_and_bom(self):
        inv, vendor = source_inventory()
        embedded = inv["embedded"]
        self.assertEqual([(n, len(p)) for n, p, _ in textmate_collection_records(embedded)],
                         [("io", 10), ("vala", 31)])
        for n, license_id, notice in (
                ("io", "LicenseRef-TextMate-Bundle", "textmate-io-bundle-license.txt"),
                ("vala", "LicenseRef-TextMate-Bundle AND MIT", "vala-tmbundle-mit.txt")):
            cid = "ace-textmate-" + n + "-snippets"
            record = next(c for c in embedded["components"] if c["id"] == cid)
            self.assertEqual(record["license"], license_id)
            expected = ["third_party/licenses/embedded/" + notice]
            if n == "vala":
                expected.append(VALA_LICENSE_PATH)
            self.assertEqual(record["notices"], expected)
            component = next(c for c in sbom(inv, vendor)["components"] if c["bom-ref"] == "embedded:" + cid)
            self.assertNotIn("version", component)
            self.assertNotIn("purl", component)
            self.assertFalse(any(q["package"]["name"] == record["name"] for q in scan_queries(inv, [])))
        def missing_source(doc):
            record = next(c for c in doc["components"] if c["id"] == "ace-textmate-io-snippets")
            record["evidence"] = [p for p in record["evidence"] if not p["url"].endswith("/Method.plist")]
        self.mutate_embedded(missing_source, "Incomplete TextMate collection pins")

    def test_vala_historical_provenance(self):
        inv, _ = source_inventory()
        result = validate_vala_history(inv["embedded"])
        self.assertEqual((result["inherited"], result["additions"], result["final"]), (14, 17, 31))
        self.assertEqual(result["historical_pins"], 94)
        url = VALA_REDCAR + VALA_REDCAR_REV + "/Bundles/Vala.tmbundle/Snippets/do%20while.plist"
        self.assertTrue(immutable_raw_url(url).endswith("/do%20while.plist"))
        for invalid in (url.replace("do%20while", "other%20file"),
                        url.replace("%20", "%2520"), url.replace("%20", "%2F"),
                        url.replace(VALA_REDCAR_REV, "0" * 40)):
            with self.assertRaises(ValueError):
                immutable_raw_url(invalid)
        def record(doc):
            return next(c for c in doc["components"] if c["id"] == "ace-textmate-vala-snippets")
        def missing(doc):
            record(doc)["evidence"] = [p for p in record(doc)["evidence"] if p["url"] != url]
        def changed(doc):
            next(p for p in record(doc)["evidence"] if p["url"] == url)["git_blob"] = "0" * 40
        def duplicate(doc):
            record(doc)["evidence"].append(next(p for p in record(doc)["evidence"] if p["url"] == url))
        def wrong_license(doc):
            record(doc)["license"] = "MIT"
        for edit in (missing, changed, duplicate, wrong_license):
            with self.subTest(edit=edit.__name__):
                self.mutate_embedded(edit, "Incomplete Vala historical provenance")

    def test_xqlint_grammar_body_exact(self):
        relation = "xqlint-ebnf-body-exact"
        signature = (b"var XQueryTokenizer = exports.XQueryTokenizer = function "
                     b"XQueryTokenizer(string, parsingEventHandler)\n{\n"
                     b"  init(string, parsingEventHandler);\n?>\n")
        body = signature + b"\nRule ::= 'a'\n"
        old = (b"<?xqlint\n/* ***** BEGIN LICENSE BLOCK *****\n"
               b" * Copyright (c) 2010, Ajax.org B.V.\n"
               b" * ***** END LICENSE BLOCK ***** */\n\n"
               b"define(function(require, exports, module){\n"
               + body + b"\n<?ENCORE?>\n\n<?xqlint\n});\n?>\n")
        new = b"<?xqlint\n" + body + b"\n<?ENCORE?>\n\n<?xqlint\n?>\n"
        self.assertTrue(embedded_source_relation(old, new, relation))
        self.assertFalse(embedded_source_relation(old, new.replace(b"'a'", b"'b'"), relation))
        self.assertFalse(embedded_source_relation(old, new.replace(b"Rule ::=", b"Rule  ::="), relation))
        self.assertFalse(embedded_source_relation(old, new + b"\n", relation))

    def test_xqlint_jsoniq_string_delta(self):
        relation = "xqlint-jsoniq-string-delta"
        old_rule = b"         ::= PredefinedEntityRef | CharRef | EscapeQuot | QuotChar | '\"' | EOF"
        new_rule = b"         ::= JSONPredefinedCharRef | JSONCharRef | JSONChar | '\"' | EOF"
        anchor = b"<?TOKENS?>\n\n"
        insertion = b"JSONChar ::= [^\"\\]\n\nJSONCharRef\n         ::= '\\' 'u' [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]\n         \nJSONPredefinedCharRef\n         ::= '\\' ( '\\' | '/' | '\"' | \"'\" | 'b' | 'f' | 'n' | 'r' | 't' )\n         \n"
        old = b"QuotString\n" + old_rule + b"\n" + anchor + b"ModuleDecl\n"
        new = b"QuotString\n" + new_rule + b"\n" + anchor + insertion + b"ModuleDecl\n"
        self.assertTrue(embedded_source_relation(old, new, relation))
        self.assertFalse(embedded_source_relation(old, new + b"\n", relation))
        self.assertFalse(embedded_source_relation(old + anchor, new + anchor, relation))
        self.assertFalse(embedded_source_relation(old, new.replace(b"JSONCharRef", b"Other", 1), relation))


if __name__ == "__main__":
    unittest.main()
