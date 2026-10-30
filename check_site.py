#!/usr/bin/env python3
"""Проверка сайта перед публикацией: самостоятельная структура языковых версий и правила стиля.

Запуск: python3 check_site.py
Ноль на выходе подтверждает готовность проверки. Строка «Дефект» указывает требуемую правку.
"""
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).parent
PAGES = ["index.html", "en/index.html", "career/index.html", "en/career/index.html",
         "blog/index.html", "blog/proverka-prognoza-prodavtsa/index.html", "404.html"]
FORBIDDEN = {"—": "длинное тире", "·": "средняя точка", "•": "маркер"}
STREAMS = ("deals", "strategy", "transformation", "efficiency")
INDUSTRIES = {"manufacturing", "consumer", "finance", "telecom", "transport",
              "realestate", "media", "technology", "public", "professional"}
CASE_IDS = {
    "case-fmcg-buy-side", "case-apparel-sell-side", "case-consumer-buy-side",
    "case-hotel-valuation", "case-glonass-strategy", "case-b2b-saas",
    "case-video-streaming-product-strategy", "case-agri-market-model",
    "case-middle-east-sustainability", "case-regional-transport-strategy",
    "case-taxi-launch-model", "case-yandex-sales", "case-steel-transformation",
    "case-telecom-analyst-training", "case-glonass-incentives",
    "case-developer-workforce", "case-uzbek-bank-kpi", "case-kazakhstan-media-bi",
    "case-rocket-it-strategy", "case-rocket-data", "case-rocket-margin",
    "case-rocket-vet-forms", "case-rocket-ai-1c", "case-rocket-online",
    "case-glonass-office", "case-glonass-satellite", "case-glonass-uav",
    "case-glonass-logistics", "case-glonass-international",
    "case-yandex-client-portfolios", "case-yandex-sales-efficiency",
    "case-yandex-client-development", "case-qsr-customer-experience",
    "case-coal-fleet-efficiency", "case-pulp-hse-workforce",
    "case-bank-lean-construction", "case-development-financial-model",
    "case-warehouse-sublease-model", "case-bakery-distributor-bi",
    "case-mos-product-funnel", "case-defi-fundraising",
    "case-boutique-competitive-research",
}
ALIASES = {
    "case-rocket-infra": "case-rocket-data",
    "case-rocket-finance-bi": "case-rocket-margin",
    "case-speech-analytics": "case-b2b-saas",
    "case-rocket-pmo": "case-rocket-it-strategy",
    "case-rocket-it-effectiveness": "case-rocket-it-strategy",
    "case-rocket-procurement-bi": "case-rocket-data",
    "case-rocket-sales-bi": "case-rocket-data",
    "case-rocket-hr-bi": "case-rocket-data",
    "case-rocket-migration-register": "case-rocket-data",
    "case-rocket-planning": "case-rocket-margin",
    "case-rocket-yield": "case-rocket-margin",
    "case-rocket-slaughter-report": "case-rocket-margin",
    "case-rocket-semifinished": "case-rocket-margin",
    "case-rocket-workforce-proposal": "case-rocket-margin",
    "case-rocket-vision-proposal": "case-rocket-margin",
    "case-rocket-vet-analytics": "case-rocket-vet-forms",
    "case-rocket-1c-advisory": "case-rocket-ai-1c",
    "case-rocket-legal-ai": "case-rocket-ai-1c",
    "case-rocket-pricing": "case-rocket-online",
}
HOME_SECTIONS = {"about", "services", "field", "how", "faq", "contact"}

defects = []


def note(msg):
    defects.append(msg)


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


class Element:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children, self.parts = [], []

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()

    def descendants(self):
        for child in self.children:
            yield child
            yield from child.descendants()

    def text(self):
        return " ".join(self.parts + [child.text() for child in self.children]).strip()

    def within(self, parent):
        node = self.parent
        while node:
            if node is parent:
                return True
            node = node.parent
        return False

    def ancestor(self, tag):
        node = self.parent
        while node and node.tag != tag:
            node = node.parent
        return node


