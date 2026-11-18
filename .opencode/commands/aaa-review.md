---
description: Analiza un ticker concreto con los tres modos AAA.
agent: aaa
---

Analiza el ticker `$ARGUMENTS` con el motor AAA.

1. Ejecuta:
   `/tmp/opencode/trading-venv/bin/python strategies/aaa/main.py review $ARGUMENTS --no-write`
2. Presenta, por modo:
   - Estado y score.
   - Puertas A1/A2/A3 con el motivo de cada fallo.
   - Setup, entrada, stop, objetivo, R/R, riesgo % y earnings.
3. Si el usuario pide solo un modo, ejecuta `--mode swing|invest|day`.
4. Si faltan datos, dilo; no rellenes huecos con suposiciones.

No escribas archivos salvo que el usuario lo pida. No envíes órdenes.
