#!/usr/bin/env python3
"""Check disposable docker-save layers for excluded Ace files/identical bytes."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

try:
    from .ace_worker_profile import LOCK, read_profile
except ImportError:
    from ace_worker_profile import LOCK, read_profile


def inspect(path, excluded_hashes):
    hits = []
    count = 0
    with tarfile.open(path, "r:") as outer:
        manifest = json.load(outer.extractfile("manifest.json"))
        if len(manifest) != 1:
            raise ValueError("Expected one disposable image")
        for index, name in enumerate(manifest[0]["Layers"]):
            with tarfile.open(fileobj=outer.extractfile(name), mode="r|*") as layer:
                for member in layer:
                    basename = PurePosixPath(member.name).name
                    if basename in excluded_hashes:
                        hits.append({"layer": index, "path": member.name, "reason": "excluded filename"})
                    # Look for byte-identical renamed JS payloads by digest as
                    # well. No raw content is emitted, and no extraction occurs.
                    if member.isfile() and member.name.endswith(".js"):
                        count += 1
                        digest = hashlib.sha256()
                        raw = layer.extractfile(member)
                        for chunk in iter(lambda: raw.read(1024 * 1024), b""):
                            digest.update(chunk)
                        if digest.hexdigest() in excluded_hashes.values():
                            hits.append({"layer": index, "path": member.name, "reason": "excluded payload digest"})
    return {"layers": len(manifest[0]["Layers"]), "js_members_hashed": count, "hits": hits}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("image", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    lock = json.loads(LOCK.read_text("utf-8"))
    profile = read_profile()
    excluded = {name: lock["files_sha256"][name]
                for name in profile["excluded"] + profile["excluded_themes"]}
    report = inspect(args.image, excluded)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["hits"]:
        raise ValueError("Excluded Ace payload present in a distributable layer")
    print("Excluded Ace layer check passed:", report)


if __name__ == "__main__":
    main()
