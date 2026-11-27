#!/usr/bin/env python3
"""Build-time evidence for native Ace and retained theme/snippet resources."""
import argparse
import io
import json
from pathlib import Path
import plistlib
from xml.parsers.expat import ExpatError
import re
import subprocess
import tarfile
from urllib.request import urlopen

try:
    from .audit_supply_chain import read_file, sha, git_blob_sha1
    from .rebuild_retained_ace import materialize
    from .attribute_ace_workers import sri, require, exact_member
except ImportError:
    from audit_supply_chain import read_file, sha, git_blob_sha1
    from rebuild_retained_ace import materialize
    from attribute_ace_workers import sri, require, exact_member

ROOT = Path(__file__).resolve().parents[1]
ACE_COMMIT = "68d7fd1c0f5ac50cdb610bf06b86074eab3be652"
BUILD_COMMIT = "c9ea63c0a0a436fbb477c918d6736644f77cab9f"
BOOTSTRAP = "lib/ace/worker/worker.js"
NATIVE = {
    "ace/lib/oop": ("src/lib/oop.js", "e0489f46eb2f0ff6d39f09c1711b5cfe827d471c"),
    "ace/apply_delta": ("src/apply_delta.js", "5d2fffb1925069f02a6d9ac5fd3bce9799bd0d63"),
    "ace/lib/event_emitter": ("src/lib/event_emitter.js", "aac6f3d70c0204145e54f10476e202161a3f1e25"),
    "ace/range": ("src/range.js", "321ad67d2d623c8a0f38903a7c2ce28ed31a35cb"),
    "ace/anchor": ("src/anchor.js", "4959ec1fa0e5cd3a95247938731fcc2f56be219e"),
    "ace/document": ("src/document.js", "8501e1027fc2ce68c62e747c3a7e93ce2c1973f1"),
    "ace/lib/deep_copy": ("src/lib/deep_copy.js", "555b282454b1e4d82087312989dd22eef5f5f743"),
    "ace/lib/lang": ("src/lib/lang.js", "80163694e9aaf869b3bb3fe41c895e205c7805b5"),
    "ace/worker/mirror": ("lib/ace/worker/mirror.js", "37d8db7d48768d012c81c2a2dbc36dcaf3746bdd"),
}
SOURCE_PINS = {
    BOOTSTRAP: "e243a6c57ff763e2862c7c87844ab1134b13c575",
    "Makefile.dryice.js": "2d4596dee98c8b09333b192a8f4cd9cd09331185",
    "package.json": "6d1050778144a09cbb3dfb940c96cc898b432d23",
    "LICENSE": "4760be2a6220cf545129b233e20574f2a7bb630e",
    "tool/tmthemes/LICENSE": "08f1380f3a9bce3135253bc69f5861dec3dcae17",
    "tool/tmtheme.js": "eff23f2b777b3a1fea6d3c32ae048c4bda08b075",
    "tool/tmsnippets.js": "febc7946e892692859402053b45369033c516a3b",
    **{path: blob for path, blob in NATIVE.values()},
}
NOTICE_PATTERN = re.compile(
    r"copyright|licen[cs]e|permission is hereby|all rights reserved|"
    r"redistribution|ported from|adapted from|based on|taken from|"
    r"https?://|github\.com|author|contributor", re.I)
MAX_ARCHIVE = 64 * 1024 * 1024


def fetch(url):
    with urlopen(url, timeout=45) as response:
        raw = response.read(MAX_ARCHIVE + 1)
    require(len(raw) <= MAX_ARCHIVE, "Archive exceeds evidence size limit")
    return raw


def source_file(root, path):
    raw = read_file(root, path)
    expected = subprocess.check_output(["git", "rev-parse", "HEAD:" + path], cwd=root, text=True).strip()
    require(git_blob_sha1(raw) == expected, "Ace source file drift: " + path)
    return raw, expected


