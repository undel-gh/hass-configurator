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
            "limitations": ["Pinned reference identity and comparisons are not historical lineage or license clearance.",
                            "Differences are evidence, not failures; pin drift fails closed."]}
