"""Cálculos descriptivos y reproducibles para la primera capa de inteligencia."""

from __future__ import annotations

from datetime import date


TREND_WINDOWS = {"daily": 30, "monthly": 6, "quarterly": 4, "annual": 3}
YEAR_LAGS = {"daily": 365, "monthly": 12, "quarterly": 4, "annual": 1}

MEANING_BY_INDICATOR = {
    "exchange-rate": {"Al alza": "El colón se ha depreciado frente al dólar en la ventana reciente.", "A la baja": "El colón se ha apreciado frente al dólar en la ventana reciente.", "Estable": "El tipo de cambio muestra poca variación neta en la ventana reciente."},
    "policy-rate": {"Al alza": "La orientación de la tasa de referencia se ha vuelto más restrictiva.", "A la baja": "La orientación de la tasa de referencia se ha vuelto menos restrictiva.", "Estable": "El BCCR ha mantenido estable su tasa de referencia en la ventana reciente."},
    "inflation": {"Al alza": "La inflación interanual ha ganado impulso recientemente.", "A la baja": "La inflación interanual ha perdido impulso recientemente.", "Estable": "La inflación interanual presenta poca variación neta recientemente."},
    "imae": {"Al alza": "El crecimiento interanual de la actividad económica muestra mayor impulso.", "A la baja": "El crecimiento interanual de la actividad económica muestra menor impulso.", "Estable": "El crecimiento interanual de la actividad económica se mantiene relativamente estable."},
    "unemployment": {"Al alza": "La proporción estimada de la fuerza de trabajo sin empleo ha aumentado.", "A la baja": "La proporción estimada de la fuerza de trabajo sin empleo ha disminuido.", "Estable": "La tasa estimada de desempleo presenta poca variación neta."},
    "poverty": {"Al alza": "Aumentó la proporción de hogares bajo la línea de pobreza.", "A la baja": "Disminuyó la proporción de hogares bajo la línea de pobreza.", "Estable": "La proporción de hogares en pobreza presenta poca variación."},
    "fiscal-balance": {"Al alza": "El balance financiero mejoró: el déficit se redujo o el superávit aumentó.", "A la baja": "El balance financiero se deterioró: el déficit aumentó o el superávit disminuyó.", "Estable": "El balance financiero presenta poca variación neta."},
    "public-debt": {"Al alza": "La deuda aumentó en relación con el PIB.", "A la baja": "La deuda disminuyó en relación con el PIB.", "Estable": "La deuda en relación con el PIB presenta poca variación."},
    "reserves": {"Al alza": "Aumentó el nivel de activos de reserva brutos del BCCR.", "A la baja": "Disminuyó el nivel de activos de reserva brutos del BCCR.", "Estable": "Las reservas brutas presentan poca variación neta."},
    "exports": {"Al alza": "El valor mensual exportado muestra mayor dinamismo reciente.", "A la baja": "El valor mensual exportado muestra menor dinamismo reciente.", "Estable": "El valor mensual exportado presenta poca variación neta."},
    "tourism": {"Al alza": "Las llegadas internacionales muestran mayor dinamismo reciente.", "A la baja": "Las llegadas internacionales muestran menor dinamismo reciente.", "Estable": "Las llegadas internacionales presentan poca variación neta."},
    "fdi": {"Al alza": "El flujo trimestral de inversión directa aumentó.", "A la baja": "El flujo trimestral de inversión directa disminuyó.", "Estable": "El flujo trimestral de inversión directa presenta poca variación neta."},
}

