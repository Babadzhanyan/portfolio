#!/usr/bin/env python3
"""Единый счётчик версии ассетов: HTML, data-v у самопроверки и version.json.

Запуск: python3 bump.py
Ставит сегодняшнюю дату и следующий порядковый номер, потом гоняет check_site.py.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
PAGES = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)

current = set()
for page in PAGES:
    current |= set(re.findall(r"\?v=([0-9.]+)", page.read_text(encoding="utf-8")))

today = date.today().strftime("%Y%m%d")
serial = 1
for value in current:
    stamp, _, num = value.partition(".")
    if stamp == today and num.isdigit():
        serial = max(serial, int(num) + 1)
new = f"{today}.{serial}"

for page in PAGES:
    text = page.read_text(encoding="utf-8")
    updated = re.sub(r"\?v=[0-9.]+", f"?v={new}", text)
    updated = re.sub(r'data-v="[0-9.]+"', f'data-v="{new}"', updated)
    if updated != text:
        page.write_text(updated, encoding="utf-8")

(ROOT / "version.json").write_text(json.dumps({"assets": new}) + "\n", encoding="utf-8")

print(f"было {sorted(current)} → стало {new}")
sys.exit(subprocess.call([sys.executable, str(ROOT / "check_site.py")]))
