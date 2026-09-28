"""Ejecuta un ensayo temporal de recuperación sin tocar la base de origen."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fq_observatorio.recovery_rehearsal import run_recovery_rehearsal


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="Ruta de la base SQLite que se comprobará")
    args = parser.parse_args()
    report = run_recovery_rehearsal(args.database)
    print(json.dumps(report.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
