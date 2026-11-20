from pathlib import Path
import re

root = Path("lib")
loc = (root / "core/localization/app_localizations.dart").read_text(encoding="utf-8")
# extract each map block by splitting at _en/_ar definitions
en_match = re.search(r"const Map<String, String> _en = \{(.*?)\n\};", loc, re.S)
ar_match = re.search(r"const Map<String, String> _ar = \{(.*?)\n\};", loc, re.S)
assert en_match and ar_match


def keys_of(block: str) -> set[str]:
    return set(re.findall(r"^\s*'([^']+)'\s*:", block, re.M))


en = keys_of(en_match.group(1))
ar = keys_of(ar_match.group(1))
used = set()
for path in root.rglob("*.dart"):
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\.(?:t|tr)\(\s*'([^']+)'", text):
        used.add(match.group(1))
print("EN keys:", len(en), "AR keys:", len(ar))
print("missing EN:", sorted(used - en))
print("missing AR:", sorted(used - ar))
print("only EN:", sorted(en - ar))
print("only AR:", sorted(ar - en))
print("unused:", sorted(en - used))
