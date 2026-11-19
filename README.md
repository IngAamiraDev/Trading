# Trading

Repositorio personal de trading: ingestas de datos, screeners, bots y una mesa de
señales web. Cada carpeta es un proyecto autónomo con su propio README y sus
propias dependencias.

| Carpeta | Qué es |
|---|---|
| `strategies/aaa/` | Motor AAA-CDI (aproximación configurable): régimen, candidatos y plan diario. |
| `aaa-web/` | Mesa de señales web (Next.js + Postgres) que consume los runs del motor. |
| `scripts/aaa_web_sync/` | Publicación de `candidates.json` en la web y cron diario. |
| `strategies/vcp_scanner/` | Screener VCP. |
| `Trades-XTB/` | Ingesta de exportes de XTB y dashboard Power BI. |
| `scripts/bot-scripts/` | Bots live para MetaTrader 5 (Windows). |
| `scripts/screener/`, `scripts/extracciones/` | Screeners sueltos y extracción de movimientos. |

## Un Setup AAA:

¿Cómo está el mercado en general: alcista, bajista o lateral?
¿Cómo está el sector o grupo al que pertenece la acción?
¿Cómo se comporta la acción en comparación con su propio sector?

Contexto operativo y trampas del entorno en `AGENTS.md`.

[Market Tide](https://unusualwhales.com/flow/overview)
