import { EmptyState } from "./empty-state";

export function DataUnavailable({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : String(error);

  return (
    <EmptyState
      title="No se pudo leer la base de datos"
      description="La app no encuentra una conexión válida a Postgres. Revisa DATABASE_URL y que las migraciones se hayan aplicado."
    >
      <details className="max-w-2xl border border-line bg-panel px-4 py-3 text-sm text-muted">
        <summary className="cursor-pointer text-paper">Detalle técnico</summary>
        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap font-mono text-xs text-down">
          {message}
        </pre>
      </details>
    </EmptyState>
  );
}
