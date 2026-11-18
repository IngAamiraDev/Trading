"""Carga y acceso a la configuracion del motor AAA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = PACKAGE_ROOT.parent.parent
DEFAULT_CONFIG_PATH = PACKAGE_ROOT / "config" / "aaa.json"
CACHE_DIR = PACKAGE_ROOT / ".cache"
REPORTS_DIR = REPO_ROOT / "reports"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Lee el JSON de configuracion. Falla ruidosamente si no existe."""
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise FileNotFoundError(f"No existe la configuracion: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Acceso anidado tolerante a claves ausentes."""
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
