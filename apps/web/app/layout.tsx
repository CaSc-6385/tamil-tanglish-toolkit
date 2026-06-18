import type { Metadata } from "next";
import { Inter, Noto_Sans_Tamil } from "next/font/google";
import type { ReactNode } from "react";

import "./globals.css";

// Self-hosted via next/font — fixes the flaky Google-Fonts @import so Tamil always
// renders in Noto Sans Tamil instead of a tofu/fallback system face.
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const notoTamil = Noto_Sans_Tamil({
  subsets: ["tamil", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-tamil",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AOST Tamil — Tanglish → Tamil for kids",
  description:
    "Type Tanglish like vanakkam and get correct Tamil like வணக்கம். Built for kids learning Tamil.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${notoTamil.variable}`}>
      <body className="min-h-screen font-sans antialiased">{children}</body>
    </html>
  );
}
