import type { Metadata } from "next";

import { login } from "./actions";

export const metadata: Metadata = {
  title: "Entrar · AAA",
};

type LoginPageProps = {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

const ERRORS: Record<string, string> = {
  "1": "La contraseña no es correcta.",
  config:
    "Falta configurar AUTH_SECRET y APP_PASSWORD_HASH (o APP_PASSWORD) en el entorno.",
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const errorKey = typeof params.error === "string" ? params.error : "";
  const error = ERRORS[errorKey];

  return (
    <main className="grid min-h-svh lg:grid-cols-[1.15fr_0.85fr]">
      <section className="relative flex flex-col justify-between overflow-hidden border-b border-line bg-panel px-6 py-10 sm:px-10 lg:border-b-0 lg:border-r lg:px-14 lg:py-14">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_10%,rgba(210,140,76,0.14),transparent_45%)]" />
        <div className="relative">
          <p className="font-mono text-xs tracking-[0.18em] text-copper">AAA · CDI</p>
          <h1 className="mt-8 max-w-xl font-display text-6xl leading-[0.92] tracking-tight text-paper sm:text-7xl">
            Primero el mercado. Después el sector.
          </h1>
          <p className="mt-6 max-w-md text-base leading-relaxed text-muted">
            Mesa de señales para el plan diario. Mercado, sector y acción frente
            a su propio sector. Sin órdenes, sin promesas de rentabilidad.
          </p>
        </div>

        <div className="relative mt-14 grid max-w-xl grid-cols-3 gap-px border border-line bg-line">
          {[
            ["01", "Mercado", "¿Alcista, bajista o lateral? Los índices mandan."],
            ["02", "Sector", "¿El grupo de la acción aguanta o se cae?"],
            ["03", "Acción vs sector", "¿Lidera a su propio sector o solo sube con él?"],
          ].map(([tag, title, copy]) => (
            <article key={tag} className="bg-canvas p-4">
              <span className="font-mono text-[11px] text-copper">{tag}</span>
              <h2 className="mt-3 font-display text-xl text-paper">{title}</h2>
              <p className="mt-2 text-xs leading-relaxed text-muted">{copy}</p>
            </article>
          ))}
        </div>

        <p className="relative mt-10 max-w-md text-xs leading-relaxed text-muted">
          Aproximación configurable a los tres pilares públicos de CDI. No es
          asesoría financiera y no ejecuta operaciones.
        </p>
      </section>

      <section className="flex items-center px-6 py-12 sm:px-10 lg:px-16">
        <div className="w-full max-w-sm">
          <p className="font-mono text-xs text-muted">Acceso restringido</p>
          <h2 className="mt-3 font-display text-4xl tracking-tight text-paper">
            Entrar a la mesa
          </h2>

          <form action={login} className="mt-10 space-y-6">
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-paper"
              >
                Contraseña
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                autoFocus
                className="mt-2 h-12 w-full border border-line bg-panel px-3 font-mono text-base text-paper outline-none transition-colors placeholder:text-muted/50 focus:border-copper"
                placeholder="••••••••••••"
              />
            </div>

            {error ? (
              <p
                role="alert"
                className="border-l-2 border-down bg-down/10 px-3 py-2 text-sm text-down"
              >
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              className="h-12 w-full border border-copper bg-copper px-4 font-medium text-canvas transition-colors hover:bg-paper hover:border-paper focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-copper"
            >
              Entrar
            </button>
          </form>

          <p className="mt-8 text-xs leading-relaxed text-muted">
            Sesión privada de un solo usuario. La cookie se firma con
            AUTH_SECRET y caduca a los 30 días.
          </p>
        </div>
      </section>
    </main>
  );
}
