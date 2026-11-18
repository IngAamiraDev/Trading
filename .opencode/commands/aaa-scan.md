---
description: Escanea un modo AAA (swing, invest o day) y resume los candidatos.
agent: aaa
---

Ejecuta un escaneo AAA-CDI. Parámetros: $ARGUMENTS

Interpreta `$ARGUMENTS` así:
- Vacio: `--mode swing`.
- `swing`, `invest` o `day`: ese modo.
- Un número: límite de candidatos para el modo swing.
- `swing 20`, `invest 10`, `day 8`: modo y límite.

Comando base:
`/tmp/opencode/trading-venv/bin/python strategies/aaa/main.py scan --mode <modo> --limit <N> --no-write`

Después del escaneo:

1. Ordena por score y separa accionables, vigilancia y descartados.
2. Explica por que cada accionable cumple A1/A2/A3.
3. Si el régimen es `risk_off`, dilo y no presentes entradas nuevas.
4. Senala errores de datos o presets vacios.

No escribas archivos en este comando. Devuelve una tabla compacta en espanol.
