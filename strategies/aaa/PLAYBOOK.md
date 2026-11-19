# Playbook AAA-CDI

Sistema de apoyo a decisiones para acciones de EE. UU. No ejecuta órdenes.
No es una reproducción oficial del método privado de El Club de Inversionistas
(CDI); es una implementación configurable de sus tres pilares públicos.

## 1. Las tres preguntas

AAA se lee de arriba abajo, en este orden. Si una pregunta falla, no hay setup.

1. **Mercado**: ¿está alcista, bajista o lateral? Se lee de SPY y QQQ contra
   SMA50 y SMA200. El VIX decide el riesgo permitido, no la dirección.
2. **Sector**: ¿el grupo al que pertenece la acción aguanta? ETF del sector
   contra SMA50/SMA200 y su fuerza relativa frente a SPY.
3. **Acción frente a su propio sector**: ¿la acción lidera a su sector o solo
   sube con él? Fuerza relativa de la acción contra el ETF de su sector a 1 y 3
   meses.

Un setup es **AAA** solo si cumple las tres puertas. La puntuación ordena
candidatos, pero no compensa un pilar fallido.

### A1. Mercado y sector

- Mercado: SPY y QQQ por encima de SMA50 y SMA200; tendencia distinta de
  bajista.
- Sector: ETF del sector por encima de SMA50/SMA200 y con fuerza relativa
  positiva frente a SPY.
- Acción: precio > SMA50 > SMA200 y pendiente positiva de SMA200.

### A2. Acción frente a SPY y a su sector

- Fuerza relativa positiva vs SPY en 1 y 3 meses.
- Fuerza relativa positiva vs el ETF de su sector a 1 mes (puerta configurable
  con `require_sector_rs`, activada por defecto). Si el run no trae datos del
  sector, esta condición no penaliza.
- A ≤15% del máximo de 52 semanas.
- Volumen relativo ≥1.5 en la ruptura.
- Proxy de Momentum List / CAN SLIM: crecimiento de EPS y ventas, ROE,
  márgenes positivos y, para inversión, deuda controlada.

### A3. Entrada clara y riesgo

- Base, bandera, VCP o pullback identificable.
- Pivote o nivel de invalidación evidente.
- Stop técnico, no arbitrario.
- R/R mínimo 2.0 para swing.
- Earnings fuera de la ventana.
- Riesgo por operación: 0.5% del capital.

## 2. Régimen de mercado

| Condición | Lectura |
|---|---|
| SPY y QQQ > SMA50 y SMA200; VIX < 25 | Risk-on: se permiten setups AAA |
| Índices sobre SMA50 pero no sobre SMA200 | Neutral: solo A+ y media posición |
| Índices bajo SMA50 o VIX ≥ 25 | Risk-off: no abrir nuevos largos |

La **tendencia** (alcista/lateral/bajista) sale de la estructura de los índices:
alcista si todos están sobre SMA50 y SMA200; bajista si todos perdieron SMA200;
lateral en el resto. Es independiente del régimen: el régimen mide cuánto riesgo
se permite, la tendencia mide hacia dónde va el mercado. Ambos se evalúan una
vez por sesión y se escriben en el reporte.

## 3. Universo

- Solo acciones comunes de EE. UU.; sin ETFs, OTC ni penny stocks.
- Swing: precio > $10, volumen medio > 1M, market cap > $2B.
- Day: precio > $5, volumen medio > 2M.
- Inversión: precio > $10, volumen medio > 500K, empresa rentable.
- Excluir earnings dentro de la ventana indicada en la config.

## 4. Modos

### Swing (núcleo CDI)

- Horizonte: 2–15 días.
- Entrada: ruptura de pivote de 20 días o pullback a SMA20/SMA50.
- Stop: mínimo de 10 días o 1.5 ATR, el que quede más cerca sin superar 8%.
- Objetivo: 2.5R.
- Salida: 2R parcial, trailing o tiempo máximo 15 días.
- Earnings: no mantener dentro de los 5 días previos.

### Inversión

- Horizonte: 3–12 meses.
- Puerta de calidad obligatoria: ROE, margen neto, crecimiento de EPS/ventas,
  deuda (excepto financieras) y rentabilidad.
- Valoración: PEG, P/FCF y EV/EBITDA como score, no como verdad absoluta.
- Compra escalonada en zona de valor; stop de tesis y revisión trimestral.

### Day

- Horizonte: misma sesión.
- Universo desde Finviz; confirmación con yfinance 5m/1m.
- Entrada: ruptura de máximo premarket o reclaim de VWAP.
- Stop: mínimo premarket o 1 ATR; objetivo 2R.
- Cierre antes de 15:55 ET. Sin overnight.
- yfinance puede tener retraso: solo research y paper trading.

## 5. Puntuación

Cada modo calcula 0–100 con tres bloques:

| Modo | Alineación | Fortaleza | Entrada/riesgo |
|---|---|---|---|
| Swing | 35% | 40% | 25% |
| Day | 25% | 45% | 30% |
| Inversión | 15% (tendencia) | 60% (calidad + crecimiento + valor) | 25% (zona/riesgo) |

Estados:

- **AAA listo / Core**: todas las puertas duras y score ≥ umbral.
- **Vigilancia / Watch**: puertas duras OK pero falta gatillo o score.
- **Descartado / Reject**: falla una puerta dura.

## 6. Riesgo

- Riesgo por operación: 0.5% del capital.
- Riesgo abierto máximo: 2%.
- Máximo 2 posiciones por sector y 6 en swing.
- Tamaño = (capital × riesgo%) / (entrada − stop).
- Sin stop no hay operación.
- Si el stop implica un tamaño menor a 1 acción, no se opera.

## 7. Datos y calidad

- Finviz: screeners y fundamentales; datos pueden ser de fin de día.
- yfinance: OHLCV diario e intradía; puede estar retrasado.
- Cada candidato debe llevar timestamp de la última barra.
- Si falta un dato crítico, se marca `sin datos` y no se convierte en certeza.
- No se inventan precios, earnings, fundamentales ni noticias.

## 8. Reporte

`reports/YYYY-MM-DD/plan.md` contiene régimen, riesgo, watchlists y descartes.
Los CSV y la watchlist de TradingView se generan en la misma carpeta.

Cada fila debe incluir: ticker, sector, score, estado, setup, entrada, stop,
objetivo, R/R, tamaño, earnings y motivos.

## 9. Reglas de oro

1. Primero el régimen; después el sector; después la acción.
2. Sin alineación no hay AAA, aunque el gráfico parezca perfecto.
3. No se persigue el precio: si está extendido, se espera.
4. No se promedia a la baja.
5. No se opera por impulso ni por noticia no verificada.
6. El plan se escribe antes de la sesión; el journal después.
7. Los agentes proponen; la ejecución es humana.
