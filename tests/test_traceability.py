"""Guard normative requirement and architecture register completeness."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TraceabilityTests(unittest.TestCase):
    def test_requirements_have_traceability_owner_and_evidence_column(self):
        spec = (ROOT / "docs/SPECIFICATION.md").read_text(encoding="utf-8")
        arch = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
        trace = (ROOT / "docs/TRACEABILITY.md").read_text(encoding="utf-8")
        # Exclude examples/checkpoints, which may legitimately repeat IDs.
        canonical_trace = trace.split("## Release gates", 1)[0]

        ids = set(re.findall(r"\|\s*((?:FR|NFR)-\d{3})\s*\|", spec))
        ids.update(re.findall(r"\|\s*(ADR-\d{3})\s*\|", arch))
        self.assertTrue(ids)
        for requirement_id in sorted(ids):
            with self.subTest(requirement=requirement_id):
                # We don't mark it verified automatically; checking registry
                # ownership is separate from implementation proof.
                matches = re.findall(
                    r"^\|\s*" + re.escape(requirement_id) +
                    r"\s*\|([^\n]+)$", canonical_trace, re.MULTILINE)
                self.assertEqual(len(matches), 1)
                self.assertIn("#", matches[0], "Every requirement needs an Issue")
                self.assertTrue("pending" in matches[0] or
                                "verified" in matches[0])

    def test_pr_template_requires_evidence(self):
        template = (ROOT / ".github/pull_request_template.md").read_text()
        for keyword in ("Requirements", "ADR", "test", "TRACEABILITY.md", "risk"):
            self.assertIn(keyword.lower(), template.lower())


if __name__ == "__main__":
    unittest.main()
