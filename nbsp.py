#!/usr/bin/env python3
"""Неразрывные пробелы по правилам русской типографики.

Короткие предлоги, союзы и частицы не остаются в конце строки; число не
отрывается от единицы измерения; тире не переносится в начало строки.
Идемпотентно: повторный запуск ничего не меняет.

Запуск: python3 nbsp.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
NB = " "

_RU_BASE = ("в во с со к ко о об обо у из изо за на по до от ото при для над "
            "под про без не ни и а но да же бы ль ли то как что это или чем уж "
            "их его её мы вы он я")
# предлог с большой буквы в начале предложения ловится тем же правилом
RU_SHORT = " ".join(_RU_BASE.split() + [w.capitalize() for w in _RU_BASE.split()])
# по-английски связывать все артикли вредно: строки становятся жёсткими
# и рвут узкие колонки. Держим только неразрывные пары, которые реально ломались.
EN_SHORT = ""

UNITS = ("млн млрд тыс руб лет года год году дней дня день недель недели неделю "
         "месяцев месяца месяц сотрудников сотрудника человек проектов проекта "
         "проект часов часа рублей раз мин сек кг км м % ₽ "
         "bn m k years year months month weeks week days day people projects project hours")


def protect(text, shorts):
    words = "|".join(sorted(shorts.split(), key=len, reverse=True))
    # короткое слово + пробел -> неразрывный пробел
    text = re.sub(rf"(?<![^\s >(«\"„–—-]) ?\b({words})\b ",
                  lambda m: (m.group(0)[0] if m.group(0)[0] == " " else "") + m.group(1) + NB,
                  text)
    # число и единица держатся вместе
    units = "|".join(sorted(UNITS.split(), key=len, reverse=True))
    text = re.sub(rf"(\d) ({units})\b", rf"\1{NB}\2", text)
    text = re.sub(r"(\d) (тыс|млн|млрд)", rf"\1{NB}\2", text)
    # тире не уезжает в начало строки
    text = text.replace(" – ", NB + "– ")
    return text


SKIP = re.compile(r"(?is)<(script|style|svg)\b.*?</\1>")


def walk(html, shorts):
    parts, last = [], 0
    for block in SKIP.finditer(html):
        parts.append((html[last:block.start()], True))
        parts.append((block.group(0), False))
        last = block.end()
    parts.append((html[last:], True))

    out = []
    for chunk, editable in parts:
        if not editable:
            out.append(chunk)
            continue
        pieces, pos = [], 0
        for tag in re.finditer(r"<[^>]+>", chunk):
            pieces.append(protect(chunk[pos:tag.start()], shorts))
            pieces.append(tag.group(0))
            pos = tag.end()
        pieces.append(protect(chunk[pos:], shorts))
        out.append("".join(pieces))
    return "".join(out)


changed = 0
for page in sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts):
    html = page.read_text(encoding="utf-8")
    shorts = EN_SHORT if "/en/" in page.as_posix() else RU_SHORT
    new = walk(html, shorts)
    if new != html:
        page.write_text(new, encoding="utf-8")
        changed += 1
        print(f"{page.relative_to(ROOT)}: +{new.count(NB) - html.count(NB)} неразрывных")

print(f"страниц изменено: {changed}")
sys.exit(0)