class Document(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Element("document", [])
        self.stack = [self.root]
        self.feed(html)
        self.elements = list(self.root.descendants())
        self.ids = {node.attrs["id"]: node for node in self.elements if "id" in node.attrs}

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in self.VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].parts.append(data)

    def classes(self, name):
        return [node for node in self.elements if node.has_class(name)]


def require_ids(page, doc, required):
    missing = sorted(required - set(doc.ids))
    if missing:
        note(f"Дефект {page}: требуются идентификаторы {missing}")


def named(node, doc):
    if node.attrs.get("aria-label", "").strip() or node.text():
        return True
    return any(doc.ids.get(ref) and doc.ids[ref].text()
               for ref in node.attrs.get("aria-labelledby", "").split())


def check_cases(page, doc):
    cards = doc.classes("case-card")
    found = {card.attrs.get("id") for card in cards}
    if len(cards) != 42 or found != CASE_IDS:
        note(f"Дефект {page}: каталог требует 42 кейса, получено {len(cards)}, "
             f"требуются {sorted(CASE_IDS - found)}, лишние {sorted(found - CASE_IDS, key=str)}")
    aliases = doc.classes("case-alias")
    actual_aliases = {node.attrs.get("id"): node.attrs.get("data-case-target") for node in aliases}
    if len(aliases) != 19 or actual_aliases != ALIASES:
        note(f"Дефект {page}: исторические адреса требуют 19 согласованных переходов к кейсам")
    for card in cards:
        case_id = card.attrs.get("id", "кейс")
        categories = set(card.attrs.get("data-categories", "").split())
        industries = set(card.attrs.get("data-industries", "").split())
        if not categories or categories - set(STREAMS):
            note(f"Дефект {page}: кейс {case_id} требует направления из каталога")
        if not industries or industries - INDUSTRIES:
            note(f"Дефект {page}: кейс {case_id} требует отрасли из каталога")
        if not card.attrs.get("data-company"):
            note(f"Дефект {page}: кейс {case_id} требует компанию")
        nodes = list(card.descendants())
        summaries = [node for node in card.children if node.tag == "summary"]
        if card.tag != "details" or len(summaries) != 1 or summaries[0].attrs.get("aria-haspopup") != "dialog":
            note(f"Дефект {page}: кейс {case_id} требует доступное открытие окна проекта")
        for cls in ("case-title", "case-context", "case-kicker"):
            if not any(node.has_class(cls) and node.text() for node in nodes):
                note(f"Дефект {page}: кейс {case_id} требует заполненный элемент {cls}")
        project_facts = [node for node in nodes if node.has_class("project-facts")]
        if (len(project_facts) != 1 or project_facts[0].tag != "dl"
                or not project_facts[0].has_class("project-facts--star")):
            note(f"Дефект {page}: кейс {case_id} требует единый блок project-facts--star")
            continue
        fields = [node for node in project_facts[0].children if node.has_class("fact")]
        ordered = ("fact--situation", "fact--task", "fact--action", "fact--result")
        if (len(fields) < 4 or any(not field.has_class(cls)
                                  for field, cls in zip(fields[:4], ordered))):
            note(f"Дефект {page}: кейс {case_id} требует порядок ситуация, задача, действия, результат")
        for cls in ordered + ("fact--artifacts", "fact--team"):
            matches = [node for node in fields if node.has_class(cls)]
            if len(matches) != 1:
                note(f"Дефект {page}: кейс {case_id} требует единственное поле {cls}")
                continue
            for tag in ("dt", "dd"):
                values = [node for node in matches[0].children if node.tag == tag]
                if len(values) != 1 or not values[0].text():
                    note(f"Дефект {page}: поле {cls} кейса {case_id} требует заполненный {tag}")
        own_role = [node for node in nodes if node.has_class("case-team-own")]
        if len(own_role) != 1 or not any(node.tag == "p" and node.text() for node in own_role[0].children):
            note(f"Дефект {page}: кейс {case_id} требует собственную ответственность автора")
        material_lists = [node for node in nodes if node.has_class("case-artifact-list--detailed")]
        if len(material_lists) != 1:
            note(f"Дефект {page}: кейс {case_id} требует подробный состав материалов")
        else:
            for material in material_lists[0].children:
                if material.tag != "li":
                    continue
                content = list(material.descendants())
                if not any(node.tag == "strong" and node.text() for node in content):
                    note(f"Дефект {page}: материал кейса {case_id} требует название")
                if not any(node.tag == "p" and node.text() for node in content):
                    note(f"Дефект {page}: материал кейса {case_id} требует описание")
                components = [node for node in content if node.has_class("artifact-components")]
                if len(components) != 1 or not any(node.tag == "li" and node.text() for node in components[0].children):
                    note(f"Дефект {page}: материал кейса {case_id} требует состав")
                purpose = [node for node in content if node.has_class("artifact-purpose")]
                if len(purpose) != 1 or not any(part.strip() for part in purpose[0].parts):
                    note(f"Дефект {page}: материал кейса {case_id} требует описание применения")
        for person in [node for node in nodes if node.has_class("team-person")]:
            kinds = [kind for kind in ("execution", "expertise", "client", "decision") if person.has_class("team-person--" + kind)]
            if len(kinds) != 1:
                note(f"Дефект {page}: участник кейса {case_id} требует единственную категорию")
    return cards, aliases


