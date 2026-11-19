# AGENTS.md

Repositorio personal de trading: varios scripts independientes (Python, TypeScript) y un dashboard Power BI. No hay aplicación única, manifest raíz, tests, lint ni CI. Cada subproyecto se ejecuta desde su propio directorio y tiene sus propias dependencias.

## Mapa

- `Trades-XTB/` — ingesta de exportes de XTB. `scripts/read_data_xtb.py` lee `data/*.xlsx` con nombre `USD_<cuenta>_*.xlsx`, hojas `Closed Positions` y `Cash Operations` (con `skiprows=4`), y hace upsert en `data/trades_xtb.csv` (clave `ID` + `id_account`) y `data/transactions_xtb.csv` (clave `Type` + `Time` + `Amount` + `id_account`). No borra filas existentes.
  `dashboard/dashboard_xtb.pbix` es binario de Power BI: no se edita como texto.
- `strategies/vcp_scanner/` — screener VCP. Entrada `main.py`; puntuación en `src/scorer.py`; tickers en `input/tickers.txt` (una línea separada por comas); salidas versionadas en `output/` (`all_ranked.csv`, `top20.csv`, `ready_to_breakout.csv` = Score ≥ 70, `tradingview_watchlist.txt`).
- `strategies/aaa/` — motor AAA-CDI (aproximación configurable, no el método privado de CDI). `main.py` (CLI `scan`/`plan`/`review`), reglas en `PLAYBOOK.md`, umbrales en `config/aaa.json`, lógica en `src/` (presets Finviz, indicadores, scoring, riesgo, reporte) y tests en `tests/`. Salidas en `reports/YYYY-MM-DD/` (`plan.md`, `candidates.csv`, `candidates.json`, `watchlist_tradingview.txt`, `summary.json`).
- `aaa-web/` — mesa de señales Next.js 16 (App Router) + TypeScript + Tailwind v4 + Drizzle/Postgres. Login de un solo usuario (`lib/auth.ts`), dashboard, candidatos y detalle; `POST /api/ingest` (Bearer token) recibe `candidates.json` de forma idempotente por `run_id`. Migraciones en `aaa-web/drizzle/`. Desplegable en Vercel + Neon (ver `aaa-web/README.md`).
- `scripts/aaa_web_sync/` — `sync.py` publica un `candidates.json` en `/api/ingest`; `daily.sh` ejecuta `main.py plan` y lo sincroniza; `seed_from_csv.py` reconstruye un payload aproximado para reportes antiguos que solo tienen CSV/plan.md. `README.md` con cron y variables.
- `.opencode/agents/*.md` y `.opencode/commands/*.md` — agentes (`aaa`, `aaa-swing`, `aaa-invest`, `aaa-day`, `aaa-risk`, `aaa-auditor`) y comandos (`/aaa-plan`, `/aaa-scan`, `/aaa-review`, `/aaa-journal`). Solo generan señales: no ejecutan órdenes.
- `scripts/convert_tickers/` — reescribe `strategies/vcp_scanner/input/tickers.txt`. La ruta está hardcodeada relativa a la raíz: ejecutar desde la raíz del repo.
- `scripts/screener/finviz-py/` — scripts sueltos de Finviz/yfinance (`screener-finviz.py`, `smart_screener.py`, `entry-smart.py`, `automatiza_busqueda_yf.py`, `scraping.py`). Requieren red; los que exportan guardan el CSV en el directorio actual.
- `scripts/bot-scripts/{MA_RSI_Bot,SAR_Bot}/` — bots live para MetaTrader 5. Requieren Windows + terminal MT5 y `.env` con `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`. No se pueden ejecutar en Linux/WSL.
- `scripts/stock-analysis-project/` — app TypeScript/Finnhub. Sin `node_modules` ni lockfile; no está lista para `npm run build`/`npm start` (ver trampas).
- `scripts/extracciones/` — extracción de movimientos bancarios desde Excel (`openpyxl`), con `--input-dir`/`--output`.
- `Docs/`, `plots/`, `strategies/volumen/` — material de referencia en español (docx/pdf/md). `Data/` — Excel de revisión.

## Comandos

