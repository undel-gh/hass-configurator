#!/usr/bin/env python3
"""Assemble an isolated local Home Assistant OS Ingress test app from this checkout.

No credentials or local HA config are copied, no network is accessed, and an
existing destination is NEVER overwritten. Output is installed manually on a
test HA OS system into its local apps directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "hass_configurator"
TEMPLATES = REPO / "haos-fixture"
REQUIRED_FIRST_PARTY = (
    "dev.html", "jquery-3.6.0.min.js", "js-yaml.min.js",
    "materialize.min.js", "style.css", "material-icons.fallback.css",
    "flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2",
)


def verify_checkout():
    manifest = json.loads((PACKAGE / "vendor" / "manifest.json").read_text("utf8"))
    if manifest["schema"] != 1 or len(manifest["resources"]) < 460:
        raise ValueError("Incomplete offline vendor manifest")
    for name, sha in manifest["resources"].items():
        item = PACKAGE / name
        if not item.is_file() or item.is_symlink():
            raise ValueError("Unsafe or missing vendor asset: " + name)
        if hashlib.sha256(item.read_bytes()).hexdigest() != sha:
            raise ValueError("Vendor hash mismatch: " + name)
    for name in REQUIRED_FIRST_PARTY:
        if not (PACKAGE / name).is_file():
            raise ValueError("Missing first-party app asset: " + name)
    for item in PACKAGE.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlink in source package: " + str(item))
    return manifest


def build(destination):
    manifest = verify_checkout()
    target = Path(destination).expanduser().resolve()
    if target.exists() and any(target.iterdir()):
        raise ValueError("Refusing to overwrite nonempty fixture directory: " + str(target))
    target.mkdir(parents=True, exist_ok=True)
    try:
        for source, dest in (
            ("config.yaml.template", "config.yaml"), ("Dockerfile", "Dockerfile"),
            ("nginx.conf", "nginx.conf"), ("run.sh", "run.sh"),
        ):
            shutil.copyfile(TEMPLATES / source, target / dest)
        (target / "run.sh").chmod(0o755)
        src = target / "app"
        src.mkdir()
        shutil.copy2(REPO / "setup.py", src / "setup.py")
        shutil.copy2(REPO / "MANIFEST.in", src / "MANIFEST.in")
        shutil.copytree(
            PACKAGE, src / "hass_configurator",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        (target / ".dockerignore").write_text(
            ".git\n__pycache__\n*.pyc\n*.pyo\n", encoding="utf8")
        commit = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=REPO,
            capture_output=True, text=True, check=False,
        )
        metadata = {
            "source_commit": commit.stdout.strip() if commit.returncode == 0 else "unknown",
            "vendor_resource_count": len(manifest["resources"]),
            "vendor_manifest_sha256": hashlib.sha256(
                (PACKAGE / "vendor" / "manifest.json").read_bytes()).hexdigest(),
            "workspace_inside_container": "/data/hc-ingress-validation",
            "external_host_ports": False,
            "home_assistant_api": False,
            "fixture_only": True,
        }
        (target / "fixture-provenance.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf8")
        return metadata
    except Exception:
        # Do not leave half-constructed app directories that Supervisor might
        # accidentally pick up as usable apps.
        shutil.rmtree(target)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="Empty destination e.g. /addons/hc_ingress_validation")
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))


if __name__ == "__main__":
    main()
