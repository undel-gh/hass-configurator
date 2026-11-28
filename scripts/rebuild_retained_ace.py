#!/usr/bin/env python3
"""Disposable upstream worker reproduction, never a runtime promotion.

Materialize only the candidate archives and explicit build-tool closure, at
the original lock paths. No npm install or lifecycle scripts. Execute the
pinned upstream build and CSS data generator in the disposable checkout.
Archive/member identity and actual output equality are separate evidence.
"""
import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import tarfile
from urllib.parse import quote

try:
    from .attribute_ace_workers import (SOURCE_COMMIT, LOCK_BLOB, LINTER_SHA256,
        LINTER_SRI, LINTER_URL, sources, fetch, require, sha, sri, exact_member,
        git_blob_sha1)
    from .audit_supply_chain import read_file
except ImportError:
    from attribute_ace_workers import (SOURCE_COMMIT, LOCK_BLOB, LINTER_SHA256,
        LINTER_SRI, LINTER_URL, sources, fetch, require, sha, sri, exact_member,
        git_blob_sha1)
    from audit_supply_chain import read_file

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = "packages/ace-legacy-linters"
BUILD_BLOB = "f052326468c9ad723174aea0153ef8f6d9de5fd3"
GENERATOR_BLOB = "864a62977458ca8a35909345073fcca213d1d615"
WORKERS = ("worker-css.js", "worker-html.js", "worker-javascript.js",
           "worker-json.js", "worker-yaml.js")
TOOLS = (
    "node_modules/esbuild",
    "node_modules/esbuild/node_modules/@esbuild/linux-x64",
    "node_modules/terser",
    "node_modules/@jridgewell/source-map",
    "node_modules/acorn", "node_modules/commander", "node_modules/source-map-support",
    "node_modules/@jridgewell/gen-mapping", "node_modules/@jridgewell/trace-mapping",
    "node_modules/buffer-from", "node_modules/source-map",
    "node_modules/@jridgewell/set-array", "node_modules/@jridgewell/sourcemap-codec",
    "node_modules/@jridgewell/resolve-uri",
    "node_modules/path-browserify",  # upstream YAML alias, may be tree-shaken
)
EXTRA_PINS = {
    "esrecurse": ("4.3.0", "3ecf9370d7296b47b570c88a11f70b35bb965af8d536536b259eb55f9b793b61",
                 "sha512-KmfKL3b6G+RXvP8N1vr3Tq1kL/oCFgn2NYXEtqP8/L3pKapUA4G8cFVaoF3SU323CD4XypR/ffioHmkti6/Tag=="),
    "@vscode/l10n": ("0.0.18", "f1c2dc897488595f6bb42121869f525c6c6a5f7c8dca550754199c3251ed7c5c",
                    "sha512-KYSIHVmslkaCDyw013pphY+d7x1qV8IZupYfeIfzNA+nsaWHbn5uPuQRvdRFsa9zFzGeudPuoGoZ1Op4jrJXIQ=="),
}


# Exact relations independently checked against the published Git build bytes
# and research #1 artifact 15202630304. No general whitespace normalization.
UNMINIFIED_PINS = {
    "worker-css.js": [
        "d763c653af477e96c3548c13ef73d30867db0c72c7714b38918177eb422da830",
        "745cacd12eb24bbd796e0c51da2f7fa8c31493aafa292bfde3aa6849311b88b5"
    ],
    "worker-html.js": [
        "3b355e152ed4376a15e70118b5e1084808cbb89a1c18c10362e974ddfd5e71cf",
        "0452c723bf6897f22ccbe88ba87436c148708136add80c0c99d9f4af3e45e494"
    ],
    "worker-javascript.js": [
        "d5cc296f0965881dd92a9de86423201bc8e0fb0ff4d516055935a72c4d9e46ec",
        "3bd94888ddff72db9fc946ec82d93ca8c2a208757a3b641bd1d8a6a43d35a233"
    ],
    "worker-json.js": [
        "291e9a2d6ecd52e3327f871df93a0d1eabc79bac05dc1185f0a02c5ad373e829",
        "929a25f12f918630b88f17af09aa2c7b8b11022be1cb5ab9666ba8cdd346acf5"
    ],
    "worker-yaml.js": [
        "a214479de0bd5adb6fa80992c120a7cb36610baa61c53e958ffc792bb58e4616",
        "cde46e4d22cbb176880858b0c05e0ef82e16e999c69f6ef56b4e5e932196c0bd"
    ]
}
# Three build-only inputs lacking SRI in upstream source lock: observed
# registry archives from inspected research #1, now pinned for repeatability.
TOOL_OBSERVED_PINS = {
    "path-browserify": ("1.0.1", "74ad6965c6f8cb61d17b1798d48095c3238eca5707b517640a12150f17b8f93d",
                       "sha512-b7uo2UCUOYZcnF/3ID0lulOJi/bafxa1xPe7ZPsammBSpjSWQkjNxlt635YGS2MiR9GjvuXCtz2emr3jbsz98g=="),
    "source-map": ("0.6.1", "bdbca10d17ff5a5802d5acfc7b2f22f9f9bf587632a95650d3c5f513c7092b86",
                   "sha512-UjgapumWlbMhkBgzT7Ykc5YXUT46F0iKu8SGXq0bcwP5dz/h0Plj6enJqjz1Zbq2l5WaqYnrVbwWOWMyF3F47g=="),
    "@jridgewell/resolve-uri": ("3.1.0", "fe4cb2ab38b4813b27926d9e08852ad81d8c14d0034cfa4a23555ec134ee16b0",
                               "sha512-F2msla3tad+Mfht5cJq7LSXcdudKTWCVYUgw6pLFOOHSTtZlj6SWNYAp+AhuqLmWdBO2X5hPrLcu8cVP8fy28w=="),
}


