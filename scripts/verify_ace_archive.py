#!/usr/bin/env python3
"""Inspect a pinned Ace npm tarball; no silent build-family mixing.

Called in CI using `npm pack ace-builds@1.9.6`. Outputs a lock candidate
as JSON between markers for review/commit. Does not vendor the package.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "runtime-dependencies.json"
BUILD = "package/src-min-noconflict/"


def inspect(tarball):
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    required = {
        "ace.js", "ext-modelist.js", "ext-language_tools.js",
    }
    required.update("mode-%s.js" % n for n in inventory["ace"]["language_modes_offered"])
    required.update("theme-%s.js" % n for n in inventory["ace"]["themes_offered"])
    required.update(("keybinding-vim.js", "keybinding-emacs.js"))
    digest = hashlib.sha256(tarball.read_bytes()).hexdigest()
    with tarfile.open(tarball, "r:gz") as archive:
        members = {
            n.name[len(BUILD):]: n for n in archive.getmembers()
            if n.isfile() and n.name.startswith(BUILD)
        }
        missing = sorted(required.difference(members))
        # All files in the build family are fingerprinted. The next step
        # can vendor the required subset plus verified transitive deps.
        hashes = {}
        for name in sorted(members):
            data = archive.extractfile(members[name]).read()
            hashes[name] = hashlib.sha256(data).hexdigest()
    return {
        "name": "ace-builds", "version": "1.9.6",
        "tarball": "https://registry.npmjs.org/ace-builds/-/ace-builds-1.9.6.tgz",
        "sha256": digest, "family": "src-min-noconflict",
        "required_files_checked": len(required), "family_files": len(members),
        "missing_required_files": missing,
        "worker_files": sorted(k for k in members if k.startswith("worker-")),
        "files_sha256": hashes,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("tarball", type=Path)
    args = p.parse_args()
    report = inspect(args.tarball)
    print("ACE_LOCK_CANDIDATE_BEGIN")
    print(json.dumps(report, indent=2, sort_keys=True))
    print("ACE_LOCK_CANDIDATE_END")
    # Commit-based supply-chain lock makes upstream tarball changes visible.
    lock = json.loads((ROOT / "docs" / "ace-builds-1.9.6-lock.json")
                      .read_text(encoding="utf-8"))
    for key in ("sha256", "family", "worker_files", "files_sha256"):
        if lock[key] != report[key]:
            print("Pinned Ace archive mismatch: " + key, file=sys.stderr)
            return 1
    import base64
    payload = args.tarball.read_bytes()
    computed_integrity = "sha512-" + base64.b64encode(
        hashlib.sha512(payload).digest()).decode("ascii")
    if computed_integrity != lock["npm_integrity"]:
        print("npm SRI mismatch", file=sys.stderr)
        return 1

    # Three obsolete mode selectors were removed from dev.html as part of #3.
    # The archive remains bit-for-bit the same; every currently offered mode
    # now has a matching module in the pinned build.
    if report["missing_required_files"]:
        print("Current UI requests missing Ace modules: " +
              ", ".join(report["missing_required_files"]), file=sys.stderr)
        return 1
    print("Pinned Ace archive verified: %d files, all %d offered modules present." %
          (len(report["files_sha256"]), report["required_files_checked"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
