#!/usr/bin/env python3
"""Клиентские формы в PDF: взаимное NDA и согласие на обработку персональных данных.

Движок – reportlab поверх общего билдера SecondBrain_OS (никакого pandoc → soffice).
Источник: docs/*.md, чистовые версии без внутренних переговорных заметок.

Запуск: python3 build_docs_pdf.py
"""
import importlib.util
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).parent
BASE = ROOT.parent
spec = importlib.util.spec_from_file_location("fb", BASE / "build_finance_bible_pdf.py")
fb = importlib.util.module_from_spec(spec)
sys.modules["fb"] = fb
spec.loader.exec_module(fb)

DOCS = [
    dict(src="nda.md", out="NDA_Babadzhanyan.pdf",
         eyebrow="ФОРМА ИСПОЛНИТЕЛЯ",
         title="Взаимное соглашение о конфиденциальности",
         sub="Подписывается до передачи данных заказчика и до показа моделей"),
    dict(src="consent.md", out="Consent_Personal_Data_Babadzhanyan.pdf",
         eyebrow="ФОРМА ИСПОЛНИТЕЛЯ",
         title="Согласие на обработку персональных данных",
         sub="Требуется, когда обработка выходит за пределы исполнения договора"),
]


def footer_for(label):
    """Свой колонтитул: заголовок документа, номер страницы, без «|» по канону."""
    def draw(canvas, doc_obj):
        canvas.saveState()
        canvas.setFont("TNR", 8)
        canvas.setFillColor(colors.HexColor("#999999"))
        page = canvas.getPageNumber()
        if page > 1:
            canvas.drawString(20 * mm, 10 * mm, label)
            canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, str(page))
            canvas.drawCentredString(A4[0] / 2, 10 * mm, "ИП Бабаджанян К. С.")
        canvas.restoreState()
    return draw


def cover(styles, doc):
    return [
        Spacer(1, 62 * mm),
        Paragraph(doc["eyebrow"], styles["cover_sub"]),
        Spacer(1, 6 * mm),
        Paragraph(doc["title"], styles["cover_title"]),
        Spacer(1, 8 * mm),
        Paragraph(doc["sub"], styles["cover_sub"]),
        Spacer(1, 16 * mm),
        HRFlowable(width="40%", thickness=1.5, color=colors.HexColor("#1a1a2e"), hAlign="CENTER"),
        Spacer(1, 14 * mm),
        Paragraph("ИП Бабаджанян Константин Сергеевич", styles["cover_author"]),
        Spacer(1, 4 * mm),
        Paragraph("ОГРНИП 326774600502903, ИНН 772482469459", styles["cover_sub"]),
        Spacer(1, 10 * mm),
        Paragraph("Поля в квадратных скобках заполняются под конкретную сделку", styles["cover_sub"]),
        PageBreak(),
    ]


def main():
    fb.register_fonts()
    styles = fb.make_styles()
    for doc in DOCS:
        md = (ROOT / "docs" / doc["src"]).read_text(encoding="utf-8")
        story = cover(styles, doc) + fb.build_flowables(md, styles)
        out = ROOT / "docs" / doc["out"]
        SimpleDocTemplate(
            str(out), pagesize=A4,
            leftMargin=20 * mm, rightMargin=20 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
            title=f'{doc["title"]} – Константин Бабаджанян', author="Константин Бабаджанян",
        ).build(story, onFirstPage=footer_for(doc["title"]), onLaterPages=footer_for(doc["title"]))
        print(f"OK: {out.name} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
