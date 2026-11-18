# AAA Scanner

Motor de screening y planificación para acciones de EE. UU. basado en los tres
pilares AAA-CDI: alineación, fortaleza relativa/momentum y asimetría/riesgo.

Es una **aproximación configurable** a los tres pilares públicos de El Club de
Inversionistas (CDI). No reproduce reglas privadas del taller ni ejecuta
órdenes.

## Instalación

```bash
python3 -m venv /tmp/opencode/trading-venv
. /tmp/opencode/trading-venv/bin/activate
pip install -r strategies/aaa/requirements.txt
```

## Uso

Desde la raíz del repositorio:

```bash
# Plan completo del día (swing + inversión + day)
python strategies/aaa/main.py plan --capital 10000

# Escaneo de un modo
python strategies/aaa/main.py scan --mode swing
python strategies/aaa/main.py scan --mode invest
python strategies/aaa/main.py scan --mode day

# Análisis de un ticker
python strategies/aaa/main.py review NVDA --mode swing

# Sin escribir reportes y con universo reducido
python strategies/aaa/main.py scan --mode swing --limit 10 --no-write
```

Los reportes se guardan en `reports/YYYY-MM-DD/`:

- `plan.md` — régimen, riesgo, watchlists y descartes.
- `candidates.csv` — una fila por candidato.
- `watchlist_tradingview.txt` — tickers accionables y en vigilancia.
- `summary.json` — conteos y errores del escaneo.

## Agentes y comandos

Los perfiles viven en `.opencode/agents/` y los comandos en
`.opencode/commands/`:

| Agente | Rol |
|---|---|
| `aaa` | Director: régimen, delegación y plan en `reports/` |
| `aaa-swing` | Núcleo AAA-CDI a 2–15 días |
| `aaa-invest` | Calidad, crecimiento y valoración a 3–12 meses |
| `aaa-day` | Universo premarket y niveles intradía (paper) |
| `aaa-risk` | Tamaño, R/R, exposición y vetos |
| `aaa-auditor` | Revisión read-only de datos y coherencia |

Comandos: `/aaa-plan`, `/aaa-scan`, `/aaa-review`, `/aaa-journal`.

## Tests

```bash
python -m unittest discover -s strategies/aaa/tests
```

Los tests no usan red: cubren indicadores, scoring, riesgo, presets y reporte.

## Límites

- Finviz y yfinance pueden tener retraso, rate limits o datos incompletos.
- yfinance intradía no es un feed de ejecución: day trading es research/paper.
- No hay backtest fundamental histórico gratuito. No se presenta ninguno como
  validación real.
- El sistema genera señales; la ejecución es humana.
- No es asesoría financiera.