def notice_scan(raw):
    return [{"line": i, "text": line.strip()} for i, line in
            enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1)
            if NOTICE_PATTERN.search(line)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--ace", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    source, work, out = args.source.resolve(), args.work.resolve(), args.output.resolve()
    require(not work.exists() and not work.is_relative_to(ROOT)
            and not work.is_relative_to(source), "Use fresh disposable work directory")
    require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == ACE_COMMIT,
            "Wrong Ace source checkout")
    require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=source, text=True).strip(),
            "Dirty upstream source checkout")
    work.mkdir(parents=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / "docs/ace-builds-1.45.2-lock.json").read_text("utf-8"))
    require(lock["source_commit"] == ACE_COMMIT and lock["build_commit"] == BUILD_COMMIT, "Ace pin drift")
    raw = args.ace.read_bytes()
    require(sha(raw) == lock["sha256"] and sri(raw) == lock["npm_integrity"], "Ace archive pin mismatch")
    source_rows = {}
    for path, blob in SOURCE_PINS.items():
        data, actual = source_file(source, path)
        require(actual == blob, "Pinned Ace source mismatch: " + path)
        source_rows[path] = {"git_blob": actual, "sha256": sha(data), "notice_hits": notice_scan(data)}
    # Exact source files from the immutable checkout, including per-file
    # TextMate exception evidence. Never infer a license from missing matches.
    for directory in ("src/theme", "src/snippets", "tool/tmthemes"):
        for path in sorted((source / directory).iterdir()):
            if not path.is_file():
                continue
            name = path.relative_to(source).as_posix()
            data, blob = source_file(source, name)
            row = {"git_blob": blob, "sha256": sha(data), "notice_hits": notice_scan(data)}
            if name.endswith(".tmTheme"):
                try:
                    parsed = plistlib.loads(data)
                    row["plist_metadata"] = {k: v for k, v in parsed.items()
                                             if isinstance(v, str) and k != "uuid"}
                except (ValueError, plistlib.InvalidFileException, TypeError, ExpatError) as exc:
                    row["plist_parse_error"] = str(exc)
            source_rows[name] = row
    selected = sorted(name for name in lock["files_sha256"] if
                      name == "worker-base.js" or name.startswith(("theme-", "snippets/")))
    assets = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for name in selected:
            plain = exact_member(archive, "package/src-noconflict/" + name)
            mini = exact_member(archive, "package/src-min-noconflict/" + name)
            require(sha(mini) == lock["files_sha256"][name] and
                    mini == read_file(ROOT / "hass_configurator", "vendor/ace/" + name),
                    "Shipped resource mismatch: " + name)
            for folder, data in (("plain", plain), ("mini", mini)):
                path = work / folder / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            assets.append({"file": name, "published_unminified_sha256": sha(plain),
                           "shipped_minified_sha256": sha(mini)})
    # Upstream builder pins this TypeScript version. Record the observed
    # registry integrity and archive hash; not a historical toolchain lock.
    package = json.loads(read_file(source, "package.json"))
    version = package["devDependencies"]["typescript"]
    require(version == "5.9.2", "Unexpected native TypeScript version")
    meta = json.loads(fetch("https://registry.npmjs.org/typescript/" + version))
    url = "https://registry.npmjs.org/typescript/-/typescript-" + version + ".tgz"
    require(meta["name"] == "typescript" and meta["version"] == version and
            meta["dist"]["tarball"] == url, "TypeScript registry identity mismatch")
    ts = fetch(url)
    require(sri(ts) == meta["dist"]["integrity"], "TypeScript registry integrity mismatch")
    materialize(ts, work / "typescript", "typescript", version)
    report = {
        "schema": 1,
        "status": "source-audit-in-progress",
        "source_checkout": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "ace_source_commit": ACE_COMMIT, "ace_build_commit": BUILD_COMMIT,
        "ace_archive_sha256": sha(raw),
        "typescript": {"version": version, "archive_sha256": sha(ts), "integrity": sri(ts),
                       "provenance": "upstream declared version, observed registry archive"},
        "sources": source_rows, "assets": assets,
        "native_sources": {key: value[0] for key, value in NATIVE.items()},
        "limitations": [
            "Native source comparison uses upstream transpilation and AST printer without comments; not a raw rebuild of the native minified file.",
            "Theme/snippet static data comparison and marker scans do not establish historical authorship, licensing, or absence of additional terms.",
            "No generated or transformed runtime files are promoted; no upstream JS is executed.",
        ],
    }
    out.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    subprocess.run(["node", str(ROOT / "scripts/audit_ace_native_payloads.cjs"), str(source),
                    str(work), str(out)], check=True)


if __name__ == "__main__":
    main()
