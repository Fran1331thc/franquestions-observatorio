"""Regression checks for charts rendered in mobile browsers.

Some mobile browsers used by FranQuestions do not support WebGL.  Public
Plotly charts therefore need to use SVG explicitly so the dashboard never
falls back to ``scattergl`` when a series grows.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_FILES = tuple(
    path
    for path in PROJECT_ROOT.rglob("*.py")
    if ".venv" not in path.parts and "tests" not in path.parts
)
PLOTLY_EXPRESS_SERIES_CHARTS = {"line", "scatter", "area", "line_3d", "scatter_3d"}


def _call_name(node: ast.Call) -> str | None:
    if not isinstance(node.func, ast.Attribute):
        return None
    if isinstance(node.func.value, ast.Name):
        return f"{node.func.value.id}.{node.func.attr}"
    return node.func.attr


class MobileChartCompatibilityTests(unittest.TestCase):
    def test_plotly_express_series_charts_explicitly_use_svg(self) -> None:
        violations: list[str] = []

        for path in PYTHON_FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = _call_name(node)
                if name not in {f"px.{chart}" for chart in PLOTLY_EXPRESS_SERIES_CHARTS}:
                    continue
                render_mode = next(
                    (keyword.value for keyword in node.keywords if keyword.arg == "render_mode"),
                    None,
                )
                if not (
                    isinstance(render_mode, ast.Constant)
                    and render_mode.value == "svg"
                ):
                    relative_path = path.relative_to(PROJECT_ROOT)
                    violations.append(f"{relative_path}:{node.lineno}")

        self.assertFalse(
            violations,
            "Los gráficos Plotly de series deben declarar render_mode='svg': "
            + ", ".join(violations),
        )

    def test_no_webgl_trace_is_created_directly(self) -> None:
        violations: list[str] = []

        for path in PYTHON_FILES:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if _call_name(node) in {"go.Scattergl", "Scattergl"}:
                    relative_path = path.relative_to(PROJECT_ROOT)
                    violations.append(f"{relative_path}:{node.lineno}")

        self.assertFalse(
            violations,
            "WebGL no es compatible con todos los teléfonos usados por FranQuestions: "
            + ", ".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
