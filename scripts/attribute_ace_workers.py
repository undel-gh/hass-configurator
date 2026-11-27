#!/usr/bin/env python3
"""Build-time attribution evidence, not a new runtime dependency or license waiver.

Compare the actual shipped worker with both official npm build forms. Resolve
esbuild source-path comments against the pinned upstream source lock, including
workspace-local dependency paths. These latter versions are *source candidates*,
not proven versions of the minified code. Never execute npm package code.
"""
import argparse
import base64
import hashlib
import json
import posixpath
from pathlib import Path
import re
import subprocess
import tarfile
from urllib.parse import quote
from urllib.request import urlopen

try:
    from .audit_supply_chain import git_blob_sha1, query_osv, read_file, sha
    from .prepare_ace_migration import ACE_SHA256, ACE_SRI, exact_member, sri
except ImportError:
    from audit_supply_chain import git_blob_sha1, query_osv, read_file, sha
    from prepare_ace_migration import ACE_SHA256, ACE_SRI, exact_member, sri

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "hass_configurator"
WORKSPACE = "packages/ace-legacy-linters"
SOURCE_COMMIT = "e0d223c5a880cb2f258c96ccd22feaaffb29e5a5"
LOCK_BLOB = "17e9297cb3a744c12b1bd2a6c55a7b3138b39918"
LINTER_LICENSE_BLOB = "319b7eddf9ad9ee57746f4bb486597c87a35929c"
LINTER_URL = "https://registry.npmjs.org/ace-legacy-linters/-/ace-legacy-linters-1.0.2.tgz"
REPLACEMENTS = frozenset("worker-" + name + ".js" for name in
                         ("php", "lua", "html", "json", "css", "xml", "yaml", "javascript"))
NATIVE = frozenset(("worker-base.js", "worker-coffee.js", "worker-xquery.js"))
LIMIT = 32 * 1024 * 1024
SOURCE_COMMENT = re.compile(r"^\s*// ((?:\.\./)*node_modules/[^\s]+)\s*$", re.M)
PACKAGE_NAME = re.compile(r"(?:@[a-z0-9_.-]+/)?[a-z0-9_.-]+")
VERSION = re.compile(r"[0-9][a-zA-Z0-9.+-]*")
NOTICE_NAME = re.compile(r"(?:licen[cs]e|copying|notice|third[-_ ]?party[-_ ]?notices)(?:[._-][^/]*)?", re.I)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text("utf-8"))


def resolve_comment(comment, packages):
    """Resolve deepest node_modules package root, never a same-name global guess."""
    if "\\" in comment or any(p in {"", "."} for p in comment.split("/")):
        raise ValueError("Unsafe source comment: " + comment)
    path = posixpath.normpath(WORKSPACE + "/" + comment)
    if path.startswith("../") or path.startswith("/") or "/../" in path:
        raise ValueError("Source comment escapes workspace: " + comment)
    parts = path.split("/")
    indices = [i for i, p in enumerate(parts) if p == "node_modules"]
    require(indices, "Missing node_modules path: " + comment)
    i = indices[-1] + 1
    require(i < len(parts), "Missing package name: " + comment)
    end = i + (2 if parts[i].startswith("@") else 1)
    name = "/".join(parts[i:end])
    require(PACKAGE_NAME.fullmatch(name) and end < len(parts),
            "Malformed package source path: " + comment)
    key = "/".join(parts[:end])
    entry = packages.get(key)
    return key, name, "/".join(parts[end:]), entry


def sources(unminified, packages):
    result = {}
    for comment in sorted(set(SOURCE_COMMENT.findall(unminified.decode("utf-8")))):
        key, name, file, entry = resolve_comment(comment, packages)
        row = result.setdefault(key, {"name": name, "lock_path": key,
            "source_files": [], "source_lock_version": entry.get("version") if entry else None,
            "source_lock_license": entry.get("license") if entry else None,
            "source_lock_integrity": entry.get("integrity") if entry else None,
            "identity_basis": "published unminified source path; version from source lock, not byte proof"})
        row["source_files"].append(file)
    return list(result.values())


