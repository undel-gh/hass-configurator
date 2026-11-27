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
    # Match only the literal and its own terminator. Later JS statements
    # may independently end in a quote and semicolon.
    match = re.match(rb'((?:\\\n|[^"\\\r\n])*)";(?=\n|$)', tail)
    if match is None:
        raise ValueError("Unexpected historical CSS literal terminator")
    literal = match.group(1)
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



# Remaining wrappers in the September 2012 relicensing merge tree.
# These pins establish a wrapper declaration, not an inline CSS grant.
ADDITIONAL_BSD_THEME_WRAPPERS = (
    ("chrome", "4f26b06c45ebd09b24b9238ace0fd1705f4ff70f"),
    ("crimson_editor", "943930d9ec067b2d08c7c803685638bfbdd1a2c7"),
    ("dreamweaver", "25a7fcba3157c7004746b1d128d9077b3523b48e"),
    ("github", "b5839dd40a0c70a3eed3158bcce67bd0a013572f"),
    ("merbivore", "254fdad0827be303d323331f9f0115a1e4ecb783"),
    ("merbivore_soft", "d5e7dbbd0333c3f2e33161e0b26b7dfbbf88a226"),
    ("pastel_on_dark", "2867215093c3388a777910d06ed8cdcfd10f3933"),
    ("solarized_dark", "2b09b3378bada7b233c822fa5c32e4a99cd9028c"),
    ("solarized_light", "e4095c1e4f274b8b0b3552f93e96517f10b755b3"),
    ("tomorrow", "e740a080243df08ea074d3b1fc6e47fcc989579f"),
    ("tomorrow_night", "b943b414ef5f9e2fdad5e6c9182d46ba40e5cdef"),
    ("tomorrow_night_blue", "e3874f09029f430cbf61112be1cac46fab744ee1"),
    ("tomorrow_night_bright", "5f18ee4496108add8797f9b740a7fd1057b6fb25"),
    ("tomorrow_night_eighties", "fff11892a272cb6eef01c4fe895c711066b7484f"),
    ("vibrant_ink", "28bd0496a30b9adbb47f1c8a68959623204e7b56"),
)


def additional_bsd_wrappers(fetch):
    rows = []
    for name, blob in ADDITIONAL_BSD_THEME_WRAPPERS:
        raw, pin = reference("ajaxorg/ace", BSD_COMMIT,
                             "lib/ace/theme/" + name + ".js", blob, fetch)
        header, body = historic_header(raw, b"Distributed under the BSD license:")
        if (b"Copyright (c) 2010, Ajax.org B.V." not in header or
                ("./" + name + ".css").encode() not in body):
            raise ValueError("Unexpected historical BSD wrapper: " + name)
        rows.append({"theme": name, "wrapper": pin,
                     "declaration": "BSD-3-Clause", "css_scope": "separate-file",
                     "license_status": "review-open"})
    return rows


def krtheme_input_relation(original, imported):
    # Only these two exact value substitutions are permitted. Do not
    # collapse metadata, scopes, whitespace or unrelated settings.
    changes = ((b"<string>#000000</string>", b"<string>#0B0A09</string>"),
               (b"<string>#E97A5459</string>", b"<string>#FFB16F52</string>"))
    expected = original
    for old, new in changes:
        if expected.count(old) != 1:
            raise ValueError("Unexpected krTheme original color multiplicity")
        expected = expected.replace(old, new, 1)
    if expected != imported:
        raise ValueError("Unexpected krTheme input relation")
    return {"exact_except": ["background", "invisibles"],
            "plist": compare_plist(original, imported),
            "disposition": "excluded-reassessment-open"}


def krtheme_reassessment(fetch, source, source_file):
    original, origin_pin = reference("kennethreitz-archive/krTheme.tmTheme",
        "ec21b6d65a3d38d699b47b76026b2746f38d1681", "krTheme.tmTheme",
        "6b4da423a8e7a9f005ed0cd20436a74bd2d1def4", fetch)
    imported, import_pin = reference("ajaxorg/ace",
        "cba64d86be96864665b26e109603f021e1141e67", "tool/tmthemes/krTheme.tmTheme",
        "65c5c9b6aac1d42dc65c1ee537093404fe207b64", fetch)
    current, blob = source_file(source, "tool/tmthemes/krTheme.tmTheme")
    if current != imported or blob != "65c5c9b6aac1d42dc65c1ee537093404fe207b64":
        raise ValueError("Current krTheme input drift")
    css, _ = source_file(source, "src/theme/kr_theme-css.js")
    css_pin = verify_blob(css, "3f7d001d2ab54d56e56f9f69835964b931bde849")
    readme, readme_pin = reference("kennethreitz-archive/krTheme.tmTheme",
        "ec21b6d65a3d38d699b47b76026b2746f38d1681", "Readme.md",
        "b9618416c8e135efd9e84520495b551415eb1bd4", fetch)
    if b"Copyright 2010 Kenneth Reitz. All Rights Reserved." not in readme:
        raise ValueError("Historical krTheme author notice drift")
    return {"author_input": origin_pin, "ace_import": import_pin,
            "current_css_source": css_pin, "author_readme": readme_pin,
            "relation": krtheme_input_relation(original, imported),
            "limitations": ["Near-identical plist is evidence of close lineage, not copying direction.",
                            "Ace historical declarations do not establish upstream author permission.",
                            "Research only; excluded runtime payload is not restored."]}



