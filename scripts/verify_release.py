"""Verificacion local, reproducible y sin escrituras para FranQuestions."""

from __future__ import annotations

import compileall
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_PATHS = (
    "streamlit_app.py",
    "requirements.txt",
    "pyproject.toml",
    "fq_observatorio",
    "tests",
)


def print_step(number: int, title: str) -> None:
    print(f"\n[{number}/3] {title}")


def check_structure() -> bool:
    missing = [name for name in REQUIRED_PATHS if not (PROJECT_ROOT / name).exists()]
    if missing:
        print("Faltan elementos obligatorios:")
        for name in missing:
            print(f"  - {name}")
        return False
    print("Estructura minima completa.")
    return True


def check_compilation() -> bool:
    targets = [PROJECT_ROOT / "streamlit_app.py", PROJECT_ROOT / "fq_observatorio"]
    success = True
    for target in targets:
        if target.is_dir():
            success = compileall.compile_dir(
                str(target), quiet=1, force=True, legacy=True
            ) and success
        else:
            success = compileall.compile_file(
                str(target), quiet=1, force=True, legacy=True
            ) and success
    print("Codigo compilado correctamente." if success else "La compilacion encontro errores.")
    return success


def check_tests() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if result.returncode == 0:
        print("Todas las pruebas terminaron correctamente.")
        return True
    print("Una o mas pruebas fallaron. Revise el detalle anterior.")
    return False


def main() -> int:
    print("=" * 62)
    print("VERIFICACION DE PUBLICACION - FRANQUESTIONS")
    print("Esta comprobacion no modifica la base de datos.")
    print("=" * 62)

    print_step(1, "Comprobar estructura")
    structure_ok = check_structure()

    print_step(2, "Comprobar sintaxis y compilacion")
    compilation_ok = check_compilation() if structure_ok else False

    print_step(3, "Ejecutar pruebas de seguridad y formatos oficiales")
    tests_ok = check_tests() if structure_ok and compilation_ok else False

    print("\n" + "=" * 62)
    if structure_ok and compilation_ok and tests_ok:
        print("RESULTADO: APTO PARA CONTINUAR CON LA REVISION DE PUBLICACION")
        print("Nota: esto no sustituye la revision visual ni autoriza un despliegue.")
        print("Siguiente paso: abra INICIAR_REVISION_PUBLICACION.cmd y complete la lista.")
        return 0

    print("RESULTADO: NO APTO PARA PUBLICAR")
    print("Corrija los fallos mostrados antes de actualizar la version publica.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
