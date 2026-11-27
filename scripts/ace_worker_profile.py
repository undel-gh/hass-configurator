"""Read the single #37 worker profile from the first-party bootstrap.

Phase 1 validates the proposed subset against the complete upstream lock.
The installed manifest still describes the full family until physical pruning.
"""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "hass_configurator/ace-bootstrap.js"
LOCK = ROOT / "docs/ace-builds-1.45.2-lock.json"


def read_profile(path=BOOTSTRAP):
    source = path.read_text("utf-8")
    matches = re.findall(
        r"/\* HC_WORKER_PROFILE_BEGIN \*/\s*(.*?)\s*/\* HC_WORKER_PROFILE_END \*/",
        source, re.S)
    if len(matches) != 1:
        raise ValueError("Expected exactly one Ace worker profile")
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("Duplicate profile key: " + key)
            obj[key] = value
        return obj
    return json.loads(matches[0], object_pairs_hook=unique)


def selected_family(profile, lock):
    """Check exact partition of upstream workers; preserve all non-workers."""
    if set(profile) != {"schema", "ace_version", "infrastructure", "languages", "excluded"}:
        raise ValueError("Unexpected worker profile fields")
    if profile["schema"] != 1 or profile["ace_version"] != lock["version"]:
        raise ValueError("Worker profile version mismatch")
    if profile["infrastructure"] != ["worker-base.js"]:
        raise ValueError("Unexpected worker infrastructure")
    kept = list(profile["infrastructure"])
    for mode, entry in profile["languages"].items():
        if not re.fullmatch(r"ace/mode/[a-z]+", mode) or set(entry) != {"module", "file", "class"}:
            raise ValueError("Invalid worker language entry")
        suffix = mode.rsplit("/", 1)[1]
        if (entry["module"] != mode + "_worker" or entry["file"] != "worker-" + suffix + ".js"
                or not re.fullmatch(r"[A-Za-z]+", entry["class"])):
            raise ValueError("Invalid worker module mapping: " + mode)
        kept.append(entry["file"])
    excluded = profile["excluded"]
    workers = {name for name in lock["files_sha256"] if name.startswith("worker-")}
    if (len(set(kept)) != len(kept) or len(set(excluded)) != len(excluded)
            or set(kept) & set(excluded) or set(kept) | set(excluded) != workers
            or workers != set(lock["worker_files"])):
        raise ValueError("Worker profile does not exactly partition upstream family")
    return {name: digest for name, digest in lock["files_sha256"].items()
            if name not in excluded}


def main():
    profile = read_profile()
    lock = json.loads(LOCK.read_text("utf-8"))
    selected = selected_family(profile, lock)
    print(json.dumps({"status": "target-profile-only", "upstream_family": len(lock["files_sha256"]),
                      "target_family": len(selected), "excluded": profile["excluded"],
                      "target_workers": sorted(name for name in selected if name.startswith("worker-"))},
                     indent=2))


if __name__ == "__main__":
    main()