# Earliest located wrapper under its current name (or re-addition for
# Gruvbox). iPlastic is a rename; a snapshot is not proof of first creation.
# name, revision, wrapper path/blob, separate CSS path/blob, declaration.
POST_BSD_THEMES = (
    ("ambiance", "df4816a769c0ddc5a8453b27054a550862a41f0e", "lib/ace/theme/ambiance.js", "4c74d6f8ae8718cd5f209b04c571887951352e7a", "lib/ace/theme/ambiance.css", "fba5dcc35a08302984c7b43278d2099c51e7109c", "mit-labelled-bsd"),
    ("chaos", "ba4c463ba9f7190c53d7455cead138a4ddea6bff", "lib/ace/theme/chaos.js", "9ee83720c367e8f435307755b51716dc153e25cd", "lib/ace/theme/chaos.css", "a2b6c9eb8a3528188e3a7a6a97e540f6e14dc174", "mit-labelled-bsd"),
    ("cloud9_day", "87ad55daf243bdc619e15fbf220dc5ded235ed4c", "lib/ace/theme/cloud9_day.js", "7e999aec70b0a2cbf49d6a27458c29412aaa3475", "lib/ace/theme/cloud9_day.css", "8df0dbe5ddaaddb6495193073b95a2ca49607081", "ajax-bsd"),
    ("cloud9_night", "87ad55daf243bdc619e15fbf220dc5ded235ed4c", "lib/ace/theme/cloud9_night.js", "b88197f631631ef79af09226b74b5761313d05de", "lib/ace/theme/cloud9_night.css", "5577fd2d454b1ee3f063ac33b20e20f9ab75c2ef", "ajax-bsd"),
    ("cloud9_night_low_color", "87ad55daf243bdc619e15fbf220dc5ded235ed4c", "lib/ace/theme/cloud9_night_low_color.js", "7d24cc55ce3b2b67f54512bc357fa2c59385036b", "lib/ace/theme/cloud9_night_low_color.css", "bbeaf2690914b336d5dfbe5087c40a17ea245225", "ajax-bsd"),
    ("cloud_editor", "b0ee067fadaf9593ed2207f363a402eb9ab8d57a", "src/theme/cloud_editor.js", "23a5eb5a835ebf0d87fb4ad621f97ac261bea157", "src/theme/cloud_editor-css.js", "4ec44de04bda12403d959bbc60839f9038b65d42", "root-only"),
    ("cloud_editor_dark", "b0ee067fadaf9593ed2207f363a402eb9ab8d57a", "src/theme/cloud_editor_dark.js", "9aa93b85cd3fe1fb8dff8e4ca3f705ebea80eabf", "src/theme/cloud_editor_dark-css.js", "14df54d84370abb16788bdaeee50d3f15cdcf29c", "root-only"),
    ("dracula", "3f3faa50800f19f395de95b64be6789cc7665a64", "lib/ace/theme/dracula.js", "24b0e5dc57fcd1ec6eba070642a366058eb6b08b", "lib/ace/theme/dracula.css", "17d7df82f626314e7ffafecb96f61e61d61c6373", "ajax-bsd"),
    ("github_dark", "3f29428f1d9e6c1c16d1d37be8e54e6b435a6a05", "src/theme/github_dark.js", "cb66c090ed5e9139180ea9099f837ec0619207f2", "src/theme/github_dark.css.js", "116ab49a9449e6b59f46b868ed7a5050a6467a1a", "root-only"),
    ("github_light_default", "e78b1acabe5f599b3c5da31a7839a3e9274fc86e", "src/theme/github_light_default.js", "434e31677f54e553c16d38039d5cd3ccdac577e5", "src/theme/github_light_default-css.js", "a44571416044088b456a27ed4edc4e8789fb652e", "root-only"),
    ("gob", "75c000988ba29a7ed447d7dc7ebf9857cb5a664b", "lib/ace/theme/gob.js", "4b8e487d230fcfab530e0abc0f56cebfcb7c772e", "lib/ace/theme/gob.css", "2c2b50de80de07cebedca07767f313456782fa75", "ajax-bsd"),
    ("gruvbox", "d9199ac2d8efb42f2781126ee125cff5f00ceef9", "lib/ace/theme/gruvbox.js", "67d90430a208226366874409852af3b748f502d3", "lib/ace/theme/gruvbox.css", "48a4161e6866f562d091fccf506d83f4559c447f", "mit-labelled-bsd"),
    ("gruvbox_dark_hard", "f03ae9d3f5a76e12d3fbbdff41cbb1c070530c27", "lib/ace/theme/gruvbox_dark_hard.js", "2cd402ab9b96b080709fd2962cf0444d4b089b0e", "lib/ace/theme/gruvbox_dark_hard.css", "a0f30186b1a5fbee3e765b2b35bc7295165ec521", "ajax-bsd"),
    ("gruvbox_light_hard", "f03ae9d3f5a76e12d3fbbdff41cbb1c070530c27", "lib/ace/theme/gruvbox_light_hard.js", "e33217c61b4e9aa1f0a5d68da0dfb21b55e8bf90", "lib/ace/theme/gruvbox_light_hard.css", "8a106cadd7713c986ae14671cc12d05e1300fc80", "ajax-bsd"),
    ("iplastic", "fb5f272f815d4ea44eb0e1279cf858137624f37a", "lib/ace/theme/iplastic.js", "ff784196953be3797d3db8dbf6617edd78aa72fb", "lib/ace/theme/iplastic.css", "b07dc8f926c47006c1e8d16eb11493170f3dcdff", "ajax-bsd"),
    ("katzenmilch", "4d88770435f1700b8de66630d97fef8b3d82b890", "lib/ace/theme/katzenmilch.js", "4787483dac3b41518a56a8d1f016f5de9cdb88bc", "lib/ace/theme/katzenmilch.css", "e2526b93e20ea1bcd9d8673928d62951a9bdb33c", "ajax-bsd"),
    ("kuroir", "4d88770435f1700b8de66630d97fef8b3d82b890", "lib/ace/theme/kuroir.js", "cef6a50b5741eba87d688ef1ddb285c91a8c3a5b", "lib/ace/theme/kuroir.css", "fe2ba3027bbb64f0e59b0d6812f5ba227b993934", "ajax-bsd"),
    ("nord_dark", "1f20fd2c15bb8acd1178cf92d5438ca3acd894ac", "lib/ace/theme/nord_dark.js", "70af5da870c8c2d3a0af70a1e0a21d0b4ccb2747", "lib/ace/theme/nord_dark.css", "f1b8efa13e5ca5436faef70be0984e5ed1033f9f", "ajax-bsd"),
    ("one_dark", "87b220585c5ae0af7b9c3ddb7889aa1fb0715bf2", "lib/ace/theme/one_dark.js", "a088df130a0d35645ffa2fb8d2bcfc52a81c99da", "lib/ace/theme/one_dark.css", "897f45a49de86f85f0e7c1963247bd58a46966ab", "ajax-bsd"),
    ("sqlserver", "ede82e7137516dcc0f4e6afa155fa4e93f8d35c4", "lib/ace/theme/sqlserver.js", "ab657483aa140c8b38aed5fb7f992e34492c8660", "lib/ace/theme/sqlserver.css", "a752280d25d1e8953a0e3ad471baa83330e48d72", "ajax-bsd"),
    ("terminal", "6f6ec76f7b84f02789297128882d8b89475fcbb6", "lib/ace/theme/terminal.js", "d7ff36ae392e2bb38a89e5335fbdf8ecc85b9aaa", "lib/ace/theme/terminal.css", "911ef755fcf881033c76b1e4f4954197809e5faf", "ajax-bsd"),
    ("xcode", "ecfdc5fbc4691b7d3933416b65da340768111f04", "lib/ace/theme/xcode.js", "c6cba5b9cd68e24700684410ce20bf5118636ffa", "lib/ace/theme/xcode.css", "c457d2f7a0c60f726d35a3b8dbe1bff0158c4247", "ajax-bsd"),
)


