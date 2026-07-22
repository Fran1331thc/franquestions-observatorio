"""Centro local de alertas reproducibles para los indicadores favoritos."""

from __future__ import annotations

from hashlib import sha256


SEVERITY_ORDER = {"high": 0, "medium": 1, "info": 2}


def _alert_id(slug: str, alert_type: str, period: str) -> str:
    raw = f"{slug}|{alert_type}|{period}".encode("utf-8")
    return sha256(raw).hexdigest()[:16]


def build_local_alerts(
    favorites: list[str],
    latest_by_slug: dict,
    snapshot_by_slug: dict,
    revisions_by_slug: dict,
    enabled_types: list[str],
    names_by_slug: dict,
) -> list[dict]:
    """Construye alertas estables sin enviar datos fuera de la aplicación."""
    alerts: list[dict] = []
    for slug in favorites:
        latest = latest_by_slug.get(slug)
        if not latest:
            continue
        period = str(latest["period"])[:10]
        name = names_by_slug[slug]
        if "official_update" in enabled_types:
            alerts.append(
                {
                    "id": _alert_id(slug, "official_update", period),
                    "slug": slug,
                    "type": "official_update",
                    "severity": "info",
                    "title": f"Dato oficial disponible: {name}",
                    "message": f"La observación más reciente corresponde al {period}.",
                    "period": period,
                }
            )
        snapshot = snapshot_by_slug.get(slug, {})
        if "extreme_change" in enabled_types and snapshot.get("extreme"):
            alerts.append(
                {
                    "id": _alert_id(slug, "extreme_change", period),
                    "slug": slug,
                    "type": "extreme_change",
                    "severity": "high",
                    "title": f"Cambio excepcional: {name}",
                    "message": "Revise la nota metodológica, el carácter preliminar y posibles efectos estacionales antes de interpretarlo.",
                    "period": period,
                }
            )
        revision = revisions_by_slug.get(slug)
        if "revision" in enabled_types and revision:
            revision_period = str(revision["period"])[:10]
            alerts.append(
                {
                    "id": _alert_id(slug, "revision", revision_period),
                    "slug": slug,
                    "type": "revision",
                    "severity": "medium",
                    "title": f"Dato revisado: {name}",
                    "message": f"La observación del {revision_period} cambió de {revision['old_value']} a {revision['new_value']}.",
                    "period": revision_period,
                }
            )
    return sorted(alerts, key=lambda item: (SEVERITY_ORDER[item["severity"]], item["title"]))