def compare_worker(ace, linters, worker, actual, packages):
    min_name = "src-min-noconflict/" + worker
    plain_name = "src-noconflict/" + worker
    shipped = exact_member(ace, "package/" + min_name)
    plain = exact_member(ace, "package/" + plain_name)
    require(actual == shipped, "Shipped worker differs from pinned Ace archive: " + worker)
    row = {"worker": worker, "shipped_sha256": sha(actual),
           "ace_unminified_sha256": sha(plain)}
    if worker not in REPLACEMENTS:
        row.update({"status": "native-worker-review-open",
                    "source_lock_candidates": []})
        return row
    candidate = exact_member(linters, "package/build/" + min_name)
    candidate_plain = exact_member(linters, "package/build/" + plain_name)
    exact = actual == candidate and plain == candidate_plain
    row.update({"status": "exact-linter-build-match" if exact else "linter-build-mismatch",
                "linter_min_sha256": sha(candidate), "linter_unminified_sha256": sha(candidate_plain),
                "min_equal": actual == candidate, "unminified_equal": plain == candidate_plain,
                "source_lock_candidates": sources(plain, packages) if exact else []})
    return row


def fetch(url):
    with urlopen(url, timeout=25) as response:
        raw = response.read(LIMIT + 1)
    require(len(raw) <= LIMIT, "Oversize npm attribution response")
    return raw