def candidate_pins():
    records = json.loads((ROOT / "hass_configurator/third_party/embedded.json").read_text("utf-8"))
    pins = dict(EXTRA_PINS)
    for row in records["notices"].values():
        if row["kind"] == "npm-archive-member":
            pin = (row["version"], row["archive_sha256"], row["npm_integrity"])
            require(row["name"] not in pins or pins[row["name"]] == pin,
                    "Conflicting archive pins: " + row["name"])
            pins[row["name"]] = pin
    return pins


def materialize(raw, dest, name, version):
    """Extract only canonical regular members, with bounded sizes, no links."""
    require(not dest.exists(), "Rebuild package directory already exists: " + str(dest))
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        manifest = json.loads(exact_member(archive, "package/package.json"))
        require((manifest.get("name"), manifest.get("version")) == (name, version),
                "Rebuild package identity mismatch: " + name)
        entries = archive.getmembers()
        require(len(entries) <= 25000 and sum(m.size for m in entries) <= 160 * 1024 * 1024,
                "Oversize rebuild archive")
        seen = set()
        for member in entries:
            if member.name == "package" and member.isdir():
                continue
            path = PurePosixPath(member.name)
            require(member.name.startswith("package/") and path.as_posix() == member.name
                    and ".." not in path.parts and "\\" not in member.name and ":" not in member.name
                    and (member.isfile() or member.isdir()) and member.name not in seen,
                    "Unsafe or duplicate rebuild member: " + member.name)
            seen.add(member.name)
            if member.isdir():
                continue
            relative = path.relative_to("package").as_posix()
            data = archive.extractfile(member).read()
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            require(not target.exists(), "Rebuild member collision: " + relative)
            target.write_bytes(data)
            target.chmod(0o755 if member.mode & 0o111 else 0o644)
            files[relative] = sha(data)
    return files


def relation(actual, expected):
    first = next((i for i, (a, b) in enumerate(zip(actual, expected)) if a != b), None)
    if first is None and len(actual) != len(expected):
        first = min(len(actual), len(expected))
    return {"equal": actual == expected, "actual_sha256": sha(actual),
            "published_sha256": sha(expected), "actual_size": len(actual),
            "published_size": len(expected), "first_difference": first}


