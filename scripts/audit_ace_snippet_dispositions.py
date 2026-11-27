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
EXCLUSION_CANDIDATES = {"abc", "edifact", "gobstones", "lsl"}
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
    require(set(matrix) == {"schema", "ace_version", "ace_source_commit", "ace_build_commit", "review_status", "rows"}
            and type(matrix["schema"]) is int and matrix["schema"] == 1, "invalid schema")
    require(matrix["review_status"] == "independent-review-pending", "unexpected review status")
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
    result = "# Ace snippet disposition matrix (R5.3)\n\nThe [machine-readable matrix](ace-snippet-dispositions.json) is canonical.\nThis is a proposed review disposition, not legal clearance or release acceptance.\nAll 202 assets are currently retained; no exclusion is authorized or implemented.\nThe Ace root BSD-3-Clause declaration applies separately, not as proof of external\ninput rights. Additional component IDs refer to `hass_configurator/third_party/embedded.json`.\nA partial attribution is not a license for the whole payload. Review-only records\nare not libraries. Priority is proposed review order, not a risk rating.\nHistorical references record research endpoints or exact original inputs, not\nnecessarily a unique copy revision. See [research](ACE_SNIPPET_RESEARCH.md).\n\nThe offline source inventory gate checks exact row closure, hashes against\nthe lock and vendor manifest, generated stub bytes by their exact hash,\ncomponent mappings, source pin consistency for mapped records and this rendered\ndocument. The native research gate separately compares all 202 row types and\nthe 52 current source Git blobs against the immutable checkout and static\npayload/empty-stub evidence. It does not replay all historical transformations\nor adjudicate rights. R5.3b shared loader template license, independent artifact\ninspection and review remain open.\n\n## Counts\n\n| Evidence class | Count |\n| --- | ---: |\n"
    result += "".join(f"| {key} | {count} |\n" for key, count in sorted(counts.items()))
    result += "\nProposed snippet-only exclusion candidates: abc, edifact, gobstones, lsl.\nLanguage modes are outside this decision; any exclusion requires explicit\nmaintainer approval, profile/manifest changes and validation in a separate increment.\n\n## Nonempty payloads\n\n| Snippet | Evidence class | Additional components | Priority | Proposed disposition | Remaining review |\n| --- | --- | --- | --- | --- | --- |\n"
    for row in matrix["rows"]:
        if row["payload_kind"] == "nonempty":
            result += "| " + " | ".join((row["snippet"], row["evidence_class"],
                ", ".join(row["additional_components"]) or "—", row["review_priority"],
                row["proposed_disposition"], row["remaining_review"])) + " |\n"
    result += "\n## Empty generated stubs\n\nAll rows below have identical structural loader semantics with a name-specific\nmodule ID, not an empty file. Exact published hashes are recorded in JSON.\nNo independent per-language license grant or payload is inferred.\n\n| Snippet | Proposed disposition |\n| --- | --- |\n"
    for row in matrix["rows"]:
        if row["payload_kind"] == "empty-stub":
            result += f"| {row['snippet']} | {row['proposed_disposition']} |\n"
    return result
