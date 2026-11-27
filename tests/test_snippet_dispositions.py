"""Version-bound snippet matrix must fail closed on evidence drift."""
import copy
import json
from pathlib import Path
import unittest

from scripts.audit_ace_snippet_dispositions import (
    MATRIX_PATH, DOCUMENT_PATH, COUNTS, load_matrix, render_document,
    verify_snippet_dispositions, verify_native_snippet_dispositions,
)

ROOT = Path(__file__).resolve().parents[1]


class SnippetDispositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = load_matrix(ROOT)
        cls.lock = json.loads((ROOT / "docs/ace-builds-1.45.2-lock.json").read_text("utf-8"))
        cls.vendor = json.loads((ROOT / "hass_configurator/vendor/manifest.json").read_text("utf-8"))
        cls.embedded = json.loads((ROOT / "hass_configurator/third_party/embedded.json").read_text("utf-8"))

    def verify(self, matrix, vendor=None, embedded=None):
        return verify_snippet_dispositions(matrix, self.lock, vendor or self.vendor, embedded or self.embedded)

    def test_matrix_closure_and_render(self):
        self.assertEqual(self.verify(self.matrix), COUNTS)
        self.assertEqual((ROOT / DOCUMENT_PATH).read_text("utf-8"), render_document(self.matrix))
        self.assertEqual(len(self.matrix["rows"]), 202)
        self.assertEqual(sum(r["payload_kind"] == "nonempty" for r in self.matrix["rows"]), 52)
        self.assertEqual(sum(r["payload_kind"] == "empty-stub" for r in self.matrix["rows"]), 150)
        self.assertEqual({r["snippet"] for r in self.matrix["rows"]
                          if r["proposed_disposition"] == "consider-snippet-only-exclusion"},
                         {"abc", "edifact", "gobstones", "lsl"})

    def test_matrix_rejects_missing_duplicate_extra_hash_and_clearance(self):
        for mutation in (
            lambda m: m["rows"].pop(),
            lambda m: m["rows"].append(copy.deepcopy(m["rows"][0])),
            lambda m: m["rows"][0].update(snippet="not_a_module"),
            lambda m: m["rows"][0].update(asset_sha256="0" * 64),
            lambda m: m["rows"][0].update(distribution="excluded"),
            lambda m: m["rows"][0].update(payload_kind="nonempty"),
            lambda m: m["rows"][0].update(proposed_disposition="cleared"),
            lambda m: m.update(review_status="accepted"),
            lambda m: m.update(ace_source_commit="a" * 40),
        ):
            changed = copy.deepcopy(self.matrix)
            mutation(changed)
            with self.assertRaises(ValueError):
                self.verify(changed)

    def test_matrix_rejects_source_component_and_vendor_drift(self):
        for field, value in (("additional_components", []), ("evidence_class", "historical-endpoint-review-open"),
                             ("historical_reference", None)):
            changed = copy.deepcopy(self.matrix)
            row = next(r for r in changed["rows"] if r["snippet"] == "java")
            row[field] = value
            with self.assertRaises(ValueError):
                self.verify(changed)
        changed = copy.deepcopy(self.matrix)
        next(r for r in changed["rows"] if r["snippet"] == "java")["source_payload"]["git_blob"] = "0" * 40
        with self.assertRaises(ValueError):
            self.verify(changed)
        vendor = copy.deepcopy(self.vendor)
        vendor["resources"].pop("vendor/ace/snippets/abap.js")
        with self.assertRaises(ValueError):
            self.verify(self.matrix, vendor=vendor)
        embedded = copy.deepcopy(self.embedded)
        next(c for c in embedded["components"] if c["id"] == "ace-lsl-snippet-source-review")["kind"] = "library"
        with self.assertRaises(ValueError):
            self.verify(self.matrix, embedded=embedded)

    def test_native_matrix_requires_all_rows_and_exact_source_pins(self):
        # Synthetic report tests the cross-check, not upstream parsing.
        report = {"ace_source_commit": self.matrix["ace_source_commit"],
                  "ace_build_commit": self.matrix["ace_build_commit"],
                  "theme_snippet_assets": [], "sources": {}}
        for row in self.matrix["rows"]:
            src = row["source_payload"]
            asset = {"file": "snippets/" + row["snippet"] + ".js",
                     "status": "static-payload-equal" if src else "exact-generated-empty-stub",
                     "source_files": []}
            if src:
                report["sources"][src["path"]] = {"git_blob": src["git_blob"]}
                asset["source_files"].append({"source": src["path"], "source_present": True})
            report["theme_snippet_assets"].append(asset)
        self.assertEqual(verify_native_snippet_dispositions(self.matrix, report)["nonempty"], 52)
        for mutation in (
            lambda r: r["theme_snippet_assets"].pop(),
            lambda r: r["theme_snippet_assets"].append(copy.deepcopy(r["theme_snippet_assets"][0])),
            lambda r: r["theme_snippet_assets"][0].update(status="static-payload-equal"),
            lambda r: r["sources"]["src/snippets/java.snippets.js"].update(git_blob="0" * 40),
            lambda r: next(x for x in r["theme_snippet_assets"] if x["file"] == "snippets/java.js").update(source_files=[]),
        ):
            changed = copy.deepcopy(report)
            mutation(changed)
            with self.assertRaises(ValueError):
                verify_native_snippet_dispositions(self.matrix, changed)

    def test_matrix_duplicate_json_keys_fail(self):
        from scripts.audit_ace_snippet_dispositions import unique_json
        with self.assertRaises(ValueError):
            json.loads('{"schema": 1, "schema": 2}', object_pairs_hook=unique_json)


if __name__ == "__main__":
    unittest.main()
