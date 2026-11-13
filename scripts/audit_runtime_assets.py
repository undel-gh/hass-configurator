#!/usr/bin/env python3
"""Check inventory drift against shipped HTML; no claim of offline readiness.

Run: python scripts/audit_runtime_assets.py [--strict-offline]
The normal mode is a baseline gate. Strict mode is intentionally not green
until all CDN/images and dynamic Ace dependencies are localized (#3/#4/#6).
"""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "hass_configurator" / "dev.html"
MANIFEST = ROOT / "docs" / "runtime-dependencies.json"


def extract(html):
    """Return independently loaded remote resources and Ace choices."""
    resources = sorted(set(re.findall(
        r'<(?:script|link|img)\b[^>]*?(?:src|href)="(https?://[^"]+)"',
        html,
    )))
    cdn = sorted(u for u in resources if "cdnjs.cloudflare.com" in u)
    avatars = sorted(u for u in resources if "avatars" in u and
                     "githubusercontent.com" in u)
    other = sorted(set(resources) - set(cdn) - set(avatars))
    modes = sorted(set(re.findall(r'value="ace/mode/([^"]+)"', html)))
    themes = sorted(set(re.findall(r'value="ace/theme/([^"]+)"', html)))
    return {
        "cdn": cdn, "avatars": avatars, "other_remote": other,
        "modes": modes, "themes": themes,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-offline", action="store_true",
                        help="Fail on any automatically loaded external resource")
    args = parser.parse_args()

    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    scanned = extract(HTML.read_text(encoding="utf-8"))
    expected = {
        "cdn": sorted(data["required_external_files"]),
        "avatars": sorted(data["auto_loaded_external_images"]),
        "other_remote": [],
        "modes": sorted(data["ace"]["language_modes_offered"]),
        "themes": sorted(data["ace"]["themes_offered"]),
    }
    if scanned != expected:
        print("Asset inventory out of sync with HTML. Update inventory and review "
              "new outbound runtime requests before merging.", file=sys.stderr)
        for field in expected:
            if scanned[field] != expected[field]:
                print("%s expected=%s actual=%s" %
                      (field, expected[field], scanned[field]), file=sys.stderr)
        return 1

    print("Inventory matches HTML: %i CDN resources, %i remote avatar images, "
          "%i Ace modes, %i themes" %
          (len(scanned["cdn"]), len(scanned["avatars"]),
           len(scanned["modes"]), len(scanned["themes"])))
    print("WARNING: static inventory is not a browser runtime trace.")
    if args.strict_offline and (scanned["cdn"] or scanned["avatars"] or
                                scanned["other_remote"]):
        print("Strict offline gate FAILED: runtime external fetches remain.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
