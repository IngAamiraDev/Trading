# AAA Web

Mesa de señales del motor AAA: mercado, sector y acción frente a su sector,
con candidatos, niveles y riesgo. Solo señales; no envía órdenes ni se conecta a
MT5/XTB.

Next.js 16 (App Router) + TypeScript + Tailwind v4 + Drizzle ORM sobre Postgres
(Neon en producción).

## Estructura

```
app/
  (app)/                 rutas protegidas: dashboard, candidatos, detalle
  api/ingest/            POST idempotente que publica un run
  api/export/            CSV de candidatos y watchlist de TradingView
  login/                 formulario y server actions de sesión
components/              tabla, régimen, escalera de precios, badges
lib/
  auth.ts                JWT en cookie (jose) + contraseña bcrypt
  db/schema.ts           scan_runs, regime_indices, candidates
  db/queries.ts          consultas de dashboard y detalle
  ingest-schema.ts       validación Zod del payload
drizzle/                 migraciones SQL versionadas
proxy.ts                 protección de rutas (equivalente a middleware)
```

## Variables de entorno

Copia `.env.example` a `.env.local` en desarrollo. En Vercel se configuran en
Project → Settings → Environment Variables.

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Postgres/Neon. En Neon usa la cadena *pooled*. |
| `AUTH_SECRET` | 32+ bytes aleatorios para firmar la cookie. |
| `APP_PASSWORD_HASH_B64` | Hash bcrypt de la contraseña, en base64. |
| `APP_PASSWORD` | Alternativa en claro solo para desarrollo local. |
| `AAA_INGEST_TOKEN` | Token Bearer que usa `scripts/aaa_web_sync/sync.py`. |

El hash va en base64 porque Next interpreta `$` en `.env` como variable. Para
generarlo:

```bash
node -e "console.log(Buffer.from(require('bcryptjs').hashSync(process.argv[1], 12)).toString('base64'))" 'tu-password'
```

## Desarrollo local

```bash
cd aaa-web
npm install
cp .env.example .env.local   # rellena los valores
npm run db:migrate
npm run dev
```

Scripts:

- `npm run dev` / `build` / `start`
- `npm run typecheck`
- `npm run db:generate` (nueva migración tras cambiar el esquema)
- `npm run db:migrate` (aplica migraciones)
- `npm run db:studio`

## Ingesta

`POST /api/ingest` recibe el `candidates.json` que escribe el motor y exige
`Authorization: Bearer $AAA_INGEST_TOKEN`. El `run_id` (UUID) es la clave: si
se reenvía el mismo run, se reemplazan sus filas en una transacción; no se
duplica.

```bash
python scripts/aaa_web_sync/sync.py --file reports/2026-11-17/candidates.json
```

`sync.py` toma `AAA_WEB_URL` y `AAA_INGEST_TOKEN` del entorno o de `--url` /
`--token`. `--dry-run` valida el JSON sin enviarlo.

## Despliegue en Vercel + Neon

1. Crea el proyecto en Neon y copia la cadena **pooled** como `DATABASE_URL`.
2. Importa el repositorio en Vercel y fija el *Root Directory* en `aaa-web`.
3. Añade las variables de entorno de la tabla anterior (Production y Preview).
4. Aplica las migraciones contra Neon desde local:

   ```bash
   cd aaa-web
   DATABASE_URL="postgresql://...neon.tech/aaa_web?sslmode=require" npm run db:migrate
   ```

5. Despliega. Comprueba `/login`, publica un run con `sync.py` y verifica que
   el dashboard lo muestra.
6. Programa el plan diario donde esté el motor (cron o Programador de tareas):

   ```cron
   CRON_TZ=America/New_York
   30 8 * * 1-5  /ruta/al/repo/scripts/aaa_web_sync/daily.sh >> /ruta/al/repo/logs/aaa.log 2>&1
   ```

`daily.sh` ejecuta `main.py plan` y publica el resultado del día. Si el plan
falla, no se envía nada y la web conserva el último run (marcado como antiguo
pasadas 36 h).

## Modelo de datos

- `scan_runs` — una fila por ejecución (`id` = `run_id`), con régimen, tendencia
  (`alcista`/`lateral`/`bajista`), VIX, capital, líderes, errores y notas. Si un
  run antiguo no trae `trend`, la web lo deduce de los índices.
- `regime_indices` — cierre, SMA50/SMA200 y posición de cada índice.
- `candidates` — una fila por `(run, modo, ticker)` con score, puertas, niveles,
  motivos y métricas JSON.

## Lectura AAA en pantalla

El detalle de cada candidato abre con las tres preguntas, en orden:

1. **01 · Mercado** — tendencia (alcista/lateral/bajista) y régimen (cuánto
   riesgo se permite).
2. **02 · Sector** — estado del sector de la acción (`fuerte`/`lateral`/`débil`)
   y su fuerza relativa frente a SPY.
3. **03 · Acción vs sector** — fuerza relativa de la acción frente a su propio
   sector a 1 y 3 meses, y frente a SPY.

Las puertas se leen con el mismo criterio: `A1` mercado y sector, `A2` la acción
contra SPY y contra su sector, `A3` entrada y riesgo. Cuando el motor marca
`extreme_move`, la serie tiene un salto extremo y la UI lo dice en vez de
mostrar una fuerza relativa falsa.

## Límites

- Un solo usuario: no hay registro ni multi-tenant.
- La web no calcula señales: solo muestra lo que publica el motor.
- Los datos de Finviz/yfinance pueden llegar incompletos; la UI muestra `—` y
  no rellena huecos.
- AAA-CDI es una aproximación configurable, no el método privado de CDI ni
  asesoría financiera.
