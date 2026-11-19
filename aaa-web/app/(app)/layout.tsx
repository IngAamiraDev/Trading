import Link from "next/link";
import { redirect } from "next/navigation";

import { logout } from "@/app/login/actions";
import { NavLinks } from "@/components/nav-links";
import { getSession } from "@/lib/auth";

export default async function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const session = await getSession();
  if (!session) {
    redirect("/login");
  }

  return (
    <div className="min-h-svh lg:grid lg:grid-cols-[220px_minmax(0,1fr)]">
      <aside className="sticky top-0 hidden h-svh flex-col border-r border-line bg-panel/50 px-4 py-6 lg:flex">
        <Link href="/" className="block px-3">
          <span className="font-display text-4xl leading-none tracking-tight text-paper">
            AAA
          </span>
          <span className="mt-1 block font-mono text-[10px] tracking-[0.18em] text-copper">
            MESA DE SEÑALES
          </span>
        </Link>

        <div className="mt-10">
          <p className="px-3 font-mono text-[10px] tracking-[0.16em] text-muted">
            Sesión
          </p>
          <div className="mt-2">
            <NavLinks orientation="vertical" />
          </div>
        </div>

        <div className="mt-auto space-y-4 border-t border-line pt-4">
          <p className="px-3 text-[11px] leading-relaxed text-muted">
            Aproximación configurable a los tres pilares públicos de CDI. Solo
            señales; la ejecución es humana.
          </p>
          <form action={logout} className="px-3">
            <button
              type="submit"
              className="text-xs text-muted underline-offset-4 transition-colors hover:text-paper hover:underline"
            >
              Cerrar sesión
            </button>
          </form>
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-20 border-b border-line bg-canvas/90 backdrop-blur">
          <div className="flex h-14 items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-4 lg:hidden">
              <Link href="/" className="font-display text-2xl tracking-tight text-paper">
                AAA
              </Link>
              <NavLinks />
            </div>
            <p className="hidden font-mono text-[11px] text-muted lg:block">
              Plan diario · datos de Finviz y yfinance
            </p>
            <div className="flex items-center gap-3">
              <span className="hidden font-mono text-[11px] text-muted sm:inline">
                Sesión privada
              </span>
              <form action={logout} className="lg:hidden">
                <button
                  type="submit"
                  className="text-xs text-muted underline-offset-4 hover:text-paper hover:underline"
                >
                  Salir
                </button>
              </form>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1500px] flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          {children}
        </main>

        <footer className="border-t border-line px-4 py-5 sm:px-6 lg:px-8">
          <p className="mx-auto max-w-[1500px] text-[11px] leading-relaxed text-muted">
            AAA-CDI es una aproximación configurable, no el método privado de El
            Club de Inversionistas. No ejecuta órdenes, no promete rentabilidad
            y no es asesoría financiera. Si falta un dato, se muestra como
            ausente.
          </p>
        </footer>
      </div>
    </div>
  );
}
