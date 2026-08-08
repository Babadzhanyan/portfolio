#!/usr/bin/env python3
"""Проверка сайта перед деплоем: паритет русской и английской версий плюс канон стиля.

Запуск: python3 check_site.py
Ноль на выходе – можно деплоить. Любая строка ДЕФЕКТ – чинить до пуша.
"""
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
PAGES = ["index.html", "en/index.html", "career/index.html", "en/career/index.html",
         "blog/index.html", "blog/proverka-prognoza-prodavtsa/index.html", "404.html"]
BLOCKS = {"ind-list", "artifacts", "steps", "formats", "edge-grid", "offer-grid",
          "evidence-ledger", "field-strip", "field-shot", "faq", "case-grid",
          "stream-tabs", "stream-panel", "reasons", "contact-inner",
          "profile-credentials", "case-card", "claim", "project-facts"}
FORBIDDEN = {"—": "em-dash", "·": "middle dot", "•": "bullet"}

defects = []


def note(msg):
    defects.append(msg)


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def shape(html):
    sections = re.findall(r'<section[^>]*\bid="([^"]+)"', html)
    counts = Counter()
    for m in re.finditer(r'class="([^"]+)"', html):
        for cls in m.group(1).split():
            if cls in BLOCKS:
                counts[cls] += 1
    return sections, counts, len(re.findall(r"<h2\b", html)), len(re.findall(r"<h3\b", html))


ru, en = read("index.html"), read("en/index.html")
ru_sec, ru_cnt, ru_h2, ru_h3 = shape(ru)
en_sec, en_cnt, en_h2, en_h3 = shape(en)

if ru_sec != en_sec:
    note(f"ДЕФЕКТ секции расходятся: только RU {[s for s in ru_sec if s not in en_sec]}, "
         f"только EN {[s for s in en_sec if s not in ru_sec]}")
for key in sorted(set(ru_cnt) | set(en_cnt)):
    if ru_cnt.get(key, 0) != en_cnt.get(key, 0):
        note(f"ДЕФЕКТ блок {key}: RU {ru_cnt.get(key, 0)}, EN {en_cnt.get(key, 0)}")
if (ru_h2, ru_h3) != (en_h2, en_h3):
    note(f"ДЕФЕКТ заголовки: RU h2={ru_h2} h3={ru_h3}, EN h2={en_h2} h3={en_h3}")
if ru_cnt.get("case-card") != 18:
    note(f"ДЕФЕКТ кейсов на русской: {ru_cnt.get('case-card')} вместо 18")

versions = set()
for page in PAGES:
    html = read(page)
    versions |= set(re.findall(r"\?v=([0-9.]+)", html))
    for sym, name in FORBIDDEN.items():
        if sym in html:
            note(f"ДЕФЕКТ {page}: запрещённый символ {name}")
    if " а не " in html:
        note(f"ДЕФЕКТ {page}: противопоставление «а не»")
    if re.search(r"<main id=\"main\"(?![^>]*tabindex)", html):
        note(f"ДЕФЕКТ {page}: у main нет tabindex=-1")
    for term in re.findall(r'<[^>]*tooltip-term[^>]*>', html):
        if "data-definition" in term and "aria-describedby" not in term:
            note(f"ДЕФЕКТ {page}: подсказка без aria-describedby")
            break
if len(versions) > 1:
    note(f"ДЕФЕКТ версии ассетов расходятся: {sorted(versions)}")

for sentence_start in re.findall(r"(?:^|[.!?]\s|>)(I\s)", read("en/index.html")):
    note("ДЕФЕКТ английская версия: предложение начинается с «I»")
    break

css = read("assets/site.css")
for value in re.findall(r"letter-spacing:\s*([^;}]+)", css):
    value = value.strip()
    if value in ("0", "normal") or value.startswith("var(") or value.startswith("-"):
        continue
    note(f"ДЕФЕКТ положительный letter-spacing: {value}")
for value in re.findall(r"--(?:ls|tr)-[a-z0-9]+:\s*([^;}]+)", css):
    if not value.strip().startswith("-"):
        note(f"ДЕФЕКТ положительный трекинг в токене: {value}")

used = set(re.findall(r"var\((--[a-z0-9-]+)\s*\)", css))  # с фолбэком – не проблема
declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
missing = sorted(used - declared)
if missing:
    note(f"ДЕФЕКТ переменные без объявления: {missing}")

if defects:
    print("\n".join(defects))
    print(f"\nвсего дефектов: {len(defects)}")
    sys.exit(1)

print(f"чисто: секций {len(ru_sec)}, кейсов {ru_cnt.get('case-card')} в обеих версиях, "
      f"версия ассетов {versions.pop()}")
