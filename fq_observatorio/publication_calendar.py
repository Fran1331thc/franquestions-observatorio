"""Calendario operativo de revisión de indicadores oficiales."""

from __future__ import annotations

from datetime import date, datetime, time, timezone


OFFICIAL_RELEASES_2026 = {
    "policy-rate": [
        (date(2026, 7, 23), "Programada oficialmente", "https://www.bccr.fi.cr/comunicacion-y-prensa/Docs_Comunicados_Prensa/CP-BCCR-051-2025-Calendario_reuniones_politica_monetaria_2026.pdf"),
        (date(2026, 9, 24), "Programada oficialmente", "https://www.bccr.fi.cr/comunicacion-y-prensa/Docs_Comunicados_Prensa/CP-BCCR-051-2025-Calendario_reuniones_politica_monetaria_2026.pdf"),
        (date(2026, 11, 26), "Programada oficialmente", "https://www.bccr.fi.cr/comunicacion-y-prensa/Docs_Comunicados_Prensa/CP-BCCR-051-2025-Calendario_reuniones_politica_monetaria_2026.pdf"),
    ],
    "inflation": [(date(2026, month, day), "Confirmada", "https://admin.inec.cr/sites/default/files/2025-12/evCalendarioDivulgacionEstadistica2026.pdf") for month, day in ((8, 7), (9, 7), (10, 7), (11, 6), (12, 8))],
    "imae": [(date(2026, month, day), "Programada oficialmente", "https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/Calendario-esp.htm") for month, day in ((8, 11), (9, 11), (10, 12), (11, 11), (12, 11))],
    "unemployment": [(date(2026, month, day), "Confirmada", "https://admin.inec.cr/sites/default/files/2025-12/evCalendarioDivulgacionEstadistica2026.pdf") for month, day in ((8, 6), (9, 3), (10, 1), (11, 5), (12, 3))],
    "poverty": [(date(2026, 10, 27), "Confirmada", "https://admin.inec.cr/sites/default/files/2025-12/evCalendarioDivulgacionEstadistica2026.pdf")],
    "fiscal-balance": [(date(2026, month, day), "Fecha límite oficial", "https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/Calendario-esp.htm") for month, day in ((8, 20), (9, 18), (10, 20), (11, 19), (12, 19))],
    "public-debt": [(date(2026, month, day), "Programada oficialmente", "https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/Calendario-esp.htm") for month, day in ((8, 21), (9, 21), (10, 21), (11, 23), (12, 21))],
    "reserves": [(date(2026, month, day), "Programada oficialmente", "https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/Calendario-esp.htm") for month, day in ((7, 28), (8, 4), (8, 11), (8, 18), (8, 25), (9, 1), (9, 8), (9, 15), (9, 22), (9, 29))],
    "exports": [(date(2026, month, day), "Programada oficialmente", "https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/Calendario-esp.htm") for month, day in ((8, 21), (9, 21), (10, 21), (11, 23), (12, 21))],
    "fdi": [(date(2026, 9, 30), "Programada oficialmente", "https://gee.bccr.fi.cr/indicadoreseconomicos/Documentos/NEDD/Calendario-esp.htm")],
    "tourism": [
        (date(2026, 8, 10), "Semana oficial", "https://www.ict.go.cr/images/Calendario_1_Movimientos_Migratorios.png", "2.ª semana de agosto de 2026"),
        (date(2026, 9, 22), "Semana oficial", "https://www.ict.go.cr/images/Calendario_1_Movimientos_Migratorios.png", "4.ª semana de setiembre de 2026"),
        (date(2026, 10, 22), "Semana oficial", "https://www.ict.go.cr/images/Calendario_1_Movimientos_Migratorios.png", "4.ª semana de octubre de 2026"),
        (date(2026, 11, 22), "Semana oficial", "https://www.ict.go.cr/images/Calendario_1_Movimientos_Migratorios.png", "4.ª semana de noviembre de 2026"),
        (date(2026, 12, 22), "Semana oficial", "https://www.ict.go.cr/images/Calendario_1_Movimientos_Migratorios.png", "4.ª semana de diciembre de 2026"),
    ],
}

EXCHANGE_RATE_RULE_URL = "https://www.bccr.fi.cr/marco-legal/DocReglamento/Reglamento_Operaciones_Cambiarias_Contado_BCCR.pdf"


def build_calendar_events(
    statuses: list[dict],
    names_by_slug: dict,
    sources_by_slug: dict,
    today: date | None = None,
    official_releases: dict | None = None,
) -> list[dict]:
    today = today or date.today()
    official_releases = OFFICIAL_RELEASES_2026 if official_releases is None else official_releases
    events = []
    for status in statuses:
        slug = status["slug"]
        if slug == "exchange-rate":
            review_due = status.get("review_due") or today
            review_date = review_due if isinstance(review_due, date) else date.fromisoformat(str(review_due)[:10])
            events.append(
                {
                    "slug": slug,
                    "name": names_by_slug[slug],
                    "date": review_date,
                    "date_label": f"Cada día hábil · próxima revisión {review_date.strftime('%d/%m/%Y')}",
                    "source": sources_by_slug[slug],
                    "status": status.get("status", "missing"),
                    "confirmation": "Frecuencia oficial diaria",
                    "source_url": EXCHANGE_RATE_RULE_URL,
                    "note": "El BCCR calcula y publica el tipo de cambio de referencia antes de finalizar cada día hábil.",
                }
            )
            continue
        future_official = [release for release in official_releases.get(slug, []) if release[0] >= today]
        if future_official:
            for release in future_official:
                release_date, confirmation, source_url = release[:3]
                events.append(
                    {
                        "slug": slug,
                        "name": names_by_slug[slug],
                        "date": release_date,
                        "date_label": release[3] if len(release) > 3 else release_date.strftime("%d/%m/%Y"),
                        "source": sources_by_slug[slug],
                        "status": status.get("status", "missing"),
                        "confirmation": confirmation,
                        "source_url": source_url,
                        "note": "Fecha tomada de un calendario oficial; puede modificarse si la institución lo comunica.",
                    }
                )
            continue
        review_due = status.get("review_due")
        if not review_due:
            continue
        review_date = review_due if isinstance(review_due, date) else date.fromisoformat(str(review_due)[:10])
        events.append(
            {
                "slug": slug,
                "name": names_by_slug[slug],
                "date": review_date,
                "date_label": review_date.strftime("%d/%m/%Y"),
                "source": sources_by_slug[slug],
                "status": status.get("status", "missing"),
                "confirmation": "Estimada",
                "source_url": "",
                "note": "Fecha operativa estimada para revisar la fuente; no garantiza una publicación oficial.",
            }
        )
    return sorted(events, key=lambda item: (item["date"], item["name"]))


def calendar_to_ics(events: list[dict], generated_on: date) -> str:
    stamp = datetime.combine(generated_on, time.min, tzinfo=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FranQuestions//Calendario Economico//ES", "CALSCALE:GREGORIAN"]
    for event in events:
        day = event["date"].strftime("%Y%m%d")
        uid = f"fq-{event['slug']}-{day}@franquestions.local"
        summary = f"Revisar {event['name']}"
        description = f"Tipo: {event.get('confirmation', 'Estimada')}. Fuente: {event['source']}. {event['note']}".replace(",", "\\,")
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{day}",
                f"SUMMARY:{summary}",
                f"DESCRIPTION:{description}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