def later_wrapper_declaration(raw):
    if (b"Copyright 2011 Irakli Gozalishvili." in raw
            and b"Permission is hereby granted" in raw
            and b"Distributed under the BSD license:" in raw):
        return "mit-labelled-bsd"
    if (b"Copyright (c) 2010, Ajax.org B.V." in raw
            and b"Distributed under the BSD license:" in raw
            and b"Redistribution and use in source and binary forms" in raw
            and b"Neither the name of Ajax.org" in raw):
        return "ajax-bsd"
    if re.search(rb"copyright|licen[cs]e|permission is hereby", raw, re.I):
        raise ValueError("Unclassified historical theme wrapper declaration")
    return "root-only"


def post_bsd_theme_research(fetch, source, source_file):
    rows = []
    roots = {}
    current_license, _ = source_file(source, "LICENSE")
    for name, revision, js_path, js_blob, css_path, css_blob, expected in POST_BSD_THEMES:
        js, js_pin = reference("ajaxorg/ace", revision, js_path, js_blob, fetch)
        css, css_pin = reference("ajaxorg/ace", revision, css_path, css_blob, fetch)
        declaration = later_wrapper_declaration(js)
        if declaration != expected:
            raise ValueError("Historical wrapper declaration drift: " + name)
        css_name = css_path.rsplit("/", 1)[-1]
        if not any(candidate.encode() in js for candidate in
                   (css_name, css_name.removesuffix(".js"))):
            raise ValueError("Historical CSS reference drift: " + name)
        markers = re.compile(rb"copyright|licen[cs]e|permission is hereby|based on|adapted from|ported from", re.I)
        css_hits = [{"line": i, "text": line.decode("utf-8", errors="replace")}
                    for i, line in enumerate(css.splitlines(), 1) if markers.search(line)]
        if bool(css_hits) != (name == "dracula"):
            raise ValueError("Historical CSS marker scope drift: " + name)
        if expected == "root-only" and revision not in roots:
            license_raw, roots[revision] = reference("ajaxorg/ace", revision, "LICENSE",
                "4760be2a6220cf545129b233e20574f2a7bb630e", fetch)
            if license_raw != current_license:
                raise ValueError("Historical root license differs: " + name)
        rows.append({"theme": name, "wrapper": js_pin, "css": css_pin,
                     "wrapper_declaration": declaration, "css_marker_hits": css_hits,
                     "root_license": roots.get(revision) if expected == "root-only" else None,
                     "license_status": "review-open"})
    # PR #5597 identifies the official VS Code theme, not a precise release.
    # This pre-port repository snapshot supplies a historical license lead.
    _, primer = reference("primer/github-vscode-theme",
        "38b50d41bdc6b190b7351e220956af043221d763", "LICENSE",
        "fcc8ec1341626589ac053947aea5279928966bc3", fetch)
    return {"themes": rows, "github_light_default_license_reference": primer,
            "limitations": ["Snapshot under current name, not necessarily first creation.",
                            "Wrapper declarations do not establish separate CSS or external rights.",
                            "Root-only means no individual declaration found in pinned wrapper.",
                            "Primer reference is not exact port source/version; notice retained separately."]}


