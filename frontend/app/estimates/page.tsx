"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

interface UploadResult {
  id: number;
  site_name: string;
  status: string;
  total_amount: number;
}

export default function EstimatesPage() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleFile = async (file: File) => {
    const allowed = [".pdf", ".xlsx", ".xls"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowed.includes(ext)) {
      setError("PDF 또는 Excel 파일만 업로드 가능합니다");
      return;
    }

    setUploading(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("/api/estimates/upload", { method: "POST", body: form });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "업로드 실패");
      }
      const result: UploadResult = await res.json();
      router.push(`/estimates/${result.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "알 수 없는 오류");
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-xl font-bold mb-6">견적서 업로드</h2>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          dragging ? "border-blue-400 bg-blue-400/10" : "border-slate-600 hover:border-slate-400"
        } ${uploading ? "opacity-50 pointer-events-none" : ""}`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.xlsx,.xls"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        {uploading ? (
          <div>
            <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-slate-300">AI가 견적서를 분석 중입니다...</p>
            <p className="text-slate-500 text-sm mt-1">항목 추출 → 공정 분류 → 실행예산 생성</p>
          </div>
        ) : (
          <div>
            <p className="text-slate-300 text-lg mb-2">견적서를 드래그하거나 클릭하여 업로드</p>
            <p className="text-slate-500 text-sm">지원 형식: PDF, Excel (.xlsx, .xls)</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-900/50 border border-red-700 rounded-lg text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}
