"""Pinned external theme references, not a license-clearance decision."""
import plistlib
from urllib.parse import quote

try:
    from .audit_supply_chain import git_blob_sha1, sha
except ImportError:
    from audit_supply_chain import git_blob_sha1, sha


TOMORROW = ("chriskempson/tomorrow-theme", "ccf6666d888198d341b26b3a99d0bc96500ad503")
SOLARIZED = ("altercation/solarized", "62f656a02f93c5190a8753159e34b385588d5ff3")
LICENSES = {
    "tomorrow": (*TOMORROW, "LICENSE.md", "0e689d0a004eb37155ef430fe615a6e27209d30f"),
    "solarized": (*SOLARIZED, "LICENSE", "ee08d7e44f15108ef5359550399dad55955b56ca"),
}
# name, family, external plist path/blob, Ace plist path/blob, external JS path/blob
THEMES = (
    ("tomorrow", "tomorrow", "textmate/Tomorrow.tmTheme", "2b26f3cd0a78f18e45a38c370f2fc54ca4f3f2aa",
     "Tomorrow.tmTheme", "8c98c22657b272436fd55d6ce4ab3b99a1382877",
     "Ace/tomorrow.js", "4a6195df1efe24d07c494a9c744e0d98a768fac7"),
    ("tomorrow_night", "tomorrow", "textmate/Tomorrow-Night.tmTheme", "e0c504341b4760b872e1ad8d07d14e56dadfb0ea",
     "Tomorrow-Night.tmTheme", "bb1efaf06ae1687ff138243935dbeed4f3dbc8c9",
     "Ace/tomorrow-night.js", "288c26cff7a3ceadcde9de4de941467372545ac4"),
    ("tomorrow_night_blue", "tomorrow", "textmate/Tomorrow-Night-Blue.tmTheme", "b6a672eaf67c166bb720dca580a3cbd511d661cd",
     "Tomorrow-Night-Blue.tmTheme", "b1669a27dcab9a916323f544f8bf81a2083cf615",
     "Ace/tomorrow-night-blue.js", "71bb8fa6a499bde509d50a80f28b233e4437e3f9"),
    ("tomorrow_night_bright", "tomorrow", "textmate/Tomorrow-Night-Bright.tmTheme", "bf76fd7e12e791608cb8384ee1b9c1a3b358516c",
     "Tomorrow-Night-Bright.tmTheme", "15d401066ce80589fccf0f63ae0f5615076e7cb1",
     "Ace/tomorrow-night-bright.js", "dac24ad01d941aeebc2f0b742f0bb79268f9c4a6"),
    ("tomorrow_night_eighties", "tomorrow", "textmate/Tomorrow-Night-Eighties.tmTheme", "4c6b8eeb69c052b92254fe5be52b91820b589f2f",
     "Tomorrow-Night-Eighties.tmTheme", "33dabddf5e03966e995bb81a71149ca0969dd0e7",
     "Ace/tomorrow-night-eighties.js", "fe2028a7124394f1ee618a40656cae1d80638abb"),
    ("solarized_dark", "solarized", "textmate-colors-solarized/Solarized (dark).tmTheme", "a2436e4e952ed106c29c13041afb1420c45a4ea7",
     "Solarized-dark.tmTheme", "4efdabdbd5ca5e588d0357c2b3d8aa7b255f7813", None, None),
    ("solarized_light", "solarized", "textmate-colors-solarized/Solarized (light).tmTheme", "caf566c45f3410c214e1b8eab53f8ac4eefdfa0d",
     "Solarized-light.tmTheme", "9db72b86d208eec6b7611416b0376f7acc1d1927", None, None),
)


def verify_blob(raw, expected):
    if git_blob_sha1(raw) != expected:
        raise ValueError("External theme evidence blob mismatch")
    return {"git_blob": expected, "sha256": sha(raw)}


def reference(repo, commit, path, blob, fetch):
    url = "https://raw.githubusercontent.com/" + repo + "/" + commit + "/" + quote(path, safe="/")
    raw = fetch(url)
    return raw, {"repository": repo, "commit": commit, "path": path,
                 **verify_blob(raw, blob)}


