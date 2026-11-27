"""External theme evidence must not hide changes or imply license clearance."""
import plistlib
import unittest
from scripts.audit_external_themes import compare_plist, verify_blob, reference, verify_historical_import, textmate_license_relation
from scripts.audit_supply_chain import git_blob_sha1


class ExternalThemeTests(unittest.TestCase):
    def test_xml_format_only(self):
        value = {"name": "example", "settings": [{"settings": {"foreground": "#123456"}}]}
        xml = plistlib.dumps(value)
        binary = plistlib.dumps(value, fmt=plistlib.FMT_BINARY)
        result = compare_plist(xml, binary)
        self.assertFalse(result["raw_equal"])
        self.assertTrue(result["parsed_equal"])
        self.assertTrue(result["settings_equal"])

    def test_metadata_and_settings_changes_distinguished(self):
        a = {"name": "A", "settings": [{"scope": "x"}, {"scope": "y"}]}
        b = {"name": "B", "settings": a["settings"]}
        result = compare_plist(plistlib.dumps(a), plistlib.dumps(b))
        self.assertEqual(result["differing_top_level_keys"], ["name"])
        self.assertTrue(result["settings_equal"])
        b["settings"] = list(reversed(a["settings"]))
        self.assertFalse(compare_plist(plistlib.dumps(a), plistlib.dumps(b))["settings_equal"])

    def test_type_and_color_changes(self):
        for a, b in ((True, 1), ("#123456", "#123457")):
            x = plistlib.dumps({"settings": [a]})
            y = plistlib.dumps({"settings": [b]})
            self.assertFalse(compare_plist(x, y)["settings_equal"])

    def test_blob_drift_rejected_including_license(self):
        raw = b"original license\n"
        pin = git_blob_sha1(raw)
        self.assertEqual(verify_blob(raw, pin)["git_blob"], pin)
        with self.assertRaisesRegex(ValueError, "blob mismatch"):
            reference("owner/repo", "a" * 40, "LICENSE", pin, lambda _: raw + b" ")
        with self.assertRaisesRegex(ValueError, "blob mismatch"):
            verify_blob(b"changed theme", pin)

    def test_invalid_shape(self):
        with self.assertRaises(ValueError):
            compare_plist(plistlib.dumps({"name": "missing"}), plistlib.dumps({"settings": []}))

    def test_historical_import_requires_exact_bytes(self):
        a = {"settings": [{"scope": "x"}]}
        raw = plistlib.dumps(a)
        self.assertTrue(verify_historical_import(raw, raw)["raw_equal"])
        with self.assertRaisesRegex(ValueError, "import bytes differ"):
            verify_historical_import(raw, plistlib.dumps(a, fmt=plistlib.FMT_BINARY))

    def test_textmate_license_scope_only(self):
        readme = b"Intro\n\n# License\n\nfiles in this repository fall under these terms.\nException applies."
        local = b"files in this directory fall under these terms.\n\nException applies."
        self.assertEqual(textmate_license_relation(readme, local),
                         "scope-wording-and-whitespace-only")
        for changed in (local.replace(b"Exception applies.", b""), local.replace(b"directory", b"project")):
            with self.assertRaisesRegex(ValueError, "terms differ"):
                textmate_license_relation(readme, changed)
        with self.assertRaisesRegex(ValueError, "unique TextMate license"):
            textmate_license_relation(b"Missing", local)