def check_dialog(page, doc):
    require_ids(page, doc, {"caseModal", "caseModalTitle", "shareStatus"})
    modal = doc.ids.get("caseModal")
    title = doc.ids.get("caseModalTitle")
    if not modal or modal.tag != "dialog" or modal.attrs.get("aria-labelledby") != "caseModalTitle" or not title or not title.within(modal):
        note(f"Дефект {page}: окно проекта требует dialog с собственным заголовком")
        return
    nodes = list(modal.descendants())
    closes = [node for node in nodes if node.has_class("case-modal-close")]
    if len(closes) != 1 or closes[0].tag != "button" or not named(closes[0], doc):
        note(f"Дефект {page}: окно проекта требует именованную кнопку закрытия")
    for action in ("prev", "next"):
        if not any(node.tag == "button" and node.attrs.get("data-case-nav") == action and named(node, doc) for node in nodes):
            note(f"Дефект {page}: окно проекта требует именованную кнопку {action}")
    for cls in ("case-modal-stream", "case-modal-kicker", "case-modal-facts", "case-modal-share"):
        if not any(node.has_class(cls) for node in nodes):
            note(f"Дефект {page}: окно проекта требует элемент {cls}")
    status = doc.ids.get("shareStatus")
    if not status or status.attrs.get("role") != "status" or not status.within(modal):
        note(f"Дефект {page}: окно проекта требует доступный статус копирования ссылки")


