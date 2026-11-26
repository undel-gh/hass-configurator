#!/usr/bin/env python3
"""Build-time supply-chain inventory. Never imported or called by the editor."""
import argparse
import base64
import datetime
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
from urllib.parse import quote
from urllib.request import Request, urlopen

try:
    from .check_docker_runtime_lock import read_lock, normalize
except ImportError:  # direct script execution
    from check_docker_runtime_lock import read_lock, normalize

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "hass_configurator"
NOTICE = "third_party/inventory.json"
EMBEDDED = "third_party/embedded.json"
MANIFEST = "vendor/manifest.json"
OSV = "https://api.osv.dev/v1/querybatch"


def load(path):
    return json.loads(path.read_text("utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_file(root, name):
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts or "\\" in name
            or ":" in name or path.as_posix() != name or not path.parts):
        raise ValueError("Invalid inventory path: " + name)
    target = root / name
    if not target.is_file() or any(p.is_symlink() for p in
            [target, *[root.joinpath(*path.parts[:i]) for i in range(1, len(path.parts))]]):
        raise ValueError("Missing or unsafe inventory file: " + name)
    return target.read_bytes()


def verify_file(root, name, expected):
    if not re.fullmatch("[0-9a-f]{64}", expected) or sha(read_file(root, name)) != expected:
        raise ValueError("Inventory SHA256 mismatch: " + name)


def immutable_raw_url(url):
    """Only exact public GitHub commit/blob evidence, never mutable tags."""
    match = re.fullmatch(
        r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/blob/"
        r"([0-9a-f]{40})/([A-Za-z0-9_.\-/]+)", url)
    if not match:
        raise ValueError("Non-immutable embedded evidence URL: " + url)
    owner, repo, commit, filename = match.groups()
    path = PurePosixPath(filename)
    if (owner in {".", ".."} or repo in {".", ".."} or path.is_absolute()
            or ".." in path.parts or path.as_posix() != filename):
        raise ValueError("Unsafe embedded evidence URL: " + url)
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{commit}/{filename}"


def check_git_pin(url, blob):
    immutable_raw_url(url)
    if not re.fullmatch("[0-9a-f]{40}", blob):
        raise ValueError("Invalid Git blob identity: " + url)


def git_blob_sha1(raw):
    # Git object identity, NOT a SHA-1 digest of bare bytes.
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def validate_embedded(root, inv, vendor, embedded, notice_paths):
    """Parent ownership remains exclusive; embedded code can share containers."""
    if embedded["schema"] != 1 or not embedded["components"]:
        raise ValueError("Missing embedded component inventory")
    parents = {c["id"]: set(component_files(c, vendor)) for c in inv["components"]}
    seen, used, mapped = set(), set(), set()
    for c in embedded["components"]:
        cid = c["id"]
        if not re.fullmatch("[a-z0-9-]+", cid) or cid in seen:
            raise ValueError("Duplicate or invalid embedded component ID: " + cid)
        seen.add(cid)
        if c["parent"] not in parents or c["kind"] not in {"library", "review"}:
            raise ValueError("Invalid embedded parent/kind: " + cid)
        if c["status"] not in {"identified", "partial", "restricted"} or not c["note"]:
            raise ValueError("Missing embedded disposition: " + cid)
        if c["kind"] == "review" and (c["status"] != "partial" or c["ecosystem"] is not None):
            raise ValueError("Unresolved review must not masquerade as a package: " + cid)
        if c["status"] in {"identified", "restricted"} and (not c["license"] or not c["notices"]):
            raise ValueError("Missing embedded license notice: " + cid)
        if c["ecosystem"] not in {None, "npm"} or (
                c["ecosystem"] is not None and (not c["version"] or c["kind"] != "library")):
            raise ValueError("Unsubstantiated embedded package identity: " + cid)
        if not c["name"] or not c["locations"] or not c["evidence"]:
            raise ValueError("Missing embedded evidence: " + cid)
        if len(c["notices"]) != len(set(c["notices"])) or not set(c["notices"]) <= notice_paths:
            raise ValueError("Unknown/duplicate embedded license notice: " + cid)
        used.update(c["notices"])
        for location in c["locations"]:
            name = location["file"]
            marker = location["marker"]
            if name not in parents[c["parent"]] or not marker:
                raise ValueError("Embedded container does not belong to parent: " + cid)
            if marker.encode("utf-8") not in read_file(root, name):
                raise ValueError("Embedded marker missing: " + cid + " / " + name)
            mapped.add(name)
        for evidence in c["evidence"]:
            check_git_pin(evidence["url"], evidence["git_blob"])
            if not evidence["marker"]:
                raise ValueError("Missing upstream marker: " + cid)
    workers = {name for name in vendor["resources"]
               if re.fullmatch(r"vendor/ace/worker-[^/]+\.js", name)}
    if set(embedded["worker_review"]) != workers:
        raise ValueError("Incomplete Ace worker review inventory")
    for name, row in embedded["worker_review"].items():
        if row["status"] not in {"component-mapping", "open-review"} or not row["note"]:
            raise ValueError("Invalid worker review disposition: " + name)
        if row["status"] == "component-mapping" and name not in mapped:
            raise ValueError("Worker missing embedded component mapping: " + name)
    for name, info in embedded["notices"].items():
        if not name.startswith("third_party/licenses/embedded/"):
            raise ValueError("Invalid embedded notice path: " + name)
        check_git_pin(info["source"], info["source_blob"])
        if info["kind"] not in {"whole-file", "source-excerpt"}:
            raise ValueError("Invalid embedded notice source kind: " + name)
    font = embedded["font_provenance"]
    check_git_pin(font["source"], font["source_blob"])
    if (font["file"] not in inv["legacy_assets"] or font["status"] != "partial"
            or git_blob_sha1(read_file(root, font["file"])) != font["source_blob"]):
        raise ValueError("Legacy font lineage mismatch")
    candidate = font["google_repository_candidate"]
    check_git_pin(candidate["url"], candidate["git_blob"])
    if candidate["relation"] != "different-blob" or candidate["git_blob"] == font["source_blob"]:
        raise ValueError("Invalid historical font comparison")
    return used


def embedded_upstream_evidence(inv, fetch=None):
    """Build-time only: pin-check source files, full texts and exact excerpts."""
    if fetch is None:
        def fetch(url):
            with urlopen(url, timeout=25) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError("Embedded evidence exceeds size limit")
            return raw
    cache = {}
    def verified(url, blob):
        check_git_pin(url, blob)
        if url not in cache:
            cache[url] = fetch(immutable_raw_url(url))
        raw = cache[url]
        if git_blob_sha1(raw) != blob:
            raise ValueError("Embedded upstream Git blob mismatch: " + url)
        return raw
    embedded = inv["embedded"]
    for item in embedded["components"]:
        for evidence in item["evidence"]:
            raw = verified(evidence["url"], evidence["git_blob"])
            if evidence["marker"].encode("utf-8") not in raw:
                raise ValueError("Embedded upstream source marker missing: " + item["id"])
    for path, notice in embedded["notices"].items():
        raw = verified(notice["source"], notice["source_blob"])
        local = read_file(PACKAGE, path)
        if ((notice["kind"] == "whole-file" and local != raw)
                or (notice["kind"] == "source-excerpt" and local not in raw)):
            raise ValueError("Embedded upstream license text mismatch: " + path)
    font = embedded["font_provenance"]
    original = verified(font["source"], font["source_blob"])
    candidate = font["google_repository_candidate"]
    historical = verified(candidate["url"], candidate["git_blob"])
    if original != read_file(PACKAGE, font["file"]) or original == historical:
        raise ValueError("Historical font comparison mismatch")
    return {"source_files": [{"url": url, "git_blob": git_blob_sha1(raw),
                              "sha256": sha(raw)}
                             for url, raw in sorted(cache.items())],
            "component_records": len(embedded["components"]),
            "notices_verified": len(embedded["notices"]),
            "font_lineage": "repository-byte-match; original CDN archive unresolved",
            "limitations": embedded["limitations"]}


def source_inventory(root=PACKAGE):
    """Verify exact ownership, notice coverage and bytes; no network."""
    inv = load(root / NOTICE)
    if inv["schema"] != 1:
        raise ValueError("Unknown third-party inventory schema")
    verify_file(root, MANIFEST, inv["vendor_manifest_sha256"])
    vendor = load(root / MANIFEST)
    if vendor["schema"] != 1:
        raise ValueError("Unknown vendor manifest schema")
    resources = vendor["resources"]
    legacy = inv["legacy_assets"]
    embedded = json.loads(read_file(root, EMBEDDED))
    if set(inv["license_notices"]) & set(embedded["notices"]):
        raise ValueError("Overlapping embedded notices")
    notices = {**inv["license_notices"], **embedded["notices"]}
    if set(resources) & set(legacy) or set(resources) & set(notices) or set(legacy) & set(notices):
        raise ValueError("Overlapping resource inventories")
    for path, digest in {**resources, **legacy, **{
            name: item["sha256"] for name, item in notices.items()}}.items():
        verify_file(root, path, digest)
    actual_vendor = {p.relative_to(root).as_posix()
                     for p in (root / "vendor").rglob("*") if p.is_file()}
    if actual_vendor != set(resources) | {MANIFEST}:
        raise ValueError("Untracked or absent vendor resource")
    actual_notices = {p.relative_to(root).as_posix()
                      for p in (root / "third_party").rglob("*") if p.is_file()}
    if actual_notices != set(notices) | {NOTICE, EMBEDDED, "third_party/NOTICE.md"}:
        raise ValueError("Untracked or absent notice")
    expected = set(resources) | set(legacy)
    notice_paths = {name for name in resources if name.startswith("vendor/licenses/")} | set(notices)
    owned = set()
    used_notices = set()
    ids = set()
    for component in inv["components"]:
        if component["id"] in ids:
            raise ValueError("Duplicate component identity")
        ids.add(component["id"])
        if not component["license"] or not component["notices"]:
            raise ValueError("Component without license or notice")
        files = set(component["files"])
        for prefix in component["vendor_prefixes"]:
            matches = {name for name in resources if name.startswith(prefix)}
            if not matches:
                raise ValueError("Unmatched inventory prefix: " + prefix)
            files.update(matches)
        if not files or files & owned or not files <= expected - notice_paths:
            raise ValueError("Missing/duplicate component ownership: " + component["id"])
        owned.update(files)
        used_notices.update(component["notices"])
        if not set(component["notices"]) <= notice_paths:
            raise ValueError("Unknown license notice")
    if owned != expected - notice_paths:
        raise ValueError("Incomplete third-party ownership/notice coverage")
    used_notices.update(validate_embedded(root, inv, vendor, embedded, notice_paths))
    if used_notices != notice_paths:
        raise ValueError("Incomplete third-party ownership/notice coverage")
    inv["embedded"] = embedded
    inv["license_notices"] = notices
    # Router's explicit first-party boundary must remain synchronized.
    # Import only here; installed evidence never starts the editor.
    from hass_configurator.http_routing import PACKAGE_ASSETS
    if set(PACKAGE_ASSETS) != set(inv["first_party_assets"]) | set(legacy):
        raise ValueError("Unclassified first-party package asset")
    if set(inv["first_party_assets"]) & set(legacy):
        raise ValueError("First-party/third-party overlap")
    if set(read_lock()) != set(inv["python_licenses"]):
        raise ValueError("Python license inventory drift")
    if set(inv["legacy_archive_locks"]) != {p for p in legacy if p.endswith(".js")}:
        raise ValueError("Incomplete legacy JS archive locks")
    for local, pin in inv["legacy_archive_locks"].items():
        for key in ("sha256", "member_sha256"):
            if not re.fullmatch("[0-9a-f]{64}", pin[key]):
                raise ValueError("Invalid upstream digest: " + local)
        if not pin["tarball"].startswith("https://registry.npmjs.org/"):
            raise ValueError("Non-registry archive source: " + local)
    return inv, vendor


def component_files(component, vendor):
    return sorted(set(component["files"]) | {
        name for name in vendor["resources"]
        if any(name.startswith(p) for p in component["vendor_prefixes"])})


def property_(name, value):
    return {"name": name, "value": str(value)}


def sbom(inv, vendor):
    """Deterministic CycloneDX 1.5 source/locked-application BOM.

    Font versions are from embedded name tables, not archive identities. Archive hashes
    are labelled as such; they are not hashes of installed distributions.
    """
    from hass_configurator._version import VERSION
    components = []
    for item in inv["components"]:
        c = {"type": "library", "bom-ref": "asset:" + item["id"],
             "name": item["name"], "licenses": [{"expression": item["license"]}],
             "properties": [property_("hc:provenance", item["provenance"])]}
        if item["version"]:
            c["version"] = item["version"]
        if item["ecosystem"] == "npm":
            c["purl"] = "pkg:npm/" + quote(item["name"], safe="/") + "@" + item["version"]
        for name in component_files(item, vendor):
            digest = vendor["resources"].get(name, inv["legacy_assets"].get(name))
            c["properties"].append(property_("hc:file:sha256:" + name, digest))
        for notice in item["notices"]:
            c["properties"].append(property_("hc:notice", notice))
        provenance = vendor["provenance"].get(item["id"])
        legacy_pins = [inv["legacy_archive_locks"][name] for name in item["files"]
                       if name in inv["legacy_archive_locks"]]
        if not provenance and legacy_pins:
            provenance = legacy_pins[0]
        if provenance:
            c["externalReferences"] = [{"type": "distribution", "url": provenance["tarball"],
                "hashes": [{"alg": "SHA-256", "content": provenance["sha256"]}]}]
            c["properties"].append(property_("hc:npm:integrity", provenance["npm_integrity"]))
        for pin in legacy_pins:
            c["properties"].append(property_("hc:legacy:npm-member:sha256", pin["member_sha256"]))
            c["properties"].append(property_("hc:legacy:relation", pin["relation"]))
            if "git_url" in pin:
                c.setdefault("externalReferences", []).append({"type": "distribution", "url": pin["git_url"],
                    "hashes": [{"alg": "SHA-256", "content": pin["git_sha256"]}]})
        components.append(c)
    embedded_dependencies = {}
    for item in inv["embedded"]["components"]:
        if item["kind"] != "library":
            continue  # Open review records are not fictitious software packages.
        ref = "embedded:" + item["id"]
        component = {"type": "library", "bom-ref": ref, "name": item["name"],
                     "properties": [
                         property_("hc:embedded:parent", "asset:" + item["parent"]),
                         property_("hc:attribution-status", item["status"]),
                         property_("hc:attribution-note", item["note"])]}
        if item["version"]:
            component["version"] = item["version"]
        if item["license"]:
            component["licenses"] = [{"expression": item["license"]}]
        if item["ecosystem"] == "npm":
            component["purl"] = "pkg:npm/" + quote(item["name"], safe="/") + "@" + item["version"]
        for location in item["locations"]:
            name = location["file"]
            digest = vendor["resources"].get(name, inv["legacy_assets"].get(name))
            component["properties"].append(property_("hc:container:sha256:" + name, digest))
        for notice in item["notices"]:
            component["properties"].append(property_("hc:notice", notice))
        for evidence in item["evidence"]:
            component["properties"].append(property_("hc:source:git-blob:" + evidence["url"],
                                                       evidence["git_blob"]))
        component["externalReferences"] = [{"type": "vcs", "url": url} for url in sorted({
            evidence["url"] for evidence in item["evidence"]})]
        components.append(component)
        embedded_dependencies.setdefault("asset:" + item["parent"], []).append(ref)
    for name, (version, digest) in sorted(read_lock().items()):
        components.append({"type": "library", "bom-ref": "python:" + name,
            "name": name, "version": version, "purl": "pkg:pypi/" + name + "@" + version,
            "licenses": [{"expression": inv["python_licenses"][name]}],
            "properties": [property_("hc:locked-wheel:sha256", digest),
                           property_("hc:license-status", "declared; inspect exact wheel and installed notices")]})
    return {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
            "metadata": {"component": {"type": "application", "bom-ref": "app",
                "name": "hass-configurator", "version": VERSION,
                "properties": [property_("hc:scope", "vendored browser assets and locked Python runtime; not full image SBOM"),
                               property_("hc:completeness", "partial: known embedded libraries included; unresolved version/license review, font origin, OS and build tools separate"),
                               property_("hc:embedded:review-records", json.dumps([c["id"] for c in inv["embedded"]["components"] if c["kind"] == "review"], sort_keys=True))]}},
            "components": components,
            "dependencies": [{"ref": "app", "dependsOn": [
                c["bom-ref"] for c in components if c["bom-ref"].startswith("asset:") or
                c["bom-ref"] in {"python:gitpython", "python:pyotp", "python:legacy-cgi"}]},
                {"ref": "python:gitpython", "dependsOn": ["python:gitdb"]},
                {"ref": "python:gitdb", "dependsOn": ["python:smmap"]},
                *[{"ref": ref, "dependsOn": sorted(children)}
                  for ref, children in sorted(embedded_dependencies.items())]]}


def verify_legacy_relation(raw, local, relation, git_raw=None):
    """Check only the observed exact deviations; never normalize arbitrary JS."""
    if relation == "missing-final-lf":
        valid = raw.endswith(b"\n") and raw[:-1] == local
    elif relation == "one-nbsp-to-space-and-missing-final-lf":
        valid = (raw.endswith(b"\n") and raw.count(b"\xc2\xa0") == 1
                 and raw[:-1].replace(b"\xc2\xa0", b" ") == local)
    elif relation == "exact-git-release-file-not-npm-member":
        valid = git_raw is not None and git_raw == local and raw != local
    elif relation == "exact":
        valid = raw == local
    else:
        valid = False
    if not valid:
        raise ValueError("Unexpected legacy JS relationship: " + relation)


def legacy_archives(directory):
    """Verify pinned archives and the reviewed, explicitly non-identical JS bytes."""
    inv, _ = source_inventory()
    result = {}
    for local, pin in inv["legacy_archive_locks"].items():
        path = directory / pin["archive"]
        archive_bytes = path.read_bytes()
        sri = "sha512-" + base64.b64encode(hashlib.sha512(archive_bytes).digest()).decode("ascii")
        if sha(archive_bytes) != pin["sha256"] or sri != pin["npm_integrity"]:
            raise ValueError("Upstream archive integrity mismatch: " + local)
        member = pin["member"]
        with tarfile.open(path, "r:gz") as archive:
            matches = [m for m in archive.getmembers() if m.name == member and m.isfile()]
            if len(matches) != 1:
                raise ValueError("Missing or duplicate upstream JS member: " + member)
            raw = archive.extractfile(matches[0]).read()
        if sha(raw) != pin["member_sha256"]:
            raise ValueError("Upstream member integrity mismatch: " + local)
        git_raw = None
        if "git_file" in pin:
            git_raw = (directory / pin["git_file"]).read_bytes()
            if sha(git_raw) != pin["git_sha256"]:
                raise ValueError("Upstream Git file integrity mismatch: " + local)
        local_bytes = read_file(PACKAGE, local)
        verify_legacy_relation(raw, local_bytes, pin["relation"], git_raw)
        result[local] = {"archive": pin["archive"], "archive_sha256": sha(archive_bytes),
            "npm_integrity": sri, "member": member, "upstream_sha256": sha(raw),
            "local_sha256": sha(local_bytes), "byte_equal": raw == local_bytes,
            "relation": pin["relation"]}
        if git_raw is not None:
            result[local].update({"git_url": pin["git_url"], "git_sha256": sha(git_raw)})
    return result


def font_evidence():
    """Font metadata from shipped binaries; no font files modified."""
    from fontTools.ttLib import TTFont
    paths = sorted((PACKAGE / "vendor/materialize/fonts/roboto").glob("*.woff*"))
    paths.append(PACKAGE / "flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2")
    result = {}
    for path in paths:
        with TTFont(path) as font:
            values = {}
            for record in font["name"].names:
                if record.nameID in {0, 1, 5, 8, 9, 13, 14}:
                    values.setdefault(str(record.nameID), set()).add(record.toUnicode())
            result[path.relative_to(PACKAGE).as_posix()] = {
                key: sorted(items) for key, items in sorted(values.items())}
    inv, _ = source_inventory()
    for path, values in result.items():
        family = "roboto" if path.startswith("vendor/materialize/") else "material-icons"
        for key, expected in inv["font_name_table_expectations"][family].items():
            if values.get(key) != expected:
                raise ValueError("Font name-table evidence drift: " + path + " / " + key)
    return result


def installed_evidence(label, locked=False, os_packages=False):
    """Inspect actual installed distributions, not the resolver's intent."""
    dist = metadata.distribution("hass-configurator")
    installed = Path(dist.locate_file("hass_configurator")).resolve()
    expected = PACKAGE.resolve()
    if installed == expected or not installed.is_dir():
        raise ValueError("Audit must inspect a real installed wheel/sdist/image outside checkout")
    inv, vendor = source_inventory()
    paths = set(vendor["resources"]) | set(inv["legacy_assets"]) | set(inv["license_notices"])
    paths |= {MANIFEST, NOTICE, EMBEDDED, "third_party/NOTICE.md"}
    for name in sorted(paths):
        verify_file(installed, name, sha(read_file(PACKAGE, name)))
    distributions = []
    seen = {}
    for d in sorted(metadata.distributions(), key=lambda d: normalize(d.metadata["Name"])):
        name = normalize(d.metadata["Name"])
        if name in seen:
            raise ValueError("Duplicate installed distribution: " + name)
        seen[name] = d.version
        files = []
        for p in d.files or ():
            rel = str(p)
            if ".dist-info/" not in rel or not re.search(r"(^|/)(license|copying|notice)[^/]*(/|$)", rel, re.I):
                continue
            path = Path(d.locate_file(p))
            if path.is_file():
                raw = path.read_bytes()
                files.append({"path": rel, "sha256": sha(raw),
                              "text": raw.decode("utf-8", errors="replace")})
        distributions.append({"name": name, "version": d.version,
            "license_expression": d.metadata.get("License-Expression"),
            "license": d.metadata.get("License"),
            "license_classifiers": [x for x in d.metadata.get_all("Classifier", [])
                                    if x.startswith("License ::")],
            "declared_license_files": d.metadata.get_all("License-File", []),
            "license_files": files, "requires_dist": d.requires or []})
    pins = read_lock()
    if not set(pins) <= set(seen):
        raise ValueError("Missing installed runtime dependencies")
    if locked and any(seen[name] != value[0] for name, value in pins.items()):
        raise ValueError("Installed versions differ from reviewed lock")
    result = {"label": label, "python": sys.version.split()[0],
              "application_resources_verified": len(paths),
              "distributions": distributions,
              "lock_matches": all(seen[name] == value[0] for name, value in pins.items())}
    if os_packages:
        rows = subprocess.check_output(["dpkg-query", "-W",
            "-f=${binary:Package}\\t${Version}\\t${source:Package}\\t${source:Version}\\t${db:Status-Abbrev}\\n"], text=True)
        result["debian_packages"] = [
            {"binary": binary, "version": version, "source": source, "source_version": source_version}
            for binary, version, source, source_version, status in
            (row.split("\t") for row in rows.splitlines()) if status.startswith("ii")]
        if not result["debian_packages"]:
            raise ValueError("Empty installed Debian package inventory")
    return result


def scan_queries(inv, installed_reports):
    queries = {(c["ecosystem"], c["name"], c["version"])
               for c in inv["components"] if c["ecosystem"] and c["version"]}
    queries.update((c["ecosystem"], c["name"], c["version"])
                   for c in inv["embedded"]["components"]
                   if c["kind"] == "library" and c["ecosystem"] and c["version"])
    queries.update(("PyPI", name, version) for name, (version, _) in read_lock().items())
    for report in installed_reports:
        queries.update(("PyPI", d["name"], d["version"])
                       for d in report["distributions"] if d["name"] != "hass-configurator")
        queries.update(("Debian:12", p["source"], p["source_version"])
                       for p in report.get("debian_packages", []))
    if any(not all(q) for q in queries):
        raise ValueError("Missing package identity/version in scan input")
    return [{"package": {"ecosystem": eco, "name": name}, "version": version}
            for eco, name, version in sorted(queries)]


def query_osv(queries, request=None):
    """Strict batch result correlation and pagination; errors are not clean results."""
    if request is None:
        def request(batch):
            req = Request(OSV, data=json.dumps({"queries": batch}).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=90) as response:
                return json.load(response)
    output = []
    for start in range(0, len(queries), 50):
        chunk = queries[start:start + 50]
        pending = [(i, query, None) for i, query in enumerate(chunk)]
        found = [dict() for _ in chunk]
        tokens = [set() for _ in chunk]
        while pending:
            batch = [{**query, **({"page_token": token} if token else {})}
                     for _, query, token in pending]
            result = request(batch)
            rows = result.get("results")
            if not isinstance(rows, list) or len(rows) != len(pending):
                raise ValueError("Incomplete OSV batch response")
            following = []
            for (i, query, _), row in zip(pending, rows):
                if not isinstance(row, dict) or "error" in row:
                    raise ValueError("OSV query failed")
                for vuln in row.get("vulns", []):
                    if not isinstance(vuln.get("id"), str) or not vuln["id"]:
                        raise ValueError("Invalid OSV advisory result")
                    found[i][vuln["id"]] = vuln
                token = row.get("next_page_token")
                if token:
                    if token in tokens[i]:
                        raise ValueError("Repeated OSV page token")
                    tokens[i].add(token)
                    following.append((i, query, token))
            pending = following
        output.extend({"query": q, "advisories": [v for _, v in sorted(found[i].items())]}
                      for i, q in enumerate(chunk))
    return output


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    source = sub.add_parser("source")
    source.add_argument("--output", type=Path, required=True)
    source.add_argument("--archives", type=Path)
    source.add_argument("--fonts", action="store_true")
    source.add_argument("--embedded-upstream", action="store_true",
                        help="Build-time network check of pinned source evidence and notices")
    installed = sub.add_parser("installed")
    installed.add_argument("--output", type=Path, required=True)
    installed.add_argument("--label", required=True)
    installed.add_argument("--locked", action="store_true")
    installed.add_argument("--debian12", action="store_true")
    scan = sub.add_parser("scan")
    scan.add_argument("--output", type=Path, required=True)
    scan.add_argument("--installed", type=Path, nargs="+", required=True)
    args = parser.parse_args()
    if args.command == "source":
        inv, vendor = source_inventory()
        write(args.output, sbom(inv, vendor))
        if args.archives:
            write(args.output.with_name("legacy-archive-evidence.json"), legacy_archives(args.archives))
        if args.fonts:
            write(args.output.with_name("font-metadata.json"), font_evidence())
        if args.embedded_upstream:
            write(args.output.with_name("embedded-upstream-evidence.json"), embedded_upstream_evidence(inv))
        print("Verified third-party resource/notice coverage and generated source SBOM")
    elif args.command == "installed":
        write(args.output, installed_evidence(args.label, args.locked, args.debian12))
    else:
        inv, _ = source_inventory()
        queries = scan_queries(inv, [load(p) for p in args.installed])
        # Clear explicit result on failure, never a misleading zero count.
        try:
            results = query_osv(queries)
        except Exception as exc:
            write(args.output, {"status": "error", "error_type": type(exc).__name__,
                                "queries": len(queries)})
            raise
        write(args.output, {"status": "completed", "provider": OSV,
            "scanned_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "results": results,
            "limitations": ["Matches by package/version, not exploitability or absence of vulnerabilities.",
                "Known versioned embedded components included; unresolved versions/identity, unknown font releases, CPython/CPE and non-package files not covered.",
                "A package/version advisory match does not establish impact in modified embedded code.",
                "Debian source versions queried; OSV ecosystem coverage is not exhaustive.",
                "Findings require human adjudication; report is not release acceptance."]})
        print("OSV queries:", len(results), "packages with advisories:",
              sum(bool(x["advisories"]) for x in results))


if __name__ == "__main__":
    main()