def unminified_relation(actual, published, pins, expected_crlf=216):
    """Only the pinned mixed CRLF/LF published form may normalize to LF."""
    published_sha, normalized_sha = pins
    result = relation(actual, published)
    normalized = published.replace(b"\r\n", b"\n")
    if (sha(published) != published_sha or published.count(b"\r\n") != expected_crlf
            or b"\r" in normalized or sha(normalized) != normalized_sha):
        raise ValueError("Pinned unminified newline relation drift")
    result.update({"published_crlf_count": expected_crlf,
                   "normalized_published_sha256": sha(normalized),
                   "relation": "exact" if actual == published else
                   "crlf-to-lf-exact" if actual == normalized else "mismatch"})
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    source = args.source.resolve()
    pkg = source / WORKSPACE
    report_path = args.report.resolve()
    require(not source.is_relative_to(ROOT) and not ROOT.is_relative_to(source)
            and not report_path.is_relative_to(source), "Disposable source/evidence must be separate")
    report = {"status": "research-started", "source_checkout": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "upstream_source_commit": SOURCE_COMMIT, "source_lock_git_blob": LOCK_BLOB,
        "package_archives": [], "workers": [], "node": subprocess.check_output(
            ["node", "--version"], text=True).strip(), "platform": platform.platform(),
        "limitations": ["Research only; never replaces shipped JS.",
                        "Source-lock entries without SRI use reviewed archive pins or current registry integrity.",
                        "Exact reconstruction is stronger version evidence; not license or release signoff."]}
    def save():
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    save()
    try:
        require(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == SOURCE_COMMIT,
                "Wrong upstream checkout")
        require(not subprocess.check_output(["git", "status", "--porcelain"], cwd=source, text=True).strip(),
                "Upstream checkout is not clean")
        lock_raw = (source / "package-lock.json").read_bytes()
        require(git_blob_sha1(lock_raw) == LOCK_BLOB, "Source lock differs from pinned Git blob")
        packages = json.loads(lock_raw)["packages"]
        build_path = pkg / "build-worker.mjs"
        generator = pkg / "generate-css-diagnostics-data.js"
        require(git_blob_sha1(build_path.read_bytes()) == BUILD_BLOB
                and git_blob_sha1(generator.read_bytes()) == GENERATOR_BLOB, "Upstream builder drift")
        linter = fetch(LINTER_URL)
        require(sha(linter) == LINTER_SHA256 and sri(linter) == LINTER_SRI, "Linter archive drift")
        expected = {}
        selected = {}
        with tarfile.open(fileobj=io.BytesIO(linter), mode="r:gz") as archive:
            for worker in WORKERS:
                plain = exact_member(archive, "package/build/src-noconflict/" + worker)
                mini = exact_member(archive, "package/build/src-min-noconflict/" + worker)
                require(mini == read_file(ROOT / "hass_configurator", "vendor/ace/" + worker),
                        "Shipped worker differs from pinned linter archive")
                expected[worker] = (plain, mini)
                for row in sources(plain, packages):
                    require(row["source_lock_version"] is not None, "Unresolved source-lock candidate")
                    selected[row["lock_path"]] = row["name"]
        pins = candidate_pins()
        require(set(selected.values()) == set(pins), "Published candidate scope differs from reviewed pins")
        paths = {**selected, **{key: key.split("node_modules/")[-1] for key in TOOLS}}
        cache, hashes = {}, {}
        for key, name in sorted(paths.items(), key=lambda pair: (pair[0].count("/"), pair[0])):
            entry = packages[key]
            version = entry["version"]
            url = "https://registry.npmjs.org/" + name + "/-/" + name.split("/")[-1] + "-" + version + ".tgz"
            require(not entry.get("resolved") or entry["resolved"] == url, "Unexpected source-lock tarball")
            if (name, version) not in cache:
                meta = json.loads(fetch("https://registry.npmjs.org/" + quote(name, safe="") + "/" + version))
                require((meta.get("name"), meta.get("version")) == (name, version)
                        and meta["dist"]["tarball"] == url, "Registry package identity mismatch")
                raw = fetch(url)
                require(sri(raw) == meta["dist"]["integrity"], "Registry integrity mismatch")
                cache[name, version] = raw
            raw = cache[name, version]
            require(not entry.get("integrity") or sri(raw) == entry["integrity"], "Source-lock SRI mismatch")
            if key in selected:
                require(pins[name] == (version, sha(raw), sri(raw)), "Reviewed candidate archive mismatch")
            elif name in TOOL_OBSERVED_PINS:
                require(TOOL_OBSERVED_PINS[name] == (version, sha(raw), sri(raw)),
                        "Reviewed build-only archive mismatch")
            else:
                require(bool(entry.get("integrity")), "Unpinned build-tool archive")
            files = materialize(raw, source / key, name, version)
            hashes.update({key + "/" + path: digest for path, digest in files.items()})
            report["package_archives"].append({"lock_path": key, "name": name, "version": version,
                "archive_sha256": sha(raw), "npm_integrity": sri(raw), "source_lock_integrity_present": bool(entry.get("integrity")),
                "reviewed_candidate_pin": key in selected,
                "reviewed_build_only_pin": name in TOOL_OBSERVED_PINS and key not in selected,
                "files": len(files)})
        save()
        # Evidence-only instrumentation of the exact original script. Preserve
        # all output options and source inputs, generate only retained targets.
        script = build_path.read_text("utf-8")
        changes = {
            "sourcemap: false,": "sourcemap: false,\n        metafile: true,",
            "return result.outputFiles[0].text;": "await fs.writeFile(path.join(packageDir, workerConfig.fileName + '.meta.json'), JSON.stringify(result.metafile));\n    return result.outputFiles[0].text;",
            "for (const workerConfig of workerConfigs) {":
                "for (const workerConfig of workerConfigs.filter(x => " + json.dumps(list(WORKERS)) + ".includes(x.fileName))) {",
            "for (const target of outputTargets) {":
                "for (const target of outputTargets.filter(x => x.moduleFactory === 'ace.define')) {",
        }
        for old, new in changes.items():
            require(script.count(old) == 1, "Upstream builder instrumentation anchor drift")
            script = script.replace(old, new)
        instrumented = pkg / "hc-evidence-build.mjs"
        instrumented.write_text(script, encoding="utf-8")
        report["instrumented_builder_sha256"] = sha(instrumented.read_bytes())
        env = {**os.environ, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        for filename, label in ((generator, "css-data"), (instrumented, "build")):
            result = subprocess.run(["node", str(filename)], cwd=pkg, env=env,
                                    capture_output=True, text=True, timeout=180)
            report[label + "_log"] = (result.stdout + result.stderr)[-16000:]
            save()
            require(result.returncode == 0, "Upstream " + label + " failed")
        contributed = set()
        for worker in WORKERS:
            plain, mini = expected[worker]
            meta = json.loads((pkg / (worker + ".meta.json")).read_text("utf-8"))
            inputs = {}
            for output in meta["outputs"].values():
                for filename, row in output["inputs"].items():
                    if row["bytesInOutput"] <= 0:
                        continue
                    path = (pkg / filename).resolve()
                    require(path.is_relative_to(source), "Unexpected builder input outside source")
                    relative = path.relative_to(source).as_posix()
                    digest = sha(read_file(source, relative))
                    archived = relative in hashes
                    if archived:
                        require(hashes[relative] == digest, "Builder input differs from exact archive")
                    inputs[relative] = {"sha256": digest, "bytes_in_output": row["bytesInOutput"],
                                        "archive_member_verified": archived}
            # Native bootstrap and Ace modules are outside esbuild's metafile.
            additional = {}
            for filename in ("node_modules/ace-code/src/lib/oop.js",
                             "node_modules/ace-code/src/lib/event_emitter.js",
                             WORKSPACE + "/src/worker.js"):
                digest = sha(read_file(source, filename))
                if filename.startswith("node_modules/"):
                    require(hashes.get(filename) == digest, "Bootstrap module archive mismatch")
                additional[filename] = digest
            if worker == "worker-css.js":
                filename = "node_modules/vscode-css-languageservice/lib/esm/data/webCustomData.js"
                digest = sha(read_file(source, filename))
                require(hashes.get(filename) == digest, "CSS generator data archive mismatch")
                additional[filename] = digest
            # Bind each emitted dependency input to its deepest original
            # lock path, including both estraverse installations.
            contributors = {}
            for filename in inputs:
                if "/node_modules/" not in "/" + filename:
                    continue
                matched = max((key for key in paths if filename.startswith(key + "/")),
                              key=len, default=None)
                if matched is not None:
                    contributors[filename] = matched
                    contributed.add(matched)
            report["workers"].append({"worker": worker,
                "unminified": unminified_relation((pkg / "build/src-noconflict" / worker).read_bytes(),
                                                  plain, UNMINIFIED_PINS[worker]),
                "minified": relation((pkg / "build/src-min-noconflict" / worker).read_bytes(), mini),
                "contributing_inputs": inputs, "additional_inputs": additional,
                "contributing_lock_paths": sorted(set(contributors.values())),
                "unmapped_dependency_inputs": sorted(name for name in inputs
                    if "/node_modules/" in "/" + name and name not in contributors),
                "unverified_dependency_inputs": sorted(name for name, row in inputs.items()
                    if "/node_modules/" in "/" + name and not row["archive_member_verified"])})
        report["contributing_candidate_paths"] = sorted(contributed)
        report["missing_candidate_paths"] = sorted(set(selected) - contributed)
        report["unexpected_contributing_paths"] = sorted(contributed - set(selected))
        equal = all(w["unminified"]["relation"] in {"exact", "crlf-to-lf-exact"}
                    and w["minified"]["equal"] and not w["unverified_dependency_inputs"]
                    and not w["unmapped_dependency_inputs"] for w in report["workers"])
        equal = equal and contributed == set(selected)
        report["status"] = "exact-runtime-rebuild-match" if equal else "rebuild-differs"
        save()
        require(equal, "Rebuild differs; inspect actual report before attributing versions")
    except Exception as exc:
        if report["status"] == "research-started":
            report["status"] = "research-blocked"
        report["error"] = str(exc)
        save()
        raise


if __name__ == "__main__":
    main()
