import type { ReactNode } from "react";

export function SectionHeader({
  title,
  description,
  meta,
  action,
}: {
  title: string;
  description?: string;
  meta?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3 border-b border-line pb-3">
      <div className="flex items-start gap-3">
        <span className="mt-2 h-3 w-1 shrink-0 bg-copper" aria-hidden="true" />
        <div>
          <h2 className="font-display text-3xl leading-none tracking-tight text-paper">
            {title}
          </h2>
          {description ? (
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">
              {description}
            </p>
          ) : null}
        </div>
      </div>
      <div className="flex items-center gap-3 text-xs text-muted">
        {meta}
        {action}
      </div>
    </div>
  );
}