HYPOTHESES_BY_INDICATOR = {
    "exchange-rate": ("flujos de divisas", "condiciones financieras internacionales", "expectativas y decisiones del BCCR"),
    "policy-rate": ("trayectoria de la inflación", "expectativas inflacionarias", "brecha de actividad y condiciones externas"),
    "inflation": ("precios de alimentos y energía", "tipo de cambio", "demanda interna y efectos base"),
    "imae": ("demanda interna", "actividad de regímenes especiales", "entorno externo y crédito"),
    "unemployment": ("participación laboral", "creación de empleo", "estacionalidad y error de muestreo"),
    "poverty": ("ingreso laboral real", "empleo", "transferencias y costo de la canasta básica"),
    "fiscal-balance": ("recaudación", "gasto primario", "intereses y crecimiento nominal del PIB"),
    "public-debt": ("balance fiscal", "crecimiento nominal del PIB", "tipo de cambio y valoración de la deuda"),
    "reserves": ("compras o ventas de divisas", "flujos del Gobierno", "valoración de activos externos"),
    "exports": ("demanda externa", "precios y cantidades exportadas", "estacionalidad y regímenes especiales"),
    "tourism": ("estacionalidad", "conectividad aérea", "ingreso y condiciones económicas de países emisores"),
    "fdi": ("operaciones empresariales extraordinarias", "reinversión de utilidades", "nuevos proyectos y revisiones estadísticas"),
}

RELATED_INDICATORS = {
    "exchange-rate": (("reserves", "capacidad de amortiguar choques externos"), ("inflation", "posible transmisión hacia precios"), ("policy-rate", "condiciones monetarias relativas")),
    "policy-rate": (("inflation", "principal referencia para la política monetaria"), ("imae", "ritmo de la actividad económica"), ("exchange-rate", "condiciones monetarias y externas")),
    "inflation": (("policy-rate", "respuesta de política monetaria"), ("exchange-rate", "costo en colones de bienes externos"), ("imae", "presiones asociadas con la demanda")),
    "imae": (("unemployment", "respuesta del mercado laboral"), ("exports", "aporte de la demanda externa"), ("tourism", "actividad vinculada con servicios externos")),
    "unemployment": (("imae", "ritmo general de actividad"), ("poverty", "consecuencias distributivas"), ("inflation", "evolución del poder adquisitivo")),
    "poverty": (("unemployment", "acceso a ingresos laborales"), ("inflation", "costo de las necesidades básicas"), ("imae", "entorno de actividad e ingresos")),
    "fiscal-balance": (("public-debt", "acumulación de necesidades de financiamiento"), ("imae", "efecto del ciclo sobre ingresos"), ("policy-rate", "entorno del costo financiero")),
    "public-debt": (("fiscal-balance", "flujo que modifica la necesidad de deuda"), ("policy-rate", "entorno del costo financiero"), ("exchange-rate", "valoración de obligaciones en moneda extranjera")),
    "reserves": (("exchange-rate", "mercado cambiario"), ("exports", "generación de divisas por bienes"), ("tourism", "generación de divisas por servicios")),
    "exports": (("exchange-rate", "competitividad y conversión monetaria"), ("imae", "actividad productiva"), ("reserves", "posición externa")),
    "tourism": (("exchange-rate", "precios relativos para visitantes"), ("imae", "actividad de servicios"), ("reserves", "posición externa")),
    "fdi": (("imae", "actividad y capacidad productiva"), ("exchange-rate", "valoración y condiciones monetarias"), ("reserves", "posición externa")),
}


def _change(current: float, previous: float) -> tuple[float, float | None]:
    absolute = current - previous
    percent = None if previous == 0 else (absolute / abs(previous)) * 100
    return absolute, percent


def _direction(change: float, baseline: float) -> str:
    threshold = max(abs(baseline) * 0.005, 0.05)
    if change > threshold:
        return "Al alza"
    if change < -threshold:
        return "A la baja"
    return "Estable"


