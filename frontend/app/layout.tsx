import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AEONID Brain OS",
  description: "이언아이디 AI 견적 분석 시스템",
  manifest: "/manifest.json",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className={`${inter.className} bg-slate-900 text-white min-h-screen`}>
        <header className="border-b border-slate-700 px-6 py-4">
          <h1 className="text-xl font-bold text-blue-400">AEONID Brain OS</h1>
        </header>
        <main className="p-6">{children}</main>
      </body>
    </html>
  );
}