def compare_plist(left, right):
    # Preserve order of settings (scope precedence can matter), all keys,
    # and value types. No palette/color normalization or ignored UUIDs.
    a, b = plistlib.loads(left), plistlib.loads(right)
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise ValueError("Expected theme plist dictionaries")
    if not isinstance(a.get("settings"), list) or not isinstance(b.get("settings"), list):
        raise ValueError("Expected theme settings lists")

    def equal(x, y):
        if type(x) is not type(y):
            return False
        if isinstance(x, dict):
            return x.keys() == y.keys() and all(equal(x[k], y[k]) for k in x)
        if isinstance(x, list):
            return len(x) == len(y) and all(equal(i, j) for i, j in zip(x, y))
        return x == y

    keys = sorted(a.keys() | b.keys())
    changed = [k for k in keys if k not in a or k not in b or not equal(a[k], b[k])]
    return {"raw_equal": left == right, "parsed_equal": not changed,
            "settings_equal": equal(a["settings"], b["settings"]),
            "differing_top_level_keys": changed,
            "external_settings_count": len(a["settings"]),
            "ace_settings_count": len(b["settings"])}



# Historical TextMate snapshots, initial Ace imports and current Ace inputs.
# External and initial import blobs must be byte-identical; later changes
# are reported rather than normalized away.
TEXTMATE = "textmate/themes.tmbundle"
TEXTMATE_LICENSE = (TEXTMATE, "9af146748ca3f0d3935985b6c731ccc7781831d9",
                    "README.mdown", "32d8f85a4c5f41b1fd636664c7a4ca776f511b9f")