def verify_theme_history_coverage(retained, early, additional, later):
    names = [row["theme"] for group in (early, additional, later) for row in group]
    if len(names) != len(set(names)) or set(names) != set(retained) | {"kr_theme"}:
        raise ValueError("Historical theme coverage differs from retained family")
    if "kr_theme" in retained:
        raise ValueError("krTheme remains excluded during reassessment")
    return {"retained_count": len(retained), "historical_count": len(names),
            "excluded": ["kr_theme"], "retained": sorted(retained),
            "status": "historical-snapshot-coverage-not-license-clearance"}



def primer_port_evidence(fetch, source, source_file):
    import json
    repo = "primer/github-vscode-theme"
    rev = "38b50d41bdc6b190b7351e220956af043221d763"
    palette, palette_pin = reference(repo, rev, "src/classic/colors.json",
        "56b4c173dbb931fea43ca95f7deada58a543a998", fetch)
    package, package_pin = reference(repo, rev, "package.json",
        "9ba47ac5951a4b5e8b89729090a788ad73778d85", fetch)
    meta = json.loads(package)
    if (meta["publisher"], meta["name"], meta["version"]) != ("GitHub", "github-vscode-theme", "6.3.4"):
        raise ValueError("Primer reference identity drift")
    if not any(row["label"] == "GitHub Light Default" for row in meta["contributes"]["themes"]):
        raise ValueError("Primer reference theme missing")
    css, css_pin = reference("ajaxorg/ace", "e78b1acabe5f599b3c5da31a7839a3e9274fc86e",
        "src/theme/github_light_default-css.js", "a44571416044088b456a27ed4edc4e8789fb652e", fetch)
    current, _ = source_file(source, "src/theme/github_light_default-css.js")
    if current != css:
        raise ValueError("GitHub Light Default CSS changed since introduction")
    values = {v.lower() for group in json.loads(palette).values()
              for v in (group if isinstance(group, list) else [group])}
    values = {"#ffffff" if v == "#fff" else v for v in values}
    colors = {v.decode("ascii").lower() for v in re.findall(rb"#[0-9a-f]{6}\b", css, re.I)}
    if (len(colors), len(colors & values)) != (18, 15):
        raise ValueError("Primer bounded palette comparison drift")
    return {"palette": palette_pin, "package": package_pin, "css": css_pin,
            "historical_reference_version": meta["version"], "port_version": None,
            "css_hex_colors": sorted(colors), "shared": sorted(colors & values),
            "not_shared": sorted(colors - values), "current_css_equal": True,
            "limitations": ["PR #5597 identifies official extension, not exact variant/version.",
                            "Color overlap alone is not source or rights proof."]}