def check_home(page, html):
    doc = Document(html)
    sections = {node.attrs.get("id") for node in doc.elements if node.tag == "section"}
    missing = sorted(HOME_SECTIONS - sections)
    if missing:
        note(f"Дефект {page}: требуются секции {missing}")
    require_ids(page, doc, {"main", "top", "navmenu", "offer", "tip", "industries",
                           "catalogueResults", "catalogueCount", "catalogueEmpty"}
                | {"stream-" + stream for stream in STREAMS})
    cards, _ = check_cases(page, doc)
    check_dialog(page, doc)
    controls = [node for node in doc.elements if "data-stream" in node.attrs]
    if len(controls) != 4 or {node.attrs["data-stream"] for node in controls} != set(STREAMS):
        note(f"Дефект {page}: каталог требует четыре направления множественного выбора")
    groups = {node.ancestor("nav") for node in controls}
    if len(groups) != 1 or None in groups or not next(iter(groups)).attrs.get("aria-label", "").strip():
        note(f"Дефект {page}: направления требуют общую именованную группу")
    for control in controls:
        stream = control.attrs["data-stream"]
        if (control.tag != "button" or control.attrs.get("aria-pressed") != "false"
                or control.attrs.get("aria-controls") != "catalogueResults"
                or control.attrs.get("role") == "tab" or "aria-selected" in control.attrs
                or control.attrs.get("tabindex") == "-1" or not named(control, doc)):
            note(f"Дефект {page}: направление {stream} требует доступную кнопку множественного выбора в исходном состоянии")
        numbers = [node.text() for node in control.descendants() if node.has_class("stream-tab-count")]
        expected = sum(stream in card.attrs.get("data-categories", "").split() for card in cards)
        if numbers != [str(expected)]:
            note(f"Дефект {page}: счётчик направления {stream} требует значения {expected}")
    inputs = [node for node in doc.elements if "data-industry" in node.attrs]
    if len(inputs) != 10 or {node.attrs["data-industry"] for node in inputs} != INDUSTRIES:
        note(f"Дефект {page}: каталог требует десять отраслей множественного выбора")
    for control in inputs:
        industry = control.attrs["data-industry"]
        label = control.ancestor("label")
        if (control.tag != "input" or control.attrs.get("type") != "checkbox"
                or "checked" in control.attrs or control.attrs.get("aria-controls") != "catalogueResults"
                or not label or not label.text()):
            note(f"Дефект {page}: отрасль {industry} требует именованный флажок в исходном состоянии")
        if label:
            numbers = [node.text() for node in label.descendants() if node.has_class("industry-count")]
            expected = sum(industry in card.attrs.get("data-industries", "").split() for card in cards)
            if numbers != [str(expected)]:
                note(f"Дефект {page}: счётчик отрасли {industry} требует значения {expected}")
    results = doc.ids.get("catalogueResults")
    if not results or "hidden" not in results.attrs or any(not card.within(results) for card in cards):
        note(f"Дефект {page}: каталог требует исходно скрытую общую область результатов со всеми кейсами")
    count = doc.ids.get("catalogueCount")
    if not count or count.attrs.get("role") != "status" or count.attrs.get("aria-live") != "polite":
        note(f"Дефект {page}: каталог требует доступный счётчик результатов")
    empty = doc.ids.get("catalogueEmpty")
    if not empty or "hidden" not in empty.attrs or not empty.text():
        note(f"Дефект {page}: каталог требует исходно скрытое сообщение для пустой выборки")
    resets = [node for node in doc.elements if "data-reset-filters" in node.attrs]
    if len(resets) != 1 or resets[0].tag != "button" or not named(resets[0], doc):
        note(f"Дефект {page}: каталог требует именованную кнопку сброса фильтров")


ru, en = read("index.html"), read("en/index.html")

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

def check_career(page, html):
    doc = Document(html)
    required = {"main", "navmenu", "profile", "projects", "path", "skills", "contact", "resume",
                "case-glonass", "case-yandex", "case-ai", "case-steel"}
    stages = {"experience-" + name for name in ("independent", "glonass", "yandex", "yakov", "mckinsey", "early")}
    require_ids(page, doc, required | stages)
    path_items = doc.classes("path-item")
    if len(path_items) != 6 or {node.attrs.get("id") for node in path_items} != stages:
        note(f"Дефект {page}: карьера требует шесть этапов опыта")
    for stage in path_items:
        for cls in ("path-what", "path-where", "path-when", "path-note"):
            if not any(node.has_class(cls) and node.text() for node in stage.descendants()):
                note(f"Дефект {page}: этап {stage.attrs.get('id')} требует заполненный элемент {cls}")
    skills = doc.classes("skill-card")
    if len(skills) != 3:
        note(f"Дефект {page}: карьера требует три карточки навыков, получено {len(skills)}")
    for skill in skills:
        if not any(node.has_class("skill-label") and node.text() for node in skill.descendants()):
            note(f"Дефект {page}: карточка навыков требует собственный заголовок")
    cards, aliases = check_cases(page, doc)
    check_dialog(page, doc)
    libraries = doc.classes("case-library")
    if (len(libraries) != 1 or "hidden" not in libraries[0].attrs
            or any(not node.within(libraries[0]) for node in cards + aliases)):
        note(f"Дефект {page}: карьера требует скрытую библиотеку всех 42 кейсов и 19 исторических адресов")
    linked = set()
    for link in doc.elements:
        href = link.attrs.get("href", "")
        if link.tag != "a" or "#case-" not in href:
            continue
        target = href.partition("#")[2]
        canonical = ALIASES.get(target, target)
        if (not href.startswith("#case-") or canonical not in CASE_IDS
                or link.attrs.get("aria-haspopup") != "dialog"):
            note(f"Дефект {page}: ссылка {href} требует окно проекта на текущей странице")
        linked.add(canonical)
    if CASE_IDS - linked:
        note(f"Дефект {page}: этапы карьеры требуют ссылки на кейсы {sorted(CASE_IDS - linked)}")