TEXTMATE_INPUTS = (
    ("cobalt", "Cobalt.tmTheme", "0635502e6a3c8ca63c05cb80cdcb372a9c1340ce",
     "cba64d86be96864665b26e109603f021e1141e67", "3c685f253c723122c55800f7ce7ee7374963c428",
     "3c685f253c723122c55800f7ce7ee7374963c428"),
    ("dawn", "Dawn.tmTheme", "2746dd84db7e3ba0d6a40000c42278854cb73460",
     "242cfb76eb3eb68d3ad8806c98b1e79428eac336", "12cff9b6e2e9d6e1255678e7af2a685116c5ac32",
     "12cff9b6e2e9d6e1255678e7af2a685116c5ac32"),
    ("pastel_on_dark", "Pastels on Dark.tmTheme", "c2fcd871773e33529fecd77fd484f8aa9b66fe8b",
     "cba64d86be96864665b26e109603f021e1141e67", "e3928606e60f437527a03eb5f96fda92cde95bf4",
     "47b836318087d53ac60db65b83c29ca07afa327f"),
    ("twilight", "Twilight.tmTheme", "c2fcd871773e33529fecd77fd484f8aa9b66fe8b",
     "242cfb76eb3eb68d3ad8806c98b1e79428eac336", "a83f7ecbbe46792e321a1c823fb56d159bade152",
     "a5984e82e22654f4df93363c23f882645e6df3b4"),
)
ADDITIONAL_ACE_INPUTS = (
    ("kuroir", "Kuroir Theme.tmTheme", "ab6aa3be5c59b2202a737f90b78c488b419a241d",
     "36acd588d1f636c411071c0d48fefc8c6d1f14d4"),
    ("xcode", "Xcode_default.tmTheme", "ecfdc5fbc4691b7d3933416b65da340768111f04",
     "c7b5072cd31169ec9582bab8de3e007adfaede01"),
    ("kr_theme", "krTheme.tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "65c5c9b6aac1d42dc65c1ee537093404fe207b64"),
)


def verify_historical_import(external, imported):
    if external != imported:
        raise ValueError("Historical theme import bytes differ")
    return compare_plist(external, imported)


def textmate_license_relation(readme, ace_license):
    # The source uses repository-wide scope; Ace uses directory scope.
    # Compare only this observed wording change and whitespace.
    marker = b"# License\n\n"
    if readme.count(marker) != 1:
        raise ValueError("Missing unique TextMate license section")
    original = readme.split(marker, 1)[1]
    if original.count(b"files in this repository") != 1:
        raise ValueError("Unexpected TextMate license scope")
    expected = original.replace(b"files in this repository", b"files in this directory", 1)
    if expected.split() != ace_license.split():
        raise ValueError("TextMate license reference terms differ")
    return "scope-wording-and-whitespace-only"


def historical_textmate(source, fetch, source_file):
    readme, license_pin = reference(*TEXTMATE_LICENSE, fetch)
    ace_license, blob = source_file(source, "tool/tmthemes/LICENSE")
    if blob != "08f1380f3a9bce3135253bc69f5861dec3dcae17":
        raise ValueError("Ace TextMate license pin mismatch")
    license_relation = textmate_license_relation(readme, ace_license)
    rows = []
    for name, filename, external_rev, import_rev, old_blob, current_blob in TEXTMATE_INPUTS:
        original, external_pin = reference(TEXTMATE, external_rev, "Themes/" + filename, old_blob, fetch)
        path = "tool/tmthemes/" + filename
        imported, import_pin = reference("ajaxorg/ace", import_rev, path, old_blob, fetch)
        historical_comparison = verify_historical_import(original, imported)
        current, actual = source_file(source, path)
        if actual != current_blob:
            raise ValueError("Current TextMate input pin mismatch: " + name)
        rows.append({"theme": name, "external": external_pin, "initial_ace": import_pin,
                     "current_ace": {"path": path, **verify_blob(current, current_blob)},
                     "historical_import": historical_comparison,
                     "current_comparison": compare_plist(original, current),
                     "license_status": "review-open"})
    additional = []
    for name, filename, import_rev, blob in ADDITIONAL_ACE_INPUTS:
        path = "tool/tmthemes/" + filename
        imported, pin = reference("ajaxorg/ace", import_rev, path, blob, fetch)
        current, actual = source_file(source, path)
        if actual != blob:
            raise ValueError("Additional theme input pin mismatch: " + name)
        comparison = verify_historical_import(imported, current)
        meta = plistlib.loads(current)
        additional.append({"theme": name, "initial_ace": pin,
                           "current_ace": {"path": path, **verify_blob(current, blob)},
                           "comparison": comparison,
                           "author": meta.get("author"), "comment": meta.get("comment"),
                           "license_status": "external-lineage-open"})
    return {"textmate_license": license_pin,
            "ace_license": {"path": "tool/tmthemes/LICENSE", **verify_blob(ace_license, "08f1380f3a9bce3135253bc69f5861dec3dcae17")},
            "license_relation": license_relation, "themes": rows, "additional_ace_inputs": additional,
            "limitations": ["2011 original README license postdates the 2010 Ace import; Ace directory license dates to 2010.",
                            "File-specific exceptions and upstream author/derivative rights remain open.",
                            "Input identity is not generated CSS equivalence or license clearance."]}


def research(source, work, fetch, source_file):
    licenses = {}
    for family, pin in LICENSES.items():
        _, licenses[family] = reference(*pin, fetch)
    rows = []
    for name, family, path, blob, ace_path, ace_blob, js_path, js_blob in THEMES:
        repo, commit = LICENSES[family][:2]
        raw, external = reference(repo, commit, path, blob, fetch)
        ace_path = "tool/tmthemes/" + ace_path
        ace_raw, actual = source_file(source, ace_path)
        if actual != ace_blob:
            raise ValueError("Ace theme reference pin mismatch: " + name)
        row = {"theme": name, "family": family, "external": external,
               "ace": {"path": ace_path, **verify_blob(ace_raw, ace_blob)},
               "plist": compare_plist(raw, ace_raw),
               "license_reference": family, "license_status": "review-open"}
        if js_path is not None:
            js_raw, row["external_ace_port"] = reference(repo, commit, js_path, js_blob, fetch)
            dest = work / "external-theme" / (name + ".js")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(js_raw)
        rows.append(row)
    return {"licenses": licenses, "themes": rows,
            "historical_textmate": historical_textmate(source, fetch, source_file),
            "limitations": ["Pinned reference identity and comparisons are not historical lineage or license clearance.",
                            "Differences are evidence, not failures; pin drift fails closed."]}
