"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Hoy" },
  { href: "/candidatos", label: "Candidatos" },
];

export function NavLinks({
  orientation = "horizontal",
}: {
  orientation?: "horizontal" | "vertical";
}) {
  const pathname = usePathname();
  const vertical = orientation === "vertical";

  return (
    <nav
      aria-label="Principal"
      className={
        vertical ? "flex flex-col gap-1" : "flex items-center gap-1"
      }
    >
      {LINKS.map((link) => {
        const active =
          link.href === "/"
            ? pathname === "/"
            : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            className={`relative text-sm transition-colors ${
              vertical
                ? `border-l-2 px-3 py-2 ${
                    active
                      ? "border-copper bg-raised/70 text-paper"
                      : "border-transparent text-muted hover:text-paper"
                  }`
                : `px-3 py-2 ${
                    active
                      ? "text-paper after:absolute after:inset-x-3 after:-bottom-px after:h-px after:bg-copper"
                      : "text-muted hover:text-paper"
                  }`
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