def sphinx_krtheme_reference(fetch):
    repo = "kennethreitz/kr-sphinx-themes"
    rev = "010ddb33d2aaca5d3ba7e18c372bcb8850d6b07b"
    license_raw, license_pin = reference(repo, rev, "LICENSE",
        "81f4d30592d3b4270b2f52a135769c1b3df2c36b", fetch)
    readme, readme_pin = reference(repo, rev, "README.rst",
        "e8179f9690f0d3b8b9f5873cd4939614e8aa8027", fetch)
    style, style_pin = reference(repo, rev, "flask_theme_support.py",
        "33f47449c11d241e36c83d7f95d819bbe56e2c8f", fetch)
    if (b"Copyright (c) 2010 Kenneth Reitz." not in license_raw
            or b"Copyright (c) 2010 by Armin Ronacher." not in license_raw
            or b"Redistribution and use" not in license_raw
            or b"based on tango style" not in style):
        raise ValueError("Sphinx krTheme reference drift")
    return {"license": license_pin, "readme": readme_pin, "pygments_style": style_pin,
            "scope": "separate-sphinx-project-not-textmate-grant"}


def verify_theme_dispositions(matrix, embedded, historical):
    if (matrix["schema"] != 1 or matrix["review_status"] != "independent-review-pending"
            or matrix["ace_source_commit"] != "68d7fd1c0f5ac50cdb610bf06b86074eab3be652"):
        raise ValueError("Unexpected theme disposition identity")
    expected = {}
    for group in (historical["historical_ace_theme_licenses"]["themes"],
                  historical["additional_bsd_theme_wrappers"]):
        for row in group:
            expected[row["theme"]] = "ajax-bsd"
    for row in historical["post_bsd_themes"]["themes"]:
        expected[row["theme"]] = row["wrapper_declaration"]
    names = [row["theme"] for row in matrix["rows"]]
    if (len(names) != len(set(names)) or set(names) != set(expected)
            or set(names) != set(historical["theme_history_coverage"]["retained"]) | {"kr_theme"}):
        raise ValueError("Theme disposition coverage mismatch")
    for row in matrix["rows"]:
        theme = row["theme"]
        excluded = theme == "kr_theme"
        if (row["distribution"] != ("excluded" if excluded else "retained")
                or row["disposition"] != ("excluded-reassessment-open" if excluded else "retained-review-open")
                or row["historical_declaration"] != expected[theme]
                or row["review_priority"] not in {"standard", "elevated"}
                or not row["remaining_review"].strip()):
            raise ValueError("Unexpected theme disposition: " + theme)
        components = sorted(c["id"] for c in embedded["components"] if c["kind"] == "library"
                            and any(loc["file"] == "vendor/ace/theme-" + theme + ".js"
                                    for loc in c["locations"]))
        if row["additional_components"] != components or (excluded and components):
            raise ValueError("Theme additional notice mapping mismatch: " + theme)
    return matrix


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
            "additional_bsd_theme_wrappers": additional_bsd_wrappers(fetch),
            "krtheme_reassessment": krtheme_reassessment(fetch, source, source_file),
            "post_bsd_themes": post_bsd_theme_research(fetch, source, source_file),
            "primer_port_evidence": primer_port_evidence(fetch, source, source_file),
            "sphinx_krtheme_reference": sphinx_krtheme_reference(fetch),
            "limitations": ["Pinned reference identity and comparisons are not historical lineage or license clearance.",
                            "Differences are evidence, not failures; pin drift fails closed."]}
