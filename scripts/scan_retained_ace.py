#!/usr/bin/env python3
"""Retained-runtime marker inventory, not a blanket component-absence proof."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile

try:
    from .ace_worker_profile import ROOT, LOCK, read_profile, selected_family, validate_manifest, verify_vendor_tree
except ImportError:
    from ace_worker_profile import ROOT, LOCK, read_profile, selected_family, validate_manifest, verify_vendor_tree

PACKAGE = ROOT / "hass_configurator"
MARKERS = {
    "lodash": ("lodash/lodash.js", "Lodash <https://lodash.com", "4.17.21", "lodash.VERSION", "lodash"),
    "chevrotain": ("chevrotain/lib/", "Chevrotain", "chevrotain"),
    "xml-tools": ("@xml-tools/",),
    "regexp-to-ast": ("regexp-to-ast",),
    "php-parser": ("php-parser",),
    "luaparse": ("luaparse",),
    "coffee": ("CoffeeScript Compiler", 'version:"2.2.1"', "coffee-script"),
    "xqlint": ("xqlint", "XQueryTokenizer", "JSONiqTokenizer", "ace/mode/xquery/xquery_lexer", "ace/mode/xquery/jsoniq_lexer"),
    "jshint": ("Good, not Evil", "ace/mode/javascript/jshint"),
    "kr-theme-payload": ("ace/theme/kr_theme-css", ".ace-kr-theme"),
}


def scan(raw):
    # Case-sensitive literal markers: all hits require interpretation.
    return {name: [marker for marker in markers if marker.encode("utf-8") in raw]
            for name, markers in MARKERS.items()
            if any(marker.encode("utf-8") in raw for marker in markers)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ace", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    lock = json.loads(LOCK.read_text("utf-8"))
    profile = read_profile()
    selected = selected_family(profile, lock)
    manifest = json.loads((PACKAGE / "vendor/manifest.json").read_text("utf-8"))
    validate_manifest(profile, lock, manifest)
    verify_vendor_tree(PACKAGE, manifest["resources"])
    if hashlib.sha256(args.ace.read_bytes()).hexdigest() != lock["sha256"]:
        raise ValueError("Ace archive pin mismatch")
    rows = []
    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file() or path.suffix not in {".js", ".html", ".css", ".py"}:
            continue
        raw = path.read_bytes()
        name = path.relative_to(PACKAGE).as_posix()
        if name in manifest["resources"] and hashlib.sha256(raw).hexdigest() != manifest["resources"][name]:
            raise ValueError("Retained resource hash mismatch: " + name)
        hits = scan(raw)
        if name.startswith("vendor/ace/") and name.endswith(".js"):
            for excluded_name in profile["excluded_snippets"]:
                module_id = ("ace/" + excluded_name[:-3]).encode("ascii")
                # Mode metadata may mention the ID; only a module definition is forbidden.
                if any(prefix + module_id + quote in raw for prefix, quote in (
                        (b'ace.define("', b'"'), (b"ace.define('", b"'"))):
                    raise ValueError("Excluded snippet definition in retained Ace: " + name)
        if ("theme-kr_theme.js" in profile["excluded_themes"] and
                "kr-theme-payload" in hits and name.startswith("vendor/ace/")):
            raise ValueError("Excluded krTheme payload marker in retained Ace: " + name)
        rows.append({"file": name, "sha256": hashlib.sha256(raw).hexdigest(), "hits": hits})
    upstream = []
    with tarfile.open(args.ace, "r:gz") as tar:
        members = {}
        for member in tar.getmembers():
            prefix = "package/src-noconflict/"
            if not member.name.startswith(prefix) or member.isdir():
                continue
            name = member.name[len(prefix):]
            if name in members or not member.isfile():
                raise ValueError("Unsafe/duplicate upstream source member")
            members[name] = member
        for name in sorted(selected):
            if not name.endswith(".js"):
                continue
            # No assumed equivalence of minified/unminified forms: this is
            # same pinned archive evidence, not a reproducible source rebuild.
            if name not in members:
                upstream.append({"file": name, "status": "unminified-counterpart-missing"})
                continue
            raw = tar.extractfile(members[name]).read()
            upstream.append({"file": name, "sha256": hashlib.sha256(raw).hexdigest(), "hits": scan(raw)})
    report = {"source_checkout": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "status": "marker-evidence-review-required", "excluded_workers": profile["excluded"],
              "excluded_themes": profile["excluded_themes"],
              "excluded_snippets": profile["excluded_snippets"],
               "retained_family": len(selected), "runtime_files": rows,
              "upstream_unminified_counterparts": upstream,
              "limitations": ["Literal indicators may be false positives or miss renamed/minified code.",
                              "Historical notices and excluded archive members are not runtime code.",
                              "Do not infer full absence, license closure or VEX from marker results alone."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("Retained executable/source files scanned:", len(rows), "; upstream counterparts:", len(upstream))


if __name__ == "__main__":
    main()
