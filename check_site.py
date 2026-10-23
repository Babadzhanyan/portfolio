#!/usr/bin/env python3
"""Проверка сайта перед публикацией: самостоятельная структура языковых версий и правила стиля.

Запуск: python3 check_site.py
Ноль на выходе подтверждает готовность проверки. Строка «Дефект» указывает требуемую правку.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).parent
PAGES = ["index.html", "en/index.html", "career/index.html", "en/career/index.html",
         "blog/index.html", "blog/proverka-prognoza-prodavtsa/index.html", "404.html"]
BLOCKS = {"ind-list", "artifacts", "steps", "formats", "edge-grid", "offer-grid",
          "evidence-ledger", "field-strip", "field-shot", "faq", "case-grid",
          "stream-tabs", "stream-panel", "reasons", "contact-inner",
          "profile-credentials", "case-card", "claim", "project-facts",
          "featured-project", "proof-flow"}
FORBIDDEN = {"—": "длинное тире", "·": "средняя точка", "•": "маркер"}
STREAMS = ("deals", "strategy", "transformation", "efficiency")
CASE_IDS = {
    "case-fmcg-buy-side", "case-apparel-sell-side", "case-consumer-buy-side",
    "case-hotel-valuation", "case-glonass-strategy", "case-b2b-saas",
    "case-video-streaming-product-strategy", "case-agri-market-model",
    "case-middle-east-sustainability", "case-regional-transport-strategy",
    "case-taxi-launch-model", "case-yandex-sales", "case-steel-transformation",
    "case-telecom-analyst-training", "case-glonass-incentives",
    "case-developer-workforce", "case-uzbek-bank-kpi", "case-kazakhstan-media-bi",
}
HOME_SECTIONS = {"evidence", "industries", "about", "services",
                 "field", "how", "faq", "contact"} | {"stream-" + s for s in STREAMS}
HOME_BLOCKS = {"ind-list": 1, "artifacts": 2, "steps": 1, "formats": 1,
               "evidence-ledger": 1, "field-strip": 1,
               "field-shot": 3, "faq": 1, "case-grid": 4, "stream-tabs": 1,
               "stream-panel": 4, "reasons": 1, "contact-inner": 1,
               "profile-credentials": 1, "case-card": 18, "claim": 13,
               "project-facts": 19}

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


def attributes(tag):
    return dict(re.findall(r'([\w-]+)="([^"]*)"', tag))


def check_home(page, html):
    sections, counts, h2, h3 = shape(html)
    russian = page == "index.html"
    required = HOME_SECTIONS | ({"selected"} if russian else {"offer"})
    missing = sorted(required - set(sections))
    if missing:
        note(f"Дефект {page}: требуются секции {missing}")
    ids = set(re.findall(r'(?<![\w-])id="([^"]+)"', html))
    required_ids = CASE_IDS | {"main", "top", "navmenu", "offer", "caseModal", "caseModalTitle", "shareStatus", "tip"}
    missing = sorted(required_ids - ids)
    if missing:
        note(f"Дефект {page}: требуются идентификаторы {missing}")
    expected = {**HOME_BLOCKS, "edge-grid": 0 if russian else 1,
                "offer-grid": 0 if russian else 1,
                "featured-project": 3 if russian else 0,
                "proof-flow": 3 if russian else 0}
    for key, count in expected.items():
        if counts.get(key, 0) != count:
            note(f"Дефект {page}: блок {key}, получено {counts.get(key, 0)}, требуется {count}")
    minimum = (9, 10) if russian else (8, 8)
    if h2 < minimum[0] or h3 < minimum[1]:
        note(f"Дефект {page}: заголовки h2={h2}, h3={h3}, требуется минимум {minimum}")
    tabs = [attributes(t) for t in re.findall(r'<[^>]+\brole="tab"[^>]*>', html)]
    tablists = [attributes(t) for t in re.findall(r'<[^>]+\brole="tablist"[^>]*>', html)]
    if len(tablists) != 1 or not tablists[0].get("aria-label", "").strip():
        note(f"Дефект {page}: требуется одна именованная группа вкладок")
    panels = {attributes(t).get("id"): t for t in re.findall(r'<[^>]+\brole="tabpanel"[^>]*>', html)}
    if len(tabs) != 4 or len(panels) != 4:
        note(f"Дефект {page}: требуется четыре вкладки и четыре панели")
    selected = [t for t in tabs if t.get("aria-selected") == "true"]
    if len(selected) != 1:
        note(f"Дефект {page}: требуется одна выбранная вкладка")
    for stream in STREAMS:
        tab = next((t for t in tabs if t.get("id") == "tab-" + stream), {})
        panel = panels.get("stream-" + stream, "")
        active = tab.get("aria-selected") == "true"
        if (tab.get("aria-controls") != "stream-" + stream
                or tab.get("aria-selected") not in {"true", "false"}
                or tab.get("tabindex") != ("0" if active else "-1")
                or attributes(panel).get("aria-labelledby") != "tab-" + stream
                or bool(re.search(r"\bhidden(?:\s|>)", panel)) == active):
            note(f"Дефект {page}: вкладка {stream} требует согласованных связей и начального состояния")


ru, en = read("index.html"), read("en/index.html")
ru_sec, ru_cnt, ru_h2, ru_h3 = shape(ru)
en_sec, en_cnt, en_h2, en_h3 = shape(en)

check_home("index.html", ru)
check_home("en/index.html", en)

versions = set()
for page in PAGES:
    html = read(page)
    page_ids = Counter(re.findall(r'(?<![\w-])id="([^"]+)"', html))
    duplicate_ids = [key for key, count in page_ids.items() if count > 1]
    if duplicate_ids:
        note(f"Дефект {page}: повторяются идентификаторы {duplicate_ids}")
    for relation, value in re.findall(r'\b(aria-labelledby|aria-describedby|aria-controls)="([^"]+)"', html):
        missing = sorted(set(value.split()) - set(page_ids))
        if missing:
            note(f"Дефект {page}: связь {relation} требует идентификаторы {missing}")
    versions |= set(re.findall(r"\?v=([0-9.]+)", html))
    for sym, name in FORBIDDEN.items():
        if sym in html:
            note(f"Дефект {page}: запрещённый символ {name}")
    if " а не " in html:
        note(f"Дефект {page}: противопоставление «а не»")
    if re.search(r"<main id=\"main\"(?![^>]*tabindex)", html):
        note(f"Дефект {page}: main требует tabindex=-1")
    for term in re.findall(r'<[^>]*tooltip-term[^>]*>', html):
        if "data-definition" in term and "aria-describedby" not in term:
            note(f"Дефект {page}: подсказка требует aria-describedby")
            break
if len(versions) > 1:
    note(f"Дефект версии ассетов расходятся: {sorted(versions)}")
declared_version = json.loads(read("version.json"))["assets"]
if versions != {declared_version}:
    note(f"Дефект version.json {declared_version} против data-v {sorted(versions)}")
for page in PAGES:
    html = read(page)
    if "v-reload" not in html:
        note(f"Дефект {page}: требуется самопроверка свежести")
    elif html.count("v-reload") != 2:
        note(f"Дефект {page}: самопроверка вставлена дважды")
    if f'data-v="{declared_version}"' not in html:
        note(f"Дефект {page}: data-v требует значения version.json")

CAREER_BLOCKS = {"path-item", "path-cases", "path-note", "path-what", "path-where",
                 "path-when", "skill-card", "skill-label", "brand-item", "brand-logo", "cv-head"}
def career_shape(html):
    counts = Counter()
    for m in re.finditer(r'class="([^"]+)"', html):
        for cls in m.group(1).split():
            if cls in CAREER_BLOCKS:
                counts[cls] += 1
    return counts
for page, path_cases, skill_cards in [("career/index.html", 4, 3), ("en/career/index.html", 6, 4)]:
    html = read(page)
    counts = career_shape(html)
    expected = {"path-item": 6, "path-what": 6, "path-where": 6, "path-when": 6,
                "path-note": 6, "path-cases": path_cases, "skill-card": skill_cards,
                "skill-label": skill_cards, "brand-item": 4, "brand-logo": 3, "cv-head": 1}
    for key, count in expected.items():
        if counts.get(key, 0) != count:
            note(f"Дефект {page}: блок {key}, получено {counts.get(key, 0)}, требуется {count}")
    ids = set(re.findall(r'(?<![\w-])id="([^"]+)"', html))
    required = {"main", "navmenu", "path", "skills", "contact"}
    if page == "career/index.html":
        required |= {"profile", "projects", "resume", "case-glonass", "case-yandex", "case-ai", "case-steel"}
        required |= {"experience-" + name for name in ("independent", "glonass", "yandex", "yakov", "mckinsey", "early")}
    missing = sorted(required - ids)
    if missing:
        note(f"Дефект {page}: требуются идентификаторы {missing}")

for sentence_start in re.findall(r"(?:^|[.!?]\s|>)(I\s)", read("en/index.html")):
    note("Дефект английская версия: предложение начинается с «I»")
    break

css = read("assets/site.css")
for value in re.findall(r"letter-spacing:\s*([^;}]+)", css):
    value = value.strip()
    if value in ("0", "normal") or value.startswith("var(") or value.startswith("-"):
        continue
    note(f"Дефект положительный letter-spacing: {value}")
for value in re.findall(r"--(?:ls|tr)-[a-z0-9]+:\s*([^;}]+)", css):
    if not value.strip().startswith("-"):
        note(f"Дефект положительный трекинг в токене: {value}")

used = set(re.findall(r"var\((--[a-z0-9-]+)\s*\)", css))  # с фолбэком – не проблема
declared = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
missing = sorted(used - declared)
if missing:
    note(f"Дефект переменные требуют объявления: {missing}")

def check_links(root, page, html):
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(("http", "mailto:", "data:", "/")):
            continue
        path, _, frag = href.partition("#")
        path = path.split("?")[0]
        target = (page.parent / path).resolve() if path else page.resolve()
        rel = page.relative_to(root)
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            note(f"Дефект {rel}: ссылка требует существующей цели {href}")
        elif frag and f'id="{frag}"' not in target.read_text(encoding="utf-8"):
            note(f"Дефект {rel}: требуется якорь {href}")


for page in [p for p in ROOT.rglob("*.html") if ".git" not in p.parts]:
    check_links(ROOT, page, page.read_text(encoding="utf-8"))

if "--self-check" in sys.argv:
    start = len(defects)
    try:
        check_home("index.html", ru.replace('class="case-card', 'class="removed-card', 1))
        assert any("блок case-card, получено 17" in msg for msg in defects[start:])
        del defects[start:]
        check_home("index.html", ru.replace('id="case-fmcg-buy-side"', 'id="removed-case"', 1))
        assert any("case-fmcg-buy-side" in msg for msg in defects[start:])
        del defects[start:]
        with TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "index.html"
            page.write_text('<a href="missing.html">Переход</a>', encoding="utf-8")
            check_links(root, page, page.read_text(encoding="utf-8"))
            assert any("missing.html" in msg for msg in defects[start:])
    finally:
        del defects[start:]
    print("Самопроверка подтвердила обнаружение потери кейса, его идентификатора и битой ссылки")


if defects:
    print("\n".join(defects))
    print(f"\nвсего дефектов: {len(defects)}")
    sys.exit(1)

print(f"чисто: русских секций {len(ru_sec)}, английских {len(en_sec)}, по 18 кейсов, "
      f"версия ассетов {versions.pop()}")
