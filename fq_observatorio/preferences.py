"""Preferencias locales del MVP, antes de incorporar cuentas de usuario."""

from __future__ import annotations

import json
from pathlib import Path


DEFAULT_PREFERENCES = {
    "favorites": ["exchange-rate", "inflation", "imae"],
    "default_indicator": "exchange-rate",
    "detail_level": "Completo",
    "alert_types": ["official_update", "extreme_change", "revision"],
    "alert_frequency": "Diaria",
    "read_alert_ids": [],
    "onboarding_complete": False,
}

ALLOWED_ALERT_TYPES = {"official_update", "extreme_change", "revision"}
ALLOWED_ALERT_FREQUENCIES = {"Inmediata", "Diaria", "Semanal"}


def load_preferences(path: str | Path, allowed_slugs: set[str]) -> dict:
    target = Path(path)
    try:
        raw = json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    except (OSError, json.JSONDecodeError):
        raw = {}
    favorites = [slug for slug in raw.get("favorites", DEFAULT_PREFERENCES["favorites"]) if slug in allowed_slugs]
    if not favorites:
        favorites = [slug for slug in DEFAULT_PREFERENCES["favorites"] if slug in allowed_slugs]
    default_indicator = raw.get("default_indicator", DEFAULT_PREFERENCES["default_indicator"])
    if default_indicator not in allowed_slugs:
        default_indicator = favorites[0]
    detail_level = raw.get("detail_level", DEFAULT_PREFERENCES["detail_level"])
    if detail_level not in {"Esencial", "Completo"}:
        detail_level = "Completo"
    alert_types = [
        value for value in raw.get("alert_types", DEFAULT_PREFERENCES["alert_types"])
        if value in ALLOWED_ALERT_TYPES
    ]
    alert_frequency = raw.get("alert_frequency", DEFAULT_PREFERENCES["alert_frequency"])
    if alert_frequency not in ALLOWED_ALERT_FREQUENCIES:
        alert_frequency = DEFAULT_PREFERENCES["alert_frequency"]
    read_alert_ids = [str(value) for value in raw.get("read_alert_ids", []) if isinstance(value, str)][-500:]
    onboarding_complete = bool(raw.get("onboarding_complete", False))
    return {
        "favorites": favorites,
        "default_indicator": default_indicator,
        "detail_level": detail_level,
        "alert_types": alert_types,
        "alert_frequency": alert_frequency,
        "read_alert_ids": read_alert_ids,
        "onboarding_complete": onboarding_complete,
    }


def save_preferences(path: str | Path, preferences: dict, allowed_slugs: set[str]) -> dict:
    clean = load_preferences_from_values(preferences, allowed_slugs)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    return clean


def load_preferences_from_values(preferences: dict, allowed_slugs: set[str]) -> dict:
    favorites = [slug for slug in preferences.get("favorites", []) if slug in allowed_slugs]
    if not favorites:
        favorites = [slug for slug in DEFAULT_PREFERENCES["favorites"] if slug in allowed_slugs]
    default_indicator = preferences.get("default_indicator")
    if default_indicator not in favorites:
        default_indicator = favorites[0]
    detail_level = preferences.get("detail_level", "Completo")
    if detail_level not in {"Esencial", "Completo"}:
        detail_level = "Completo"
    alert_types = [
        value for value in preferences.get("alert_types", DEFAULT_PREFERENCES["alert_types"])
        if value in ALLOWED_ALERT_TYPES
    ]
    alert_frequency = preferences.get("alert_frequency", DEFAULT_PREFERENCES["alert_frequency"])
    if alert_frequency not in ALLOWED_ALERT_FREQUENCIES:
        alert_frequency = DEFAULT_PREFERENCES["alert_frequency"]
    read_alert_ids = [str(value) for value in preferences.get("read_alert_ids", []) if isinstance(value, str)][-500:]
    onboarding_complete = bool(preferences.get("onboarding_complete", False))
    return {
        "favorites": favorites,
        "default_indicator": default_indicator,
        "detail_level": detail_level,
        "alert_types": alert_types,
        "alert_frequency": alert_frequency,
        "read_alert_ids": read_alert_ids,
        "onboarding_complete": onboarding_complete,
    }
