import Link from "next/link";

export default function Home() {
  return (
    <div className="max-w-2xl mx-auto mt-12">
      <h2 className="text-2xl font-bold mb-2">안녕하세요, 이언아이디입니다</h2>
      <p className="text-slate-400 mb-8">AI 기반 견적 분석 시스템에 오신 것을 환영합니다</p>
      <div className="grid grid-cols-1 gap-4">
        <Link
          href="/estimates"
          className="block p-6 bg-slate-800 rounded-xl border border-slate-700 hover:border-blue-500 transition-colors"
        >
          <h3 className="text-lg font-semibold text-blue-400 mb-1">견적 분석</h3>
          <p className="text-slate-400 text-sm">PDF/Excel 견적서를 업로드하여 공정분리 및 실행예산을 자동 생성합니다</p>
        </Link>
      </div>
    </div>
  );
}