def analyze_series(rows: list[dict], frequency: str, unit: str) -> dict:
    """Resume último movimiento, comparación anual y tendencia reciente."""
    clean = sorted(
        (
            {
                "period": value["period"] if isinstance(value["period"], date) else date.fromisoformat(str(value["period"])[:10]),
                "value": float(value["value"]),
            }
            for value in rows
        ),
        key=lambda value: value["period"],
    )
    if not clean:
        raise ValueError("La serie no contiene observaciones")

    latest = clean[-1]
    previous = clean[-2] if len(clean) >= 2 else None
    recent_change = recent_percent = None
    if previous:
        recent_change, recent_percent = _change(latest["value"], previous["value"])

    lag = YEAR_LAGS.get(frequency, 1)
    annual_reference = clean[-1 - lag] if len(clean) > lag else None
    annual_change = annual_percent = None
    if annual_reference:
        annual_change, annual_percent = _change(latest["value"], annual_reference["value"])

    requested_window = TREND_WINDOWS.get(frequency, 6)
    trend_rows = clean[-min(len(clean), requested_window):]
    trend_change = trend_rows[-1]["value"] - trend_rows[0]["value"] if len(trend_rows) > 1 else 0.0
    trend = _direction(trend_change, trend_rows[0]["value"])
    is_rate = unit.strip().startswith("%")
    extreme_change = False
    if recent_change is not None:
        extreme_change = abs(recent_change) >= 5 if is_rate else bool(recent_percent is not None and abs(recent_percent) >= 100)

    return {
        "latest_period": latest["period"],
        "latest_value": latest["value"],
        "previous_period": previous["period"] if previous else None,
        "recent_change": recent_change,
        "recent_percent": recent_percent,
        "annual_reference_period": annual_reference["period"] if annual_reference else None,
        "annual_change": annual_change,
        "annual_percent": annual_percent,
        "trend": trend,
        "trend_observations": len(trend_rows),
        "is_rate": is_rate,
        "extreme_change": extreme_change,
    }


def explain_analysis(name: str, analysis: dict) -> str:
    """Produce una explicación neutral: describe movimientos, no recomienda ni predice."""
    latest = analysis["latest_value"]
    if analysis["recent_change"] is None:
        return f"{name} registra {latest:,.2f}. No hay suficientes observaciones para comparar."
    if analysis["is_rate"]:
        recent = f"{analysis['recent_change']:+.2f} puntos porcentuales"
        annual = (
            f"{analysis['annual_change']:+.2f} puntos porcentuales"
            if analysis["annual_change"] is not None
            else "no disponible"
        )
    else:
        recent = f"{analysis['recent_percent']:+.2f}%" if analysis["recent_percent"] is not None else "no calculable"
        annual = f"{analysis['annual_percent']:+.2f}%" if analysis["annual_percent"] is not None else "no disponible"
    return (
        f"El último dato de {name} es {latest:,.2f}. Frente a la observación anterior cambió {recent}; "
        f"la comparación interanual es {annual}. En las últimas {analysis['trend_observations']} "
        f"observaciones, la trayectoria descriptiva es: {analysis['trend'].lower()}."
    )


def build_fq_reading(slug: str, name: str, analysis: dict, caveat: str = "") -> dict:
    """Separa hechos, significado descriptivo e hipótesis que aún requieren evidencia."""
    direction = analysis["trend"]
    meaning = MEANING_BY_INDICATOR.get(slug, {}).get(
        direction,
        f"{name} presenta una trayectoria reciente {direction.lower()}.",
    )
    hypotheses = HYPOTHESES_BY_INDICATOR.get(
        slug,
        ("cambios de demanda", "factores de oferta", "efectos estacionales o metodológicos"),
    )
    return {
        "fact": explain_analysis(name, analysis),
        "meaning": meaning,
        "hypotheses": hypotheses,
        "questions": (
            "¿El movimiento aparece también en componentes relacionados?",
            "¿La fuente publicó una revisión o nota metodológica?",
            "¿Se mantiene la señal al comparar más de un período?",
        ),
        "caveat": caveat or "La descripción no demuestra causalidad y puede cambiar con nuevas observaciones.",
    }


def related_indicator_specs(slug: str) -> tuple[tuple[str, str], ...]:
    """Devuelve señales relacionadas y el motivo analítico para observarlas juntas."""
    return RELATED_INDICATORS.get(slug, ())


