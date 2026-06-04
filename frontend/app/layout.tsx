import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AEONID Brain OS",
  description: "AEONID AI 견적 분석 시스템",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-slate-900 font-sans text-white">
        <header className="border-b border-slate-700 px-6 py-4">
          <h1 className="text-xl font-bold text-blue-400">AEONID Brain OS</h1>
        </header>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
