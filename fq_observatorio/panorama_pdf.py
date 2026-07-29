"""Generación del Panorama Económico descargable de FranQuestions."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#172033")
BLUE = colors.HexColor("#176B87")
PALE_BLUE = colors.HexColor("#EAF4F7")
PALE_GRAY = colors.HexColor("#F3F5F7")
GREEN = colors.HexColor("#237A57")
AMBER = colors.HexColor("#A66A00")
RED = colors.HexColor("#A33A45")


def _status_color(status: str) -> colors.Color:
    normalized = status.lower()
    if "pendiente" in normalized:
        return RED
    if "revisar" in normalized:
        return AMBER
    return GREEN


def _page_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D7DDE3"))
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#5E6875"))
    canvas.drawString(18 * mm, 9 * mm, "FranQuestions - datos oficiales con fuente y contexto")
    canvas.drawRightString(192 * mm, 9 * mm, f"Página {document.page}")
    canvas.restoreState()


def build_panorama_pdf(
    records: Iterable[dict],
    generated_on: date,
    attention_names: Iterable[str],
) -> bytes:
    """Devuelve un PDF en memoria con un panorama factual de los indicadores."""
    records = list(records)
    attention_names = list(attention_names)
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Panorama Económico FranQuestions",
        author="FranQuestions",
        subject="Resumen descriptivo de indicadores oficiales de Costa Rica",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="FQTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=INK,
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FQSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#526071"),
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FQHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=INK,
            spaceBefore=4 * mm,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FQBody",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=14,
            textColor=INK,
            spaceAfter=2.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="FQSmall",
            parent=styles["BodyText"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#526071"),
        )
    )

    story = [
        Spacer(1, 15 * mm),
        Paragraph("Panorama Económico", styles["FQTitle"]),
        Paragraph(
            "FranQuestions - Observatorio Económico de Costa Rica",
            styles["FQSubtitle"],
        ),
        Table(
            [
                ["Fecha de generación", generated_on.strftime("%d/%m/%Y")],
                ["Cobertura", f"{len(records)} indicadores oficiales"],
                ["Naturaleza", "Resumen factual y descriptivo"],
            ],
            colWidths=[48 * mm, 92 * mm],
            hAlign="CENTER",
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), PALE_BLUE),
                    ("TEXTCOLOR", (0, 0), (0, -1), BLUE),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D5DB")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            ),
        ),
        Spacer(1, 10 * mm),
        Paragraph("Lectura rápida", styles["FQHeading"]),
        Paragraph(
            "Este documento reúne el último dato disponible de cada serie. "
            "Las fechas y frecuencias son distintas, por lo que los indicadores "
            "no deben compararse como si correspondieran al mismo periodo.",
            styles["FQBody"],
        ),
    ]

    if attention_names:
        story.append(
            Table(
                [
                    [
                        Paragraph(
                            "<b>Revisión necesaria:</b> " + ", ".join(attention_names) + ".",
                            styles["FQBody"],
                        )
                    ]
                ],
                colWidths=[174 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4D8")),
                        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#D7A73A")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                ),
            )
        )
    else:
        story.append(
            Paragraph(
                "Los 12 indicadores están dentro de su ventana operativa de revisión.",
                styles["FQBody"],
            )
        )

    story.extend([PageBreak(), Paragraph("Indicadores", styles["FQHeading"])])
    current_group = None
    for record in records:
        group_header = None
        if record["group"] != current_group:
            current_group = record["group"]
            group_header = Table(
                [[current_group]],
                colWidths=[174 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), INK),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 11),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )

        status_text = record["status"]
        status_paragraph = Paragraph(
            f'<font color="{_status_color(status_text).hexval()}"><b>{status_text}</b></font>',
            styles["FQSmall"],
        )
        block = Table(
            [
                [
                    Paragraph(f"<b>{record['name']}</b>", styles["FQBody"]),
                    Paragraph(
                        f"<b>{record['value']}</b><br/><font color='#526071'>{record['unit']}</font>",
                        styles["FQBody"],
                    ),
                    Paragraph(record["period"], styles["FQBody"]),
                    status_paragraph,
                ],
                [
                    Paragraph(f"Fuente: {record['source']}", styles["FQSmall"]),
                    "",
                    "",
                    "",
                ],
            ],
            colWidths=[70 * mm, 38 * mm, 30 * mm, 36 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALE_GRAY),
                    ("SPAN", (0, 1), (-1, 1)),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7DDE3")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, 0), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
                    ("TOPPADDING", (0, 1), (-1, 1), 2),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
                ]
            ),
        )
        if group_header is not None:
            story.append(
                KeepTogether(
                    [
                        Spacer(1, 3 * mm),
                        group_header,
                        Spacer(1, 2 * mm),
                        block,
                    ]
                )
            )
        else:
            story.append(KeepTogether([Spacer(1, 2 * mm), block]))

    story.extend(
        [
            PageBreak(),
            Paragraph("Cómo interpretar este panorama", styles["FQHeading"]),
            Paragraph(
                "<b>1. Revise el periodo.</b> Un valor diario, mensual, trimestral "
                "y anual no representa el mismo horizonte temporal.",
                styles["FQBody"],
            ),
            Paragraph(
                "<b>2. Revise la unidad.</b> Porcentajes, puntos porcentuales, "
                "personas, colones y dólares no son intercambiables.",
                styles["FQBody"],
            ),
            Paragraph(
                "<b>3. Revise la fuente.</b> Las cifras pueden ser preliminares, "
                "revisadas o estar sujetas a cambios metodológicos.",
                styles["FQBody"],
            ),
            Paragraph(
                "<b>4. No confunda coincidencia con causalidad.</b> Que dos series "
                "se muevan al mismo tiempo no demuestra que una cause la otra.",
                styles["FQBody"],
            ),
            Spacer(1, 8 * mm),
            Table(
                [
                    [
                        Paragraph(
                            "<b>Advertencia metodológica</b><br/>"
                            "Este panorama no constituye una predicción, recomendación "
                            "financiera ni evaluación causal. Antes de citar un dato, "
                            "consulte la publicación oficial y sus notas metodológicas.",
                            styles["FQBody"],
                        )
                    ]
                ],
                colWidths=[174 * mm],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                        ("BOX", (0, 0), (-1, -1), 0.7, BLUE),
                        ("LEFTPADDING", (0, 0), (-1, -1), 11),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                        ("TOPPADDING", (0, 0), (-1, -1), 9),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                ),
            ),
        ]
    )

    document.build(story, onFirstPage=_page_footer, onLaterPages=_page_footer)
    return output.getvalue()
