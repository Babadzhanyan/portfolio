#!/usr/bin/env python3
"""Перевод сайта на собственный домен и открытие индексации.

    python3 switch_live.py babadzhanyan.com

Делает четыре вещи:
  1. CNAME в корне репозитория
  2. заменяет все абсолютные адреса babadzhanyan.github.io/portfolio на новый домен
  3. снимает noindex со всех публичных страниц (оферта, политика, og-card остаются закрытыми)
  4. открывает robots.txt

После запуска: git add -A && git commit && git push, затем в настройках
репозитория GitHub Pages указать Custom domain и включить Enforce HTTPS,
дождаться сертификата и подать сайт в Яндекс.Вебмастер и Google Search Console.
"""
import pathlib, re, sys

OLD = "https://babadzhanyan.github.io/portfolio"
KEEP_NOINDEX = {"oferta.html", "privacy.html", "og-card.html"}

def main(domain):
    root = pathlib.Path(__file__).resolve().parent
    new = f"https://{domain}"
    changed = []

    (root / "CNAME").write_text(domain + "\n", encoding="utf-8")
    changed.append("CNAME")

    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.suffix not in {".html", ".xml"}:
            continue
        if ".git" in path.parts:
            continue
        text = original = path.read_text(encoding="utf-8")
        text = text.replace(OLD, new)
        text = text.replace('"/portfolio/', '"/')  # корневые пути со страницы 404
        if path.name not in KEEP_NOINDEX:
            text = re.sub(r'\s*<meta name="robots" content="noindex,\s*nofollow">\n?', "\n", text, count=1)
        if text != original:
            path.write_text(text, encoding="utf-8")
            changed.append(str(path.relative_to(root)))

    (root / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % new, encoding="utf-8")
    changed.append("robots.txt")

    print(f"Домен: {domain}")
    print(f"Обновлено файлов: {len(changed)}")
    for name in changed:
        print("  " + name)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Использование: python3 switch_live.py <домен без протокола>")
    main(sys.argv[1].strip().lstrip("https://").lstrip("http://").rstrip("/"))
