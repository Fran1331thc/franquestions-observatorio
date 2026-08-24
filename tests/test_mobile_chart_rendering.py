from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHART_FILES = (
    PROJECT_ROOT / "streamlit_app_stable.py",
    PROJECT_ROOT / "fq_observatorio" / "dashboard.py",
)


def _plotly_line_calls(path: Path) -> list[ast.Call]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "px"
        and node.func.attr == "line"
    ]


def test_all_plotly_line_charts_force_svg_for_mobile_compatibility() -> None:
    for path in CHART_FILES:
        calls = _plotly_line_calls(path)
        assert calls, f"No se encontraron gráficos px.line en {path.name}"

        for call in calls:
            render_mode = next(
                (keyword.value for keyword in call.keywords if keyword.arg == "render_mode"),
                None,
            )
            assert isinstance(render_mode, ast.Constant)
            assert render_mode.value == "svg"
