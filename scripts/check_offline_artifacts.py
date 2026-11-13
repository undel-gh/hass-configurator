#!/usr/bin/env python3
"""Validate that wheel/sdist contain the exact committed offline assets."""
import hashlib
from email.parser import BytesParser
import json
from pathlib import Path
import sys
import tarfile
import zipfile

from hass_configurator.http_routing import PACKAGE_ASSETS
from hass_configurator._version import VERSION

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "hass_configurator/vendor/manifest.json").read_text("utf8"))


def verify(files, label):
    required = dict(MANIFEST["resources"])
    # Bundle integrity is not complete if the six application-owned static
    # resources are missing, even when the third-party vendor tree is intact.
    # dev.html is the primary first-party UI entrypoint. It is not a
    # fingerprinted /assets/ route, but MUST be byte-exact in both archives.
    first_party = set(PACKAGE_ASSETS) | {"dev.html"}
    for name in first_party:
        required[name] = hashlib.sha256(
            (ROOT / "hass_configurator" / name).read_bytes()).hexdigest()
    missing = []
    different = []
    for name, expected in required.items():
        archive_path = "hass_configurator/" + name
        if archive_path not in files:
            missing.append(archive_path)
        elif hashlib.sha256(files[archive_path]).hexdigest() != expected:
            different.append(archive_path)
    if missing or different:
        raise RuntimeError("%s incomplete/corrupted packaged resources: missing=%s changed=%s" %
                           (label, missing[:5], different[:5]))
    version_file = "hass_configurator/_version.py"
    if files.get(version_file) != (ROOT / version_file).read_bytes():
        raise RuntimeError("%s missing or stale shared runtime version file" % label)
    extra_manifest = files.get("hass_configurator/vendor/manifest.json")
    if extra_manifest is None:
        raise RuntimeError("%s missing the vendor integrity manifest" % label)
    if json.loads(extra_manifest)["resources"] != MANIFEST["resources"]:
        raise RuntimeError("%s embedded manifest differs from source" % label)
    print("%s: %d vendor resources, %d first-party resources (including dev.html) and manifest validated" %
          (label, len(MANIFEST["resources"]), len(first_party)))



def assert_metadata(payload, label):
    metadata = BytesParser().parsebytes(payload)
    # A same-named public PyPI package must not masquerade as this fork.
    homepage = metadata.get("Home-page", "")
    if homepage != "https://github.com/undel-gh/hass-configurator":
        raise RuntimeError("%s distribution metadata points outside the fork: %s" %
                           (label, homepage))
    if metadata.get("Version") != VERSION or metadata.get("Name", "").lower().replace("_", "-") != "hass-configurator":
        raise RuntimeError("%s wrong distribution metadata: %s/%s; expected hass-configurator/%s" %
                           (label, metadata.get("Name"), metadata.get("Version"), VERSION))



def main(wheel_dir, sdist_dir):
    wheels = list(wheel_dir.glob("*.whl"))
    sdists = list(sdist_dir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("Expected exactly one wheel and one sdist")
    with zipfile.ZipFile(wheels[0]) as archive:
        dist_info = [n for n in archive.namelist() if n.endswith(".dist-info/METADATA")]
        if len(dist_info) != 1:
            raise RuntimeError("wheel missing unique distribution METADATA")
        assert_metadata(archive.read(dist_info[0]), "wheel")
        verify({n: archive.read(n) for n in archive.namelist() if
                n.startswith("hass_configurator/vendor/") or
                n == "hass_configurator/_version.py" or
                n in {"hass_configurator/" + filename for filename in (set(PACKAGE_ASSETS) | {"dev.html"})}},
               "wheel")
    with tarfile.open(sdists[0], "r:gz") as archive:
        files = {}
        top_metadata = [
            member for member in archive.getmembers()
            if member.isfile() and member.name.count("/") == 1
            and member.name.endswith("/PKG-INFO")
        ]
        if len(top_metadata) != 1:
            raise RuntimeError("sdist missing unique root PKG-INFO")
        assert_metadata(archive.extractfile(top_metadata[0]).read(), "sdist")
        for member in archive.getmembers():
            if not member.isfile() or "hass_configurator/" not in member.name:
                continue
            path = member.name[member.name.index("hass_configurator/"):]
            if path.startswith("hass_configurator/vendor/") or path == "hass_configurator/_version.py" or path in {
                    "hass_configurator/" + name for name in (set(PACKAGE_ASSETS) | {"dev.html"})}:
                files[path] = archive.extractfile(member).read()
        verify(files, "sdist")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_offline_artifacts.py WHEEL_DIR SDIST_DIR")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
