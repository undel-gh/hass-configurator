"""Review-only Ace snippet matrix; no runtime or license acceptance decisions."""
import hashlib
import json
import re
from collections import Counter

MATRIX_PATH = "docs/ace-snippet-dispositions.json"
DOCUMENT_PATH = "docs/ACE_SNIPPET_DISPOSITIONS.md"
COUNTS = {
    "exact-generated-empty-stub": 150,
    "exact-source-license-open": 1,
    "historical-endpoint-review-open": 15,
    "microsoft-partial": 1,
    "snipmate-derived": 3,
    "snipmate-exact": 22,
    "snipmate-modified": 8,
    "textmate-exact": 2
}
SHARED_STUB_LOADER = {
    "status": "source-mapped-review-open",
    "scope": "150-exact-generated-empty-stubs",
    "parent_component": "ace",
    "license": "BSD-3-Clause",
    "notice": "vendor/licenses/ace.txt",
    "license_git_blob": "4760be2a6220cf545129b233e20574f2a7bb630e",
    "source": {
        "commit": "68d7fd1c0f5ac50cdb610bf06b86074eab3be652",
        "path": "Makefile.dryice.js",
        "git_blob": "2d4596dee98c8b09333b192a8f4cd9cd09331185"
    },
    "history": [
        {
            "commit": "d63863ac0cbc2d5387cb44ef3db6cc65c46ece6e",
            "git_blob": "8bf5456296033ef22fe15a469ad3dd9af316c5e9",
            "variant": "require-only"
        },
        {
            "commit": "eccdf0521294eca13b8b2e1df639f180753a07de",
            "git_blob": "d799677440f3f41301d26758f201f7baf7b07d0d",
            "variant": "module-export"
        },
        {
            "commit": "3a9793cbc1a7c583f42955a09c8b0b8a73f3c42e",
            "git_blob": "0e683d2a8b0fb32eaaf5394ac7a4c6dc093bbcae",
            "variant": "module-export"
        },
        {
            "commit": "fc284ad191a7ed0c6451a80dc2e9614eaeb39624",
            "git_blob": "2556766137e948c70f6e1a8ccf86ab7f58b324b6",
            "variant": "guarded-export"
        }
    ]
}

EXCLUSION_CANDIDATES = {"abc", "gobstones", "lsl"}
EXACT = set("actionscript c_cpp clojure coffee css diff django erlang haml haskell java jsp lua makefile perl rst ruby snippets sql tcl tex textile".split())
MODIFIED = set("dart html javascript markdown php python r sh".split())
DERIVED = {"edifact", "liquid", "wollok"}
ROW_FIELDS = {"snippet", "distribution", "asset_sha256", "payload_kind",
              "source_payload", "historical_reference", "evidence_class",
              "additional_components", "review_priority", "proposed_disposition",
              "remaining_review"}


def require(condition, message):
    if not condition:
        raise ValueError("Snippet disposition: " + message)


