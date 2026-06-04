"use client";

import { useRef, useState } from "react";
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
    const allowed = [".pdf", ".xlsx"];
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!allowed.includes(ext)) {
      setError("PDF 또는 XLSX 파일만 업로드할 수 있습니다.");
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
      setError(e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다.");
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
    <div className="mx-auto max-w-2xl">
      <h2 className="mb-6 text-xl font-bold">견적서 업로드</h2>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-12 text-center transition-colors ${
          dragging ? "border-blue-400 bg-blue-400/10" : "border-slate-600 hover:border-slate-400"
        } ${uploading ? "pointer-events-none opacity-50" : ""}`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.xlsx"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        {uploading ? (
          <div>
            <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
            <p className="text-slate-300">AI가 견적서를 분석 중입니다.</p>
            <p className="mt-1 text-sm text-slate-500">항목 추출, 공정 분류, 실행예산 생성</p>
          </div>
        ) : (
          <div>
            <p className="mb-2 text-lg text-slate-300">
              견적서를 드래그하거나 클릭하여 업로드하세요.
            </p>
            <p className="text-sm text-slate-500">지원 형식: PDF, XLSX</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-700 bg-red-900/50 p-4 text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}
