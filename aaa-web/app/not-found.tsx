import Link from "next/link";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-svh max-w-2xl flex-col justify-center px-6 py-16">
      <p className="font-mono text-[11px] tracking-[0.18em] text-copper">404</p>
      <h1 className="mt-4 font-display text-6xl leading-none tracking-tight text-paper">
        Fuera del mapa.
      </h1>
      <p className="mt-4 max-w-md text-sm leading-relaxed text-muted">
        Esta ruta no existe. Vuelve al plan de la sesión o a la lista de
        candidatos.
      </p>
      <div className="mt-8 flex flex-wrap gap-2">
        <Link
          href="/"
          className="border border-copper bg-copper px-4 py-2 text-sm font-medium text-canvas transition-colors hover:border-paper hover:bg-paper"
        >
          Ir al plan
        </Link>
        <Link
          href="/candidatos"
          className="border border-line bg-panel px-4 py-2 text-sm text-paper transition-colors hover:border-copper hover:text-copper"
        >
          Ver candidatos
        </Link>
      </div>
    </main>
  );
}
