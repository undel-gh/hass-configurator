#!/usr/bin/env python3
"""Validate that wheel/sdist contain the exact committed offline assets."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import zipfile

from hass_configurator.http_routing import PACKAGE_ASSETS

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "hass_configurator/vendor/manifest.json").read_text("utf8"))


def verify(files, label):
    required = dict(MANIFEST["resources"])
    # Bundle integrity is not complete if the six application-owned static
    # resources are missing, even when the third-party vendor tree is intact.
    for name in PACKAGE_ASSETS:
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
    extra_manifest = files.get("hass_configurator/vendor/manifest.json")
    if extra_manifest is None:
        raise RuntimeError("%s missing the vendor integrity manifest" % label)
    if json.loads(extra_manifest)["resources"] != MANIFEST["resources"]:
        raise RuntimeError("%s embedded manifest differs from source" % label)
    print("%s: %d vendor resources, %d first-party resources and manifest validated" %
          (label, len(MANIFEST["resources"]), len(PACKAGE_ASSETS)))


def main(wheel_dir, sdist_dir):
    wheels = list(wheel_dir.glob("*.whl"))
    sdists = list(sdist_dir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("Expected exactly one wheel and one sdist")
    with zipfile.ZipFile(wheels[0]) as archive:
        verify({n: archive.read(n) for n in archive.namelist() if
                n.startswith("hass_configurator/vendor/") or
                n in {"hass_configurator/" + filename for filename in PACKAGE_ASSETS}},
               "wheel")
    with tarfile.open(sdists[0], "r:gz") as archive:
        files = {}
        for member in archive.getmembers():
            if not member.isfile() or "hass_configurator/" not in member.name:
                continue
            path = member.name[member.name.index("hass_configurator/"):]
            if path.startswith("hass_configurator/vendor/") or path in {
                    "hass_configurator/" + name for name in PACKAGE_ASSETS}:
                files[path] = archive.extractfile(member).read()
        verify(files, "sdist")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_offline_artifacts.py WHEEL_DIR SDIST_DIR")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