for page in ("career/index.html", "en/career/index.html"):
    check_career(page, read(page))

# Общий каталог сохраняет те же направления, отрасли и компании на четырёх страницах.
catalogues = {}
for page in ("index.html", "en/index.html", "career/index.html", "en/career/index.html"):
    doc = Document(read(page))
    catalogues[page] = {
        card.attrs.get("id"): tuple(frozenset(card.attrs.get(key, "").split())
                                   for key in ("data-categories", "data-industries", "data-company"))
        for card in doc.classes("case-card")
    }
for page, catalogue in catalogues.items():
    if catalogue != catalogues["index.html"]:
        note(f"Дефект {page}: классификация кейсов требует согласования с главным каталогом")

# Согласованные тексты портфолио используют первое лицо для личного вклада.

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
    root = root.resolve()
    page = page.resolve()
    home = root / "index.html"
    base_path = ""
    if home.exists():
        canonical = next((node.attrs.get("href", "") for node in Document(home.read_text(encoding="utf-8")).elements
                          if node.tag == "link" and node.attrs.get("rel") == "canonical"), "")
        base_path = urlsplit(canonical).path.rstrip("/")
    for node in Document(html).elements:
        href = node.attrs.get("href")
        if href is None:
            continue
        url = urlsplit(href)
        if url.scheme or url.netloc:
            continue
        path, frag = unquote(url.path), unquote(url.fragment)
        if path.startswith("/"):
            if base_path and (path == base_path or path.startswith(base_path + "/")):
                path = path[len(base_path):]
            target = (root / path.lstrip("/")).resolve()
        else:
            target = (page.parent / path).resolve() if path else page.resolve()
        rel = page.relative_to(root)
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            note(f"Дефект {rel}: ссылка требует существующей цели {href}")
        elif frag and target.suffix.lower() == ".html" and frag not in Document(target.read_text(encoding="utf-8")).ids:
            note(f"Дефект {rel}: требуется якорь {href}")


for page in [p for p in ROOT.rglob("*.html") if ".git" not in p.parts]:
    check_links(ROOT, page, page.read_text(encoding="utf-8"))

