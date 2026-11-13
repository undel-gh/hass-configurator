#!/usr/bin/env python3
"""Validate that wheel/sdist contain the exact committed offline assets."""
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "hass_configurator/vendor/manifest.json").read_text("utf8"))


def verify(files, label):
    required = MANIFEST["resources"]
    missing = []
    different = []
    for name, expected in required.items():
        archive_path = "hass_configurator/" + name
        if archive_path not in files:
            missing.append(archive_path)
        elif hashlib.sha256(files[archive_path]).hexdigest() != expected:
            different.append(archive_path)
    if missing or different:
        raise RuntimeError("%s incomplete/corrupted vendor files: missing=%s changed=%s" %
                           (label, missing[:5], different[:5]))
    extra_manifest = files.get("hass_configurator/vendor/manifest.json")
    if extra_manifest is None:
        raise RuntimeError("%s missing the vendor integrity manifest" % label)
    if json.loads(extra_manifest)["resources"] != required:
        raise RuntimeError("%s embedded manifest differs from source" % label)
    print("%s: %d resources and manifest validated" % (label, len(required)))


def main(wheel_dir, sdist_dir):
    wheels = list(wheel_dir.glob("*.whl"))
    sdists = list(sdist_dir.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError("Expected exactly one wheel and one sdist")
    with zipfile.ZipFile(wheels[0]) as archive:
        verify({n: archive.read(n) for n in archive.namelist() if
                n.startswith("hass_configurator/vendor/")}, "wheel")
    with tarfile.open(sdists[0], "r:gz") as archive:
        files = {}
        for member in archive.getmembers():
            if not member.isfile() or "hass_configurator/vendor/" not in member.name:
                continue
            path = member.name[member.name.index("hass_configurator/vendor/"):]
            files[path] = archive.extractfile(member).read()
        verify(files, "sdist")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: check_offline_artifacts.py WHEEL_DIR SDIST_DIR")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