def notices_for(name, version, integrities, fetcher=fetch):
    """Archive identity and license texts for a candidate, never execute scripts."""
    require(PACKAGE_NAME.fullmatch(name) and VERSION.fullmatch(version), "Unsafe npm identity")
    meta = json.loads(fetcher("https://registry.npmjs.org/" + quote(name, safe="") + "/" + version))
    require((meta.get("name"), meta.get("version")) == (name, version), "Registry identity mismatch")
    dist = meta["dist"]
    expected = ("https://registry.npmjs.org/" + name + "/-/" +
                name.split("/")[-1] + "-" + version + ".tgz")
    require(dist["tarball"] == expected, "Unexpected npm tarball URL")
    raw = fetcher(expected)
    actual_sri = sri(raw)
    require(dist.get("integrity") == actual_sri, "Candidate registry SRI mismatch: " + name)
    require(all(pin == actual_sri for pin in integrities), "Candidate source-lock SRI mismatch: " + name)
    import io
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        package = json.loads(exact_member(archive, "package/package.json"))
        require((package.get("name"), package.get("version")) == (name, version),
                "Candidate package identity mismatch")
        files = {}
        for member in archive.getmembers():
            if not member.name.startswith("package/"):
                continue
            relative = member.name[len("package/"):]
            if "/" in relative or not NOTICE_NAME.fullmatch(relative):
                continue
            content = exact_member(archive, member.name)
            require(len(content) <= 512 * 1024, "Oversize candidate notice")
            files[relative] = {"sha256": sha(content),
                               "base64": base64.b64encode(content).decode("ascii")}
    return {"name": name, "version": version, "tarball": expected,
            "archive_sha256": sha(raw), "npm_integrity": actual_sri,
            "source_lock_integrity_present": bool(integrities),
            "declared_license": package.get("license"), "notice_files": files,
            "status": "candidate-notices-collected" if files else "candidate-notices-missing",
            "identity_basis": "source-lock candidate; not final runtime attribution"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("ace", "linters", "registry", "source-lock", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    ace_raw = args.ace.read_bytes()
    require(sha(ace_raw) == ACE_SHA256 and sri(ace_raw) == ACE_SRI,
            "Ace archive differs from reviewed pin")
    linter_raw = args.linters.read_bytes()
    registry = load(args.registry)
    require(registry.get("dist.tarball") == LINTER_URL and
            registry.get("dist.integrity") == sri(linter_raw), "Linter archive registry mismatch")
    lock_raw = args.source_lock.read_bytes()
    require(git_blob_sha1(lock_raw) == LOCK_BLOB, "Linter source lock Git blob mismatch")
    packages = json.loads(lock_raw)["packages"]
    lock = load(ROOT / "docs/ace-builds-1.45.2-lock.json")
    require(set(lock["worker_files"]) == REPLACEMENTS | NATIVE,
            "Unexpected runtime worker set")
    with tarfile.open(args.ace, "r:gz") as ace, tarfile.open(args.linters, "r:gz") as linters:
        meta = json.loads(exact_member(linters, "package/package.json"))
        require((meta.get("name"), meta.get("version")) == ("ace-legacy-linters", "1.0.2"),
                "Unexpected linter package identity")
        license_bytes = exact_member(linters, "package/LICENSE")
        # A different archive notice is a finding, not permission to use it.
        # Collect actual bytes and worker comparisons before failing the gate.
        shipped_license = read_file(PKG, "third_party/licenses/embedded/ace-legacy-linters.txt")
        license_match = (git_blob_sha1(license_bytes) == LINTER_LICENSE_BLOB
                         and license_bytes == shipped_license)
        workers = []
        for name in sorted(REPLACEMENTS | NATIVE):
            actual = read_file(PKG, "vendor/ace/" + name)
            require(sha(actual) == lock["files_sha256"][name], "Worker lock drift: " + name)
            workers.append(compare_worker(ace, linters, name, actual, packages))
    candidates = {}
    for row in workers:
        for candidate in row["source_lock_candidates"]:
            name, version = candidate["name"], candidate["source_lock_version"]
            if version:
                pins = candidates.setdefault((name, version), set())
                if candidate["source_lock_integrity"]:
                    pins.add(candidate["source_lock_integrity"])
    report = {"schema": 1, "source_checkout": subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "ace_archive_sha256": ACE_SHA256,
              "linter_archive": {"name": meta["name"], "version": meta["version"],
                  "tarball": LINTER_URL, "sha256": sha(linter_raw), "npm_integrity": sri(linter_raw),
                  "license_sha256": sha(license_bytes),
                  "license_git_blob": git_blob_sha1(license_bytes),
                  "license_base64": base64.b64encode(license_bytes).decode("ascii"),
                  "expected_source_license_git_blob": LINTER_LICENSE_BLOB,
                  "shipped_license_sha256": sha(shipped_license),
                  "license_source_equal": git_blob_sha1(license_bytes) == LINTER_LICENSE_BLOB,
                  "license_shipped_equal": license_bytes == shipped_license,
                  "source_lock_git_blob": LOCK_BLOB,
                  "source_commit": SOURCE_COMMIT},
              "workers": workers, "candidate_notices": [],
              "limitations": ["Exact equality of the two published build forms proves worker-package attribution only.",
                              "Source paths and source lock identify candidate dependency versions, not a verified rebuild.",
                              "Candidate notices are reference evidence, not shipped notice closure.",
                              "Native workers, non-worker extensions and theme/snippet attribution remain separate.",
                              "Candidate OSV matches do not prove applicability; no risk waiver."]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    save()
    for (name, version), pins in sorted(candidates.items()):
        try:
            report["candidate_notices"].append(notices_for(name, version, pins))
        except Exception as exc:
            # Preserve explicitly unresolved notice fetches without making
            # a candidate look cleared or discarding the worker comparisons.
            report["candidate_notices"].append({"name": name, "version": version,
                "status": "candidate-notice-error", "error": str(exc)})
        save()
    queries = [{"package": {"ecosystem": "npm", "name": name}, "version": version}
               for name, version in sorted(set(candidates) | {("ace-legacy-linters", "1.0.2")})]
    report["candidate_osv"] = query_osv(queries)
    exact_count = sum(w["status"] == "exact-linter-build-match" for w in workers)
    report["status"] = ("partial-attribution-evidence" if license_match and exact_count == len(REPLACEMENTS)
                        else "attribution-blocked")
    save()
    print("Ace worker exact linter matches:", exact_count,
          "/", len(REPLACEMENTS), "; source-lock candidate queries:", len(queries))
    require(license_match, "Linter notice mismatch: actual bytes retained in attribution report")
    require(exact_count == len(REPLACEMENTS), "Linter worker build mismatch: actual evidence retained")


if __name__ == "__main__":
    main()