if "--self-check" in sys.argv:
    start = len(defects)
    checked = []

    def detects(label, checker, source, original, replacement, message):
        if original not in source:
            raise AssertionError(f"Самопроверка требует исходный фрагмент: {label}")
        try:
            checker(source.replace(original, replacement, 1))
            if not any(message in msg for msg in defects[start:]):
                raise AssertionError(f"Самопроверка требует обнаружения: {label}")
            checked.append(label)
        finally:
            del defects[start:]

    try:
        home = lambda source: check_home("index.html", source)
        career = lambda source: check_career("career/index.html", source)
        career_html = read("career/index.html")
        detects("потеря кейса", home, ru, 'class="case-card', 'class="removed-card', "получено 41")
        detects("потеря адреса кейса", home, ru, 'id="case-fmcg-buy-side"', 'id="removed-case"', "case-fmcg-buy-side")
        detects("потеря направления", home, ru, 'data-stream="strategy"', 'data-removed="strategy"', "четыре направления")
        detects("исключительный выбор направления", home, ru, 'aria-pressed="false"', 'aria-selected="false"', "кнопку множественного выбора")
        detects("исключительный выбор отрасли", home, ru, 'type="checkbox"', 'type="radio"', "именованный флажок")
        detects("расхождение счётчика", home, ru, 'class="stream-tab-count">15', 'class="stream-tab-count">999', "счётчик направления strategy")
        detects("потеря исторического адреса", home, ru, 'data-case-target="case-rocket-data"', 'data-case-target="missing"', "19 согласованных переходов")
        detects("потеря отрасли кейса", home, ru, 'data-industries="manufacturing"', 'data-industries="missing"', "требует отрасли из каталога")
        detects("потеря поля ситуации", home, ru, 'class="fact fact--situation"', 'class="fact fact--removed"', "единственное поле fact--situation")
        detects("потеря материалов заказчика", home, ru, 'class="fact fact--artifacts"', 'class="fact fact--removed"', "единственное поле fact--artifacts")
        detects("потеря команды проекта", home, ru, 'class="fact fact--team"', 'class="fact fact--removed"', "единственное поле fact--team")
        detects("потеря собственной роли", home, ru, 'class="case-team-own"', 'class="removed-role"', "собственную ответственность автора")
        detects("потеря подробных материалов", home, ru, 'case-artifact-list case-artifact-list--detailed', 'case-artifact-list', "подробный состав материалов")
        material_description = re.search(r'<p class="artifact-purpose">.*?</p>', ru, re.S)
        if not material_description:
            raise AssertionError("Самопроверка требует описание материала")
        detects("пустое описание материала", home, ru, material_description.group(0), '<p class="artifact-purpose"></p>', "требует описание")
        detects("потеря состава материала", home, ru, 'class="artifact-components"', 'class="removed-components"', "требует состав")
        detects("потеря применения материала", home, ru, 'class="artifact-purpose"', 'class="removed-purpose"', "требует описание применения")
        detects("потеря блока структуры кейса", home, ru, 'project-facts project-facts--star', 'project-facts', "единый блок project-facts--star")
        situation_title = re.search(r'<div class="fact fact--situation">(<dt>.*?</dt>)', ru, re.S)
        if not situation_title:
            raise AssertionError("Самопроверка требует заголовок ситуации")
        detects("пустой заголовок поля", home, ru, situation_title.group(1), '<dt></dt>', "требует заполненный dt")
        situation = re.search(r'(<div class="fact fact--situation"><dt>.*?</dt><dd>).*?(</dd>)', ru, re.S)
        if not situation:
            raise AssertionError("Самопроверка требует исходное поле ситуации")
        detects("пустое содержание поля", home, ru, situation.group(0),
                situation.group(1) + situation.group(2), "требует заполненный dd")
        first_fields = re.search(r'(<div class="fact fact--situation">.*?</div>)(<div class="fact fact--task">.*?</div>)', ru, re.S)
        if not first_fields:
            raise AssertionError("Самопроверка требует исходный порядок полей")
        detects("нарушение порядка полей", home, ru, first_fields.group(0),
                first_fields.group(2) + first_fields.group(1), "требует порядок ситуация, задача, действия, результат")
        detects("потеря этапа карьеры", career, career_html, 'class="path-item ', 'class="removed-item ', "шесть этапов")
        detects("потеря карточки навыков", career, career_html, 'class="skill-card', 'class="removed-skill', "три карточки навыков")
        detects("видимая библиотека", career, career_html, 'class="case-library" hidden="True"', 'class="case-library"', "скрытую библиотеку")
        detects("переход с карьеры на другую страницу", career, career_html, 'href="#case-glonass-office"', 'href="../#case-glonass-office"', "на текущей странице")
        detects("потеря заголовка окна", career, career_html, '<dialog aria-labelledby="caseModalTitle"', '<dialog aria-labelledby="missingTitle"', "с собственным заголовком")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "index.html"
            page.write_text('<a href="missing.html">Переход</a>', encoding="utf-8")
            check_links(root, page, page.read_text(encoding="utf-8"))
            if not any("missing.html" in msg for msg in defects[start:]):
                raise AssertionError("Самопроверка требует обнаружения битой ссылки")
            checked.append("битая ссылка")
            del defects[start:]
            page.write_text('<a href="#missing">Переход</a>', encoding="utf-8")
            check_links(root, page, page.read_text(encoding="utf-8"))
            if not any("якорь #missing" in msg for msg in defects[start:]):
                raise AssertionError("Самопроверка требует обнаружения потерянного якоря")
            checked.append("потеря якоря")
    finally:
        del defects[start:]
    print(f"Самопроверка подтвердила обнаружение видов дефектов: {len(checked)}")


if defects:
    print("\n".join(defects))
    print(f"\nПроверка выявила дефекты: {len(defects)}")
    sys.exit(1)

print(f"Проверка подтвердила структуру четырёх страниц: по 42 кейса и 19 исторических адресов, "
      f"каждый кейс содержит ситуацию, задачу, действия, результат и материалы заказчика, "
      f"главные страницы содержат 4 направления и 10 отраслей, карьера содержит 6 этапов и 3 карточки навыков, "
      f"версия ассетов {declared_version}")
