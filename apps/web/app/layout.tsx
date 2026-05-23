import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "AOST Tamil — Tanglish → Tamil for kids",
  description:
    "Type Tanglish like vanakkam and get correct Tamil like வணக்கம். Built for kids learning Tamil.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
