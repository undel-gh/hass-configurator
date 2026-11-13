#!/usr/bin/env python3
"""Bounded, nonsecret layer-diff diagnostics for disposable Docker images.

Read ordinary docker-save image tar archives; never dump file contents.
Do not run against images containing real credentials/user files.
"""
import hashlib
import json
import sys
import tarfile


def inspect_layers(path):
    outer = tarfile.open(path, mode="r:")
    try:
        manifest = json.load(outer.extractfile("manifest.json"))[0]
        return outer, manifest["Layers"]
    except Exception:
        outer.close()
        raise


def inventory(outer, layer_path):
    data = outer.extractfile(layer_path)
    result = {}
    with tarfile.open(fileobj=data, mode="r|*") as layer:
        for member in layer:
            metadata = (
                member.size, member.mtime, member.mode, member.uid, member.gid,
                member.uname, member.gname, member.linkname, member.type,
                tuple(sorted(member.pax_headers.items())),
            )
            digest = ""
            if member.isfile():
                content = layer.extractfile(member)
                hasher = hashlib.sha256()
                while True:
                    chunk = content.read(1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
                digest = hasher.hexdigest()
            result[member.name] = (metadata, digest)
    return result


def main(first, second):
    a, alayers = inspect_layers(first)
    b, blayers = inspect_layers(second)
    try:
        if len(alayers) != len(blayers):
            print("Layer count differs:", len(alayers), len(blayers))
        for index, (left, right) in enumerate(zip(alayers, blayers)):
            # Do not assume identical layer archive paths imply identical
            # bytes: real docker save paths are content-addressed, but an
            # intentionally malformed/constructed archive could reuse names.
            la = inventory(a, left)
            lb = inventory(b, right)
            changed = [p for p in sorted(set(la) | set(lb))
                       if la.get(p) != lb.get(p)]
            altered = sum(la.get(p, ((), None))[1] !=
                          lb.get(p, ((), None))[1] for p in changed)
            print("Layer %d: %d changed paths; %d changed contents" %
                  (index, len(changed), altered))
            for p in changed[:12]:
                lv, rv = la.get(p), lb.get(p)
                if lv is None or rv is None:
                    print("  %r: only in %s" % (p, "B" if lv is None else "A"))
                else:
                    print("  %r: same_bytes=%s A=%r B=%r" %
                          (p, lv[1] == rv[1], lv[0], rv[0]))
            if len(changed) > 12:
                print("  ... %d more paths" % (len(changed) - 12))
    finally:
        a.close()
        b.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: diagnose_docker_layers.py A.tar B.tar")
    main(sys.argv[1], sys.argv[2])