En este entorno, el Python del sistema (3.12) no tiene pandas, openpyxl ni yfinance. Crea el venv fuera del repo: la raíz `.gitignore` solo cubre `__pycache__`, `*.pyc`, `.venv/` y `strategies/aaa/.cache/`. El venv existente en `strategies/vcp_scanner/env` está roto (paquetes de Python 3.14 con intérprete 3.12) y no está versionado: no lo reutilices. Los agentes AAA esperan el venv en `/tmp/opencode/trading-venv`.

Trades-XTB (desde `Trades-XTB/scripts`):

```bash
python3 -m venv /tmp/opencode/trading-venv
. /tmp/opencode/trading-venv/bin/activate
pip install -r requirements.txt openpyxl
python read_data_xtb.py
```

`requirements.txt` omite `openpyxl` aunque `pandas.read_excel` lo necesita. El `README.md` de esa carpeta menciona un `env/` inexistente y ejecuta el script desde el directorio equivocado.

VCP scanner (desde `strategies/vcp_scanner`):

```bash
pip install -r requirements.txt
python main.py
```

`main.py` usa rutas relativas (`input/`, `output/`) e importa `src.*`: hay que ejecutarlo desde esa carpeta, no desde la raíz.

AAA (desde la raíz del repo):

```bash
/tmp/opencode/trading-venv/bin/python strategies/aaa/main.py plan --capital 10000
/tmp/opencode/trading-venv/bin/python strategies/aaa/main.py scan --mode swing
/tmp/opencode/trading-venv/bin/python strategies/aaa/main.py review NVDA --mode swing
/tmp/opencode/trading-venv/bin/python -m unittest discover -s strategies/aaa/tests
```

`--no-write` evita escribir reportes y `--limit N` reduce el universo. `plan` ejecuta swing + inversión + day; `day` necesita datos intradía de yfinance (pueden estar retrasados). El motor escribe en `reports/YYYY-MM-DD/`, no en `strategies/aaa/`.

Web AAA (desde `aaa-web`):

```bash
npm install
npm run db:migrate          # requiere DATABASE_URL
npm run dev                 # http://localhost:3000
npm run typecheck && npm run build
```

Publicación de runs (desde la raíz):

```bash
/tmp/opencode/trading-venv/bin/python scripts/aaa_web_sync/sync.py --file reports/YYYY-MM-DD/candidates.json
AAA_CAPITAL=10000 ./scripts/aaa_web_sync/daily.sh
```

`sync.py` necesita `AAA_WEB_URL` y `AAA_INGEST_TOKEN`; `--dry-run` valida sin enviar. `daily.sh` encadena `main.py plan` y la sincronización. Los secretos van en `aaa-web/.env.local` (ignorado) o en las variables de Vercel.

Resto:

```bash
python scripts/convert_tickers/convert_tickers.py          # desde la raíz
python scripts/screener/finviz-py/smart_screener.py        # desde su carpeta
python scripts/extracciones/script.py --input-dir ... --output ...
```

Los bots se arrancan con `python app.py` desde su carpeta y los backtests con `python src/backtest.py` (también requieren MT5). `MA_RSI_Bot/test.py` no es un test de pytest: es un script manual que se conecta a MT5.

## Validación

No hay lint ni CI. La suite de AAA (28 tests, sin red) y el typecheck/build de la web son la validación principal:

```bash
/tmp/opencode/trading-venv/bin/python -m unittest discover -s strategies/aaa/tests
cd aaa-web && npm run typecheck && npm run build
```

Valida el resto ejecutando el script afectado:

- Python sin dependencias: `python3 -m py_compile <archivo>` (solo sintaxis).
- `read_data_xtb.py` no necesita red, pero reescribe los CSV versionados; comprueba los conteos `✔ Trades guardados`/`✔ Cash guardados` y revisa el diff.
- `vcp_scanner`, los screeners y AAA necesitan red (yfinance/Finviz) y reescriben `output/` o `reports/`.
- `aaa-web`: con Postgres local, aplica migraciones y prueba login, dashboard, candidatos y detalle; publica un run con `sync.py` y reenvíalo para confirmar que no duplica. `sync.py --dry-run` valida el payload sin red.
- Bots MT5: no ejecutables aquí; valida por inspección o en Windows.

## Trampas

