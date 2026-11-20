import re
import os

path = os.path.join(os.environ["TEMP"], "cur.xml")
text = open(path, encoding="utf-8").read()
for match in re.finditer(r"<node[^>]*>", text):
    node = match.group(0)
    values = []
    for name in ("text", "content-desc"):
        found = re.search(rf'{name}="([^"]*)"', node)
        if found and found.group(1):
            values.append(f"{name}={found.group(1)!r}")
    bounds = re.search(r'bounds="([^"]*)"', node)
    if values:
        print(" | ".join(values), bounds.group(1) if bounds else "")
