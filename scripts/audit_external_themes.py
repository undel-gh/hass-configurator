"""Pinned external theme references, not a license-clearance decision."""
import plistlib
import re
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



# Exact copies are evidence of file identity, not necessarily the direction
# of copying. Keep author archive and collection references separate.
EXTERNAL_PORT_REFERENCES = (
    ("kuroir", "Kuroir Theme.tmTheme", "36acd588d1f636c411071c0d48fefc8c6d1f14d4",
     ("MarioRicalde/TextMate-Kuroir-Theme", "085bd4d4e1a9a691a47b6e1b477e6b7c0aa348b0",
      "Kuroir Theme.tmTheme", "36acd588d1f636c411071c0d48fefc8c6d1f14d4"),
     ("MarioRicalde/TextMate-Kuroir-Theme", "085bd4d4e1a9a691a47b6e1b477e6b7c0aa348b0",
      "README.markdown", "605b342597b1cdeca94363625333570b2f1ac0c7"),
     True, "exact-external-port", "explicit-license-not-established"),
    ("xcode", "Xcode_default.tmTheme", "c7b5072cd31169ec9582bab8de3e007adfaede01",
     ("crmne/xcode-default.tmtheme", "88df84daf46d6d5e57742f5c9e82ac0a408cbd67",
      "Xcode default.tmTheme", "c7b5072cd31169ec9582bab8de3e007adfaede01"),
     ("crmne/xcode-default.tmtheme", "88df84daf46d6d5e57742f5c9e82ac0a408cbd67",
      "README.markdown", "1d7b8dc487917a7715187b12d414cc0587f80301"),
     True, "exact-author-source", "explicit-license-not-established"),
    ("kr_theme", "krTheme.tmTheme", "65c5c9b6aac1d42dc65c1ee537093404fe207b64",
     ("kennethreitz-archive/krTheme.tmTheme", "ec21b6d65a3d38d699b47b76026b2746f38d1681",
      "krTheme.tmTheme", "6b4da423a8e7a9f005ed0cd20436a74bd2d1def4"),
     ("kennethreitz-archive/krTheme.tmTheme", "ec21b6d65a3d38d699b47b76026b2746f38d1681",
      "Readme.md", "b9618416c8e135efd9e84520495b551415eb1bd4"),
     False, "author-archive-different-input", "all-rights-reserved-no-permission-established"),
    ("kr_theme", "krTheme.tmTheme", "65c5c9b6aac1d42dc65c1ee537093404fe207b64",
     ("filmgirl/TextMate-Themes", "87743ad74d04cd59099bfda39a0552e673edbc54",
      "krTheme.tmTheme", "65c5c9b6aac1d42dc65c1ee537093404fe207b64"),
     ("filmgirl/TextMate-Themes", "87743ad74d04cd59099bfda39a0552e673edbc54",
      "README.md", "822ed07e40de94be2fd73725942a57f89d85d598"),
     True, "exact-third-party-collection-copy", "collection-not-original-grant"),
)


def verify_expected_comparison(external, current, expected_equal):
    comparison = compare_plist(external, current)
    if comparison["raw_equal"] != expected_equal:
        raise ValueError("Unexpected external port byte relation")
    return comparison


def external_port_references(source, fetch, source_file):
    rows = []
    for name, filename, ace_blob, theme_pin, readme_pin, expected_equal, relation, status in EXTERNAL_PORT_REFERENCES:
        original, external = reference(*theme_pin, fetch)
        readme, readme_ref = reference(*readme_pin, fetch)
        if status == "all-rights-reserved-no-permission-established":
            if b"Copyright 2010 Kenneth Reitz. All Rights Reserved." not in readme:
                raise ValueError("Missing historical krTheme copyright statement")
        path = "tool/tmthemes/" + filename
        current, actual = source_file(source, path)
        if actual != ace_blob:
            raise ValueError("External port Ace pin mismatch: " + name)
        rows.append({"theme": name, "external": external, "readme": readme_ref,
                     "current_ace": {"path": path, **verify_blob(current, ace_blob)},
                     "comparison": verify_expected_comparison(original, current, expected_equal),
                     "source_relation": relation, "license_status": status})
    return rows


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
            "external_port_references": external_port_references(source, fetch, source_file),
            "limitations": ["2011 original README license postdates the 2010 Ace import; Ace directory license dates to 2010.",
                            "File-specific exceptions and upstream author/derivative rights remain open.",
                            "Input identity is not generated CSS equivalence or license clearance."]}



