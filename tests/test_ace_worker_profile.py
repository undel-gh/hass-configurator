"""Pin the agreed #37 subset and reject incomplete or inconsistent profiles."""
import copy
import json
import unittest

from scripts.ace_worker_profile import LOCK, read_profile, selected_family


class AceWorkerProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = read_profile()
        self.lock = json.loads(LOCK.read_text("utf-8"))

    def test_agreed_profile_preserves_every_non_worker(self):
        selected = selected_family(self.profile, self.lock)
        excluded = {"worker-coffee.js", "worker-lua.js", "worker-php.js",
                    "worker-xml.js", "worker-xquery.js"}
        self.assertEqual(set(self.lock["files_sha256"]) - set(selected), excluded)
        self.assertEqual(set(self.profile["languages"]), {"ace/mode/" + name for name in
                         ("yaml", "json", "javascript", "css", "html")})
        self.assertEqual(len(selected), 490)
        self.assertEqual(selected, {n: h for n, h in self.lock["files_sha256"].items() if n not in excluded})

    def test_reject_unclassified_or_duplicate_workers(self):
        for excluded in (self.profile["excluded"][1:], self.profile["excluded"] + ["worker-yaml.js"],
                         self.profile["excluded"] + [self.profile["excluded"][0]]):
            with self.subTest(excluded=excluded):
                profile = copy.deepcopy(self.profile)
                profile["excluded"] = excluded
                with self.assertRaisesRegex(ValueError, "partition"):
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
