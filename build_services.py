"""Render bilingual service pages and their links on the two portfolio homepages."""
import argparse
import json
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
PUBLIC = "https://babadzhanyan.github.io/portfolio/"
FACTS = json.loads((ROOT / "services/content.json").read_text())
VERSION = json.loads((ROOT / "version.json").read_text())["assets"]
LABELS = {
    "ru": dict(name="Константин Бабаджанян", home="Главная", short="К. Бабаджанян", practice="Консалтинговое бюро Константина Бабаджаняна",
               services="Консалтинговые услуги", skip="К содержанию", resume="Резюме", lang="Язык страницы",
               outputs="Что получит ваша команда", proof="Опыт по этой задаче", more="Все проекты по направлению",
               telegram="Написать в Telegram", email="По электронной почте", discuss="Обсудить проект", other="Другие услуги",
               nav="Навигация", legal="Правовая информация", privacy="Обработка данных", terms="Условия работы",
               photograph="Константин Бабаджанян выступает на конференции"),
    "en": dict(name="Konstantin Babadzhanyan", home="Home", short="K. Babadzhanyan", practice="Konstantin Babadzhanyan’s independent consulting practice",
               services="Consulting services", skip="Skip to content", resume="Résumé", lang="Page language",
               outputs="What your team receives", proof="Relevant experience", more="Explore projects in this area",
               telegram="Message on Telegram", email="Send an email", discuss="Discuss a project", other="Other services",
               nav="Navigation", legal="Legal information", privacy="Privacy policy (in Russian)", terms="Engagement terms (in Russian)",
               photograph="Konstantin Babadzhanyan speaking at a conference")
}
ICONS = {
    "strategy": '<path d="M4 19V5m0 14h16M7 14l4-4 3 2 6-7m-4 0h4v4"/>',
    "deals": '<path d="M4 9h16v11H4zM8 9V7a2 2 0 012-2h4a2 2 0 012 2v2M4 13c5 2 11 2 16 0m-9 1h2"/>',
    "efficiency": '<path d="M5 4v8m0 4v4M12 4v2m0 4v10M19 4v10m0 4v2M2 12h6m1-6h6m1 8h6"/>',
    "transformation": '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/><path d="M9 6h5a4 4 0 014 4v5M6 9v5a4 4 0 004 4h5"/>'
}


def icon(key):
    return f'<svg aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{ICONS[key]}</svg>'


