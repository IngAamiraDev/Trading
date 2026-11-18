---
description: Compara el plan AAA con las operaciones reales de XTB y escribe el journal en reports/.
agent: aaa
---

Genera el journal de adherencia AAA-CDI. $ARGUMENTS

1. Localiza los reportes recientes en `reports/` y el histórico de operaciones
   en `Trades-XTB/data/trades_xtb.csv`.
2. Compara, por ticker y fecha:
   - Operaciones que estaban en el plan vs operaciones fuera del plan.
   - Respeto de entrada, stop y objetivo.
   - Riesgo real por operación frente al 0.5% configurado.
   - Resultado por R multiple cuando los datos lo permitan.
3. Calcula agregados: número de operaciones, adherencia %, R medio, win rate,
   expectancy y desviacion de riesgo. Si no hay datos suficientes, dilo.
4. Escribe `reports/YYYY-MM-DD/journal.md` con los hallazgos y tres acciones
   concretas de mejora.

Privacidad: no copies numeros de cuenta, saldos ni movimientos individuales
en el reporte. Usa solo agregados y tickers.

No prometas rentabilidad ni presentes el journal como asesoría financiera.
