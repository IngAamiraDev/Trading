#!/usr/bin/env python3
"""Publica un candidates.json del motor AAA en la web.

Uso:
    python scripts/aaa_web_sync/sync.py --file reports/2026-11-17/candidates.json

Variables de entorno:
    AAA_WEB_URL       URL base de la app (por ejemplo https://aaa.vercel.app)
    AAA_INGEST_TOKEN  Token compartido con /api/ingest
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def default_file() -> Path:
    return REPO_ROOT / "reports" / date.today().isoformat() / "candidates.json"


def load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"No existe el archivo: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON inválido en {path}: {exc}") from exc

    required = {"run_id", "generated_at", "trading_date", "regime", "candidates"}
    missing = sorted(required - set(payload))
    if missing:
        raise SystemExit(f"Faltan claves en el payload: {', '.join(missing)}")
    if not isinstance(payload["candidates"], list):
        raise SystemExit("'candidates' debe ser una lista.")
    return payload


def post(url: str, token: str, payload: dict[str, Any], timeout: float) -> tuple[int, str]:
    endpoint = f"{url.rstrip('/')}/api/ingest"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "aaa-web-sync/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")
    except urllib.error.URLError as exc:
        raise SystemExit(f"No se pudo conectar con {endpoint}: {exc.reason}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publica un run AAA en la web.")
    parser.add_argument("--file", type=Path, default=None, help="Ruta del candidates.json")
    parser.add_argument("--url", default=None, help="URL base de la web")
    parser.add_argument("--token", default=None, help="Token de ingesta")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout en segundos")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida el JSON sin enviarlo",
    )
    args = parser.parse_args(argv)

    path = args.file or default_file()
    payload = load_payload(path)

    print(
        f"Run {payload['run_id']} | {payload['trading_date']} | "
        f"{len(payload['candidates'])} candidatos | régimen {payload['regime'].get('label')}"
    )

    if args.dry_run:
        print("Dry-run: payload válido, no se envió nada.")
        return 0

    url = args.url or os.environ.get("AAA_WEB_URL", "")
    token = args.token or os.environ.get("AAA_INGEST_TOKEN", "")
    if not url:
        raise SystemExit("Falta --url o la variable AAA_WEB_URL.")
    if not token:
        raise SystemExit("Falta --token o la variable AAA_INGEST_TOKEN.")

    status, response = post(url, token, payload, args.timeout)
    print(f"HTTP {status}: {response}")
    if status < 200 or status >= 300:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
