# AAA Web Sync

Publica los runs del motor AAA en la web (`aaa-web/`) sin acoplar el motor a la base de datos.

## Flujo

1. El motor escribe `reports/YYYY-MM-DD/candidates.json` junto al resto del reporte.
2. `sync.py` envía ese JSON a `POST /api/ingest` con un token Bearer.
3. La base de datos guarda el run y la web lo muestra.

El envío es idempotente: el `run_id` identifica la ejecución y reenviarla
reemplaza sus filas, no las duplica.

## Uso manual

```bash
export AAA_WEB_URL="https://tu-app.vercel.app"
export AAA_INGEST_TOKEN="..."

python scripts/aaa_web_sync/sync.py \
  --file reports/2026-11-17/candidates.json
```

Para validar sin enviar:

```bash
python scripts/aaa_web_sync/sync.py --file reports/2026-11-17/candidates.json --dry-run
```

## Ejecución diaria

`daily.sh` ejecuta el plan y publica el resultado:

```bash
AAA_CAPITAL=10000 ./scripts/aaa_web_sync/daily.sh
```

Variables:

- `AAA_PYTHON`: intérprete con pandas/yfinance (por defecto `/tmp/opencode/trading-venv/bin/python`).
- `AAA_CAPITAL`: capital de referencia (por defecto `10000`).
- `AAA_TIMEZONE`: zona para la fecha del reporte (por defecto `America/New_York`).
- `AAA_WEB_URL` y `AAA_INGEST_TOKEN`: destino.

### Cron

```cron
CRON_TZ=America/New_York
30 8 * * 1-5  /ruta/al/repo/scripts/aaa_web_sync/daily.sh >> /ruta/al/repo/logs/aaa.log 2>&1
```

En WSL el cron solo corre mientras la instancia esté activa. En Windows,
programa `wsl.exe -e bash -lc '/ruta/al/repo/scripts/aaa_web_sync/daily.sh'`
con el Programador de tareas.

El modo `day` necesita barras intradía. Si el plan se lanza antes de la
apertura, es normal que ese modo aparezca como `sin datos`; la web lo muestra
así y no lo convierte en una señal.

## Sembrar un reporte antiguo

Los reportes anteriores solo tienen CSV y Markdown. Para cargar uno:

```bash
python scripts/aaa_web_sync/seed_from_csv.py \
  --report-dir reports/2026-11-17
python scripts/aaa_web_sync/sync.py \
  --file reports/2026-11-17/candidates.json
```

`seed_from_csv.py` no recalcula señales: reconstruye un payload aproximado con
los campos del CSV y los bloques que aparecen en `plan.md`. Úsalo solo para
histórico. Si el `summary.json` no trae `trend`, el script lo deduce de los
índices del `plan.md` con la misma regla del motor.

## Qué viaja del motor a la web

El payload lleva la lectura de AAA en tres niveles:

| Campo | Qué es |
|---|---|
| `regime.trend` | Dirección del mercado: `alcista`, `lateral` o `bajista`. |
| `regime.label` + `regime.vix` | Cuánto riesgo se permite (no la dirección). |
| `metrics.sector_state` | Estado del sector de la acción: `fuerte`, `lateral`, `débil`. |
| `metrics.sector_rs21` | Fuerza relativa del sector frente a SPY. |
| `metrics.rs_sector21/63` | Fuerza relativa de la acción frente a su propio sector. |
| `metrics.rs21/63` | Fuerza relativa de la acción frente a SPY. |
| `metrics.extreme_move` | La serie tiene un salto extremo: la RS no es comparable. |

Si un dato falta, la web lo muestra como ausente (`—`), no lo rellena.
