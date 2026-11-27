"""Read the single #37 curated Ace profile from the first-party bootstrap.

Validate the curated subset against the complete upstream lock.
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
    """Check upstream worker partition and explicit theme exclusions."""
    if set(profile) != {"schema", "ace_version", "infrastructure", "languages", "excluded", "excluded_themes", "excluded_snippets"}:
        raise ValueError("Unexpected worker profile fields")
    if profile["schema"] != 3 or profile["ace_version"] != lock["version"]:
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
    themes = profile["excluded_themes"]
    if (not isinstance(themes, list) or
            any(not isinstance(name, str) or not re.fullmatch(r"theme-[a-z0-9_]+\.js", name)
                or name not in lock["files_sha256"]
                or name in {"theme-monokai.js", "theme-chrome.js", "theme-textmate.js"}
                for name in themes) or len(set(themes)) != len(themes)):
        raise ValueError("Invalid curated theme exclusions")
    snippets = profile["excluded_snippets"]
    approved = ["snippets/abc.js","snippets/cedar.js","snippets/cedarschema.js","snippets/csound_document.js","snippets/csound_orchestra.js","snippets/drools.js","snippets/edifact.js","snippets/fsl.js","snippets/gobstones.js","snippets/jsoniq.js","snippets/lsl.js","snippets/maze.js","snippets/razor.js","snippets/velocity.js","snippets/wollok.js","snippets/xquery.js"]
    if snippets != approved or any(name not in lock["files_sha256"] for name in approved):
        raise ValueError("Invalid curated snippet exclusions")
    removed = set(excluded) | set(themes) | set(snippets)
    return {name: digest for name, digest in lock["files_sha256"].items()
            if name not in removed}


def validate_manifest(profile, lock, manifest):
    expected = {"vendor/ace/" + name: digest
                for name, digest in selected_family(profile, lock).items()}
    actual = {name: digest for name, digest in manifest["resources"].items()
              if name.startswith("vendor/ace/")}
    if actual != expected:
        raise ValueError("Curated Ace manifest differs from selected upstream subset")
    return expected


def verify_vendor_tree(root, resources):
    """Exact filesystem closure, including untracked files and symlinks."""
    vendor = root / "vendor"
    if vendor.is_symlink() or not vendor.is_dir():
        raise ValueError("Unsafe vendor directory")
    paths = set()
    for item in vendor.rglob("*"):
        if item.is_symlink() or (not item.is_dir() and not item.is_file()):
            raise ValueError("Unsafe vendor entry: " + str(item))
        if item.is_file():
            paths.add(item.relative_to(root).as_posix())
    if paths != set(resources) | {"vendor/manifest.json"}:
        raise ValueError("Untracked or absent vendor resource")


def main():
    profile = read_profile()
    lock = json.loads(LOCK.read_text("utf-8"))
    selected = selected_family(profile, lock)
    manifest = json.loads((ROOT / "hass_configurator/vendor/manifest.json").read_text("utf-8"))
    validate_manifest(profile, lock, manifest)
    verify_vendor_tree(ROOT / "hass_configurator", manifest["resources"])
    print(json.dumps({"status": "curated-profile-verified", "upstream_family": len(lock["files_sha256"]),
                      "target_family": len(selected), "excluded": profile["excluded"],
                      "excluded_themes": profile["excluded_themes"],
                      "excluded_snippets": profile["excluded_snippets"],
                      "target_workers": sorted(name for name in selected if name.startswith("worker-"))},
                     indent=2))


if __name__ == "__main__":
    main()
