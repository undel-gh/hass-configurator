#!/usr/bin/env python3
"""Vendor immutable npm archives for offline HASS Configurator assets.

This is a BUILD-TIME command (network is external to this script). Runtime
must never download assets. Usage:
  python scripts/vendor_offline_assets.py --ace /tmp/ace-builds-1.9.6.tgz \
      --materialize /tmp/materialize-css-0.100.2.tgz \
      --mdi /tmp/mdi-font-3.4.93.tgz
The source artifacts must be downloaded only by an authenticated package manager
and must match the checked-in integrity metadata after the first generation.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "hass_configurator" / "vendor"
ACE_LOCK = json.loads((ROOT / "docs/ace-builds-1.9.6-lock.json").read_text("utf8"))
SOURCES = {
    "ace": ("ace-builds", "1.9.6", "package/src-min-noconflict/"),
    "materialize": ("materialize-css", "0.100.2", "package/dist/css/"),
    "mdi": ("@mdi/font", "3.4.93", "package/css/"),
}
CSS_NAMES = {
    "materialize": "materialize.min.css",
    "mdi": "materialdesignicons.min.css",
}
URL_PATTERN = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def member_bytes(archive, path):
    try:
        member = archive.getmember(path)
    except KeyError as exc:
        raise RuntimeError("Missing upstream resource: " + path) from exc
    if not member.isfile() or member.issym() or member.islnk():
        raise RuntimeError("Unexpected symlink/nonfile in npm archive: " + path)
    return archive.extractfile(member).read()


def safe_path(name):
    parts = PurePosixPath(name).parts
    if not parts or any(x in ("", ".", "..") for x in parts):
        raise RuntimeError("Unsafe vendored relative resource path: " + name)
    return name


def referenced_css_paths(css, archive_name):
    """Return paths used by CSS relative to its original directory."""
    result = []
    for _, raw in URL_PATTERN.findall(css):
        url = raw.strip()
        if url.startswith(("data:", "#")):
            continue
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or url.startswith("//"):
            raise RuntimeError("Automatic external CSS fetch in %s: %s" %
                               (archive_name, url))
        if not parsed.path:
            continue
        base = PurePosixPath(archive_name).parent
        parts = []
        for part in (base / parsed.path).parts:
            if part in ("", "."):
                continue
            if part == "..":
                if not parts:
                    raise RuntimeError("CSS escapes package root: " + url)
                parts.pop()
            else:
                parts.append(part)
        resolved = "/".join(parts)
        safe_path(resolved)
        result.append(resolved)
    return sorted(set(result))


def archive_index(archive):
    return {m.name for m in archive.getmembers() if m.isfile()}


def add_file(output_map, relative_path, data):
    safe_path(relative_path)
    if relative_path in output_map and output_map[relative_path] != data:
        raise RuntimeError("Duplicate resource with different bytes: " + relative_path)
    output_map[relative_path] = data


def package_license(archive, name, output_map):
    choices = [
        "package/LICENSE", "package/LICENSE.md", "package/LICENSE.txt",
        "package/license", "package/license.md", "package/license.txt",
        "package/License", "package/License.md",
    ]
    found = next((x for x in choices if x in archive_index(archive)), None)
    if found is None:
        raise RuntimeError("Missing license in upstream package " + name)
    add_file(output_map, "licenses/" + name + ".txt", member_bytes(archive, found))
    return found


def build(archives, integrity_values):
    resources = {}
    provenance = {}
    for alias, (package, version, archive_prefix) in SOURCES.items():
        filename = archives[alias]
        tarbytes = filename.read_bytes()
        sri = "sha512-" + base64.b64encode(hashlib.sha512(tarbytes).digest()).decode()
        if integrity_values.get(alias) and integrity_values[alias] != sri:
            raise RuntimeError("%s npm SRI mismatch" % package)
        if alias == "ace":
            if sri != ACE_LOCK["npm_integrity"] or digest(tarbytes) != ACE_LOCK["sha256"]:
                raise RuntimeError("Ace archive doesn't match pinned artifact")
        with tarfile.open(filename, "r:gz") as archive:
            index = archive_index(archive)
            if alias == "ace":
                for rel, expected in ACE_LOCK["files_sha256"].items():
                    raw = member_bytes(archive, archive_prefix + rel)
                    if digest(raw) != expected:
                        raise RuntimeError("Ace file hash mismatch: " + rel)
                    add_file(resources, "ace/" + rel, raw)
                if any(x.startswith(archive_prefix) and x[len(archive_prefix):]
                       not in ACE_LOCK["files_sha256"] for x in index):
                    raise RuntimeError("Untracked Ace file in upstream archive")
            else:
                css_path = archive_prefix + CSS_NAMES[alias]
                css = member_bytes(archive, css_path)
                # Reuse package-relative paths so CSS url(../fonts/...) still works.
                css_rel = "css/" + CSS_NAMES[alias]
                add_file(resources, alias + "/" + css_rel, css)
                for dep in referenced_css_paths(css.decode("utf8"), css_rel):
                    tarpath = "package/" + dep
                    if alias == "materialize" and archive_prefix.startswith("package/dist/"):
                        tarpath = "package/dist/" + dep
                    if tarpath not in index:
                        raise RuntimeError("%s CSS reference unavailable: %s" %
                                           (package, tarpath))
                    add_file(resources, alias + "/" + dep, member_bytes(archive, tarpath))
            license_file = package_license(archive, alias, resources)
        provenance[alias] = {
            "package": package, "version": version,
            "tarball": "https://registry.npmjs.org/" +
                       (package.replace("@", "%40").replace("/", "%2F")) +
                       "/-/" + package.split("/")[-1] + "-" + version + ".tgz",
            "sha256": digest(tarbytes),
            "npm_integrity": sri,
            "license_path_in_archive": license_file,
        }
    # All URLs are deliberately relative to the package root.
    # Fail on external or absolute CSS imports and unlisted transitive assets.
    keys = sorted(resources)
    manifest = {
        "schema": 1,
        "provenance": provenance,
        "resources": {"vendor/" + k: digest(resources[k]) for k in keys},
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, data in resources.items():
        dest = OUTPUT / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf8")
    print("Vendored %s resources: Ace=%d; other=%d" %
          (len(resources), len(ACE_LOCK["files_sha256"]),
           len(resources) - len(ACE_LOCK["files_sha256"])))
    print("Provenance:", json.dumps(provenance, indent=2))
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ace", type=Path, required=True)
    ap.add_argument("--materialize", type=Path, required=True)
    ap.add_argument("--mdi", type=Path, required=True)
    ap.add_argument("--sri-file", type=Path,
                    help="JSON mapping aliases to immutable npm integrity values")
    opts = ap.parse_args()
    sri = {}
    if opts.sri_file:
        sri = json.loads(opts.sri_file.read_text("utf8"))
    build({k: getattr(opts, k) for k in SOURCES}, sri)


if __name__ == "__main__":
    main()