def page(slug, lang):
    en = lang == "en"
    data = FACTS[slug][lang]
    label = LABELS[lang]
    root = "../../../" if en else "../../"
    path = f"services/{slug}/"
    url_ru, url_en = PUBLIC + path, PUBLIC + "en/" + path
    url = url_en if en else url_ru
    alt_path = "../../../" + path if en else "../../en/" + path
    title = f"{data['name']}, {label['name']}"
    description = data["lead"]
    share = PUBLIC + f"share-portfolio-{lang}-20261121.jpg"
    mail = "mailto:babadzhanyan.k.s@gmail.com?subject=" + quote(data["name"])
    tg = "https://t.me/kostya_younker?text=" + quote(data["contact"])
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type":"WebPage", "@id":url + "#webpage", "url":url, "name":title,
             "description":description, "inLanguage":lang, "mainEntity":{"@id":url + "#service"},
             "isPartOf":{"@id":PUBLIC + "#website"}},
            {"@type":"Service","@id":url + "#service", "url":url, "name":data["name"],
             "serviceType":data["name"], "description":description,
             "brand":{"@id":PUBLIC + "#practice-brand"},
             "provider":{"@type":"Person","@id":PUBLIC + "#person","name":label["name"],"url":PUBLIC + ("en/career/" if en else "career/")}},
            {"@type":"Brand","@id":PUBLIC + "#practice-brand","name":label["practice"],"url":PUBLIC}
        ]
    }
    outputs = "".join(f"<li><h3>{escape(name)}</h3><p>{escape(detail)}</p></li>" for name, detail in data["outputs"])
    examples = "".join(f'<li><h3><a data-event="service_case_open" data-placement="service-{slug}" href="../../?areas={slug}#{key}">{escape(name)}</a></h3><p>{escape(detail)}</p></li>' for key, name, detail in data["proof"])
    related = "".join(f'<a href="../{key}/">{escape(val[lang]["name"])}</a>' for key, val in FACTS.items() if key != slug)
    alternate = "ru" if en else "en"
    language_links = "".join(
        f'<span aria-current="page">{code.upper()}</span>' if code == lang else
        f'<a hreflang="{alternate}" lang="{alternate}" href="{alt_path}">{code.upper()}</a>'
        for code in ("ru", "en")
    )
    styles = "\n".join(f'<link rel="stylesheet" href="{root}assets/{name}.css?v={VERSION}">' for name in ("site", "editorial", "typography", "service-page"))
    article = '<a href="../../blog/proverka-prognoza-prodavtsa/">Как проверить прогноз продавца перед покупкой бизнеса</a>' if slug == "deals" and not en else ""
    return f'''<!doctype html>
<html lang="{lang}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#124b38">
<title>{escape(title)}</title><meta name="description" content="{escape(description)}">
<link rel="canonical" href="{url}"><link rel="alternate" hreflang="ru" href="{url_ru}"><link rel="alternate" hreflang="en" href="{url_en}"><link rel="alternate" hreflang="x-default" href="{url_ru}">
<meta property="og:type" content="website"><meta property="og:url" content="{url}"><meta property="og:title" content="{escape(title)}"><meta property="og:description" content="{escape(description)}"><meta property="og:image" content="{share}"><meta property="og:image:alt" content="{label["photograph"]}"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}apple-touch-icon.png">
{styles}
<script defer src="{root}assets/site.js?v={VERSION}"></script>
<script type="application/ld+json">{json.dumps(graph, ensure_ascii=False, indent=2)}</script>
</head><body class="design-system editorial-site service-page">
<a class="service-skip" href="#main">{label["skip"]}</a>
<header class="service-nav"><div class="wrap">
<a class="service-brand" href="../../"><span>{label["name"]}</span><span>{label["short"]}</span></a>
<nav aria-label="{label["nav"]}"><a href="../../career/">{label["resume"]}</a><span class="service-lang" role="group" aria-label="{label["lang"]}">{language_links}</span></nav>
</div></header>
<main id="main" tabindex="-1"><div class="wrap">
<div class="service-intro">
<div><a class="service-parent" href="../../#advisory">{label["services"]}</a>
<h1>{escape(data["name"])}</h1><p class="service-lead">{escape(description)}</p>
<a class="service-button" href="#contact">{label["discuss"]}</a></div>
<figure class="service-evidence">{icon(slug)}<strong>{escape(data["metric"])}</strong><figcaption>{escape(data["caption"])}</figcaption></figure>
</div>
<section class="service-scope"><h2>{label["outputs"]}</h2><ul>{outputs}</ul></section>
<section class="service-proof"><h2>{label["proof"]}</h2><ul>{examples}</ul><div class="service-reading"><a href="../../?areas={slug}#services">{label["more"]}</a>{article}</div></section>
<section class="service-contact" id="contact"><div><h2>{escape(data["ask"])}</h2><p>{escape(data["brief"])}</p></div>
<div class="service-actions"><a class="service-button" data-event="contact_click" data-channel="telegram" data-placement="service-{slug}" href="{tg}">{label["telegram"]}</a><a data-event="contact_click" data-channel="email" data-placement="service-{slug}" href="{mail}">{label["email"]}</a></div></section>
</div></main>
<footer class="service-footer"><nav class="wrap" aria-label="{label["other"]}"><strong>{label["other"]}</strong>{related}</nav>
<nav class="wrap" aria-label="{label["legal"]}"><a href="{root}oferta.html">{label["terms"]}</a><a href="{root}privacy.html">{label["privacy"]}</a></nav></footer>
</body></html>
'''


def offers(lang):
    links = []
    for slug, entry in FACTS.items():
        d = entry[lang]
        links.append(f'<a class="practice-offer" data-event="service_open" data-placement="home-{slug}" href="services/{slug}/">{icon(slug)}<h3>{escape(d["name"])}</h3><p>{escape(d["question"])}</p></a>')
    title = LABELS[lang]["services"]
    return f'<section class="section" id="advisory"><div class="wrap"><h2><span class="section-title-text">{title}</span></h2><div class="practice-offers">' + "\n".join(links) + '</div></div></section>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify rendered files against their source")
    check = parser.parse_args().check
    stale = []
    for lang in LABELS:
        folder = ROOT / ("en" if lang == "en" else "")
        home = folder / "index.html"
        source = home.read_text()
        start = "<!-- consulting services -->"
        end = "<!-- /consulting services -->"
        before, sep, tail = source.partition(start)
        if not sep or end not in tail:
            raise ValueError(f"Service section markers missing from {home}")
        content = before + start + "\n" + offers(lang) + "\n" + end + tail.split(end, 1)[1]
        pages = {home: content}
        for slug in FACTS:
            pages[folder / "services" / slug / "index.html"] = page(slug, lang)
        for target, html in pages.items():
            if target.is_file() and target.read_text() == html:
                continue
            if check:
                stale.append(str(target.relative_to(ROOT)))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(html)
    if stale:
        raise SystemExit("Regenerate these pages: " + ", ".join(stale))


if __name__ == "__main__":
    main()
