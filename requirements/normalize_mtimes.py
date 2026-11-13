#!/usr/bin/env python3
"""Normalize only newly built/installed release artifacts to SOURCE_DATE_EPOCH.

This script is copied into intermediate Docker stages, not installed as app
code. Its input epoch is the exact reviewed commit timestamp used by CI.
No dependencies or network access.
"""
import argparse
import importlib.metadata
import os
from pathlib import Path
import re
import sys


def apply_epoch(path, epoch):
    if path.exists() or path.is_symlink():
        os.utime(path, ns=(epoch * 1_000_000_000,) * 2,
                 follow_symlinks=False)


def normalize_tree(root, epoch):
    root = Path(root)
    if not root.is_dir():
        raise ValueError("Missing reproducible build artifact directory")
    for item in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        apply_epoch(item, epoch)
    apply_epoch(root, epoch)


def normalize_installed(lock, epoch):
    """Touch only files belonging to explicitly locked installed packages."""
    prefix = Path(sys.prefix).resolve()
    names = []
    for line in Path(lock).read_text("utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==", line.strip())
        if match:
            names.append(match.group(1))
    if not names:
        raise ValueError("Empty installed-distribution lock")
    touched = set()
    for name in names + ["hass-configurator"]:
        dist = importlib.metadata.distribution(name)
        if not dist.files:
            raise ValueError("Missing installed RECORD for " + name)
        for relative in dist.files:
            item = Path(dist.locate_file(relative)).absolute()
            if not item.is_relative_to(prefix) or not item.exists():
                raise ValueError("Installed package path missing/escaped prefix: " +
                                 str(item))
            touched.add(item)
            parent = item.parent
            while parent != prefix and parent.is_relative_to(prefix):
                touched.add(parent)
                parent = parent.parent
    for item in sorted(touched, key=lambda p: len(p.parts), reverse=True):
        apply_epoch(item, epoch)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epoch", type=int, required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--tree", type=Path)
    choice.add_argument("--installed", type=Path, metavar="LOCK")
    args = parser.parse_args()
    if not 315532800 <= args.epoch <= 4102444800:
        raise ValueError("SOURCE_DATE_EPOCH outside supported ZIP datetime range")
    if args.tree:
        normalize_tree(args.tree, args.epoch)
    else:
        normalize_installed(args.installed, args.epoch)


if __name__ == "__main__":
    main()
