"""Planes y permisos comerciales de FranQuestions.

Esta capa define qué puede habilitarse por plan, pero no procesa pagos ni autentica
usuarios. Durante el desarrollo se utiliza ``owner``, que conserva acceso total.
"""

from __future__ import annotations


PLAN_LABELS = {
    "public": "FranQuestions Público",
    "pro": "FranQuestions Pro",
    "business": "FranQuestions Empresas",
    "institutional": "FranQuestions Institucional",
    "owner": "Modo propietario",
}

FEATURE_LABELS = {
    "basic_observatory": "Observatorio e indicadores básicos",
    "official_sources": "Fuentes y metodología",
    "historical_charts": "Gráficos históricos",
    "indicator_explanations": "Fichas explicativas",
    "local_preferences": "Indicadores favoritos y preferencias locales",
    "public_reasoning_reading": "Lectura pública verificable",
    "full_executive_summary": "Resumen ejecutivo completo",
    "cross_indicator_analysis": "Contraste completo entre indicadores",
    "research_brief_download": "Descarga de fichas de investigación",
    "economic_snapshot_download": "Descarga del panorama económico",
    "personal_alerts": "Alertas personalizadas",
    "revision_history": "Historial de revisiones",
    "data_export": "Exportación de datos",
    "custom_dashboards": "Tableros personalizados",
    "private_company_data": "Integración de datos empresariales",
    "sector_reports": "Informes sectoriales",
    "api_access": "Acceso mediante API",
    "contract_research": "Investigación contratada",
    "policy_briefs": "Policy briefs institucionales",
    "sponsored_observatories": "Observatorios patrocinados",
    "reasoning_foundations_lab": "Laboratorio: definir y verificar afirmaciones",
    "causal_reasoning_lab": "Laboratorio: prueba de mecanismos causales",
    "system_reasoning_lab": "Laboratorio: implementación y restricciones",
    "outcome_reasoning_lab": "Laboratorio: resultados y atribución",
    "conclusion_audit_lab": "Laboratorio: auditoría de conclusiones",
    "conclusion_update_lab": "Laboratorio: actualización de conclusiones",
}

PUBLIC_FEATURES = {
    "basic_observatory",
    "official_sources",
    "historical_charts",
    "indicator_explanations",
    "local_preferences",
    "public_reasoning_reading",
}

PRO_FEATURES = PUBLIC_FEATURES | {
    "full_executive_summary",
    "cross_indicator_analysis",
    "research_brief_download",
    "economic_snapshot_download",
    "personal_alerts",
    "revision_history",
    "data_export",
}

BUSINESS_FEATURES = PRO_FEATURES | {
    "custom_dashboards",
    "private_company_data",
    "sector_reports",
    "api_access",
}

INSTITUTIONAL_FEATURES = PRO_FEATURES | {
    "contract_research",
    "policy_briefs",
    "sponsored_observatories",
}

PLAN_FEATURES = {
    "public": PUBLIC_FEATURES,
    "pro": PRO_FEATURES,
    "business": BUSINESS_FEATURES,
    "institutional": INSTITUTIONAL_FEATURES,
    "owner": set(FEATURE_LABELS),
}


def normalize_plan(plan: str | None) -> str | None:
    """Normaliza planes conocidos y deniega por defecto cualquier otro valor."""
    normalized = (plan or "").strip().lower()
    return normalized if normalized in PLAN_FEATURES else None


def has_feature(plan: str | None, feature: str) -> bool:
    """Indica si un plan tiene una función; una función desconocida nunca se habilita."""
    normalized = normalize_plan(plan)
    return normalized is not None and feature in PLAN_FEATURES[normalized]


def features_for_plan(plan: str | None) -> tuple[str, ...]:
    normalized = normalize_plan(plan)
    if normalized is None:
        return ()
    return tuple(sorted(PLAN_FEATURES[normalized]))
