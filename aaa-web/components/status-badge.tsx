import { statusTone } from "@/lib/format";

export function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap border px-2 py-0.5 font-mono text-[11px] leading-5 ${statusTone(
        status,
      )}`}
    >
      {status}
    </span>
  );
}