- `.gitignore` raíz cubre `__pycache__/`, `*.pyc`, `.venv/`, `env/` y `strategies/aaa/.cache/`, pero hay `.pyc` versionados de antes. `aaa-web/` tiene su propio `.gitignore` (`node_modules`, `.next`, `.env*`). No añadas venvs, `__pycache__`, `node_modules` ni CSV generados nuevos sin necesidad.
- Los artefactos generados están versionados y suelen aparecer modificados (`strategies/vcp_scanner/output/*`, `input/tickers.txt`, `Trades-XTB/data/*.csv`, `Data/*.xlsx`, `.pbix`). No hagas `git checkout -- .`, `reset` ni `clean`: hay trabajo local sin commit. Revierte solo lo que haya producido tu cambio y avísalo.
- `scripts/stock-analysis-project/src/conf/local-config.json` contiene una API key de Finnhub **committed**. No la copies, imprimas ni uses en archivos nuevos; muévela a entorno y rótala si tocas esa zona.
- `Trades-XTB/data/` y `scripts/extracciones/temp/` contienen números de cuenta y movimientos reales. No los incluyas en logs, fixtures, ejemplos ni commits.
- `Data/~$*.xlsx` son archivos de bloqueo de Excel, no datos; no los restaures.
- `scripts/stock-analysis-project` no compila tal cual: falta `@types/node` (usa `fs`, `path`, `__dirname`) y las rutas `../../conf`/`../conf` no apuntan a `src/conf` tras compilar a `dist/`. No pierdas tiempo intentando `npm start` sin arreglarlo.
- `strategies/aaa` es una **aproximación configurable** a los tres pilares públicos de CDI, no una reproducción del método privado. No presentes sus salidas como "Setup AAA oficial de CDI". El AAA se lee como tres preguntas en orden: mercado (alcista/lateral/bajista), sector y acción frente a su propio sector (`rs_sector21/63`; puerta A2 configurable con `require_sector_rs`). Si cambias umbrales, hazlo en `config/aaa.json` y actualiza `PLAYBOOK.md`.
- Los 7 presets de `src/finviz_presets.py` replican `Docs/Finviz screener swing.pdf`. `Sales growth ttm` se inyecta en `finvizfinance` porque esa versión no la lista; no la elimines sin comprobar que la librería ya la soporta.
- AAA solo genera señales y reportes. Los agentes no deben enviar órdenes ni tocar MT5/XTB. `aaa` escribe solo en `reports/`; los especialistas son de solo lectura.
- yfinance intradía (5m/1m) puede estar retrasado: el modo day es research/paper, no un feed de ejecución. Si faltan datos, el estado correcto es `sin datos`/`Descartado`, no una suposición.
- `strategies/aaa/.cache/fundamentals.json` se regenera solo y está ignorado; no lo versiones.
- La contraseña de `aaa-web` va como hash bcrypt en **base64** (`APP_PASSWORD_HASH_B64`): Next interpreta los `$` del hash crudo como variables en `.env`. No commitees `aaa-web/.env.local`. El servidor de desarrollo local puede compartir el puerto 3000 con otro proyecto: usa `PORT=3100` si está ocupado, no mates procesos ajenos.
- `aaa-web` no calcula señales ni habla con el motor: solo consume `candidates.json` vía `/api/ingest` con `AAA_INGEST_TOKEN`. No añadas scraping ni ejecución de órdenes en la web.
- `scripts/aaa_web_sync/seed_from_csv.py` genera un payload **aproximado** para reportes históricos sin `candidates.json`; no recalcula señales ni sustituye al motor. Los runs sembrados pueden tener `metrics` incompletas.
- `MEMORY.md` sigue siendo una plantilla con `PENDIENTE`; no lo uses como fuente de verdad. Si actualizas estado, hazlo con hechos verificados.

## Reglas de trabajo

- No introduzcas frameworks, capas ni dependencias compartidas: cada carpeta es un script/proyecto autónomo.
- No commitees secretos ni datos personales; no ejecutes operaciones de git destructivas.
- Si cambias el scoring, el esquema de columnas o los filtros, regenera las salidas afectadas o indica explícitamente que quedan pendientes.
- Al terminar, informa qué se ejecutó realmente y qué no (p. ej. "no validado: requiere MT5/Windows").
