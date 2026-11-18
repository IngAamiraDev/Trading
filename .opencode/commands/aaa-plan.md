---
description: Genera el plan AAA del dia (swing, inversión y day) y lo escribe en reports/.
agent: aaa
---

Genera el plan AAA-CDI del dia. $ARGUMENTS

Pasos:

1. Lee `strategies/aaa/PLAYBOOK.md` y `strategies/aaa/config/aaa.json`.
2. Ejecuta el motor:
   `/tmp/opencode/trading-venv/bin/python strategies/aaa/main.py plan --capital 10000`
   Si el usuario indica otro capital en `$ARGUMENTS`, usalo.
3. Si el régimen es `risk_off`, no presentes entradas nuevas: solo vigilancia.
4. Delega en `aaa-swing`, `aaa-invest` y `aaa-day` si necesitas detalle
   adicional. Usa `aaa-risk` para validar tamaños y `aaa-auditor` antes de
   cerrar si hay dudas.
5. Consolida un único plan en espanol y confirma que se escribio en
   `reports/YYYY-MM-DD/plan.md`, `candidates.csv` y
   `watchlist_tradingview.txt`.

Devuelve un resumen ejecutivo: régimen, presupuesto de riesgo, mejores
candidatos por modo y descartes importantes. No prometas rentabilidad y no
presentes esto como el método oficial de CDI.
