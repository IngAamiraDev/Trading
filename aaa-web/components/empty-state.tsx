import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <section className="border border-dashed border-line bg-panel/40 px-6 py-14">
      <p className="font-mono text-[11px] tracking-[0.14em] text-copper">
        Sin datos
      </p>
      <h1 className="mt-3 font-display text-4xl tracking-tight text-paper">
        {title}
      </h1>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted">
        {description}
      </p>
      {children ? <div className="mt-6">{children}</div> : null}
    </section>
  );
}
