#!/usr/bin/env python3
"""Assemble an isolated local Home Assistant OS Ingress test app from this checkout.

No credentials or local HA config are copied, no network is accessed, and an
existing destination is NEVER overwritten. Output is installed manually on a
test HA OS system into its local apps directory.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "hass_configurator"
TEMPLATES = REPO / "haos-fixture"
REQUIRED_FIRST_PARTY = (
    "dev.html", "ace-bootstrap.js", "ui-handlers.js",
    "jquery-3.6.0.min.js", "js-yaml.min.js",
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


def build(destination, *, with_ha_api_probe=False,
          fixture_version="0.0.1", cache_revision=None):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", fixture_version):
        raise ValueError("Invalid test fixture version")
    if cache_revision is not None and not re.fullmatch(
            r"[A-Za-z0-9_-]{1,24}", cache_revision):
        raise ValueError("Invalid test cache revision")
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
        config_path = target / "config.yaml"
        config = config_path.read_text(encoding="utf8")
        config = config.replace('version: "0.0.1"',
                                'version: "%s"' % fixture_version, 1)
        if with_ha_api_probe:
            config += "\nhomeassistant_api: true\n"
        config_path.write_text(config, encoding="utf8")
        # A dedicated deliberate opt-in is required because this Supervisor
        # permission grants an app administrator-level Home Assistant access.
        (target / "ha-api-mode").write_text(
            "enabled\n" if with_ha_api_probe else "disabled\n",
            encoding="ascii")
        shutil.copyfile(REPO / "scripts" / "haos_local_api_probe.py",
                        target / "haos_local_api_probe.py")
        src = target / "app"
        src.mkdir()
        shutil.copy2(REPO / "setup.py", src / "setup.py")
        shutil.copy2(REPO / "MANIFEST.in", src / "MANIFEST.in")
        shutil.copytree(
            PACKAGE, src / "hass_configurator",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        if cache_revision is not None:
            # Test-only CSS comment intentionally changes the immutable
            # content digest while leaving the vendored manifest untouched.
            # Never modify the source checkout or real user's HA files.
            stylesheet = src / "hass_configurator" / "style.css"
            with stylesheet.open("a", encoding="utf8") as stream:
                stream.write("\n/* HAOS_TEST_CACHE_REVISION:%s */\n"
                             % cache_revision)
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
            "home_assistant_api": with_ha_api_probe,
            "read_only_supervisor_probe": with_ha_api_probe,
            "fixture_version": fixture_version,
            "test_cache_revision": cache_revision,
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
    parser.add_argument("--fixture-version", default="0.0.1",
                        help="Local app version for explicit HAOS-12 update test")
    parser.add_argument("--cache-revision",
                        help="Test-only CSS digest marker, e.g. A or B")
    parser.add_argument(
        "--with-ha-api-probe", action="store_true",
        help="DANGEROUS: enable admin-scope Home Assistant API permission for "
             "read-only REST/WS probe; isolated test device only")
    args = parser.parse_args()
    print(json.dumps(build(
        args.output, with_ha_api_probe=args.with_ha_api_probe,
        fixture_version=args.fixture_version, cache_revision=args.cache_revision),
        indent=2))


if __name__ == "__main__":
    main()