def unique_json(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def load_matrix(root):
    return json.loads((root / MATRIX_PATH).read_text("utf-8"), object_pairs_hook=unique_json)


def empty_stub(name):
    # Exact minified generated wrapper from audit_ace_native_payloads.cjs.
    return (';                (function() {\n'
            '                    ace.require(["ace/snippets/' + name + '"], function(m) {\n'
            '                        if (typeof module == "object" && typeof exports == "object" && module) {\n'
            '                            module.exports = m;\n'
            '                        }\n'
            '                    });\n'
            '                })();\n'
            '            ').encode("ascii")


def evidence_class(name, stub):
    if stub:
        return "exact-generated-empty-stub"
    if name in EXACT:
        return "snipmate-exact"
    if name in MODIFIED:
        return "snipmate-modified"
    if name in DERIVED:
        return "snipmate-derived"
    if name in {"io", "vala"}:
        return "textmate-exact"
    if name == "sqlserver":
        return "microsoft-partial"
    if name == "lsl":
        return "exact-source-license-open"
    return "historical-endpoint-review-open"


def expected_components(name, category):
    if category.startswith("snipmate-"):
        return ["ace-snipmate-snippets"]
    if category == "textmate-exact":
        return ["ace-textmate-" + name + "-snippets"]
    if category == "microsoft-partial":
        return ["ace-sqlserver-microsoft-template-material"]
    if category == "exact-source-license-open":
        return ["ace-lsl-snippet-source-review"]
    return []


def verify_snippet_dispositions(matrix, lock, vendor, embedded):
    """Offline, version-bound closure; no claim of independent license review."""
    require(set(matrix) == {"schema", "ace_version", "ace_source_commit", "ace_build_commit", "review_status", "rows", "shared_stub_loader"}
            and type(matrix["schema"]) is int and matrix["schema"] == 1, "invalid schema")
    require(matrix["review_status"] == "independent-review-pending", "unexpected review status")
    require(matrix["shared_stub_loader"] == SHARED_STUB_LOADER, "shared stub loader evidence drift")
    require(matrix["shared_stub_loader"]["source"]["commit"] == lock["source_commit"]
            and matrix["shared_stub_loader"]["license_git_blob"] == lock["license_git_blob"],
            "shared stub loader source/license pin drift")
    require(all(matrix[key] == lock[pin] for key, pin in (
        ("ace_version", "version"), ("ace_source_commit", "source_commit"),
        ("ace_build_commit", "build_commit"))), "Ace pin drift")
    files = {k: v for k, v in lock["files_sha256"].items() if k.startswith("snippets/")}
    require(all(re.fullmatch(r"snippets/[a-z0-9_]+\.js", k) for k in files), "unexpected locked filename")
    resources = {k.removeprefix("vendor/ace/"): v for k, v in vendor["resources"].items()
                 if k.startswith("vendor/ace/snippets/")}
    require(files == resources and len(files) == 202, "lock/vendor snippet closure mismatch")
    rows = matrix["rows"]
    require(isinstance(rows, list) and all(isinstance(row, dict) and set(row) == ROW_FIELDS
                                          for row in rows), "invalid row fields")
    require(all(isinstance(row["snippet"], str) and re.fullmatch("[a-z0-9_]+", row["snippet"])
                for row in rows), "invalid snippet name")
    names = [row["snippet"] for row in rows]
    require(names == sorted(k[9:-3] for k in files), "missing, duplicate, extra or unordered row")
    by_component = {c["id"]: c for c in embedded["components"]}
    counts = Counter()
    for row in rows:
        name = row["snippet"]
        file = "snippets/" + name + ".js"
        loc = "vendor/ace/" + file
        digest = files[file]
        require(row["distribution"] == "retained" and row["asset_sha256"] == digest,
                "distribution/hash drift: " + name)
        stub = hashlib.sha256(empty_stub(name)).hexdigest() == digest
        category = evidence_class(name, stub)
        counts[category] += 1
        require(row["payload_kind"] == ("empty-stub" if stub else "nonempty")
                and row["evidence_class"] == category, "payload/evidence class drift: " + name)
        proposal = ("retain-stub-review-open" if stub else
                    "consider-snippet-only-exclusion" if name in EXCLUSION_CANDIDATES else "retain-review-open")
        require(row["proposed_disposition"] == proposal
                and row["review_priority"] in {"standard", "elevated"}
                and isinstance(row["remaining_review"], str) and row["remaining_review"].strip()
                and not any(c in row["remaining_review"] for c in "|\r\n"),
                "unexpected proposal/review fields: " + name)
        mapped = sorted(c["id"] for c in embedded["components"]
                        if any(x["file"] == loc for x in c["locations"]))
        require(row["additional_components"] == mapped == expected_components(name, category),
                "component mapping drift: " + name)
        for cid in mapped:
            c = by_component[cid]
            review = category == "exact-source-license-open"
            require(c["status"] == "partial" and c["kind"] == ("review" if review else "library")
                    and c["version"] is None and c["ecosystem"] is None
                    and (c["license"] is None and c["notices"] == [] if review else
                         bool(c["license"]) and bool(c["notices"]))
                    and {"file": loc, "marker": "ace/snippets/" + name} in c["locations"],
                    "component scope drift: " + name)
        src, hist = row["source_payload"], row["historical_reference"]
        if stub:
            require(src is None and hist is None, "stub must have no payload source pin: " + name)
            continue
        prefix = "lib/ace/snippets/" if name in {"jsoniq", "xquery"} else "src/snippets/"
        path = prefix + name + (".js" if name in {"io", "vala"} else ".snippets.js")
        require(isinstance(src, dict) and set(src) == {"path", "git_blob"}
                and src["path"] == path and re.fullmatch("[0-9a-f]{40}", src["git_blob"]),
                "current source pin drift: " + name)
        require(isinstance(hist, dict) and set(hist) == {"first_contribution", "url", "git_blob"}
                and re.fullmatch("[0-9a-f]{40}", hist["first_contribution"])
                and re.fullmatch("[0-9a-f]{40}", hist["git_blob"])
                and re.fullmatch(r"https://github\.com/(?:ajaxorg/ace|honza/vim-snippets)/blob/"
                                 r"[0-9a-f]{40}/[a-zA-Z0-9_./-]+", hist["url"])
                and ".." not in hist["url"].split("/"), "historical reference pin invalid: " + name)
        current_url = "https://github.com/ajaxorg/ace/blob/" + matrix["ace_source_commit"] + "/" + path
        if category == "textmate-exact":
            evidence = by_component[mapped[0]]["evidence"]
            require(any(x["url"] == current_url and x["git_blob"] == src["git_blob"] for x in evidence),
                    "TextMate source pin mismatch: " + name)
        elif mapped:
            relations = [r for r in embedded["source_relationships"]
                         if r["relation"] == "ace-snippet-template-literal"
                         and r["container"]["url"] == current_url]
            require(len(relations) == 1 and relations[0]["container"]["git_blob"] == src["git_blob"]
                    and relations[0]["upstream"]["url"] == hist["url"]
                    and relations[0]["upstream"]["git_blob"] == hist["git_blob"],
                    "mapped source relation drift: " + name)
    require(dict(counts) == COUNTS, "evidence class totals drift")
    return dict(sorted(counts.items()))



def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def verify_stub_parent_notice(matrix, inventory, lock, notice):
    """Reuse the actual parent Ace notice; no new package or notice identity."""
    record = matrix["shared_stub_loader"]
    require(record == SHARED_STUB_LOADER, "shared stub loader evidence drift")
    matches = [c for c in inventory["components"] if c["id"] == record["parent_component"]]
    require(len(matches) == 1, "missing Ace notice owner")
    parent = matches[0]
    require(parent["license"] == record["license"] and record["notice"] in parent["notices"]
            and "vendor/ace/" in parent["vendor_prefixes"], "shared stub parent notice mapping drift")
    require(git_blob(notice) == record["license_git_blob"] == lock["license_git_blob"]
            and hashlib.sha256(notice).hexdigest() == lock["license_sha256"], "shared stub notice bytes drift")


def loader_template(builder, license_bytes, variant):
    """Static extraction of the exact observed Ace template, never execute JS."""
    require(variant in {"require-only", "module-export", "guarded-export"}, "unknown loader variant")
    header = re.match(rb"#!/usr/bin/env node\n/\* \*\*\*\*\* BEGIN LICENSE BLOCK \*\*\*\*\*\n"
                      rb" \* Distributed under the BSD license:\n \*\n([\s\S]*?)"
                      rb" \*\n \* \*\*\*\*\* END LICENSE BLOCK \*\*\*\*\* \*/\n", builder)
    require(header is not None, "builder BSD header missing")
    lines = header[1].splitlines()
    require(all(line == b" *" or line.startswith(b" * ") for line in lines),
            "builder BSD header formatting drift")
    text = b"\n".join(line[3:] if line.startswith(b" * ") else b"" for line in lines) + b"\n"
    require(text == license_bytes, "builder BSD header differs from shipped notice")
    matches = re.findall(rb"        if \(extModules\) \{\n            template = (function\(\) \{\n"
                         rb"[\s\S]*?\n            \});\n        \}", builder)
    require(len(matches) == 1, "expected one extModules template")
    body = matches[0]
    expected = (
        b"function() {\n"
        b"                (function() {\n"
        b"                    REQUIRE_NS.require(MODULES, function(m) {\n"
        b'                        if (typeof module == "object" && typeof exports == "object" && module) {\n'
        b"                            module.exports = m;\n"
        b"                        }\n"
        b"                    });\n"
        b"                })();\n"
        b"            }")
    if variant == "module-export":
        expected = expected.replace(b' && typeof exports == "object" && module', b"")
    elif variant == "require-only":
        expected = (b"function() {\n"
                    b"                (function() {\n"
                    b"                    REQUIRE_NS.require(MODULES, function() {});\n"
                    b"                })();\n"
                    b"            }")
    require(body == expected, "unexpected extModules template bytes")
    require(builder.count(b"function exportAce(ns, modules, requireBase, extModules)") == 1,
            "exportAce declaration drift")
    require(all(builder.count(token) == 1 for token in (
        b".replace(/MODULES/g, JSON.stringify(modules))",
        b".replace(/REQUIRE_NS/g, requireBase)",
        b".replace(/NS/g, ns)", b".slice(13, -1)")), "loader substitution drift")
    return body


def render_loader_template(template, name):
    require(re.fullmatch("[a-z0-9_]+", name) is not None, "invalid loader name")
    module = json.dumps(["ace/snippets/" + name], separators=(",", ":")).encode("ascii")
    return b";" + template.replace(b"MODULES", module).replace(b"REQUIRE_NS", b"ace").replace(b"NS", b"ace")[13:-1]


def verify_stub_loader_sources(matrix, source, notice, fetch, work):
    """Verify pinned historical templates, current generator, and both archive forms."""
    record = matrix["shared_stub_loader"]
    require(record == SHARED_STUB_LOADER, "shared stub loader evidence drift")
    require(git_blob(notice) == record["license_git_blob"], "shared stub notice blob drift")
    pin = record["source"]
    require(git_blob(source) == pin["git_blob"], "current loader generator blob drift")
    current = loader_template(source, notice, "guarded-export")
    # Check the actual current build path: per-mode snippet build, export
    # filter after compression and namespace selection, and exact LF handling.
    require(all(token in source for token in (
        b'require: ["ace/snippets/" + name]',
        b'}, "snippets/" + name, addCb());',
        b'if (projectType !== "worker")',
        b'opts.noconflict ? ns : "", projectType !== "main"',
        b'code = result.codeMin;',
        b'filters.forEach(function(f) { code = f(code); });',
        b'text.replace(/;\\s*$/, "") + ";" + template',
        b'filters.push(normalizeLineEndings);')), "current loader build path drift")
    historical = []
    for entry in record["history"]:
        base = "https://raw.githubusercontent.com/ajaxorg/ace/" + entry["commit"] + "/"
        builder, license_bytes = fetch(base + pin["path"]), fetch(base + "LICENSE")
        require(git_blob(builder) == entry["git_blob"] and license_bytes == notice,
                "historical loader source/license drift: " + entry["commit"])
        body = loader_template(builder, license_bytes, entry["variant"])
        if entry["variant"] == "guarded-export":
            require(body == current, "2018/current loader template mismatch")
        historical.append({**entry, "license_git_blob": git_blob(license_bytes)})
    rows = []
    for row in matrix["rows"]:
        if row["payload_kind"] != "empty-stub":
            continue
        name = row["snippet"]
        mini = render_loader_template(current, name)
        require(mini == empty_stub(name) and hashlib.sha256(mini).hexdigest() == row["asset_sha256"],
                "generated loader hash mismatch: " + name)
        file = "snippets/" + name + ".js"
        require((work / "mini" / file).read_bytes() == mini
                and (work / "plain" / file).read_bytes() == b"\n" + mini,
                "generated loader archive byte mismatch: " + name)
        rows.append({"snippet": name, "sha256": row["asset_sha256"]})
    require(len(rows) == 150, "generated loader closure mismatch")
    return {"status": "source-mapped-review-open", "source": pin,
            "license": record["license"], "notice": record["notice"],
            "license_git_blob": record["license_git_blob"], "historical_sources": historical,
            "exact_minified": len(rows), "exact_unminified": len(rows), "rows": rows}


def verify_native_snippet_dispositions(matrix, report):
    """Cross-check actual native audit classifications and current source blobs."""
    require(report["ace_source_commit"] == matrix["ace_source_commit"]
            and report["ace_build_commit"] == matrix["ace_build_commit"], "native pin drift")
    assets = [x for x in report["theme_snippet_assets"] if x["file"].startswith("snippets/")]
    expected = {"snippets/" + x["snippet"] + ".js": x for x in matrix["rows"]}
    require(len(assets) == len(expected) and {x["file"] for x in assets} == set(expected),
            "native report row closure mismatch")
    for asset in assets:
        row = expected[asset["file"]]
        stub = row["payload_kind"] == "empty-stub"
        require(asset["status"] == ("exact-generated-empty-stub" if stub else "static-payload-equal"),
                "native payload status mismatch: " + asset["file"])
        if not stub:
            pin = row["source_payload"]
            require(report["sources"].get(pin["path"], {}).get("git_blob") == pin["git_blob"]
                    and any(x.get("source") == pin["path"] and x.get("source_present")
                            for x in asset["source_files"]), "native source blob mismatch: " + asset["file"])
    return {"status": "matrix-closure-verified-review-open", "rows": len(assets),
            "nonempty": sum(x["payload_kind"] == "nonempty" for x in matrix["rows"]),
            "empty_stubs": sum(x["payload_kind"] == "empty-stub" for x in matrix["rows"])}


def render_document(matrix):
    counts = Counter(x["evidence_class"] for x in matrix["rows"])
    result = "# Ace snippet disposition matrix (R5.3)\n\nThe [machine-readable matrix](ace-snippet-dispositions.json) is canonical.\nThis is a proposed review disposition, not legal clearance or release acceptance.\nAll 202 assets are currently retained; no exclusion is authorized or implemented.\nThe Ace root BSD-3-Clause declaration applies separately, not as proof of external\ninput rights. Additional component IDs refer to `hass_configurator/third_party/embedded.json`.\nA partial attribution is not a license for the whole payload. Review-only records\nare not libraries. Priority is proposed review order, not a risk rating.\nHistorical references record research endpoints or exact original inputs, not\nnecessarily a unique copy revision. See [research](ACE_SNIPPET_RESEARCH.md).\n\nThe offline source inventory gate checks exact row closure, hashes against\nthe lock and vendor manifest, generated stub bytes by their exact hash,\ncomponent mappings, source pin consistency for mapped records and this rendered\ndocument. The native research gate separately compares all 202 row types and\nthe 52 current source Git blobs against the immutable checkout and static\npayload/empty-stub evidence. It does not replay all historical transformations\nor adjudicate rights. R5.3b maps the 150 generated loaders to the exact Ace\nexportAce extModules template, with a file-specific BSD-3-Clause header identical\nto the existing parent notice. Independent artifact inspection and review remain open.\n\n## Counts\n\n| Evidence class | Count |\n| --- | ---: |\n"
    result += "".join(f"| {key} | {count} |\n" for key, count in sorted(counts.items()))
    result += "\nOptional license-risk exclusion candidates: abc, gobstones, lsl.\nEDIFACT: retain under scoped attribution; product-only removal is a separate decision.\nLanguage modes are outside this decision; any exclusion requires explicit\nmaintainer approval, profile/manifest changes and validation in a separate increment.\n\n## Nonempty payloads\n\n| Snippet | Evidence class | Additional components | Priority | Proposed disposition | Remaining review |\n| --- | --- | --- | --- | --- | --- |\n"
    for row in matrix["rows"]:
        if row["payload_kind"] == "nonempty":
            result += "| " + " | ".join((row["snippet"], row["evidence_class"],
                ", ".join(row["additional_components"]) or "—", row["review_priority"],
                row["proposed_disposition"], row["remaining_review"])) + " |\n"
    result += "\n## Empty generated stubs\n\nAll rows below have identical structural loader semantics with a name-specific\nmodule ID, not an empty file. Exact published hashes are recorded in JSON.\nThe shared loader is mapped to `Makefile.dryice.js` (`exportAce`, `extModules`),\nwith a file-specific BSD-3-Clause header matching `vendor/licenses/ace.txt`.\nThe historical guarded-export variant matches the current template exactly.\nThe native audit verifies all 150 minified and unminified archive members by\nstatic substitution; no separate library or notice is created. This mapping is\nreview-open; no independent per-language license grant or payload is inferred.\n\n| Snippet | Proposed disposition |\n| --- | --- |\n"
    for row in matrix["rows"]:
        if row["payload_kind"] == "empty-stub":
            result += f"| {row['snippet']} | {row['proposed_disposition']} |\n"
    return result
