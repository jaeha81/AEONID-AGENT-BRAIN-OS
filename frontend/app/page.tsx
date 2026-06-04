import Link from "next/link";

export default function Home() {
  return (
    <div className="mx-auto mt-12 max-w-2xl">
      <h2 className="mb-2 text-2xl font-bold">AEONID Brain OS</h2>
      <p className="mb-8 text-slate-400">
        AI 기반 견적 분석, 공정 분류, 실행예산 생성을 위한 로컬 운영 대시보드입니다.
      </p>
      <div className="grid grid-cols-1 gap-4">
        <Link
          href="/estimates"
          className="block rounded-xl border border-slate-700 bg-slate-800 p-6 transition-colors hover:border-blue-500"
        >
          <h3 className="mb-1 text-lg font-semibold text-blue-400">견적 분석</h3>
          <p className="text-sm text-slate-400">
            PDF 또는 XLSX 견적서를 업로드하고 공정별 실행예산을 생성합니다.
          </p>
        </Link>
      </div>
    </div>
  );
}
