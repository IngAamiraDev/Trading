import type { Metadata, Viewport } from "next";
import {
  Barlow_Condensed,
  IBM_Plex_Mono,
  IBM_Plex_Sans,
} from "next/font/google";

import "./globals.css";

const displayFace = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display-face",
  display: "swap",
});

const bodyFace = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-body-face",
  display: "swap",
});

const monoFace = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono-face",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AAA · Mesa de señales",
    template: "%s · AAA",
  },
  description:
    "Plan diario AAA-CDI: régimen, candidatos, niveles y riesgo. Solo señales.",
};

export const viewport: Viewport = {
  themeColor: "#0b1214",
  colorScheme: "dark",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body
        className={`${displayFace.variable} ${bodyFace.variable} ${monoFace.variable} font-sans`}
      >
        {children}
      </body>
    </html>
  );
}
