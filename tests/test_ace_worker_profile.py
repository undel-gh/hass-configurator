"""Pin the agreed #37 subset and reject incomplete or inconsistent profiles."""
import copy
import json
import unittest
from pathlib import Path
import tempfile

from scripts.ace_worker_profile import LOCK, read_profile, selected_family, validate_manifest, verify_vendor_tree


class AceWorkerProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = read_profile()
        self.lock = json.loads(LOCK.read_text("utf-8"))

    def test_agreed_profile_preserves_all_other_upstream_assets(self):
        selected = selected_family(self.profile, self.lock)
        excluded = {"worker-coffee.js", "worker-lua.js", "worker-php.js",
                    "worker-xml.js", "worker-xquery.js", "theme-kr_theme.js"}
        self.assertEqual(self.profile["excluded_themes"], ["theme-kr_theme.js"])
        self.assertEqual(set(self.lock["files_sha256"]) - set(selected), excluded)
        self.assertEqual(set(self.profile["languages"]), {"ace/mode/" + name for name in
                         ("yaml", "json", "javascript", "css", "html")})
        self.assertEqual(len(selected), 489)
        self.assertEqual(selected, {n: h for n, h in self.lock["files_sha256"].items() if n not in excluded})

    def test_reject_unclassified_or_duplicate_workers(self):
        for excluded in (self.profile["excluded"][1:], self.profile["excluded"] + ["worker-yaml.js"],
                         self.profile["excluded"] + [self.profile["excluded"][0]]):
            with self.subTest(excluded=excluded):
                profile = copy.deepcopy(self.profile)
                profile["excluded"] = excluded
                with self.assertRaisesRegex(ValueError, "partition"):
                    selected_family(profile, self.lock)

    def test_reject_invalid_theme_exclusions(self):
        for excluded in (["ace.js"], ["theme-missing.js"], ["theme-monokai.js"],
                         ["theme-kr_theme.js", "theme-kr_theme.js"], ["../theme-kr_theme.js"]):
            with self.subTest(excluded=excluded):
                profile = copy.deepcopy(self.profile)
                profile["excluded_themes"] = excluded
                with self.assertRaisesRegex(ValueError, "theme exclusions"):
                    selected_family(profile, self.lock)

    def test_reject_wrong_module_or_version(self):
        profile = copy.deepcopy(self.profile)
        profile["languages"]["ace/mode/yaml"]["module"] = "ace/mode/xml_worker"
        with self.assertRaisesRegex(ValueError, "mapping"):
            selected_family(profile, self.lock)
        profile = copy.deepcopy(self.profile)
        profile["ace_version"] = "1.9.6"
        with self.assertRaisesRegex(ValueError, "version"):
            selected_family(profile, self.lock)

    def test_manifest_rejects_reintroduced_worker_and_drift(self):
        expected = {"vendor/ace/" + n: h for n, h in selected_family(self.profile, self.lock).items()}
        validate_manifest(self.profile, self.lock, {"resources": expected})
        for change in ({**expected, "vendor/ace/worker-xml.js": self.lock["files_sha256"]["worker-xml.js"]},
                       {**expected, "vendor/ace/theme-kr_theme.js": self.lock["files_sha256"]["theme-kr_theme.js"]},
                       {**expected, "vendor/ace/ace.js": "0" * 64}):
            with self.assertRaisesRegex(ValueError, "Curated Ace manifest"):
                validate_manifest(self.profile, self.lock, {"resources": change})

    def test_tree_rejects_reintroduction_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "vendor/ace").mkdir(parents=True)
            (root / "vendor/manifest.json").touch()
            (root / "vendor/ace/ace.js").touch()
            resources = {"vendor/ace/ace.js": "unused"}
            verify_vendor_tree(root, resources)
            extra = root / "vendor/ace/worker-xml.js"
            extra.touch()
            with self.assertRaisesRegex(ValueError, "Untracked or absent"):
                verify_vendor_tree(root, resources)
            extra.unlink()
            try:
                extra.symlink_to(root / "not-present")
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unavailable")
            with self.assertRaisesRegex(ValueError, "Unsafe vendor entry"):
                verify_vendor_tree(root, resources)
