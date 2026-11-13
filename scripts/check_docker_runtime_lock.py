#!/usr/bin/env python3
"""Release gate: pinned dependency closure and exact local wheel bytes.

Usage:
    python scripts/check_docker_runtime_lock.py --lock requirements/docker-runtime.lock
    python scripts/check_docker_runtime_lock.py --lock ... --wheelhouse /tmp/wheels
    python scripts/check_docker_runtime_lock.py --lock ... --installed

No external network calls or non-standard Python dependencies.
"""
import argparse
import ast
from email.parser import BytesParser
import hashlib
import importlib.metadata
from pathlib import Path
import re
import zipfile

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "requirements" / "docker-runtime.lock"
PIN = re.compile(
    r"^([A-Za-z0-9_.-]+)==([0-9][A-Za-z0-9.+_-]*) "
    r"--hash=sha256:([a-f0-9]{64})$"
)


def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def read_lock(path=LOCK):
    """Reject placeholders, mutable ranges, extra pip flags and repeated pins."""
    entries = {}
    has_binary_only = False
    for line_no, raw in enumerate(Path(path).read_text("utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "--only-binary=:all:" and not has_binary_only:
            has_binary_only = True
            continue
        match = PIN.fullmatch(line)
        if not match:
            raise ValueError("Bad dependency hash lock syntax on line %d" % line_no)
        name, version, digest = match.groups()
        key = normalize(name)
        if key in entries:
            raise ValueError("Duplicate locked distribution: " + key)
        entries[key] = (version, digest)
    if not entries or not has_binary_only:
        raise ValueError("Lock must contain binary-only complete distribution pins")
    return entries


def direct_dependencies_from_setup(path=None):
    """Parse metadata rather than executing setup.py in a test."""
    path = path or REPO / "setup.py"
    tree = ast.parse(Path(path).read_text("utf-8"))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and
             isinstance(node.func, ast.Name) and node.func.id == "setup"]
    if len(calls) != 1:
        raise ValueError("Expected one setup() call")
    values = [kw.value for kw in calls[0].keywords if kw.arg == "install_requires"]
    if len(values) != 1:
        raise ValueError("Missing install_requires in setup metadata")
    direct = ast.literal_eval(values[0])
    return {normalize(re.match(r"^[A-Za-z0-9_.-]+", req).group(0))
            for req in direct}


def validate_lock(path=LOCK):
    locked = read_lock(path)
    direct = direct_dependencies_from_setup()
    missing = direct - set(locked)
    if missing:
        raise ValueError("Direct package dependencies missing from hash lock: " +
                         ", ".join(sorted(missing)))
    return locked


def verify_wheelhouse(folder, locked):
    """Only an exact set of reviewed wheels is allowed; verify SHA and metadata."""
    wheel_paths = sorted(Path(folder).iterdir())
    if any(not p.is_file() or p.suffix != ".whl" for p in wheel_paths):
        raise ValueError("Wheelhouse contains an unexpected non-wheel artifact")
    seen = set()
    for wheel in wheel_paths:
        pieces = wheel.name[:-4].split("-")
        if len(pieces) != 5 or pieces[-3:] != ["py3", "none", "any"]:
            raise ValueError("Expected reviewed py3-none-any wheel: " + wheel.name)
        key, version = normalize(pieces[0]), pieces[1]
        if key not in locked or key in seen or locked[key][0] != version:
            raise ValueError("Unexpected distribution/version/duplicate: " + wheel.name)
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        if digest != locked[key][1]:
            raise ValueError("SHA-256 wheel digest mismatch: " + wheel.name)
        with zipfile.ZipFile(wheel) as archive:
            paths = [p for p in archive.namelist()
                     if p.endswith(".dist-info/METADATA")]
            if len(paths) != 1:
                raise ValueError("Missing unique wheel METADATA: " + wheel.name)
            meta = BytesParser().parsebytes(archive.read(paths[0]))
            if normalize(meta.get("Name", "")) != key or meta.get("Version") != version:
                raise ValueError("Wheel METADATA identity does not match pin: " +
                                 wheel.name)
        seen.add(key)
    if seen != set(locked):
        raise ValueError("Incomplete wheel closure: missing " +
                         ", ".join(sorted(set(locked) - seen)))
    return seen


def verify_installed(locked):
    """Check exact versions in the final, network-disconnected runtime."""
    for name, (expected, _) in sorted(locked.items()):
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as exc:
            raise ValueError("Missing locked installed dependency: " + name) from exc
        if installed != expected:
            raise ValueError("Installed dependency %s: expected %s got %s" %
                             (name, expected, installed))
    return set(locked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=LOCK)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    locked = validate_lock(args.lock)
    if args.wheelhouse:
        verify_wheelhouse(args.wheelhouse, locked)
    if args.installed:
        verify_installed(locked)
    print("Verified %d pinned direct/transitive distributions and SHA256 lock" %
          len(locked))


if __name__ == "__main__":
    main()
