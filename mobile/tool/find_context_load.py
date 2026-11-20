from pathlib import Path
import re

for path in Path("lib/features").rglob("*_page.dart"):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"Future<[^\n]*> _load\(\)[^\n]*", text)
    if not match:
        continue
    snippet = text[match.start() : match.start() + 900]
    if "context." in snippet:
        print("---", path)
        print("\n".join(snippet.splitlines()[:20]))