# R5.2e: historical Ace snapshots for remaining converter inputs, plus
# two historical inputs with exact TextMate counterparts. These are
# evidence of input identity, not proof of generated CSS or permission.
GROUPED_TEXTMATE_INPUTS = (
    ("clouds", "Clouds.tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "Clouds.tmTheme", "821476be783ba004772b44d5de72b66ae0b62efc", "821476be783ba004772b44d5de72b66ae0b62efc", None, "active"),
    ("clouds_midnight", "Clouds Midnight.tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "Clouds Midnight.tmTheme", "1859deba9fb48277dd2527d32db121591cc33a72", "1859deba9fb48277dd2527d32db121591cc33a72", None, "active"),
    ("idle_fingers", "idleFingers.tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "idleFingers.tmTheme", "51666df3fc100fd15ed9156ee4224bcff5c31958", "d86a0edd29a73726bb317cc86b57120133642067", None, "active"),
    ("merbivore", "Merbivore.tmTheme", "abd7a158583ae06fa95d14716977f119d8b89d15",
     "Merbivore.tmTheme", "ce8e56e3ad9d0906bbf9c1987140dc22dc66cf96", "41afeb81f5d65e901ce3bfab8819e6e2649daa12", None, "active"),
    ("merbivore_soft", "Merbivore Soft.tmTheme", "abd7a158583ae06fa95d14716977f119d8b89d15",
     "Merbivore Soft.tmTheme", "0a4c97cea018e77e834e22c4e749cb9126274038", "60c4cc94d138e03dbdd26fe4efc78ef5da00e287", None, "active"),
    ("mono_industrial", "monoindustrial.tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "monoindustrial.tmTheme", "81f8eb701c1989e4e7257c3717a3deb05e5b6171", "81f8eb701c1989e4e7257c3717a3deb05e5b6171", None, "active"),
    ("monokai", "Monokai.tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "Monokai.tmTheme", "fb01ff36d194c6d24a9d68ba6c32ea06e01c109e", "c179cbe2f97509d5f1d96132641e50707c7b223f", None, "active"),
    ("katzenmilch", "Katzenmilch.tmTheme", "ab6aa3be5c59b2202a737f90b78c488b419a241d",
     "Katzenmilch.tmTheme", "3878ffe9c3b7911bc27d6cca60e24661bc496b03", "3878ffe9c3b7911bc27d6cca60e24661bc496b03", None, "active"),
    ("vibrant_ink", "Vibrant Ink.tmTheme", "abd7a158583ae06fa95d14716977f119d8b89d15",
     "Vibrant Ink.tmTheme", "67d774a6bf8369d6810a2fcdd7543568e5a5f0f1", "a1e5cf288b8fb82ef8a6d2182feef521d886aa4b", None, "active"),
    ("iplastic", "iPlastic.tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "iPlastic.tmTheme", "7253df6a7516986b50acb280acb6d8d2959d8b7b", "7253df6a7516986b50acb280acb6d8d2959d8b7b", "iPlastic.tmTheme", "unmapped"),
    ("textmate", "Textmate (Mac Classic).tmTheme", "cba64d86be96864665b26e109603f021e1141e67",
     "Mac Classic.tmTheme", "4b789dfea34e1328a9b4a6fa4c7172aeb023310f", "4b789dfea34e1328a9b4a6fa4c7172aeb023310f", "Mac Classic.tmTheme", "commented"),
)
GROUP_TEXTMATE_REV = "c2fcd871773e33529fecd77fd484f8aa9b66fe8b"


def input_rights_indicators(raw, filename, directory_names):
    """Record candidates for manual review; absence is not permission."""
    parsed = plistlib.loads(raw)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("settings"), list):
        raise ValueError("Expected theme settings lists")
    markers = re.compile(rb"copyright|licen[cs]e|all\s+rights\s+reserved|permission|redistribut|based\s+on|inspired\s+by", re.I)
    hits = [{"line": i, "text": line.decode("utf-8", errors="replace")}
            for i, line in enumerate(raw.splitlines(), 1) if markers.search(line)]
    stem = filename.rsplit(".", 1)[0].casefold() + "-license"
    companions = sorted(name for name in directory_names
                        if name.casefold() == stem or name.casefold().startswith(stem + "."))
    return {"metadata": {key: value for key, value in parsed.items()
                         if isinstance(value, str) and key != "uuid"},
            "rights_marker_hits": hits, "companion_candidates": companions,
            "license_status": "review-open"}


def converter_input_status(converter, name, filename):
    block = converter.split("var themes = {", 1)[1].split("\n};", 1)[0]
    expression = (r'^\s*(//\s*)?"' + re.escape(name) + r'":\s*"([^"]+)"\s*,?\s*$')
    matches = re.findall(expression, block, re.M)
    if not matches:
        return "unmapped"
    if len(matches) != 1 or matches[0][1] + ".tmTheme" != filename:
        raise ValueError("Unexpected converter mapping: " + name)
    return "commented" if matches[0][0] else "active"


def grouped_textmate(source, fetch, source_file):
    converter, blob = source_file(source, "tool/tmtheme.js")
    verify_blob(converter, "eff23f2b777b3a1fea6d3c32ae048c4bda08b075")
    names = [p.name for p in (source / "tool/tmthemes").iterdir() if p.is_file()]
    rows = []
    for name, filename, revision, historical_name, old_blob, new_blob, tm_name, mapping in GROUPED_TEXTMATE_INPUTS:
        historic, historical_pin = reference("ajaxorg/ace", revision,
                                            "tool/tmthemes/" + historical_name, old_blob, fetch)
        path = "tool/tmthemes/" + filename
        current, actual = source_file(source, path)
        if actual != new_blob:
            raise ValueError("Grouped theme input pin mismatch: " + name)
        observed_mapping = converter_input_status(converter.decode("utf-8"), name, filename)
        if observed_mapping != mapping:
            raise ValueError("Grouped converter status drift: " + name)
        row = {"theme": name, "historical_ace": historical_pin,
               "current_ace": {"path": path, **verify_blob(current, new_blob)},
               "comparison": verify_expected_comparison(historic, current, old_blob == new_blob),
               "converter_status": observed_mapping,
               "historical_indicators": input_rights_indicators(historic, historical_name, []),
               "current_indicators": input_rights_indicators(current, filename, names),
               "external_source_status": "not-established-in-group-review",
               "license_status": "review-open"}
        # Historical companion inventories are not obtained by this function.
        row["historical_indicators"]["companion_candidates"] = None
        if tm_name is not None:
            original, external_pin = reference(TEXTMATE, GROUP_TEXTMATE_REV,
                                               "Themes/" + tm_name, old_blob, fetch)
            row["textmate"] = external_pin
            row["external_comparison"] = verify_historical_import(original, historic)
            row["external_source_status"] = "exact-historical-textmate-input"
        rows.append(row)
    return {"themes": rows,
            "limitations": ["Historical snapshots are not necessarily first imports.",
                            "Current mapping is not proof of conversion into shipped CSS.",
                            "Current companion filenames and literal rights markers are leads, not exhaustive permission checks.",
                            "Historical companion directories and upstream ports require individual review."]}



# Historical license declarations on complete Ace theme implementations.
# Keep the original misspelling in the 2010 paths.
HEADER_PARENT = "b32d86fd609be6e625ce6fad4e759f55e600e23d"
HEADER_COMMIT = "bb6854aeeb62efd0a5bf084175c170b100bcaa3c"
SPLIT_PARENT = "0e6bf2bd822015eeaa26d9133c2de199c59fbfdf"
SPLIT_COMMIT = "8a3e7b0f00e7cf7e0f10e693f0502a3da6920576"
BSD_COMMIT = "16b2f1c9cff5cc01385fcde4ad9eaac0e77e670c"
# name, pre-header JS, licensed JS, pre-split JS, split CSS, split JS, BSD JS
HISTORIC_THEME_LICENSES = (
    ("clouds", "f0f266319c1ed5c2649afe6db09397c1cd0e370a", "5af60b1c6f488c54f200ae80596d81479d3482e0", "2b31c1b268f21e964de5defd784a5f633a9671de", "e666fa8b4446bbd9b3cae0381698dcf612919043", "cc8bafce375a07f4c0964eca598b9ddd79aaf980", "05e8e7199ae96e89c8f7d339c39994c20f6c5519"),
    ("clouds_midnight", "4b51d3f0fde20953b60aff740b600af9af60eefe", "130af6f44a7df0edd9073694ba8a7d28a89e06be", "6d5899db8a15ad9b6ad622c625f9a42ec8a3ec96", "0a9f338214df03799f93776725ffa540bbe5c310", "5ce5dbf0a59591c87ac89ec7b5922d20613e1127", "df4340434ae7279d095ebdb2a27acf13bead2340"),
    ("cobalt", "3e16fbbb03b6540b238a914a970daec2d261a5f1", "13e95a90e2aaf848e26663d1e21559a997ab6a23", "80b92df8c67d4fbf2312f107dbaedb7f5298e40f", "fc4c8118fb7d087aa452c144e2ea04db7417e92f", "f88f10dff9a803c6d8cee36970e2c4942dfd100d", "de0bfff7c0adc3f46824aa39e307cc635fc1eb70"),
    ("dawn", "72b57968d42777dcb7b04155bb4936aea95735c6", "638ad9c4845e0afe7074e05985256aa237fbe17f", "ff5d4c6bb875b1ac76d401f28313618d496615a3", "86fe47dd20cbef142fc2d6a7603e9935c837d963", "f8f3b181468a6d5505cdcab7fa9d51c57fce993c", "4e85d1e93774c6faa9316bba6856c7c9ec34e7c5"),
    ("eclipse", "c25a60124153196ccb8851086b2ad6c4f8b4c13f", "9a03f9e900de5ff4e3b88d3e1cf68b98bc67d097", "dd30655c27c175477bb0901256748f037c3b6578", "c39a8470aed38b147838717337b9f3e85b4fb33c", "25eaf27b3279636978ad1449e36283f61e1e73b2", "aabeeab23d814b5add173762742ba35db8a77f67"),
    ("idle_fingers", "0c02b12f530156b0d41ba5d2fe8d7d1f7d054280", "a236413bf672929f742ac440af892b31164199ad", "11afc31ab8a2042b02dd9ec20d3039985f07ee26", "a7737f6de359db744a9323fd178a26fea5f82a86", "e8606835db54a2653d1556ceaf2c9e5a4f0f890a", "251d6e631c4a50369eef718cbdb6046b078dbca6"),
    ("kr_theme", "2aa26bdee6ac9213d328dd119dd4694d5f114683", "07ddfb0c8a71d93d4c63cb01c9ef4a07f8f10476", "a12b6ab935a46a217c53484ae42b0badca90467a", "57ad4be1b888bf6702f94e85415f217f51fa7006", "2c3d667211ada8d76004df62616a3b2b9b188e68", "da7dd1d3925723b7a3c67d789f551736eefe4060"),
    ("mono_industrial", "c58fc1c29c5d7f2e96578f252ae31c56f2015c16", "d9ac5845baf8b2e5a6715dcf79fb1c8e13980b1e", "3e1e5510f798817e3b89243285813151e208eac3", "3eaf1cae368bb0a6a02f2eaeef0ba09f7a556dd3", "d967b2e46430f2eed8b24b49ff8cf01e76810f5b", "d17f39f2bf4f118d7b4d20fbced2eb45f194a041"),
    ("monokai", "e410b51c2b6d747bc6682617a2a2209df25bd206", "5bb1f5f5e43983e1dcc7679c41258fab9d219d43", "346554c48c73169c52f611b34cdb786e9de33ce7", "36b0a23c06d433eb3a4b9f36a3b0e26f3d42c1c7", "4b9062484be170deffec995b3f9a9fe404dc0265", "b41141b005bd44394b082b51d6771353f2fe5abd"),
    ("textmate", "5ffd3523d803e052e7b2afad2db028c70af27c94", "30689c8397d9a88a82da47a29da2bc1eb041cf04", "a7d028c967830813754c4ce390358bc394a1a925", "dafb9fa1e93eb577e071460f6804ba7f125628ac", "cd83f116c08d3ec5a51ef540c5042477f1f0a01a", "47bbae0b57a75e31a0dc22773e519e56e79b7afc"),
    ("twilight", "1455257a32a27cb2b4b957ae9e3bb39f61e445a1", "74e3ff90b6f54eb4e4c8180bb7b80caca6aa8ce4", "e6b09b540b76a11c423508e8934606374f4769a3", "a9637b09fc2aa8218e667dd9ddff743def863f11", "b497826fe5d0c3a9150045a400de6139a0a1d0c7", "766ba9b33846b248fbff79dba37e3e25c91dfbf6"),
)


def historic_header(raw, marker):
    start = b"/* ***** BEGIN LICENSE BLOCK *****"
    end = b"***** END LICENSE BLOCK ***** */\n\n"
    if not raw.startswith(start) or raw.count(end) != 1:
        raise ValueError("Unexpected historical theme header boundary")
    header, body = raw.split(end, 1)
    if marker not in header or not body.startswith(b"define("):
        raise ValueError("Unexpected historical theme license or body")
    return header + end, body


def split_css_source(raw):
    # This is a physical source-text relation, not a JS string decoder.
    # Only the observed backslash/LF continuation is accepted.
    prefix = b'exports.cssText = "'
    if raw.count(prefix) != 1:
        raise ValueError("Expected unique historical CSS assignment")
    tail = raw.split(prefix, 1)[1]
    if tail.count(b'";') != 1:
        raise ValueError("Unexpected historical CSS literal terminator")
    literal = tail.split(b'";', 1)[0]
    restored = literal.replace(b"\\\n", b"\n")
    if b"\\" in restored or b'"' in restored or b"\r" in restored:
        raise ValueError("Unexpected historical CSS escape")
    return restored


def historic_license_research(fetch, source, source_file):
    old_marker = b"Version: MPL 1.1/GPL 2.0/LGPL 2.1"
    bsd_marker = b"Distributed under the BSD license:"
    rows = []
    def pin(revision, name, blob, ext="js"):
        return reference("ajaxorg/ace", revision,
                         "lib/ace/theme/" + name + "." + ext, blob, fetch)
    for name, old_blob, header_blob, pre_split_blob, css_blob, split_blob, bsd_blob in HISTORIC_THEME_LICENSES:
        early = "clouds_mignight" if name == "clouds_midnight" else name
        old, old_pin = pin(HEADER_PARENT, early, old_blob)
        licensed, header_pin = pin(HEADER_COMMIT, early, header_blob)
        header, body = historic_header(licensed, old_marker)
        if body != old:
            raise ValueError("Historical header-only relation failed: " + name)
        inline = b'var cssText = "' in body
        if inline != (name not in {"eclipse", "textmate"}):
            raise ValueError("Historical inline CSS scope drift: " + name)
        pre_split, pre_split_pin = pin(SPLIT_PARENT, name, pre_split_blob)
        _, pre_split_body = historic_header(pre_split, old_marker)
        css, css_pin = pin(SPLIT_COMMIT, name, css_blob, "css")
        if split_css_source(pre_split_body) != css:
            raise ValueError("Historical CSS extraction differs: " + name)
        wrapper, split_pin = pin(SPLIT_COMMIT, name, split_blob)
        _, wrapper_body = historic_header(wrapper, old_marker)
        if ("./" + name + ".css").encode() not in wrapper_body:
            raise ValueError("Historical CSS wrapper reference differs: " + name)
        bsd, bsd_pin = pin(BSD_COMMIT, name, bsd_blob)
        _, bsd_body = historic_header(bsd, bsd_marker)
        if bsd_body != wrapper_body:
            raise ValueError("BSD wrapper body differs: " + name)
        rows.append({"theme": name, "pre_header": old_pin, "licensed_2010": header_pin,
                     "header_only": True, "inline_css_2010": inline,
                     "licensed_before_split": pre_split_pin, "split_css": css_pin,
                     "split_wrapper": split_pin, "bsd_wrapper": bsd_pin,
                     "css_source_transfer_exact": True, "bsd_wrapper_body_equal": True,
                     "disposition": "excluded-reassessment-open" if name == "kr_theme" else "retained-review-open"})
    root, root_pin = reference("ajaxorg/ace", BSD_COMMIT, "LICENSE",
                               "4760be2a6220cf545129b233e20574f2a7bb630e", fetch)
    current, _ = source_file(source, "LICENSE")
    if root != current:
        raise ValueError("Historical BSD root license differs from current")
    return {"themes": rows, "bsd_root_license": root_pin,
            "limitations": ["Header declarations do not prove authority over third-party inputs.",
                            "CSS transfer is source-text equality, not runtime JS decoding.",
                            "Later changes and original-input license exceptions remain separate.",
                            "krTheme remains physically excluded; reassessment is not restoration."]}


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
            "grouped_textmate": grouped_textmate(source, fetch, source_file),
            "historical_ace_theme_licenses": historic_license_research(fetch, source, source_file),
            "limitations": ["Pinned reference identity and comparisons are not historical lineage or license clearance.",
                            "Differences are evidence, not failures; pin drift fails closed."]}