def build_research_brief(
    slug: str,
    name: str,
    analysis: dict,
    reading: dict,
    related: list[dict],
    source: str,
    source_url: str,
    unit: str,
) -> str:
    """Genera una ficha de texto reproducible sin convertir hipótesis en conclusiones."""
    hypotheses = "\n".join(f"- {item[:1].upper() + item[1:]}." for item in reading["hypotheses"])
    questions = "\n".join(f"- {item}" for item in reading["questions"])
    related_lines = "\n".join(
        f"- {item['name']}: {item['value']} ({item['trend']}; {item['period']}"
        f"{' — cierre del período; dato provisional' if item.get('provisional') else ''}). "
        f"Motivo: {item['reason']}."
        for item in related
    ) or "- No hay señales relacionadas disponibles."
    return f"""FICHA FRANQUESTIONS — {name}

Identificador: {slug}
Último período: {analysis['latest_period'].isoformat()}
Último valor: {analysis['latest_value']:,.2f} {unit}
Fuente oficial: {source}
Enlace oficial: {source_url}

1. HECHO COMPROBADO

{reading['fact']}

2. QUÉ PUEDE SIGNIFICAR

{reading['meaning']}

3. SEÑALES RELACIONADAS

{related_lines}

4. HIPÓTESIS QUE DEBEN INVESTIGARSE

{hypotheses}

5. PREGUNTAS DE VERIFICACIÓN

{questions}

6. ADVERTENCIA METODOLÓGICA

{reading['caveat']}

Esta ficha es una lectura descriptiva automática. No constituye una predicción, una recomendación ni una demostración de causalidad.
"""


def build_economic_snapshot(groups: list[tuple[str, list[dict]]], generated_on: date) -> str:
    """Consolida el estado descriptivo de los indicadores en un panorama ejecutivo."""
    all_indicators = {
        item["slug"]: item
        for _, indicators in groups
        for item in indicators
    }
    executive_lines = build_executive_summary(all_indicators)
    executive_summary = "\n".join(f"- {line}" for line in executive_lines)
    sections = []
    for group_name, indicators in groups:
        lines = [group_name.upper()]
        for item in indicators:
            provisional = " — cierre del período; dato provisional" if item.get("provisional") else ""
            lines.append(
                f"- {item['name']}: {item['value']} | {item['period']}{provisional} | "
                f"Tendencia: {item['trend']} | Estado: {item['status']}."
            )
            if item.get("caveat"):
                lines.append(f"  Advertencia: {item['caveat']}")
        sections.append("\n".join(lines))
    body = "\n\n".join(sections)
    return f"""PANORAMA ECONÓMICO FRANQUESTIONS

Fecha de generación: {generated_on.isoformat()}
Cobertura: 12 indicadores oficiales de Costa Rica

RESUMEN EJECUTIVO

{executive_summary}

{body}

NOTA METODOLÓGICA

Este panorama es descriptivo. Las frecuencias y fechas de publicación difieren entre indicadores; una coincidencia de tendencias no demuestra causalidad. Antes de citar un dato deben revisarse su fuente y advertencia metodológica.
"""


def build_executive_summary(indicators: dict[str, dict]) -> list[str]:
    """Resume bloques económicos y alertas sin atribuir causas no verificadas."""
    def trend(slug: str) -> str:
        return indicators[slug]["trend"].lower()

    lines = [
        (
            f"Actividad y empleo: el IMAE presenta una trayectoria {trend('imae')} y la tasa de desempleo "
            f"una trayectoria {trend('unemployment')}. Deben leerse con sus diferentes períodos de referencia."
        ),
        (
            f"Precios y política monetaria: la inflación se encuentra {trend('inflation')}, mientras la TPM "
            f"permanece {trend('policy-rate')} y el tipo de cambio se mueve {trend('exchange-rate')}."
        ),
        (
            f"Finanzas públicas: el balance financiero muestra una trayectoria {trend('fiscal-balance')} y la deuda/PIB "
            f"una trayectoria {trend('public-debt')}. Son datos anuales de cierre."
        ),
        (
            f"Sector externo: reservas {trend('reserves')}, exportaciones {trend('exports')}, turismo "
            f"{trend('tourism')} e inversión directa {trend('fdi')}. Las señales del bloque no son uniformes."
        ),
    ]
    attention = [
        item["name"]
        for item in indicators.values()
        if item.get("extreme") or item.get("provisional") or item.get("status_code") in {"review", "overdue"}
    ]
    if attention:
        lines.append("Requieren atención metodológica o de actualización: " + ", ".join(attention) + ".")
    else:
        lines.append("No hay alertas extraordinarias ni actualizaciones pendientes en el corte actual.")
    lines.append("Conclusión: el panorama contiene señales mixtas; no corresponde resumirlo como mejora o deterioro general con un único indicador.")
    return lines
